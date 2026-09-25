"""Real browser/PyNaCl cross-check for the phone secret drop."""
import base64
import hashlib
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode

from nacl.public import Box, PrivateKey, PublicKey, SealedBox
from playwright.sync_api import sync_playwright

PROJECT = Path(__file__).resolve().parents[1]
DASH = PROJECT / "dashboard"
KEY = json.loads((DASH / "drop-key.json").read_text())
PRIVATE = PrivateKey(Path("/home/aurnab/.config/smatsprint/drop_x25519").read_bytes())
CHROME = "/home/aurnab/projects/smat-sprint/cache/ms-playwright/chromium_headless_shell-1217/chrome-headless-shell-linux64/chrome-headless-shell"

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DASH), **kw)
    def log_message(self, *a): pass

server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME,
                                    args=["--no-sandbox", "--disable-gpu"])
        page = browser.new_page()
        need = "n-20260926-build-abcd"
        fragment = urlencode({"need":need,"kind":"telegram-bot-token",
                              "fp":KEY["fingerprint"][:16]})
        page.goto(f"http://127.0.0.1:{server.server_port}/drop.html#{fragment}")
        page.locator("#drop-form").wait_for(state="visible")
        token = "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"
        page.locator("#value").fill(token)
        page.locator("#username").fill("SMAT_sprint_lab_bot")
        page.locator("#drop-form button").click()
        page.locator("#submit-link").wait_for(state="visible")
        envelope = page.locator("#sealed").input_value()
        encoded = envelope.splitlines()[1]
        ciphertext = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        plain = SealedBox(PRIVATE).decrypt(ciphertext)
        payload = json.loads(plain)
        assert payload["value"] == token and payload["username"] == "SMAT_sprint_lab_bot"
        assert payload["need_id"] == need and payload["key_id"] == KEY["key_id"]
        assert page.locator("#value").input_value() == ""
        assert "body=" in page.locator("#submit-link").get_attribute("href")

        # Fixed cross-implementation vector in both directions.
        recipient = base64.b64decode(KEY["public_key"])
        eph_secret = bytes(range(1, 33))
        eph = PrivateKey(eph_secret)
        nonce = hashlib.blake2b(bytes(eph.public_key) + recipient, digest_size=24).digest()
        expected = Box(eph, PublicKey(recipient)).encrypt(b"fixed-vector", nonce).ciphertext
        from_js = page.evaluate("""({pub,secret}) => {
          const e = nacl.box.keyPair.fromSecretKey(new Uint8Array(secret));
          const r = new Uint8Array(pub);
          const both = new Uint8Array(e.publicKey.length+r.length);
          both.set(e.publicKey); both.set(r,e.publicKey.length);
          const nonce = blake2b(both,null,24);
          const cipher = nacl.box(new TextEncoder().encode('fixed-vector'),nonce,r,e.secretKey);
          return {nonce:Array.from(nonce),cipher:Array.from(cipher)};
        }""", {"pub":list(recipient),"secret":list(eph_secret)})
        assert bytes(from_js["nonce"]) == nonce
        assert bytes(from_js["cipher"]) == expected

        bad = browser.new_page()
        bad.goto(f"http://127.0.0.1:{server.server_port}/drop.html#need={need}&kind=telegram-bot-token&fp=0000000000000000")
        assert bad.locator("#drop-form").is_hidden()
        assert "key changed" in bad.locator("#status").inner_text()
        browser.close()
    print("PASS browser sealed box opens in PyNaCl; fixed vector; wrong fingerprint refused")
finally:
    server.shutdown()
