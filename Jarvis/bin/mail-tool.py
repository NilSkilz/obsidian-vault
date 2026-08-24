#!/usr/bin/env python3
"""Jarvis iCloud mail helper (IMAP, credential in ~/.config/jarvis/icloud.env).

Subcommands:
  sweep   Move INBOX mail from known-junk senders to Deleted Messages.
          Sender patterns live in ~/.config/jarvis/mail-bin-senders.txt,
          one IMAP FROM substring per line (# comments allowed).
  new     Print INBOX messages that arrived since the last checkpoint
          (~/.local/state/jarvis-mail-check.uid) and advance it.
          First run just sets the checkpoint and prints nothing, so a
          fresh install never dumps years of backlog.
  bin     Move specific INBOX messages to Deleted Messages by UID:
          `mail-tool.py bin 123,124`. Used by the hourly judge to bin
          sales/marketing/spam. Recoverable for 30 days via iCloud.

Used by email-check.sh (hourly cron). Safe to run by hand.
"""
import email
import email.policy
import imaplib
import os
import sys
from email.header import decode_header
from pathlib import Path

CONF = Path.home() / ".config/jarvis/icloud.env"
SENDERS = Path.home() / ".config/jarvis/mail-bin-senders.txt"
STATE = Path.home() / ".local/state/jarvis-mail-check.uid"
SWEPTLOG = Path.home() / ".local/state/jarvis-mail-swept.log"
TRASH = '"Deleted Messages"'
SNIPPET_LEN = 600


def connect():
    env = {}
    for line in CONF.read_text().splitlines():
        k, _, v = line.strip().partition("=")
        if k:
            env[k] = v
    m = imaplib.IMAP4_SSL("imap.mail.me.com", 993)
    m.login(env["ICLOUD_USER"], env["ICLOUD_APP_PASSWORD"])
    return m


def dh(s):
    if not s:
        return ""
    return "".join(
        t.decode(enc or "utf-8", "replace") if isinstance(t, bytes) else t
        for t, enc in decode_header(s)
    )


def log_swept(m, uids):
    # Binned notification mail still carries signal in its subject line
    # (who commented, who messaged). Keep a receipt so the evening briefing
    # can spot patterns even though the mail itself goes straight to the bin.
    import datetime
    today = datetime.date.today().isoformat()
    lines = []
    for u in uids:
        typ, md = m.uid("fetch", u, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
        if typ != "OK" or not md or md[0] is None:
            continue
        msg = email.message_from_bytes(md[0][1], policy=email.policy.default)
        frm = dh(msg["From"]).replace("\t", " ").strip()
        subj = dh(msg["Subject"]).replace("\t", " ").strip()
        lines.append(f"{today}\t{frm}\t{subj}\n")
    if lines:
        SWEPTLOG.parent.mkdir(parents=True, exist_ok=True)
        with SWEPTLOG.open("a") as f:
            f.writelines(lines)


def sweep(m):
    if not SENDERS.exists():
        return
    patterns = [
        p.strip() for p in SENDERS.read_text().splitlines()
        if p.strip() and not p.strip().startswith("#")
    ]
    m.select("INBOX")
    for pat in patterns:
        typ, data = m.uid("search", None, f'(FROM "{pat}")')
        if typ != "OK" or not data or not data[0]:
            continue
        uids = data[0].split()
        try:
            log_swept(m, uids)
        except Exception as e:
            print(f"swept-log failed for '{pat}': {e}")
        for i in range(0, len(uids), 100):
            batch = b",".join(uids[i:i + 100]).decode()
            m.uid("MOVE", batch, TRASH)
        print(f"swept {len(uids)} from '{pat}'")


def body_snippet(msg):
    part = msg.get_body(preferencelist=("plain", "html"))
    if part is None:
        return ""
    try:
        text = part.get_content()
    except Exception:
        return ""
    if part.get_content_type() == "text/html":
        import re
        text = re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
    text = " ".join(text.split())
    return text[:SNIPPET_LEN]


def bin_uids(m, arg):
    uids = [u for u in arg.replace(",", " ").split() if u.isdigit()]
    if not uids:
        return
    m.select("INBOX")
    typ, _ = m.uid("MOVE", ",".join(uids), TRASH)
    if typ == "OK":
        print(f"binned {len(uids)}")
    else:
        print(f"bin failed for uids {','.join(uids)}")


def new(m):
    m.select("INBOX")
    typ, data = m.status("INBOX", "(UIDNEXT)")
    uidnext = int(data[0].split(b"UIDNEXT")[1].strip(b" ()").split()[0])
    if not STATE.exists():
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(str(uidnext))
        return
    last = int(STATE.read_text().strip())
    STATE.write_text(str(uidnext))
    if uidnext <= last:
        return
    typ, data = m.uid("search", None, f"UID {last}:*")
    if typ != "OK" or not data or not data[0]:
        return
    uids = [u for u in data[0].split() if int(u) >= last]
    for u in uids:
        typ, md = m.uid("fetch", u, "(BODY.PEEK[]<0.30000>)")
        if typ != "OK" or not md or md[0] is None:
            continue
        msg = email.message_from_bytes(md[0][1], policy=email.policy.default)
        print(f"=== uid {u.decode()}")
        print(f"From: {dh(msg['From'])}")
        print(f"To: {dh(msg['To'])}")
        print(f"Subject: {dh(msg['Subject'])}")
        print(f"Date: {msg['Date']}")
        snippet = body_snippet(msg)
        if snippet:
            print(f"Body: {snippet}")
        print()


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("sweep", "new", "bin"):
        sys.exit(__doc__)
    if cmd == "bin" and len(sys.argv) < 3:
        sys.exit("bin needs a comma-separated UID list")
    m = connect()
    try:
        if cmd == "bin":
            bin_uids(m, sys.argv[2])
        else:
            {"sweep": sweep, "new": new}[cmd](m)
    finally:
        try:
            m.logout()
        except Exception:
            pass


if __name__ == "__main__":
    main()
