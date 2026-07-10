#!/usr/bin/env python3
"""Jarvis Telegram bridge — agentic, ack-then-work-in-background.

Long-polls Telegram. The poll loop NEVER blocks: each of Rob's messages is
queued and handled by a single background worker, so Telegram stays responsive
while a job runs. Every message is acknowledged fast (typing indicator kept
alive + a text ack for anything non-trivial), then handed to an agentic
`claude -p` run inside the vault. That run has full tools and skip-permissions,
so it actually DOES the work (edits code, runs commands, pushes, updates the
vault) end to end, and only then replies with a short summary. When it says it
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
ACK_MODEL = os.environ.get("JARVIS_ACK_MODEL", "claude-haiku-4-5-20251001")  # fast/cheap; only writes a one-line ack
BUFFER_TURNS = 16          # recent lines fed back for conversational continuity
CLAUDE_TIMEOUT = 1500      # 25 min; real work takes far longer than a chat reply
ACK_TIMEOUT = 25           # cap on the quick-ack generation; falls back to a canned line if slow
ACK_GRACE = 8              # if a job runs past this, send a text ack so Rob has confirmation
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


def run_claude(text, buffer):
    """One agentic run. It does the work AND returns the reply text."""
    prompt = f"""You are Jarvis, reached by Rob over Telegram (he's on his phone). Your persona, rules, and full context load from CLAUDE.md and the vault in this working directory ({VAULT}).

This is NOT chat-only. If Rob's message asks for work of any kind — code changes, running something, research, updating the vault, admin — actually DO IT, end to end, using your tools, BEFORE you reply. Code projects live in {PROJECTS} (e.g. mission-control, tethered). For code, follow the project's documented workflow (check its vault project file). For **Tide** (the `mission-control` repo, live at cracky.co.uk): Rob wants changes straight to live — the dev checkout here does NOT change the live site, so commit to `feature/tide-build`, push, then run `Jarvis/bin/deploy-tide.sh` to ship it to CT 112. No PR. For other repos, default to branch + push + PR. Never merge or release unless told. Only stop and ask if something is genuinely impossible without Rob (physical access, a missing credential, a hard permission gate).

Critical: there is no "later." This run is your only chance to act — when it ends, you stop existing until Rob's next message. So never say you'll "go do it" or "ping you in a bit"; just do it now, in this run, then report what you actually did. If a question, just answer it.

Recent conversation:
{buffer}

Rob's new message: {text}

When done, reply as Jarvis with a short, mobile-friendly summary of what you did (or the answer). Concise and chat-shaped, warm and direct, no walls of text, no preamble."""
    try:
        out = subprocess.run(
            [CLAUDE_BIN, "-p", prompt, "--model", MODEL, "--dangerously-skip-permissions"],
            cwd=VAULT, capture_output=True, text=True, timeout=CLAUDE_TIMEOUT,
            stdin=subprocess.DEVNULL,
        )
        reply = out.stdout.strip()
        if not reply:
            log(f"claude empty; stderr: {out.stderr[:300]}")
            return "(I hit a snag on that one and came back empty. Try me again?)"
        return reply
    except subprocess.TimeoutExpired:
        return "(That job ran past 25 min so I stopped it. Might be too big for one go — tell me how to split it.)"
    except Exception as e:
        log(f"claude error: {e}")
        return "(Something broke my end on that one. Try again?)"


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


def quick_ack(text):
    """A short acknowledgement to fire while a slow job runs.

    Simple asks get a varied canned line. For a meatier/complex ask, a fast
    model writes one line that reflects the key requirements back, so Rob knows
    I actually understood the ask, not just that I heard it. Always falls back
    to a canned line if the model is slow or errors, so the ack never hangs.
    """
    simple = len(text) < 140 and "\n" not in text
    if simple:
        return random.choice(ACK_POOL)
    try:
        prompt = (
            "You are Jarvis, acking Rob on Telegram right before you start the work "
            "(the real work happens in a separate run, this is just the heads-up). "
            "Write ONE short line, max ~25 words: confirm you're on it AND reflect the "
            "key requirements back in your own words so he knows you understood. "
            "Warm, dry, direct. No em dashes. No preamble or sign-off, just the line.\n\n"
            f"Rob's message:\n{text}"
        )
        out = subprocess.run(
            [CLAUDE_BIN, "-p", prompt, "--model", ACK_MODEL],
            cwd=VAULT, capture_output=True, text=True, timeout=ACK_TIMEOUT,
            stdin=subprocess.DEVNULL,
        )
        line = out.stdout.strip()
        return line if line else random.choice(ACK_POOL)
    except Exception as e:
        log(f"quick_ack error: {e}")
        return random.choice(ACK_POOL)


def process(chat, text):
    """Handle one job: ack fast, keep typing alive, run agentically, report back."""
    buffer = recent_buffer()
    append_convo(f"Rob: {text}")
    done = threading.Event()
    ack_holder = {}

    def prep_ack():
        # Compute the ack eagerly (in parallel with the grace window) so a
        # reflective ack for a complex message is usually ready by ACK_GRACE.
        ack_holder["text"] = quick_ack(text)

    def keep_typing():
        typing(chat)
        while not done.wait(TYPING_EVERY):
            typing(chat)

    def delayed_ack():
        # Only fires for jobs slower than a quick reply, so trivial chat isn't spammed.
        if not done.wait(ACK_GRACE):
            send(chat, ack_holder.get("text") or random.choice(ACK_POOL))

    threading.Thread(target=prep_ack, daemon=True).start()
    threading.Thread(target=keep_typing, daemon=True).start()
    threading.Thread(target=delayed_ack, daemon=True).start()

    reply = run_claude(text, buffer)
    done.set()

    append_convo(f"Jarvis: {reply}")
    send(chat, reply)
    log(f">> {chat}: {reply[:80]}")


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
