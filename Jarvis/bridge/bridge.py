#!/usr/bin/env python3
"""Jarvis Telegram bridge — agentic, streamed ack-then-work-in-background.

Long-polls Telegram. The poll loop NEVER blocks: each of Rob's messages is
queued and handled by a single background worker, so Telegram stays responsive
while a job runs. Each message is handed to an agentic `claude -p` run inside
the vault, streamed as `stream-json`. That run has full tools and
skip-permissions, so it actually DOES the work (edits code, runs commands,
pushes, updates the vault) end to end. Its FIRST streamed line — Opus's own
opening, which reflects the ask back — is sent to Rob as the instant
acknowledgement; its final summary is sent once the work is done. A canned line
is only a fallback for when Opus is slow to speak. The typing indicator is kept
alive throughout. When it says it did something, it did.

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
import threading
import time
import urllib.parse
import urllib.request

HOME = pathlib.Path.home()
CONF = HOME / ".config/jarvis/telegram.env"
STATE = HOME / ".local/state/jarvis-bridge"
VAULT = "/data/memory"
PROJECTS = "/home/jarvis/projects"
MODEL = os.environ.get("JARVIS_MODEL", "claude-opus-4-8")  # anything that talks to Rob runs Opus 4.8+; override via env
BUFFER_TURNS = 16          # recent lines fed back for conversational continuity
CLAUDE_TIMEOUT = 1500      # 25 min; real work takes far longer than a chat reply
ACK_GRACE = 8              # if Opus hasn't spoken by now, send a canned ack so Rob has confirmation
TYPING_EVERY = 4           # refresh the typing indicator this often while working
# Absolute path so it works under a minimal PATH too.
CLAUDE_BIN = shutil.which("claude") or str(HOME / ".local/bin/claude")

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


def recent_buffer():
    if not CONVO.exists():
        return ""
    return "\n".join(CONVO.read_text().splitlines()[-BUFFER_TURNS:])


def append_convo(line):
    with CONVO_LOCK:
        with CONVO.open("a") as f:
            f.write(line.rstrip("\n") + "\n")


def run_claude(text, buffer, on_text):
    """One streamed agentic run. Does the work AND returns the final reply.

    Calls on_text(block) for each completed top-level assistant text block, in
    order, as it lands (subagent chatter is filtered out). The caller uses the
    first such block as Rob's live ack. Returns the run's final result text.
    """
    prompt = f"""You are Jarvis, reached by Rob over Telegram (he's on his phone). Your persona, rules, and full context load from CLAUDE.md and the vault in this working directory ({VAULT}).

This is NOT chat-only. If Rob's message asks for work of any kind — code changes, running something, research, updating the vault, admin — actually DO IT, end to end, using your tools, BEFORE you reply. Code projects live in {PROJECTS} (e.g. mission-control, tethered). For code, follow the project's documented workflow (check its vault project file). For **Tide** (the `mission-control` repo, live at cracky.co.uk): Rob wants changes straight to live — the dev checkout here does NOT change the live site, so commit to `feature/tide-build`, push, then run `Jarvis/bin/deploy-tide.sh` to ship it to CT 112. No PR. For other repos, default to branch + push + PR. Never merge or release unless told. Only stop and ask if something is genuinely impossible without Rob (physical access, a missing credential, a hard permission gate).

Critical: there is no "later." This run is your only chance to act — when it ends, you stop existing until Rob's next message. So never say you'll "go do it" or "ping you in a bit"; just do it now, in this run, then report what you actually did.

How to reply (this streams live, so Rob sees your text as it lands):
- FIRST, before touching any tool, write ONE short line (max ~25 words) that confirms you're on it AND reflects the key requirements back in your own words, so Rob knows you understood the ask. This line IS his instant acknowledgement, so make it land.
- THEN do the work with your tools. Don't narrate every step; work quietly.
- WHEN DONE, write a short, mobile-friendly summary of what you actually did. Concise and chat-shaped, warm and direct, no walls of text, no preamble.
- If Rob's message needs no tools (a question or chit-chat), skip the separate ack and just answer it in one short line.

Recent conversation:
{buffer}

Rob's new message: {text}"""

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


def process(chat, text):
    """Handle one job: stream the run, send Opus's opening line as the live ack,
    keep typing alive, then send the final summary."""
    buffer = recent_buffer()
    append_convo(f"Rob: {text}")
    done = threading.Event()
    ack = {"sent": False, "text": None}
    ack_lock = threading.Lock()

    def send_ack(t):
        # Fire exactly one ack, whoever gets there first: Opus's streamed
        # opening line, or the canned fallback if it's slow to speak.
        with ack_lock:
            if ack["sent"]:
                return
            ack["sent"] = True
            ack["text"] = t
        send(chat, t)

    def on_text(block):
        # Opus's first top-level line is the ack; later interstitial lines are
        # suppressed (the final summary is sent from the run's result).
        send_ack(block)

    def keep_typing():
        typing(chat)
        while not done.wait(TYPING_EVERY):
            typing(chat)

    def grace_fallback():
        # Safety net: if Opus hasn't produced its opening line within the grace
        # window, drop a canned ack so Rob always gets fast confirmation.
        if not done.wait(ACK_GRACE):
            send_ack(random.choice(ACK_POOL))

    threading.Thread(target=keep_typing, daemon=True).start()
    threading.Thread(target=grace_fallback, daemon=True).start()

    reply = run_claude(text, buffer, on_text)
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
        chat, text = JOBS.get()
        BUSY.set()
        try:
            process(chat, text)
        except Exception as e:
            log(f"worker error: {e}")
            try:
                send(chat, "(Something broke my end on that one. Try again?)")
            except Exception:
                pass
        finally:
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
            if chat is None or not text:
                continue
            if ALLOWED and str(chat) != ALLOWED:
                log(f"ignored msg from unlisted chat {chat}: {text[:50]}")
                continue
            log(f"<< {chat}: {text}")
            # If a job is already running (or waiting), tell Rob this one is queued.
            if BUSY.is_set() or not JOBS.empty():
                send(chat, "Noted, I'll pick this up right after the current job.")
            JOBS.put((chat, text))


if __name__ == "__main__":
    main()
