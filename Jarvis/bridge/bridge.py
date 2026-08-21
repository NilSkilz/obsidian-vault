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

Jobs are processed one at a time. Rapid-fire messages queue behind the current
job (Rob gets told), which keeps two agentic runs from fighting over the same
git repo.

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
BUFFER_TURNS = 16          # recent lines fed back for conversational continuity
CLAUDE_TIMEOUT = 1500      # 25 min; real work takes far longer than a chat reply
ACK_ENABLED = os.environ.get("JARVIS_ACK", "1") == "1"  # stream the model's opening line as the ack (on by default since 2026-08-21; Rob wants natural voice, not canned)
ACK_GRACE = 15             # if the model hasn't spoken by now, send a canned ack so Rob has confirmation (generous so the canned pool rarely fires)
LONG_JOB_NOTICE = 30       # ack-off middle ground: if still working after this long and we've said nothing, drop ONE light "still on it" line
TYPING_EVERY = 4           # refresh the typing indicator this often while working
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
ALLOWED = CONF_D.get("TELEGRAM_ALLOWED_CHAT", "").strip()
API = f"https://api.telegram.org/bot{TOKEN}"


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


def recent_buffer():
    if not CONVO.exists():
        return ""
    return "\n".join(CONVO.read_text().splitlines()[-BUFFER_TURNS:])


def append_convo(line):
    with CONVO_LOCK:
        with CONVO.open("a") as f:
            f.write(line.rstrip("\n") + "\n")


def run_claude(text, buffer, on_text, image_path=None, file_path=None):
    """One streamed agentic run. Does the work AND returns the final reply.

    Calls on_text(block) for each completed top-level assistant text block, in
    order, as it lands (subagent chatter is filtered out). The caller uses the
    first such block as Rob's live ack. Returns the run's final result text.
    """
    prompt = f"""You are Jarvis, reached by Rob over Telegram (he's on his phone). Your persona, rules, and full context load from CLAUDE.md and the vault in this working directory ({VAULT}).

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
            f"\n\nRob attached an image with this message. It's saved locally at "
            f"{image_path} — use your Read tool to open and view it before you reply "
            f"(it may be a nutrition label, a screenshot, or a photo he wants you to act on)."
        )
    if file_path:
        prompt += (
            f"\n\nRob attached a file with this message, saved locally at {file_path}. "
            f"Open and inspect it before you reply: use your Read tool for text, or Bash "
            f"(file/unzip/head/strings/xxd) to work out the format first if it's binary or "
            f"unknown. It may be a schematic/netlist/project export, a document, or data he "
            f"wants you to act on. Don't guess at the contents, actually look."
        )

    finished = threading.Event()
    killed = {"v": False}

    def watchdog():
        if not finished.wait(CLAUDE_TIMEOUT):
            killed["v"] = True
            try:
                proc.kill()
            except Exception:
                pass

    try:
        proc = subprocess.Popen(
            [CLAUDE_BIN, "-p", prompt, "--model", MODEL, "--dangerously-skip-permissions",
             "--output-format", "stream-json", "--verbose", "--include-partial-messages"],
            cwd=VAULT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            stdin=subprocess.DEVNULL, bufsize=1,
        )
    except Exception as e:
        log(f"claude spawn error: {e}")
        return "(Something broke my end on that one. Try again?)"

    # Drain stderr in its own thread so a full pipe can't deadlock the stdout read.
    err_buf = []
    threading.Thread(target=lambda: err_buf.append(proc.stderr.read() or ""), daemon=True).start()
    threading.Thread(target=watchdog, daemon=True).start()

    blocks = {}            # content-block index -> {"type", "text"}, top-level agent only
    final_result = None
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
            elif t == "result":
                final_result = obj.get("result")
    except Exception as e:
        log(f"claude stream read error: {e}")
    finally:
        finished.set()

    proc.wait()
    if killed["v"]:
        return "(That job ran past 25 min so I stopped it. Might be too big for one go — tell me how to split it.)"
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


def process(chat, text, image_path=None, file_path=None):
    """Handle one job: stream the run, send the model's opening line as the live ack,
    keep typing alive, then send the final summary."""
    buffer = recent_buffer()
    append_convo(f"Rob: {text}")
    done = threading.Event()
    ack = {"sent": False, "text": None}
    ack_lock = threading.Lock()

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

    threading.Thread(target=keep_typing, daemon=True).start()
    threading.Thread(target=grace_fallback, daemon=True).start()
    threading.Thread(target=long_job_notice, daemon=True).start()

    reply = run_claude(text, buffer, on_text, image_path, file_path)
    done.set()

    ack_text = (ack["text"] or "").strip()
    if reply and reply.strip() and reply.strip() != ack_text:
        # Distinct final summary (the normal work case): send it.
        append_convo(f"Jarvis: {reply}")
        send(chat, reply)
        log(f">> {chat}: {reply[:80]}")
    else:
        # Pure answer / chit-chat: the streamed opening line was the whole reply.
        logged = ack_text or (reply or "").strip()
        append_convo(f"Jarvis: {logged}")
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


def main():
    offset = int(OFFSET_FILE.read_text()) if OFFSET_FILE.exists() else 0
    log(f"bridge started (agentic; model={MODEL}, allowed={ALLOWED or 'ANY'})")
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
            if ALLOWED and str(chat) != ALLOWED:
                log(f"ignored msg from unlisted chat {chat}: {(text or '[media]')[:50]}")
                continue
            if voice:
                log(f"<< {chat}: [voice {str(voice.get('file_id',''))[:12]}… {voice.get('duration','?')}s]")
            elif photo:
                log(f"<< {chat}: [photo {str(photo.get('file_id',''))[:12]}…] {(text or '')[:50]}")
            elif doc:
                log(f"<< {chat}: [file {doc.get('file_name','?')}] {(text or '')[:50]}")
            else:
                log(f"<< {chat}: {text}")
            # If a job is already running (or waiting), tell Rob this one is queued.
            if BUSY.is_set() or not JOBS.empty():
                send(chat, "Noted, I'll pick this up right after the current job.")
            JOBS.put((chat, text, {"file_id": voice["file_id"]} if voice else None, photo, doc))


if __name__ == "__main__":
    main()
