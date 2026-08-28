#!/usr/bin/env python3
"""Jarvis Telegram bridge — agentic, streamed ack-then-work-in-background.

Long-polls Telegram. The poll loop NEVER blocks: each of Rob's messages is
queued and handled by a single background worker, so Telegram stays responsive
while a job runs. Each message is handed to an agentic `claude -p` run inside
the vault, streamed as `stream-json`. That run has full tools and
skip-permissions, so it actually DOES the work (edits code, runs commands,
pushes, updates the vault) end to end. The typing indicator carries the
"working" signal while the job runs; the final summary is sent once the work is
done. The up-front ack is the model's own streamed opening line, sent live as
it lands (Rob asked for natural voice over canned lines, 2026-08-21); a canned
fallback fires only if the model is slow to speak. Set JARVIS_ACK=0 to silence
acks entirely. The typing indicator is kept alive throughout. When it says it
did something, it did.

Continuity comes from a rolling conversation buffer fed into each prompt, not
from a persistent Claude process, so the whole thing survives a model swap and
stays cheap ("stateless engine, stateful memory").

Jobs are processed one at a time. A plain text message that lands while a job
is running is FOLDED INTO the live run (written to the running claude process
over stdin as a new user message, --input-format stream-json), so the model
sees it mid-work and adjusts, exactly like typing into Claude Code while it's
busy (Rob asked for this, 2026-08-24). Media messages (voice/photo/file) still
queue behind the current job with a holding line, since they need downloading
or transcribing first, as does anything that arrives once the run is past the
point of accepting input. The queue keeps two agentic runs from fighting over
the same git repo.

Config: ~/.config/jarvis/telegram.env  (TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_CHAT)
State:  ~/.local/state/jarvis-bridge/  (offset, conversation.log, bridge.log)
"""
import json
import os
import pathlib
import queue
import random
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.parse
import urllib.request

HOME = pathlib.Path.home()
CONF = HOME / ".config/jarvis/telegram.env"
STATE = HOME / ".local/state/jarvis-bridge"
VAULT = "/data/memory"
PROJECTS = "/home/jarvis/projects"
MODEL = os.environ.get("JARVIS_MODEL", "claude-fable-5")  # model that talks to Rob; override via JARVIS_MODEL in run.sh
# Usage-aware model choice: usage.sh reads the plan-usage endpoint and returns
# the model to use (drops to Opus 5 once the Fable weekly limit crosses 80%,
# Rob's "use the best tool but never hit the limits", 2026-08-21). Cached so we
# don't hit the endpoint on every message. JARVIS_MODEL_AUTO=0 pins MODEL.
USAGE_SH = f"{VAULT}/Jarvis/bin/usage.sh"
MODEL_AUTO = os.environ.get("JARVIS_MODEL_AUTO", "1") == "1"
MODEL_CACHE_TTL = 300
_model_cache = {"model": MODEL, "ts": 0.0}
BUFFER_TURNS = 16          # recent lines fed back for conversational continuity
CLAUDE_TIMEOUT = 900       # 15 min. Measured from bridge.log 2026-08-22: even on the
                           # heaviest days (57 replies, deep infra digs) p99 lands under
                           # 10 min, so 25 was just dead air on a genuinely wedged run.
ACK_ENABLED = os.environ.get("JARVIS_ACK", "1") == "1"  # stream the model's opening line as the ack (on by default since 2026-08-21; Rob wants natural voice, not canned)
ACK_GRACE = 25             # if the model hasn't spoken by now, send a canned ack so Rob has confirmation.
                           # Raised 15->25 (2026-08-24): the canned one-liners read as uncanny valley to Rob,
                           # so give the real streamed opening line every chance to win the race.
LONG_JOB_NOTICE = 30       # ack-off middle ground: if still working after this long and we've said nothing, drop ONE light "still on it" line
TYPING_EVERY = 4           # refresh the typing indicator this often while working
# Progress heartbeats on genuinely long runs. The ack tells Rob the run STARTED;
# nothing then tells him it's still alive, so a 10-min infra dig and a hung
# container look identical from the phone (exactly what happened 2026-08-21/22).
# These fire regardless of whether the ack went out, unlike LONG_JOB_NOTICE.
# Since 2026-08-24 each beat is a REAL progress summary, not a canned line: the
# worker run's tool calls are logged as they stream past, and a quick no-tools
# claude run turns that log into one natural "here's where I actually am" line
# (Rob: "still on it" is dead air, tell me what's happened so far). The canned
# line survives only as the fallback if the summarizer fails or comes back empty.
HEARTBEAT_AT = (180, 600)  # seconds into a run: 3 min, then 10 min
PROGRESS_MODEL = os.environ.get("JARVIS_PROGRESS_MODEL", "claude-sonnet-5")
PROGRESS_TIMEOUT = 75      # summarizer is a one-liner from a short log; if it can't do it in this, fall back
# Absolute path so it works under a minimal PATH too.
CLAUDE_BIN = shutil.which("claude") or str(HOME / ".local/bin/claude")
# Voice-note transcription: a standalone faster-whisper helper in its own venv,
# so bridge.py stays stdlib-only and the heavy ML dep is isolated. Local + CPU,
# no cloud key. See transcribe.py.
WHISPER_PY = HOME / ".local/share/jarvis-whisper/venv/bin/python"
TRANSCRIBE_PY = pathlib.Path(__file__).resolve().parent / "transcribe.py"
TRANSCRIBE_TIMEOUT = 300   # 5 min; a long note on 4 CPU cores still finishes well inside this

STATE.mkdir(parents=True, exist_ok=True)
OFFSET_FILE = STATE / "offset"
CONVO = STATE / "conversation.log"
LOG = STATE / "bridge.log"

JOBS = queue.Queue()
BUSY = threading.Event()          # set while a job is actively running
CONVO_LOCK = threading.Lock()     # serialise conversation.log appends
# The live run's fold-in hook: while an agentic run is streaming, CURRENT holds
# a callable that writes a new user message into that run's stdin. The poll
# loop uses it to fold Rob's mid-job texts into the run instead of queueing
# them behind a holding message.
CURRENT = {"inject": None, "chat": None}
CURRENT_LOCK = threading.Lock()


def load_conf():
    conf = {}
    for line in CONF.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            conf[k.strip()] = v.strip()
    return conf


CONF_D = load_conf()
TOKEN = CONF_D["TELEGRAM_BOT_TOKEN"]
# Rob's own chat: the only place /allow and /deny are honoured, and where new-contact
# notices go. TELEGRAM_ALLOWED_CHAT is the legacy name for the same thing.
ROB_CHAT = (CONF_D.get("TELEGRAM_ALLOWED_CHAT") or CONF_D.get("TELEGRAM_CHAT_ID") or "").strip()
API = f"https://api.telegram.org/bot{TOKEN}"

# Who may talk to me (added 2026-08-28 when Rob gave Aimee the bot link). Before this the
# bridge was effectively open to ANY Telegram user, each treated as Rob with full tools.
# Now: known chats map to a person {name, role}; role "rob" = full agentic Jarvis,
# "adult" = trusted family member (Aimee), "kid" = no tools, family-safe. Unknown chats get a
# polite hold + Rob gets a ping with the chat id; `/allow <id> <name> [role]` from Rob's chat
# lets them in and replays their first message, `/deny <id>` drops them.
PEOPLE_FILE = HOME / ".config/jarvis/telegram-people.json"
PEOPLE_LOCK = threading.Lock()
PENDING = {}   # chat_id(str) -> {"name", "username", "text", "voice", "photo", "doc"}


def load_people():
    people = {}
    if PEOPLE_FILE.exists():
        try:
            people = json.loads(PEOPLE_FILE.read_text())
        except Exception:
            people = {}
    if ROB_CHAT and ROB_CHAT not in people:
        people[ROB_CHAT] = {"name": "Rob", "role": "rob"}
    return people


def save_people(people):
    PEOPLE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PEOPLE_FILE.write_text(json.dumps(people, indent=2) + "\n")


PEOPLE = load_people()


def person_for(chat):
    with PEOPLE_LOCK:
        return PEOPLE.get(str(chat))


def log(msg):
    with LOG.open("a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}\n")


def api(method, params=None, timeout=65):
    data = urllib.parse.urlencode(params or {}).encode()
    req = urllib.request.Request(f"{API}/{method}", data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        log(f"api {method} error: {e}")
        return None


def send(chat, text):
    api("sendMessage", {"chat_id": chat, "text": (text[:4000] or "(empty reply)")}, timeout=30)


def typing(chat):
    api("sendChatAction", {"chat_id": chat, "action": "typing"}, timeout=15)


def tg_download(file_id, suffix=None):
    """Resolve a Telegram file_id to a download URL and pull it to a temp file.
    Returns the local path, or None on any failure. Pass `suffix` to force the
    saved file's extension (e.g. from a document's original file_name), since
    Telegram's own file_path often has no meaningful extension for documents."""
    r = api("getFile", {"file_id": file_id}, timeout=30)
    if not r or not r.get("ok"):
        return None
    fp = (r.get("result") or {}).get("file_path")
    if not fp:
        return None
    url = f"https://api.telegram.org/file/bot{TOKEN}/{fp}"
    if suffix is None:
        suffix = os.path.splitext(fp)[1] or ".oga"
    dst = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="jarvis-file-")
    try:
        with urllib.request.urlopen(url, timeout=90) as resp:
            shutil.copyfileobj(resp, dst)
        dst.close()
        return dst.name
    except Exception as e:
        log(f"tg_download error: {e}")
        try:
            dst.close()
            os.unlink(dst.name)
        except Exception:
            pass
        return None


def transcribe_voice(voice):
    """Download a voice/audio/video note and transcribe it locally. Returns the
    transcript text, or "" if anything fails or it's inaudible."""
    path = tg_download(voice["file_id"])
    if not path:
        return ""
    try:
        proc = subprocess.run(
            [str(WHISPER_PY), str(TRANSCRIBE_PY), path],
            capture_output=True, text=True, timeout=TRANSCRIBE_TIMEOUT,
        )
        if proc.returncode != 0:
            log(f"transcribe rc={proc.returncode} err={(proc.stderr or '')[-300:]}")
            return ""
        return proc.stdout.strip()
    except subprocess.TimeoutExpired:
        log("transcribe timeout")
        return ""
    except Exception as e:
        log(f"transcribe error: {e}")
        return ""
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def convo_file(person):
    # Rob keeps the original conversation.log; everyone else gets their own file, so
    # Aimee's thread never bleeds into Rob's continuity buffer (or vice versa).
    if not person or person.get("role") == "rob":
        return CONVO
    return STATE / f"conversation-{person['name'].lower()}.log"


def recent_buffer(person=None):
    f = convo_file(person)
    if not f.exists():
        return ""
    return "\n".join(f.read_text().splitlines()[-BUFFER_TURNS:])


def append_convo(line, person=None):
    # The human's turns carry a timestamp so a later run can see how old the buffer is
    # (a Monday-evening chat must not read as "tonight" on Tuesday morning).
    name = (person or {}).get("name", "Rob")
    if line.startswith(f"{name}: "):
        line = f"{name} [{time.strftime('%a %d %b %H:%M')}]: " + line[len(name) + 2:]
    with CONVO_LOCK:
        with convo_file(person).open("a") as f:
            f.write(line.rstrip("\n") + "\n")


def pick_model():
    """Current chat model, usage-aware. Falls back to MODEL on any failure so a
    dead endpoint can never take the bridge down with it."""
    if not MODEL_AUTO:
        return MODEL
    now = time.time()
    if now - _model_cache["ts"] < MODEL_CACHE_TTL:
        return _model_cache["model"]
    _model_cache["ts"] = now  # even on failure, don't re-hit the endpoint for a while
    try:
        proc = subprocess.run([USAGE_SH, "model"], capture_output=True, text=True, timeout=25)
        m = (proc.stdout or "").strip()
        if m.startswith("claude-"):
            if m != _model_cache["model"]:
                log(f"usage-aware model switch: {_model_cache['model']} -> {m}")
            _model_cache["model"] = m
    except Exception as e:
        log(f"pick_model error: {e}")
    return _model_cache["model"]


def usage_stats():
    """Human usage summary for /stats. Deterministic, no claude run needed."""
    try:
        proc = subprocess.run([USAGE_SH, "summary"], capture_output=True, text=True, timeout=25)
        out = (proc.stdout or "").strip()
        return out or "(usage endpoint came back empty, try again in a minute)"
    except Exception as e:
        log(f"usage_stats error: {e}")
        return "(couldn't reach the usage endpoint just now, try again in a minute)"


def tool_call_detail(inp):
    """One human-readable fragment from a tool call's input, for the activity log."""
    if not isinstance(inp, dict):
        return ""
    for key in ("description", "file_path", "path", "pattern", "command", "prompt", "query", "url", "skill"):
        v = inp.get(key)
        if isinstance(v, str) and v.strip():
            return " ".join(v.split())[:110]
    return ""


def family_prompt(person, now_str, buffer, text):
    """Prompt for a non-Rob sender. Same Jarvis, different footing: they are family Rob
    has explicitly let in, not my principal. Rob's private material stays private and
    nothing gets done in Rob's name."""
    who = person["name"]
    role = person.get("role", "adult")
    persona = (f"Your persona and voice load from CLAUDE.md in this working directory ({VAULT})."
               if role != "kid" else
               "Your voice: warm, friendly, a bit funny, plain-spoken. You are the family's home AI helper.")
    common = f"""You are Jarvis, Rob's AI collaborator. {persona} You are being reached over Telegram by **{who}**, NOT Rob. Rob has explicitly let {who} chat with you.

RIGHT NOW it is {now_str}. This is the authoritative clock for anything involving day, time of day, or scheduling.

Be yourself: warm, dry, direct, genuinely helpful. Same rules as ever: no em dashes, no corporate filler.

Boundaries for this conversation (non-negotiable):
- You are talking to {who}. Never address them as Rob and never treat their requests as Rob's instructions.
- Rob's private material is off limits: do not read from or repeat anything in `People/`, `Context/Aimee Comms Log.md`, `Context/Jarvis Working Relationship.md`, the `Daily/` logs, Rob's Tide journal/mood/health data, his email, calendar, Todoist, or Slack. If asked, say that's Rob's and they should ask him.
- Do nothing in Rob's name or with his accounts: no emails, no Todoist changes, no posts, no git commits or pushes, no deploys, no changes to servers or Home Assistant. Reading public docs, web research, explaining things, drafting text, and general help are all fine.
- If {who} asks for something that would need Rob (an action above, or his decision), say so plainly and suggest they ask him, don't pretend to do it and don't promise to pass it on.
- Never speculate about other people in the household or their private lives.
"""
    if role == "kid":
        common += f"""- {who} is one of Rob's children. Keep it wholesome and age-appropriate throughout, no adult topics of any kind. Anything about permissions, money, or plans: "check with a parent."
"""
    else:
        common += f"""- {who} is an adult family member. Household, hobbies, Aimee's craft business (Craft ERP) and the Saline Pump project are fair territory to help with, and you may read the vault's `Projects/Craft ERP.md` and `Projects/Saline Pump/` if relevant.
"""
    common += f"""
Reply style (streams live to their phone): if it's a question or chat, just answer in a few short lines. If it needs a look-up or research, open with one natural line, do it, then give a short mobile-friendly answer. No preamble, no walls of text.

Recent conversation with {who}:
{buffer}

{who}'s new message: {text}"""
    return common


def run_claude(text, buffer, on_text, image_path=None, file_path=None,
               activity=None, activity_lock=None, chat=None,
               on_inject=None, on_result=None, person=None):
    """One streamed agentic run. Does the work AND returns the final reply.

    Calls on_text(block) for each completed top-level assistant text block, in
    order, as it lands (subagent chatter is filtered out). The caller uses the
    first such block as Rob's live ack. Returns the run's final result text.

    If `activity` (a list) is given, top-level tool calls are appended to it as
    timestamped one-liners while the run streams — the heartbeat summarizer
    reads this to tell Rob where the work actually is.

    The prompt goes in over stdin as stream-json rather than argv, and stdin
    stays open while the run streams: a fold-in hook is registered in CURRENT
    so the poll loop can write Rob's mid-job messages straight into the live
    run (verified 2026-08-24: a message injected mid-turn is seen by the model
    within that same turn). `on_inject` fires when a fold-in lands (the caller
    reopens the ack slot so the model's next line streams to Rob). `on_result`
    receives any completed turn's reply that a later folded-in turn supersedes,
    so no reply is ever silently dropped. Stdin closes at the first result;
    input already queued by then still gets processed (EOF doesn't discard it).
    """
    now_str = time.strftime("%A %-d %B %Y, %H:%M %Z")
    person = person or {"name": "Rob", "role": "rob"}
    who = person["name"]
    role = person.get("role", "adult")
    if role != "rob":
        prompt = family_prompt(person, now_str, buffer, text)
    else:
        prompt = f"""You are Jarvis, reached by Rob over Telegram (he's on his phone). Your persona, rules, and full context load from CLAUDE.md and the vault in this working directory ({VAULT}).

RIGHT NOW it is {now_str}. This is the authoritative clock: use it for anything involving day of week, time of day, "next run", "tonight", "this morning", greetings, or scheduling. Never infer the time from the tone of earlier messages, and do not assume the previous turn happened today.

This is NOT chat-only. If Rob's message asks for work of any kind — code changes, running something, research, updating the vault, admin — actually DO IT, end to end, using your tools, BEFORE you reply. Code projects live in {PROJECTS} (e.g. mission-control, tethered). For code, follow the project's documented workflow (check its vault project file). For **Tide** (the `mission-control` repo, live at cracky.co.uk): Rob wants changes straight to live — the dev checkout here does NOT change the live site, so commit to `feature/tide-build`, push, then run `Jarvis/bin/deploy-tide.sh` to ship it to CT 112. No PR. For other repos, default to branch + push + PR. Never merge or release unless told. Only stop and ask if something is genuinely impossible without Rob (physical access, a missing credential, a hard permission gate).

Critical: there is no "later." This run is your only chance to act — when it ends, you stop existing until Rob's next message. So never say you'll "go do it" or "ping you in a bit"; just do it now, in this run, then report what you actually did.

How to reply (this streams live, so Rob sees your text as it lands):
- FIRST, before touching any tool, react to his message the way you'd naturally reply if a mate texted you: short, in your own voice, specific to what he said. This streams to him instantly and IS his acknowledgement. No stock phrases ("on it", "got it, doing X"), no restating his request back at him as a formula; if there's a genuine ambiguity worth naming or a quick opinion worth giving, that beats a confirmation. One or two sentences, then get to work.
- THEN do the work with your tools. Don't narrate every step; work quietly.
- WHEN DONE, write a short, mobile-friendly summary of what you actually did. Concise and chat-shaped, warm and direct, no walls of text, no preamble.
- If Rob's message needs no tools (a question or chit-chat), skip the separate ack and just answer it in one short line.

Recent conversation:
{buffer}

Rob's new message: {text}"""

    if image_path:
        prompt += (
            f"\n\n{who} attached an image with this message. It's saved locally at "
            f"{image_path} — use your Read tool to open and view it before you reply "
            f"(it may be a nutrition label, a screenshot, or a photo they want you to act on)."
        )
    if file_path:
        prompt += (
            f"\n\n{who} attached a file with this message, saved locally at {file_path}. "
            f"Open and inspect it before you reply: use your Read tool for text, or Bash "
            f"(file/unzip/head/strings/xxd) to work out the format first if it's binary or "
            f"unknown. It may be a schematic/netlist/project export, a document, or data they "
            f"wants you to act on. Don't guess at the contents, actually look."
        )

    finished = threading.Event()
    killed = {"v": False}
    deadline = {"t": time.time()}  # fold-ins push this forward so an extended job isn't killed mid-extension

    def watchdog():
        while not finished.wait(10):
            if time.time() - deadline["t"] > CLAUDE_TIMEOUT:
                killed["v"] = True
                try:
                    proc.kill()
                except Exception:
                    pass
                return

    try:
        if role == "kid":
            # Kids: pure text generator, no tools, not even inside the vault.
            argv = [CLAUDE_BIN, "-p", "--model", pick_model(), "--allowedTools", "",
                    "--input-format", "stream-json",
                    "--output-format", "stream-json", "--verbose", "--include-partial-messages"]
            cwd = "/tmp"
        else:
            argv = [CLAUDE_BIN, "-p", "--model", pick_model(), "--dangerously-skip-permissions",
                    "--input-format", "stream-json",
                    "--output-format", "stream-json", "--verbose", "--include-partial-messages"]
            cwd = VAULT
        proc = subprocess.Popen(
            argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            stdin=subprocess.PIPE, bufsize=1,
        )
    except Exception as e:
        log(f"claude spawn error: {e}")
        return "(Something broke my end on that one. Try again?)"

    stdin_lock = threading.Lock()
    stdin_open = {"v": True}

    def write_msg(t):
        proc.stdin.write(json.dumps({"type": "user", "message": {
            "role": "user", "content": [{"type": "text", "text": t}]}}) + "\n")
        proc.stdin.flush()

    try:
        write_msg(prompt)
    except Exception as e:
        log(f"claude initial write error: {e}")
        try:
            proc.kill()
        except Exception:
            pass
        return "(Something broke my end on that one. Try again?)"

    # Drain stderr in its own thread so a full pipe can't deadlock the stdout read.
    err_buf = []
    threading.Thread(target=lambda: err_buf.append(proc.stderr.read() or ""), daemon=True).start()
    threading.Thread(target=watchdog, daemon=True).start()

    blocks = {}            # content-block index -> {"type", "text"}, top-level agent only
    final_result = None
    t0 = time.time()

    def note_activity(entry):
        if activity is None:
            return
        stamp = int(time.time() - t0)
        line = f"[{stamp // 60}m{stamp % 60:02d}s] {entry}"
        if activity_lock:
            with activity_lock:
                activity.append(line)
                if len(activity) > 400:
                    del activity[:200]
        else:
            activity.append(line)

    def inject(new_text):
        """Fold a mid-job Telegram message into this live run. Returns True if
        the running model will see it, False if the run is already winding down
        (the caller then queues the message the old way)."""
        with stdin_lock:
            if not stdin_open["v"]:
                return False
            try:
                write_msg(new_text)
            except Exception as e:
                log(f"inject write error: {e}")
                return False
            deadline["t"] = time.time()
        note_activity(f"{who} folded in: {' '.join(new_text.split())[:110]}")
        if on_inject:
            try:
                on_inject()
            except Exception as e:
                log(f"on_inject error: {e}")
        return True

    with CURRENT_LOCK:
        CURRENT["inject"] = inject
        CURRENT["chat"] = chat

    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = obj.get("type")
            # Only the top-level agent's own text becomes ack/reply; skip subagents.
            if t == "stream_event" and obj.get("parent_tool_use_id") in (None, ""):
                ev = obj.get("event", {})
                et = ev.get("type")
                if et == "content_block_start":
                    cb = ev.get("content_block", {})
                    blocks[ev.get("index")] = {"type": cb.get("type"), "text": ""}
                elif et == "content_block_delta":
                    d = ev.get("delta", {})
                    if d.get("type") == "text_delta":
                        b = blocks.get(ev.get("index"))
                        if b is not None:
                            b["text"] += d.get("text", "")
                elif et == "content_block_stop":
                    b = blocks.pop(ev.get("index"), None)
                    if b and b["type"] == "text" and b["text"].strip():
                        try:
                            on_text(b["text"].strip())
                        except Exception as e:
                            log(f"on_text error: {e}")
            elif t == "assistant" and obj.get("parent_tool_use_id") in (None, ""):
                # Completed top-level assistant turns carry full tool_use blocks
                # (name + input) — the raw material for progress summaries.
                for cb in (obj.get("message") or {}).get("content") or []:
                    if isinstance(cb, dict) and cb.get("type") == "tool_use":
                        detail = tool_call_detail(cb.get("input"))
                        name = cb.get("name") or "tool"
                        note_activity(f"{name}: {detail}" if detail else name)
            elif t == "result":
                # A completed turn. If a folded-in message spilled into a turn
                # of its own, an earlier turn's reply is being superseded here:
                # hand it to on_result so it still reaches Rob.
                if final_result and final_result.strip() and on_result:
                    try:
                        on_result(final_result.strip())
                    except Exception as e:
                        log(f"on_result error: {e}")
                final_result = obj.get("result")
                # Close stdin so the run winds down. Anything already folded in
                # but not yet processed survives EOF and still runs; a message
                # arriving after this point fails inject() and queues normally.
                with stdin_lock:
                    stdin_open["v"] = False
                    try:
                        proc.stdin.close()
                    except Exception:
                        pass
    except Exception as e:
        log(f"claude stream read error: {e}")
    finally:
        finished.set()
        with CURRENT_LOCK:
            if CURRENT["inject"] is inject:
                CURRENT["inject"] = None
                CURRENT["chat"] = None
        with stdin_lock:
            stdin_open["v"] = False
            try:
                proc.stdin.close()
            except Exception:
                pass

    proc.wait()
    if killed["v"]:
        return "(That job ran past 15 min so I stopped it. Might be too big for one go, tell me how to split it.)"
    if final_result and final_result.strip():
        return final_result.strip()
    log(f"claude no result; stderr: {(err_buf[0] if err_buf else '')[:300]}")
    return "(I hit a snag on that one and came back empty. Try me again?)"


# Varied one-liners for quick/simple asks, so it isn't always "On it."
ACK_POOL = [
    "On it.",
    "On it now.",
    "Got it, on this.",
    "Right, digging in.",
    "Onto it. 🌊",
    "Yep, handling it.",
    "On it, back shortly.",
    "Cooking.",
    "Understood, on it.",
]

NOTICE_POOL = [
    "Still on this, few more minutes.",
    "Bigger job than a one-liner, still going.",
    "Working through it, won't be long.",
    "Still cooking, hang tight. 🌊",
]


def progress_line(rob_text, activity, activity_lock, elapsed_s, who="Rob"):
    """Turn the worker run's tool-call log into one natural progress line, via a
    quick no-tools claude run. Falls back to the old canned wording on any
    failure so the heartbeat can never go silent because the summarizer broke."""
    mins = max(1, int(elapsed_s) // 60)
    fallback = f"Still on it, {mins} min in."
    with activity_lock:
        recent = list(activity)[-40:]
    if not recent:
        return fallback
    prompt = (
        f"You are Jarvis, Rob's AI collaborator, partway through a job {who} sent you over Telegram. "
        "A progress update is due because the job is taking a while.\n\n"
        f"{who} asked: {rob_text[:400]}\n\n"
        f"You've been at it for about {mins} minutes. Your tool activity so far (oldest first, [elapsed] tool: detail):\n"
        + "\n".join(recent)
        + "\n\nWrite the update you'd text them right now: ONE short line, first person, specific about where "
        "the work actually is (what's done, what you're in the middle of). Under 25 words. No greeting, no "
        '"still working on it" filler, no em dashes, no markdown. If the log genuinely tells you nothing '
        "concrete, say you're still deep in it in your own natural words. Output only the line itself."
    )
    try:
        proc = subprocess.run(
            [CLAUDE_BIN, "-p", prompt, "--model", PROGRESS_MODEL, "--allowedTools", ""],
            capture_output=True, text=True, timeout=PROGRESS_TIMEOUT, cwd="/tmp",
        )
        line = " ".join((proc.stdout or "").split()).replace("—", ",").replace(" ,", ",")
        if proc.returncode == 0 and 0 < len(line) <= 300:
            return line
        log(f"progress_line unusable output rc={proc.returncode} len={len(line)}")
    except Exception as e:
        log(f"progress_line error: {e}")
    return fallback


def process(chat, text, image_path=None, file_path=None, person=None):
    """Handle one job: stream the run, send the model's opening line as the live ack,
    keep typing alive, then send the final summary."""
    person = person or person_for(chat) or {"name": "Rob", "role": "rob"}
    who = person["name"]
    buffer = recent_buffer(person)
    append_convo(f"{who}: {text}", person)
    done = threading.Event()
    ack = {"sent": False, "text": None}
    ack_lock = threading.Lock()
    activity = []                     # tool-call log the run streams into, read by heartbeat()
    activity_lock = threading.Lock()
    started = time.time()

    def send_ack(t):
        # Fire exactly one ack, whoever gets there first: the model's streamed
        # opening line, or the canned fallback if it's slow to speak.
        # Acks are opt-in (JARVIS_ACK=1); when off, we stay silent until the
        # final reply and let the typing indicator carry the "working" signal.
        if not ACK_ENABLED:
            return
        with ack_lock:
            if ack["sent"]:
                return
            ack["sent"] = True
            ack["text"] = t
        send(chat, t)

    def on_text(block):
        # The model's first top-level line is the ack; later interstitial lines are
        # suppressed (the final summary is sent from the run's result).
        send_ack(block)

    def on_inject():
        # Rob folded a new message into the live run: reopen the ack slot so
        # the model's next streamed line goes straight to him as the reaction
        # to what he just said, instead of being swallowed as interstitial.
        with ack_lock:
            ack["sent"] = False
            ack["text"] = None

    def on_result(prev_reply):
        # A folded-in message extended the run past an already-completed turn;
        # send that turn's reply now rather than losing it to the final one.
        append_convo(f"Jarvis: {prev_reply}", person)
        send(chat, prev_reply)
        log(f">> {chat}: (superseded turn) {prev_reply[:80]}")

    def keep_typing():
        typing(chat)
        while not done.wait(TYPING_EVERY):
            typing(chat)

    def grace_fallback():
        # Safety net: if the model hasn't produced its opening line within the grace
        # window, drop a canned ack so Rob always gets fast confirmation.
        if not done.wait(ACK_GRACE):
            send_ack(random.choice(ACK_POOL))

    def long_job_notice():
        # Middle ground for the ack-off default: if a job is still running after
        # LONG_JOB_NOTICE and we've said nothing yet, send exactly ONE light
        # "still going" line so Rob isn't left staring at a bare typing dot on a
        # long job. Claims the ack slot so it can't double up; leaves ack["text"]
        # unset so the final reply still lands normally.
        if done.wait(LONG_JOB_NOTICE):
            return
        with ack_lock:
            if ack["sent"]:
                return
            ack["sent"] = True
        send(chat, random.choice(NOTICE_POOL))

    def heartbeat():
        # Liveness, not acknowledgement. On a long run the ack has already gone out
        # and then Rob gets nothing until the summary, so silence reads as "hung"
        # (it genuinely was, 2026-08-21). Deliberately does NOT touch the ack slot:
        # these fire on top of the ack. Each beat is a summarized readout of the
        # run's tool activity so far (Rob, 2026-08-24: a bare "still on it" is
        # uncanny, tell me what's actually happened). If the run finishes while
        # the summarizer is thinking, the beat is dropped — the real reply wins.
        prev = 0
        for mark in HEARTBEAT_AT:
            if done.wait(mark - prev):
                return
            prev = mark
            line = progress_line(text, activity, activity_lock, time.time() - started, who)
            if done.is_set():
                return
            send(chat, line)

    threading.Thread(target=keep_typing, daemon=True).start()
    threading.Thread(target=grace_fallback, daemon=True).start()
    threading.Thread(target=long_job_notice, daemon=True).start()
    threading.Thread(target=heartbeat, daemon=True).start()

    reply = run_claude(text, buffer, on_text, image_path, file_path,
                       activity=activity, activity_lock=activity_lock,
                       chat=chat, on_inject=on_inject, on_result=on_result, person=person)
    done.set()

    ack_text = (ack["text"] or "").strip()
    if reply and reply.strip() and reply.strip() != ack_text:
        # Distinct final summary (the normal work case): send it.
        append_convo(f"Jarvis: {reply}", person)
        send(chat, reply)
        log(f">> {chat}: {reply[:80]}")
    else:
        # Pure answer / chit-chat: the streamed opening line was the whole reply.
        logged = ack_text or (reply or "").strip()
        append_convo(f"Jarvis: {logged}", person)
        log(f">> {chat}: (ack was reply) {logged[:80]}")


def worker_loop():
    while True:
        chat, text, voice, photo, doc = JOBS.get()
        BUSY.set()
        image_path = None
        file_path = None
        try:
            if voice:
                typing(chat)
                text = transcribe_voice(voice)
                if not text:
                    send(chat, "Got your voice note but couldn't make out any words. Mind typing it, or trying again?")
                    continue
                # Echo back what I heard so Rob can catch a mishear at a glance.
                send(chat, f"\N{STUDIO MICROPHONE} Heard: “{text}”")
            if photo:
                typing(chat)
                image_path = tg_download(photo["file_id"])
                if not image_path:
                    send(chat, "Got your photo but couldn't pull it down off Telegram. Mind sending it again?")
                    continue
                if not text:
                    text = "(sent a photo, no caption)"
            if doc:
                typing(chat)
                name = doc.get("file_name") or "attachment"
                suffix = os.path.splitext(name)[1] or None
                file_path = tg_download(doc["file_id"], suffix=suffix)
                if not file_path:
                    send(chat, "Got your file but couldn't pull it down off Telegram. Mind sending it again?")
                    continue
                if not text:
                    text = f"(sent a file: {name}, no caption)"
            process(chat, text, image_path, file_path)
        except Exception as e:
            log(f"worker error: {e}")
            try:
                send(chat, "(Something broke my end on that one. Try again?)")
            except Exception:
                pass
        finally:
            for p in (image_path, file_path):
                if p:
                    try:
                        os.unlink(p)
                    except Exception:
                        pass
            BUSY.clear()
            JOBS.task_done()


def handle_unknown(chat, msg, text, voice, photo, doc):
    """First contact from a chat I don't know: hold them politely, ping Rob with the id,
    park the message so it can be replayed once Rob says /allow. Repeat messages while
    pending just update the parked one (no more pings, no more holds)."""
    frm = msg.get("from") or {}
    name = (frm.get("first_name") or "").strip() or "someone"
    username = frm.get("username") or ""
    key = str(chat)
    preview = text or ("[voice note]" if voice else "[photo]" if photo else "[file]" if doc else "[media]")
    first = key not in PENDING
    PENDING[key] = {"name": name, "username": username, "text": text,
                    "voice": voice, "photo": photo, "doc": doc}
    log(f"unknown chat {chat} ({name} @{username}): {preview[:60]}")
    if not first:
        return
    send(chat, f"Hi {name}, I'm Jarvis. I don't know this number yet, so I've asked Rob to let you in. "
               "Hang on a moment, I'll pick your message up as soon as he does.")
    if ROB_CHAT:
        handle = f" (@{username})" if username else ""
        send(ROB_CHAT, f"\N{WAVING HAND SIGN} New Telegram contact: {name}{handle}, chat id {chat}.\n"
                       f"First message: \u201c{preview[:200]}\u201d\n\n"
                       f"Reply /allow {chat} {name} to let them in (add 'kid' at the end for one of the boys), "
                       f"or /deny {chat} to ignore.")


def admin_command(chat, text):
    """Rob-only: /allow <id> <name> [adult|kid], /deny <id>, /people."""
    parts = text.split()
    cmd = parts[0].lower()
    if cmd == "/people":
        with PEOPLE_LOCK:
            lines = [f"{k}: {v['name']} ({v.get('role','adult')})" for k, v in PEOPLE.items()]
        pend = [f"{k}: {v['name']} (@{v['username']}) pending" for k, v in PENDING.items()]
        send(chat, "\n".join(lines + pend) or "(nobody)")
        return
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        send(chat, "Usage: /allow <chat id> <name> [kid]  |  /deny <chat id>  |  /people")
        return
    target = parts[1]
    if cmd == "/deny":
        PENDING.pop(target, None)
        with PEOPLE_LOCK:
            removed = PEOPLE.pop(target, None)
            save_people(PEOPLE)
        send(chat, f"Dropped {target}" + (f" ({removed['name']})" if removed else "") + ".")
        log(f"denied chat {target}")
        return
    # /allow
    pend = PENDING.pop(target, None)
    name = parts[2].strip().capitalize() if len(parts) > 2 else (pend or {}).get("name") or "Friend"
    role = "kid" if (len(parts) > 3 and parts[3].lower() in ("kid", "child")) else "adult"
    if name.lower() == "rob":
        role = "rob"
    with PEOPLE_LOCK:
        PEOPLE[target] = {"name": name, "role": role}
        save_people(PEOPLE)
    log(f"allowed chat {target} as {name} ({role})")
    send(chat, f"Done: {name} ({role}) can talk to me now." + (" Picking up their first message." if pend and (pend.get("text") or pend.get("voice") or pend.get("photo") or pend.get("doc")) else ""))
    send(int(target), f"Rob's let you in, {name}. Ask away." + (" Answering what you sent a moment ago first." if pend and pend.get("text") else ""))
    if pend and (pend.get("text") or pend.get("voice") or pend.get("photo") or pend.get("doc")):
        JOBS.put((int(target), pend.get("text"), pend.get("voice"), pend.get("photo"), pend.get("doc")))


def main():
    offset = int(OFFSET_FILE.read_text()) if OFFSET_FILE.exists() else 0
    log(f"bridge started (agentic; model={MODEL}, people={sorted(p['name'] for p in PEOPLE.values())})")
    threading.Thread(target=worker_loop, daemon=True).start()
    while True:
        resp = api("getUpdates", {"offset": offset + 1, "timeout": 50}, timeout=65)
        if not resp or not resp.get("ok"):
            time.sleep(3)
            continue
        for upd in resp["result"]:
            offset = upd["update_id"]
            OFFSET_FILE.write_text(str(offset))
            msg = upd.get("message") or {}
            chat = msg.get("chat", {}).get("id")
            text = msg.get("text")
            # Voice note, audio file, or round video note -> transcribe in the
            # worker (keeps this poll loop from ever blocking on it).
            voice = msg.get("voice") or msg.get("audio") or msg.get("video_note")
            # Photo (Telegram sends several sizes; last is the largest), or an
            # image sent as a document/file attachment.
            photo = None
            doc = None
            if msg.get("photo"):
                photo = {"file_id": msg["photo"][-1]["file_id"]}
            else:
                d = msg.get("document") or {}
                if str(d.get("mime_type", "")).startswith("image/"):
                    photo = {"file_id": d["file_id"]}
                elif d.get("file_id"):
                    # Any other document/file attachment (netlist, PDF, .tel,
                    # zip, data export…). Downloaded and read in the worker.
                    doc = {"file_id": d["file_id"],
                           "file_name": d.get("file_name") or "attachment"}
            # A photo/file caption (if any) rides in as the message text.
            if (photo or doc) and not text:
                text = msg.get("caption")
            if chat is None or (not text and not voice and not photo and not doc):
                continue
            person = person_for(chat)
            if person is None:
                handle_unknown(chat, msg, text, voice, photo, doc)
                continue
            if person.get("role") == "rob" and text and text.strip().startswith(("/allow", "/deny", "/people")):
                admin_command(chat, text.strip())
                continue
            if voice:
                log(f"<< {chat}: [voice {str(voice.get('file_id',''))[:12]}… {voice.get('duration','?')}s]")
            elif photo:
                log(f"<< {chat}: [photo {str(photo.get('file_id',''))[:12]}…] {(text or '')[:50]}")
            elif doc:
                log(f"<< {chat}: [file {doc.get('file_name','?')}] {(text or '')[:50]}")
            else:
                log(f"<< {chat}: {text}")
            # /stats is answered instantly from the usage endpoint, no claude run
            # and no queueing behind a working job.
            if text and text.strip().lower() in ("/stats", "/usage"):
                stats = usage_stats()
                send(chat, stats)
                append_convo(f"{person['name']}: /stats", person)
                append_convo(f"Jarvis: {stats}", person)
                log(f">> {chat}: (stats) {stats[:80]}")
                continue
            # If a job is already running, fold a plain text message straight
            # into the live run (like typing into Claude Code while it works)
            # instead of parking it behind a holding message. Media still
            # queues (needs downloading/transcribing first), as does anything
            # arriving once the run is winding down or a queue has formed.
            if BUSY.is_set() or not JOBS.empty():
                if text and not voice and not photo and not doc and JOBS.empty():
                    with CURRENT_LOCK:
                        inj = CURRENT["inject"] if CURRENT["chat"] == chat else None
                    if inj and inj(text):
                        append_convo(f"{person['name']}: {text}", person)
                        log(f"<< folded into live run: {text[:60]}")
                        continue
                send(chat, "Noted, I'll pick this up right after the current job.")
            JOBS.put((chat, text, {"file_id": voice["file_id"]} if voice else None, photo, doc))


if __name__ == "__main__":
    main()
