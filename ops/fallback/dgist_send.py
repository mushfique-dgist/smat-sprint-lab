#!/usr/bin/env python3
"""Owner-only DGIST sendMessage and Gmail fallback for SMAT-Sprint (Part N.5)."""
import base64
import json
import urllib.parse
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



def scrub_outbound(message):
    """Withhold hard secrets and redact long opaque values in every outbound body."""
    if not isinstance(message, str) or len(message) > 1500:
        raise ValueError("invalid outbound message")
    known = []
    try:
        token, _ = owner_credentials()
        known.append(token)
    except Exception:
        pass
    try:
        settings, _ = email_settings()
        known.append(settings["GMAIL_APP_PASSWORD"])
    except Exception:
        pass
    own_env = Path("/home/aurnab/.config/smatsprint/telegram.env")
    if own_env.exists():
        for line in own_env.read_text().splitlines():
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                known.append(line.split("=", 1)[1])
    stage = Path("/home/aurnab/smatsprint-home/state/drop/staged_bot.json")
    if stage.exists():
        try:
            known.append(json.loads(stage.read_text())["token"])
        except Exception:
            pass
    gh = Path("/home/aurnab/.config/smatsprint/gh/hosts.yml")
    if gh.exists():
        for match in re.finditer(r"oauth_token:\s*([^\s]+)", gh.read_text()):
            known.append(match.group(1))
    for name in ("deploy_key", "drop_x25519"):
        file = Path("/home/aurnab/.config/smatsprint") / name
        if file.exists():
            data = file.read_bytes()
            known.append(base64.b64encode(data).decode())
            if name == "deploy_key":
                known.append(data.decode(errors="ignore"))
    variants = [message, urllib.parse.unquote(message)]
    variants += [re.sub(r"\s+", "", x) for x in variants]
    for run in re.findall(r"[A-Za-z0-9_+/-]{24,}={0,2}", message):
        try:
            raw = base64.urlsafe_b64decode(run + "=" * (-len(run) % 4))
            variants.append(raw.decode(errors="ignore"))
        except Exception:
            pass
    hard = (
        r"\d{6,12}:[A-Za-z0-9_-]{30,50}",
        r"(?:ghp_|gho_|ghs_|ghu_|ghr_|github_pat_|GOCSPX-|ya29\.|1//|AIza)",
        r"eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]+",
        r"-----BEGIN (?:OPENSSH|RSA|EC|PRIVATE) PRIVATE KEY-----",
    )
    if any(re.search(pattern, value) for pattern in hard for value in variants):
        raise ValueError("hard secret class")
    for secret in known:
        compact = re.sub(r"\s+", "", secret)
        if len(compact) >= 16:
            parts = (compact[i:i+16] for i in range(len(compact)-15))
            if any(part in value for part in parts for value in variants):
                raise ValueError("known secret")
    message = re.sub(r"(?:/home/aurnab/|~/)\.config/[^\s<>]+", "[path in secrets directory]", message)
    message = re.sub(r"\b(?:GH_TOKEN|GITHUB_TOKEN|GMAIL_APP_PASSWORD|TELEGRAM_BOT_TOKEN)\b", "[variable name]", message)
    allow = {"github.com", "docs.github.com", "mushfique-dgist.github.io",
             "www.google.com", "accounts.google.com", "console.cloud.google.com",
             "cloud.vast.ai", "vast.ai", "arxiv.org", "doi.org"}
    def link_filter(match):
        url = match.group(0)
        parsed = urllib.parse.urlsplit(url)
        if parsed.hostname in allow:
            return url
        if parsed.hostname == "t.me" and (parsed.path == "/BotFather" or re.fullmatch(r"/[A-Za-z0-9_]+_bot", parsed.path or "")):
            return url
        return "[link removed: " + (parsed.hostname or "unknown") + "]"
    message = re.sub(r"https?://[^\s<>]+", link_filter, message)
    message = re.sub(r"\b[0-9a-fA-F]{41,}\b", lambda m: "[hash "+m.group(0)[:12]+"…]", message)
    message = re.sub(r"\b[A-Za-z0-9+/=_-]{61,}\b", lambda m: "[hash "+m.group(0)[:12]+"…]", message)
    return message


def send_telegram(message):
    message = scrub_outbound(message)
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
    message = scrub_outbound(message)
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
