#!/usr/bin/env python3
"""One-off watcher for the One Direct (Fiesta) insurance certificate.

Rob, 21 Oct 2026: when the certificate email lands, forward it to Aimee
(aimeestokes@icloud.com) and Telegram her that she can use the car for work.

Runs from cron every 5 min. Looks for INBOX mail from One Direct newer than
BASE_UID. If it looks like the certificate / policy documents: forward it
(body + attachments), message Aimee, send Rob a receipt, then remove its own
cron line. Any other One Direct mail pings Rob only (never tells Aimee she
can drive on the strength of a "we need more info" email) and keeps watching.
Gives up and tells Rob if nothing has arrived by DEADLINE.

DRYRUN=1 prints what it would do without sending or touching state.
"""
import datetime
import email
import email.policy
import importlib.util
import os
import re
import smtplib
import subprocess
import sys
import urllib.parse
import urllib.request
from email.message import EmailMessage
from pathlib import Path

BIN = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mt", BIN / "mail-tool.py")
mt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mt)

BASE_UID = 123837  # last One Direct mail before the watch started (portal registration)
SENDER = "onedirect"
FORWARD_TO = "aimeestokes@icloud.com"
AIMEE_CHAT = "221989621"
DEADLINE = datetime.datetime(2026, 10, 24, 12, 0)
STATE = Path.home() / ".local/state/insurance-cert-watch.seen"
CERT_RE = re.compile(r"certificate|policy documents|your documents|cover (is|has been) (now )?(active|confirmed)", re.I)
DRY = os.environ.get("DRYRUN") == "1"
TAG = "insurance-cert-watch.py"


def env(path):
    out = {}
    for line in Path(path).read_text().splitlines():
        k, _, v = line.strip().partition("=")
        if k and not k.startswith("#"):
            out[k] = v.strip('"')
    return out


TG = env(Path.home() / ".config/jarvis/telegram.env")


def telegram(chat, text):
    if DRY:
        print(f"[dry] telegram {chat}: {text}")
        return
    data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
    urllib.request.urlopen(
        f"https://api.telegram.org/bot{TG['TELEGRAM_BOT_TOKEN']}/sendMessage", data, timeout=15
    ).read()


def remove_cron():
    if DRY:
        print("[dry] would remove cron line")
        return
    cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    keep = "".join(l + "\n" for l in cur.splitlines() if TAG not in l)
    subprocess.run(["crontab", "-"], input=keep, text=True, check=True)


def forward(msg):
    icl = env(Path.home() / ".config/jarvis/icloud.env")
    subj = mt.dh(msg["Subject"])
    fwd = EmailMessage()
    fwd["From"] = icl["ICLOUD_USER"]
    fwd["To"] = FORWARD_TO
    fwd["Subject"] = f"Fwd: {subj}"
    header = (
        "Forwarded by Jarvis for Rob: the Fiesta's new One Direct insurance has come through.\n\n"
        "---------- Forwarded message ----------\n"
        f"From: {mt.dh(msg['From'])}\nDate: {msg['Date']}\nSubject: {subj}\n\n"
    )
    plain = msg.get_body(preferencelist=("plain",))
    html = msg.get_body(preferencelist=("html",))
    fwd.set_content(header + (plain.get_content() if plain else "(see HTML version)"))
    if html is not None:
        fwd.add_alternative(
            "<p>" + header.replace("\n", "<br>") + "</p>" + html.get_content(), subtype="html"
        )
    n = 0
    for part in msg.iter_attachments():
        data = part.get_payload(decode=True)
        if not data:
            continue
        maintype, subtype = part.get_content_type().split("/", 1)
        fwd.add_attachment(data, maintype=maintype, subtype=subtype,
                           filename=part.get_filename() or f"attachment-{n + 1}")
        n += 1
    if DRY:
        print(f"[dry] would forward '{subj}' with {n} attachment(s) to {FORWARD_TO}")
        return n
    with smtplib.SMTP("smtp.mail.me.com", 587, timeout=30) as s:
        s.starttls()
        s.login(icl["ICLOUD_USER"], icl["ICLOUD_APP_PASSWORD"])
        s.send_message(fwd)
    return n


def main():
    seen = set(STATE.read_text().split()) if STATE.exists() else set()
    m = mt.connect()
    try:
        m.select("INBOX", readonly=True)
        typ, data = m.uid("search", None, f'(FROM "{SENDER}" UID {BASE_UID + 1}:*)')
        uids = [u for u in (data[0].split() if typ == "OK" and data and data[0] else [])
                if int(u) > BASE_UID and u.decode() not in seen]
        for u in uids:
            typ, md = m.uid("fetch", u, "(BODY.PEEK[])")
            msg = email.message_from_bytes(md[0][1], policy=email.policy.default)
            subj = mt.dh(msg["Subject"])
            text = subj + " " + mt.body_snippet(msg)
            has_pdf = any(p.get_content_type() == "application/pdf" for p in msg.iter_attachments())
            if CERT_RE.search(text) or has_pdf:
                n = forward(msg)
                telegram(AIMEE_CHAT,
                         "Hi Aimee, the Fiesta's new insurance has come through, so you're "
                         "fine to use the car for work. I've forwarded the email to your iCloud. Jarvis")
                telegram(TG["TELEGRAM_CHAT_ID"],
                         f"🚗 One Direct email landed: \"{subj}\". Forwarded to Aimee "
                         f"({n} attachment{'s' if n != 1 else ''}) and told her she can use the car "
                         "for work. Watcher switched itself off.")
                if not DRY:
                    STATE.write_text(" ".join(seen | {u.decode()}))
                remove_cron()
                return
            telegram(TG["TELEGRAM_CHAT_ID"],
                     f"📬 One Direct sent \"{subj}\", but it doesn't look like the certificate, "
                     "so I haven't forwarded it or told Aimee. Still watching.")
            seen.add(u.decode())
            if not DRY:
                STATE.write_text(" ".join(seen))
    finally:
        try:
            m.logout()
        except Exception:
            pass
    if datetime.datetime.now() >= DEADLINE:
        telegram(TG["TELEGRAM_CHAT_ID"],
                 "⚠️ Still no One Direct certificate email by Saturday midday. I've stopped "
                 "watching and Aimee hasn't been told anything. Worth chasing them.")
        remove_cron()


if __name__ == "__main__":
    main()
