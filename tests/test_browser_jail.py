"""CPU-only public Pages smoke from the build jail."""
from playwright.sync_api import sync_playwright
CHROME="/home/aurnab/projects/smat-sprint/cache/ms-playwright/chromium_headless_shell-1217/chrome-headless-shell-linux64/chrome-headless-shell"
URL="https://mushfique-dgist.github.io/smat-sprint-lab/drop.html#need=n-20260926-build-5d0b&kind=telegram-bot-token&fp=32c82225a1f973f5"
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=CHROME,args=["--no-sandbox","--disable-gpu"])
    page=browser.new_page()
    page.goto(URL,wait_until="domcontentloaded",timeout=30000)
    page.locator("#drop-form").wait_for(state="visible",timeout=30000)
    assert "Need 5d0b" in page.locator("#need").inner_text()
    browser.close()
print("PASS public Pages drop loads in CPU-only jailed browser")
