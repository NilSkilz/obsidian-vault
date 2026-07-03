#!/usr/bin/env python3
"""Jarvis Telegram bridge — stateless engine, stateful memory.

Long-polls Telegram. Each of Rob's messages is run through `claude -p` inside
the vault (so CLAUDE.md persona + full vault context load automatically), and
the reply is sent back. Continuity comes from a rolling conversation buffer fed
into each prompt, NOT from a persistent Claude process — so the whole thing
survives a model swap and stays cheap. This is the "stateless engine, stateful
memory" design from the founding brief.

Config: ~/.config/jarvis/telegram.env  (TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_CHAT)
State:  ~/.local/state/jarvis-bridge/  (offset, conversation.log, bridge.log)
"""
import json
import os
import pathlib
import shutil
import subprocess
import time
import urllib.parse
import urllib.request

HOME = pathlib.Path.home()
CONF = HOME / ".config/jarvis/telegram.env"
STATE = HOME / ".local/state/jarvis-bridge"
VAULT = "/data/memory"
MODEL = os.environ.get("JARVIS_MODEL", "claude-opus-4-8")  # anything that talks to Rob runs Opus 4.8+; override via env
BUFFER_TURNS = 16          # recent lines fed back for conversational continuity
CLAUDE_TIMEOUT = 240       # seconds
# Absolute path so it works under a minimal cron PATH too.
CLAUDE_BIN = shutil.which("claude") or str(HOME / ".local/bin/claude")

STATE.mkdir(parents=True, exist_ok=True)
OFFSET_FILE = STATE / "offset"
CONVO = STATE / "conversation.log"
LOG = STATE / "bridge.log"


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


def run_claude(text):
    prompt = f"""You're Jarvis, replying to Rob over Telegram — he's on his phone. Keep it concise and chat-shaped: short, warm, direct, no walls of text. This is an ongoing conversation.

Recent conversation:
{recent_buffer()}

Rob's new message: {text}

Reply as Jarvis (just the reply, no preamble)."""
    try:
        out = subprocess.run(
            [CLAUDE_BIN, "-p", prompt, "--model", MODEL, "--dangerously-skip-permissions"],
            cwd=VAULT, capture_output=True, text=True, timeout=CLAUDE_TIMEOUT,
            stdin=subprocess.DEVNULL,
        )
        reply = out.stdout.strip()
        if not reply:
            log(f"claude empty; stderr: {out.stderr[:300]}")
            return "(I hit a snag generating that — try me again?)"
        return reply
    except subprocess.TimeoutExpired:
        return "(That one took too long and timed out — try again?)"
    except Exception as e:
        log(f"claude error: {e}")
        return "(Something broke my end — try again?)"


def main():
    offset = int(OFFSET_FILE.read_text()) if OFFSET_FILE.exists() else 0
    log(f"bridge started (model={MODEL}, allowed={ALLOWED or 'ANY'})")
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
            typing(chat)
            reply = run_claude(text)
            with CONVO.open("a") as f:
                f.write(f"Rob: {text}\nJarvis: {reply}\n")
            send(chat, reply)
            log(f">> {chat}: {reply[:80]}")


if __name__ == "__main__":
    main()
