#!/usr/bin/env python3
"""Owner-only DGIST sendMessage and Gmail fallback for SMAT-Sprint (Part N.5)."""
import json
import re
import smtplib
import sys
import urllib.request
from email.message import EmailMessage
from pathlib import Path

COURSE_ENV = Path("/home/aurnab/.config/dgist-agents/course/service.env")
NOTICE_ENV = Path("/home/aurnab/.config/dgist-agents/notice/service.env")


def read_exact(path, names):
    found = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        for name in names:
            if raw.startswith(name + "="):
                if name in found:
                    raise ValueError("duplicate required setting")
                found[name] = raw[len(name) + 1:].strip().strip('"').strip("'")
    if set(found) != set(names):
        raise ValueError("missing required setting")
    return found


def owner_credentials():
    found = read_exact(COURSE_ENV, ("TELEGRAM_BOT_TOKEN", "TELEGRAM_OWNER_CHAT_ID"))
    if not re.fullmatch(r"[1-9][0-9]*", found["TELEGRAM_OWNER_CHAT_ID"]):
        raise ValueError("owner chat id must be a positive private id")
    if not re.fullmatch(r"[0-9]{6,12}:[A-Za-z0-9_-]{30,50}", found["TELEGRAM_BOT_TOKEN"]):
        raise ValueError("invalid bot token format")
    return found["TELEGRAM_BOT_TOKEN"], int(found["TELEGRAM_OWNER_CHAT_ID"])


def send_telegram(message):
    token, owner_id = owner_credentials()
    body = json.dumps({
        "chat_id": owner_id,
        "text": message,
        "link_preview_options": {"is_disabled": True},
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.telegram.org/bot" + token + "/sendMessage",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        result = json.load(response)
    if result.get("ok") is not True or result.get("result", {}).get("chat", {}).get("id") != owner_id:
        raise RuntimeError("send did not confirm owner chat")


def email_settings():
    found = read_exact(NOTICE_ENV, ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "GMAIL_SMTP_HOST", "GMAIL_SMTP_PORT", "GMAIL_TO"))
    address_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    if not re.fullmatch(address_pattern, found["GMAIL_TO"]):
        raise ValueError("GMAIL_TO must be one address")
    if not re.fullmatch(address_pattern, found["GMAIL_ADDRESS"]):
        raise ValueError("GMAIL_ADDRESS must be one address")
    port = int(found["GMAIL_SMTP_PORT"])
    if port not in (465, 587):
        raise ValueError("unexpected SMTP port")
    return found, port


def send_email(subject, message):
    settings, port = email_settings()
    mail = EmailMessage()
    mail["Subject"] = subject
    mail["From"] = settings["GMAIL_ADDRESS"]
    mail["To"] = settings["GMAIL_TO"]
    mail.set_content(message)
    if port == 465:
        with smtplib.SMTP_SSL(settings["GMAIL_SMTP_HOST"], port, timeout=20) as smtp:
            smtp.login(settings["GMAIL_ADDRESS"], settings["GMAIL_APP_PASSWORD"])
            smtp.send_message(mail)
    else:
        with smtplib.SMTP(settings["GMAIL_SMTP_HOST"], port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(settings["GMAIL_ADDRESS"], settings["GMAIL_APP_PASSWORD"])
            smtp.send_message(mail)


if __name__ == "__main__":
    try:
        message = sys.stdin.read()
        if not message or len(message) > 1500:
            raise ValueError("message length")
        if sys.argv[1:] == ["--email"]:
            send_email("SMAT-Sprint: action needed on your phone", message)
        elif len(sys.argv) == 1:
            send_telegram(message)
        else:
            raise ValueError("invalid arguments")
    except Exception:
        print("owner-only fallback send failed", file=sys.stderr)
        sys.exit(1)
    print("sent")
