## PART N — Needs: reaching the user on Telegram, the bridge, the secret drop and the session wrapper (build this first)

### N.1 The rule, and why this part is built before anything else

**Nothing in the build or in the programme waits for the user at the PC.** Whenever Codex (during the build) or
the programme (after Codex has left) needs something only the user can do or decide, it creates a **need**. The
need reaches the user's phone on Telegram in plain language, the way a colleague would ask: what is needed, why,
exactly what to do, by when, and what keeps running meanwhile. Everything that does not depend on the need keeps
going. Codex never blocks on a need and never spends tokens waiting for one; the session wrapper (N.8) does the
waiting, as a plain process.

Two failures this part exists to prevent, both from the forge build on 2026-09-22: a one-time GitHub device code
was printed only in the Codex window and expired unread, so the user had to walk to the PC for a second code; and
the forge's dedicated bot needed one line typed at a shell to install its token. Neither may happen here.

**Build order.** Part N is milestone **M0** (Part E.4). The need store and its CLI, the send-only notifier, the
secret drop, the bridge and the session wrapper are built and tested against a fake Telegram backend (N.11)
before anything that could need the user is started, with one deliberate exception: the bootstrap of N.9 uses the
send-only path for the first two needs, because the programme's own bot cannot exist before the user creates it.

Tone, from the user's own example; every phone need is written like this:

> I need to log in to GitHub to create the private dashboard repository. On your phone, open
> https://github.com/login/device and enter the code ABCD-EFGH. It expires at 14:32. Tap Done when you are in, or
> "Send a new code" if it expired. Everything else is continuing; only the repository step is waiting on this.

### N.2 The need record

One JSON file per need, `state/needs/<need_id>.json`, written atomically (tmp, fsync, rename), with
`schema_version: 1`, and one line per transition in the append-only `state/needs/events.jsonl`.

```text
need_id        n-<yyyymmdd>-<slug>-<4 hex>      short id for messages: the last 4 hex digits
code           a registered need code (N.10) or "build" for a build-time ask
kind           phone | pc                        stated in the first word of every message
title          one line, <= 80 chars             "GitHub login for the SMAT-Sprint build"
what           <= 300 chars                      what is needed
why            <= 300 chars                      why it is needed now
steps_phone    [ <= 8 short steps ]              exact links, codes, text to type, button names, what success looks like
steps_pc       [ <= 8 short steps ] | []         for kind=pc, or as an explicit fallback
page_text      optional                          the exact text of the page the user will see, to find the right button
image          optional path                     a screenshot rendered at build time (ops/needs/images/), sent with the message
expires_at     ISO time | null                   device codes: from the provider's expires_in, never guessed
deadline       ISO time | null                   "by when" for decisions and credit
blocking       [ names ]                         what waits on it ("repository creation"); printed as "only X waits"
blocks_build   bool                              true if the session wrapper must hold the next Codex session for it
check          { id, args } | null               from the fixed registry of N.3; a need with a check resolves only when it passes
reissue        { handler, max, count } | null    from the fixed registry of N.3 (device codes); default max 3
reply          none | done | yes_no | pick_one | code | text
options        [ labels ]                        for pick_one; the default used meanwhile is marked and named in the text
pattern        regex | null                      for code/text replies
skippable      bool
created_by     codex-build | runner | controller | bridge | wrapper
status         open | snoozed | resolved | skipped | expired | cancelled
resolution     { how: check | button | reply | skip | cancel, at, detail }
telegram       { message_ids: [...], nonce, last_sent_at, sent_count }
```

Invariants, each with a test (N.11): `reply` can never be `password` or `secret`; long-lived secrets arrive only
through the secret drop (N.6) or the PC fallback; a need with a `check` is never marked resolved by a button press
alone; every status change is one line in `events.jsonl` with the cause; a resolved, skipped, expired or cancelled
need never reopens (a new need is created instead, which keeps the history honest).

### N.3 One protocol, one CLI, two fixed registries

Codex and the programme create needs through exactly one interface:

```bash
sprintctl need create --code build --kind phone \
  --title "GitHub login for the SMAT-Sprint build" \
  --what "Approve a one-time GitHub login so I can create the private repository." \
  --why "The repository holds the code, the ledger and the dashboard." \
  --step "Open https://github.com/login/device" --step "Enter the code ABCD-EFGH" \
  --expires-in 900 --check gh_auth --reissue gh_device_code \
  --blocking "repository creation" --reply done
# prints the need_id at once and returns; it never waits
sprintctl need status <need_id> --json
sprintctl need list --open
sprintctl need cancel <need_id> --reason "no longer needed: the forge session already created it"
```

The Python API (`smatsprint.needs.create(...)`, `.status(...)`, `.list_open()`) is the same code. Nothing else in
the project calls the Telegram API: only the bridge and the notifier inside the bridge package do (a unit test
greps the tree for `api.telegram.org` outside `bridge/`).

**Check registry** (`bridge/checks.py`; ids only, never shell text from a message or a file):
`gh_auth` (the programme's own `GH_CONFIG_DIR`, N.7), `github_repo_access(repo)`, `bot_owner_verified`,
`pages_live(url)`, `dashboard_device_registered(min_count)`, `rclone_about(remote)`, `vast_credit_at_least(usd)`,
`file_present(path_id)` with `path_id` from a fixed map (for example `papers_pdf:<name>`), `sudo_script_ok(name)`
(reads the script's own PASS/FAIL log), `none`. Each check has a timeout of at most 30 s, runs at most once per
minute per need, and reports one plain sentence ("still not logged in", "logged in as mushfique-dgist").

**Reissue registry** (`bridge/reissue.py`): `gh_device_code` (N.7) and `google_device_code` (N.7). A reissue starts
a fresh flow, sends a new message, edits the old one to say "This code has expired; the new one is below", rotates
the button nonce, and increments `count`; after `max` reissues the need stays open with one button, "Send a new
code", and no more automatic reissues.

### N.4 Message shape

Every message is built from a template in `bridge/templates/` with typed fields, never free-form:

```text
[SMAT-Sprint] Phone: <title>
<what> <why>
1. <step>  2. <step>  ...
<expiry or deadline line, in KST, e.g. "The code expires at 14:32.">
<blocking line: "Everything else is continuing; only <blocking> is waiting on this.">
[Done] [Later] [Send a new code] [Skip]          (only the buttons that apply)
                                                  n-…-3fa2 (small print)
```

- First word after the prefix is `Phone:` or `PC only:`. A PC-only message says why the phone cannot do it ("this
  needs your password in a terminal") and gives the exact steps and the checked script; it never assumes an SSH app
  on the phone, though its steps work from one.
- One need per message. Decisions list the options as buttons and say which default is in use meanwhile ("Until
  you choose, I use option 1").
- Messages stay under 1,500 characters. Links are full URLs from the outbound allow-list (N.5). No internal host
  names, no ids beyond the short need id, no secrets, never a request for a password.
- When the exact page text helps the user find the button, include it ("You will see 'Device Activation' and a box
  'Enter the code displayed on your device'"). Screenshots are optional and are rendered at build time from public
  pages only.
- When a need resolves, the bridge edits the original message: buttons removed and one line appended, for example
  "✓ Done at 14:31 — checked: logged in as mushfique-dgist".

### N.5 The bridge

A small stdlib-only Python service (`bridge/`), systemd user unit `smatsprint-bridge.service`: enabled,
`Restart=always`, in `smatsprint-ctl.slice`, `MemoryMax=256M`, no GPU, `UMask=0077`. It is the only process that
reads the programme's bot updates, and it never reads any other bot.

**Loop.** Long-poll `getUpdates(offset, timeout=50, allowed_updates=["message","callback_query"])`; apply each
update (below); send queued outbound messages under the rate limit; run due checks; handle expiries and reissues;
write a heartbeat. No step blocks longer than 60 s (Part R.2): a check or reissue runs as a child process and is
polled.

**Who may talk to it.** An update is accepted only if all hold: `chat.type == "private"`, `chat.id` equals the
owner chat id, `from.id` equals the owner chat id, `from.is_bot` is false, the message is not forwarded (no
`forward_origin`), and its date is less than 24 h old. Everything else is dropped **without a reply** (the bot
does not confirm itself to strangers) and counted; more than 20 drops in an hour produce one alert to the owner.
The owner chat id is the same `TELEGRAM_OWNER_CHAT_ID` the DGIST agents use; it is copied once into the
programme's own `~/.config/smatsprint/telegram.env` at bootstrap (N.9) by a script that reads that one variable and
nothing else. The group chat id in the DGIST file is never read.

**Buttons.** `callback_data` is `v1|<action>|<short_id>|<nonce8>`, at most 64 bytes. On every press the bridge
first calls `answerCallbackQuery` (so the phone's spinner stops), then performs a compare-and-set on the need:
the need must be open and the nonce must be the need's current one. A stale button (an older message, a replaced
code) answers "This button is from an older message; please use the latest one." Actions:

- `done`: run the need's check now; resolve if it passes; otherwise reply with the check's sentence ("Not yet:
  GitHub still shows no login. The code is valid until 14:32.").
- `later`: snooze for 3 h (setting), then send the need once more; the snooze is logged.
- `newcode`: run the reissue handler.
- `skip`: only for skippable needs; logged with the time.
- `opt:<k>`: record the chosen option for pick-one and yes/no needs.
- Wrapper buttons (`continue`, `pausebuild`, `report`) are routed to the wrapper's state file (N.8).

**Text replies** are untrusted input. They are parsed only when exactly one open need expects a text-like reply, or
when the message starts with the need's short id (`3fa2 yes`). Parsing is by type: yes/no (a small synonym list),
pick-one (the number or the label), code (the need's `pattern`), text (length-capped at 500 characters, Unicode
normalised, stored as data, never executed and never inserted into a shell or a file path). Anything else gets a
short help message listing the open needs.

**Commands** from the owner: `/status` (the banner line of `status.json`), `/needs` (open needs, each a link to its
message), `/pause [reason]`, `/resume [reason]`, `/help`. Pause and resume go through the command channel of Part
D.3 with `source: telegram`, are logged in the Ledger panel with their reason (default "sent from Telegram"), and
are answered only after the controller acknowledges ("Paused. GPU verified free of our work at 14:02."). Nothing
else can be commanded from Telegram; the dashboard remains the full interface.

**Outbound safety.** Every outgoing text passes a scrubber before it is sent. It refuses any text that matches a
secret pattern (GitHub token prefixes `ghp_`, `gho_`, `ghs_`, `github_pat_`; a Telegram bot token
`\d{6,12}:[A-Za-z0-9_-]{30,50}`; Google `GOCSPX-`, `ya29.`, `AIza`; private-key headers; long base64 or hex runs
over 40 characters; the Vast key file's pattern), any `~/.config` path, any environment-variable name of a
credential, or any URL outside the allow-list (github.com and its docs and device page, the dashboard URL,
google.com/device, accounts.google.com, console.cloud.google.com, cloud.vast.ai and vast.ai, t.me/BotFather,
arxiv.org, doi.org). A refused message is not sent; one alert goes out by Gmail saying a message was withheld and
which template produced it, never its content.

**Inbound secrets.** A message from the owner that looks like a secret (the same patterns) and is not the expected
answer to a `code` need is deleted at once with `deleteMessage`, its text is never logged (the log says
"secret-like message deleted, 57 characters"), and the bridge replies: "I deleted a message that looked like a
secret. Secrets go through the secret-drop page, never through chat." Short one-time codes a flow asks for are the
only codes accepted by chat, and they are used once and not stored after use.

**Rate and dedup.** At most 1 message per second and 20 per minute to the owner chat; alerts are deduplicated to
one per condition per hour (Part D.8); low-priority information goes into one daily digest at 09:00 KST.

**Crash safety and idempotence.** Processed update ids of the last 48 h live in `state/bridge/seen.jsonl` (with each
update's chat id, message id and date, so a duplicate is recognised even if its id is reused). For each update:
record it as processing, apply the transition (compare-and-set on the need file), record it as done, then advance the
offset in memory and in `state/bridge/offset.json`. A restart re-applies any update left in the processing state;
because every transition is compare-and-set, a second application does nothing. **Never trust a stale saved offset:**
Telegram keeps unconfirmed updates for at most 24 h, may deliver an update twice, and after a week without updates
picks the next update id at random, so a saved offset can be higher than every new id and silently skip them. On
every start the bridge therefore first calls `getUpdates` without an offset (the earliest unconfirmed updates), drops
those already in `seen.jsonl`, and continues from the highest id it sees. Outgoing messages use
`link_preview_options` (the older `disable_web_page_preview` was replaced in Bot API 7.0), and every button press is
answered with `answerCallbackQuery` even when it is rejected; button data can be forged by anyone who talks to the
bot, which is why the owner check and the server-side nonce lookup above decide, never the data itself. To give the
bot a new token after a leak, BotFather's `/token` command regenerates it; the secret drop then delivers the new one.

**Conflicts and outages.** HTTP 409 on `getUpdates` means another process is polling this bot: stop polling for 5
minutes, alert the owner by Gmail ("another process is reading the SMAT-Sprint bot's messages"), and never fight
for the updates. Network errors back off from 5 s to a 10-minute cap; outbound messages queue. After 30 minutes
without Telegram, alerts and phone needs are also sent by Gmail through the SMTP credentials the DGIST agents
already use (read at runtime, never copied), as text with the dashboard link and the statement that e-mail replies
are not read.

**Secrets at rest.** The bot token lives only in `~/.config/smatsprint/telegram.env` (mode 0600, directory 0700),
is read at start, and never appears in argv, a log, `status.json`, the repository or a message. The bridge never
opens `~/.config/dgist-agents/` except for the one-variable copy at bootstrap, and never opens
`~/.config/ugrp-forge/`. A test greps `bridge/` for those paths and for `getUpdates` on any token other than the
programme's own.

### N.6 The secret drop (long-lived secrets from a phone, without chat and without the tailnet)

The programme needs a few long-lived secrets from the user over its life: its own Telegram bot token (M0) and the
Google OAuth client id and secret for Drive (M6); possibly a replacement bot token later. Telegram chats persist on
Telegram's servers, so chat never carries these. The user's phone is **not** on the lab tailnet (checked
2026-09-23: the peers are sail-gpu01, desktop-ri4gdgu, macbook-air and magzhan-windows), so a page on the server's
Tailscale address is not reachable from it. The drop solves this with a sealed box and GitHub's own access control:

- **Keys.** At M0 generate an X25519 key pair on the lab with a pinned library (PyNaCl or `cryptography`). The
  private key lives at `~/.config/smatsprint/drop_x25519` (0600) and never leaves the lab. The public key and its
  fingerprint are published as `drop-key.json` in the public Pages shell (D.3); that file holds nothing else.
- **The page.** `drop.html` in the shell is static: vendored `tweetnacl` plus a sealed-box helper, pinned by hash,
  under the CSP of D.3 with `connect-src https://api.github.com`. The URL fragment carries `need=<id>&kind=<kind>`
  (a fragment never reaches any server). The page explains in two sentences what it does, takes the secret in a
  password-type field, validates its format for the kind (bot token `^\d{6,12}:[A-Za-z0-9_-]{30,50}$`; Google client
  id `^\d+-[a-z0-9]+\.apps\.googleusercontent\.com$` and secret `^GOCSPX-[A-Za-z0-9_-]{20,}$`), seals
  `{need_id, kind, value, created_at}` to the lab's public key, clears the field, and delivers the ciphertext:
  1. if a dashboard token is present in this browser (after M2): one tap PUTs `inbox/drop-<need_id>-<rand>.json` on
     the `control` branch, like any command (D.3);
  2. otherwise (M0, before the dashboard exists): it opens a pre-filled new-issue page on the **private** repository
     (`/issues/new?title=secret-drop%20<need_id>&body=<ciphertext>`); the user, who is logged in to GitHub on the
     phone, taps "Submit new issue".
- **Authenticity** comes from GitHub: only the owner can open an issue in the private repository or write to
  `control`; the public key alone cannot inject anything. **Confidentiality** comes from the sealed box: the issue
  body and the git history hold only ciphertext that only the lab can open.
- **The lab side** (`bridge/drop.py`): reads drops from the controller's normal `control` fetch, and during M0 only
  from the repository's issues through the build's `gh` session; decrypts; accepts a drop only for an open need of
  the same kind whose id matches, once (a replayed ciphertext is rejected); validates; applies (for a bot token:
  writes `telegram.env` atomically at 0600 and verifies with `getMe` and the owner's `/start`, N.9); resolves the
  need; deletes the issue (`gh issue delete --yes`, the owner is admin of their own repository) or removes the inbox
  file in the daily control-branch cleanup. After the bootstrap secrets are delivered, rotate the key pair and
  republish `drop-key.json`.
- **PC fallback, always offered** in the same message: `ssh sail-gpu`, then `sprintctl secret set <kind>`, which
  reads the value from standard input with echo off (never from argv) and applies it the same way.
- If the user later adds the phone to the tailnet, the setting `phone_on_tailnet` enables a second route: a one-shot
  intake page on the lab's Tailscale address, a random 128-bit path, POST only, single use, valid 30 minutes, never
  on a public interface and never through Tailscale Funnel. It is off by default and not needed.

### N.7 Login and approval flows that must finish on a phone

- **GitHub CLI device login, isolated from the forge.** The forge build's `gh` session lives in `~/.config/gh`
  (logged in as `mushfique-dgist`, token in `hosts.yml`, verified 2026-09-23). Never use it and never log it out: it
  belongs to the forge. `GH_CONFIG_DIR` alone does **not** isolate two logins when a system keyring is available (a
  GNOME keyring daemon runs on this host): gh would store the token under one shared keyring key and either
  programme's logout would delete it. So this programme always uses **both** `GH_CONFIG_DIR=~/.config/smatsprint/gh`
  **and** `--insecure-storage` (the token stays in that directory's `hosts.yml`, mode 0600), pins the `gh` version it
  was tested with (2.101.0, installed by the forge in `~/.local/bin`), and never revokes the GitHub CLI OAuth app on
  github.com (that would revoke every gh token of the account, the forge's and the PC's included). Start the flow
  detached (a transient `systemd-run --user` unit, no TTY), with its output in a log:
  `GH_CONFIG_DIR=… gh auth login --hostname github.com --git-protocol ssh --skip-ssh-key --insecure-storage --scopes repo,workflow`
  (without a TTY, gh prints the one-time code and `https://github.com/login/device` to stderr and waits; that text is
  display output, not a stable interface, which is why the version is pinned; the default scopes lack `workflow`, which
  the dead-man workflow of Part D.8 needs). Parse the code and the URL from the log the moment they appear, create the
  need with `expires_at` 15 minutes after the code appeared (the device-code lifetime), and continue with other work.
  The check is `gh auth status` with that config directory; the reissue handler restarts the flow. When the
  repository, deploy key, rulesets and Pages are set up (M2), run `gh auth logout` with that config directory only.
- **The programme's Telegram bot** (N.9): BotFather on the phone, the token through the secret drop, the owner's
  `/start` to the new bot.
- **Dashboard tokens** (M2): one fine-grained token per device, created on the phone from the pre-filled link of
  D.3 and pasted into the dashboard page on that device, never into Telegram and never onto the server. Check:
  `dashboard_device_registered`.
- **Google Drive** (M6), phone-doable, verified 2026-09-23 against Google's documentation: the OAuth 2.0 flow for
  "TVs and Limited Input devices" lists `https://www.googleapis.com/auth/drive.file` among its allowed scopes, and
  `drive.file` is a non-sensitive scope (no verification, no unverified-app warning once published). The steps: the
  user creates a Google Cloud project, enables the Drive API, configures the consent screen with only `drive.file`
  and **publishes it "In production"** (in "Testing", refresh tokens expire after 7 days; rclone's documentation says
  the Publish button needs a homepage and a privacy-policy URL first, and the Pages site's `privacy.html` serves both),
  and creates an OAuth client of type **"TVs and Limited Input devices"** (not "Desktop app"); the client id and secret
  arrive through the secret drop; the bridge runs the device flow itself (rclone has no device-flow mode) and shows the
  code for google.com/device with its expiry; the lab exchanges the code and writes the token into the programme's own
  rclone config (`RCLONE_CONFIG=~/.config/smatsprint/rclone.conf`, remote `smatsprint-gdrive:`, `scope = drive.file`,
  `client_id`, `client_secret`, `token = <json>`). Whether rclone can refresh a token issued to that client type is
  not documented: M6 tests it live (force a refresh by setting a past expiry, then `rclone about`). If it cannot, the
  bridge refreshes the access token itself before each Drive operation and writes it into the rclone config with
  `config_refresh_token=false`; if even that fails, fall back to rclone's documented remote setup as one PC-only need,
  bundled with any other PC items so the user makes one trip.
- **Vast credit**: the link to the billing page and the amount the dashboard recommends; check
  `vast_credit_at_least`.
- **Decisions**: pick-one or yes/no needs with buttons; the default in use meanwhile is named.
- **Root**: PC only, through the E.5 protocol (one checked idempotent script, one line to type, the password typed
  by the user in their own terminal, never over Telegram).

### N.8 The session wrapper (Codex sessions per milestone; Codex never waits)

The build runs as a sequence of Codex sessions, one or more per milestone, none in goal mode and none with a thread
goal. The user starts the first session (00_README.md). From then on a small wrapper launches each session, reports
its end on Telegram, waits for the needs, and launches the next. **The wrapper waits; Codex does not.**

- **Code and unit.** `codexwrap/wrapper.py`, standard library only; unit `smatsprint-codexwrap.service`, enabled,
  `Restart=always`, in `smatsprint-ctl.slice`. State in `state/codexwrap/state.json`; one directory per session,
  `state/codexwrap/sessions/<n>/` with `prompt.md`, `events.jsonl`, `last_message.md`, `exit_code`, `started_at`,
  `ended_at`, `milestone`.
- **States.** `DISARMED` (after install; launches nothing) → `ARMED(next)` → `RUNNING(n)` → `ENDED(n)` →
  `ARMED(next)` | `HOLD(reason)` | `BACKOFF(until)` | `DONE`. Transitions are logged.
- **Launch rule.** From `ARMED`, launch when (a) no open need has `blocks_build: true`, **or** the user tapped
  Continue on the last milestone message; (b) the build is not paused (the "Pause build" button); (c) no recorded
  Codex usage-limit cool-down is running. Exactly one session at a time: a flock plus a check that no
  `smatsprint-codex-*` unit is active.
- **The session command.** Each session runs as a transient unit `smatsprint-codex-<n>` through
  `systemd-run --user` in `smatsprint-ctl.slice` with CPU and memory caps (so a runaway build process can never
  starve the forge or a lab mate), wrapped in `timeout --signal=TERM --kill-after=60s <build_session_cap_h>`
  (default 10 h): `codex exec <builder mode flags> -C /home/aurnab/projects/smat-sprint --json -o <last_message.md> -`
  with the prompt on stdin and the event stream in `events.jsonl`. Never pass `--ephemeral`. `codex exec` sessions are
  hidden from the Codex app's sidebar and from the resume list unless `--include-non-interactive` is given (openai/codex
  #42083, open on 2026-09-23), so the wrapper records each session's thread id from the `thread.started` event in
  `sessions/<n>/thread_id` and the milestone message tells the user how to open it
  (`codex resume --include-non-interactive <id>`). Sessions are never resumed by the wrapper: `codex exec resume`
  does not keep the original session's permissions, so each milestone starts a fresh session.
- **Builder mode: verified limits, then the user's decision.** Checked on 2026-09-23 against Codex 0.153.4 (the
  installed CLI) and its source at `rust-v0.153.4`: `codex exec` defaults to approval `never`, so a blocked command
  fails back to the model and never hangs; the `workspace-write` sandbox shows a minimal `/dev` (no GPU; openai/codex
  #19676 and #3141 still open), mounts `.git` read-only (commit and push fail), and with network off blocks `connect()`
  even to local sockets (so `systemctl --user` fails); `-p/--profile` only layers `$CODEX_HOME/<name>.config.toml` and is
  not a permission profile; named permission profiles (`[permissions.<name>]`) exist but do not compose with `-s` or
  `--approve-for-me`. **No sandboxed mode lets an unattended builder install, use the network, push and start GPU
  units.** So in M0: (1) run the canaries once to confirm this on the live CLI (write outside the allowed paths;
  `cat ~/.config/ugrp-forge/CANARY`; a network fetch; `git push --dry-run`; `systemd-run --user --wait nvidia-smi`),
  and record the results in `docs/PLAN.md`; (2) send the user one **decision need** with two options and this
  explanation: "Unattended build sessions need either full access with guardrails, which lets a session install,
  push and start GPU tests by itself, or auto-review mode, which is more contained but stalls when its reviewer denies
  a step (after 90 s, and three denials end the session; the wrapper then retries)."
  - **Option 1, full access with guardrails** (recommended; the default the wrapper uses once the user taps it):
    `--dangerously-bypass-approvals-and-sandbox` plus `-c shell_environment_policy.ignore_default_excludes=false`
    (so no `*KEY*`, `*SECRET*` or `*TOKEN*` environment variable reaches the model), `forbidden` command rules in the
    builder's config layer for `sudo`, `reboot`, `shutdown`, `systemctl --user stop|restart|disable` on any unit not
    named `smatsprint-*`, `kill` of processes outside `smatsprint.slice`, `rm -rf` outside the project and sandbox
    trees, `vastai destroy|stop` without the `smatsprint-` label, and `gh auth logout` without `GH_CONFIG_DIR`
    (guardrails only: whether rules apply in bypass mode is undocumented, so the canary tests them), the capped slice
    above, the deploy key as the only GitHub credential for pushes, and the rules of Part A.5.
  - **Option 2, auto-review**: `--approve-for-me -c sandbox_workspace_write.network_access=true`, with prefix rules
    that run exactly two things outside the sandbox: a vetted `git push` helper and the vetted GPU launcher
    `~/.local/share/smatsprint/launch-detached` (installed read-only, outside the workspace); never a bare
    `systemd-run --user` or `systemctl --user` rule, because either escapes the sandbox completely.
  - Until the user answers, sessions do CPU-only work that needs neither pushing nor the GPU, and queue the rest.
  - The programme's own LLM calls (Part C.13) never use either mode: they run read-only, with no shell and no network,
    and every auto-approval or bypass flag is banned there.
- **The standard continue prompt** (verbatim, on stdin):

  ```text
  Continue the SMAT-Sprint build. You are a builder session launched by the session wrapper.
  Read AGENTS.md, then docs/PROGRESS.md, then the governing Part named there (in docs/spec/).
  Needs resolved since the last session: <list with outcomes>. Needs still open: <list>.
  The user's latest decisions: <list>. Do not set a thread goal and do not use goal mode.
  Work through safe steps; create needs with sprintctl need create; never wait for one.
  End your turn only under Part E.4 (a)-(c), with the E.7 report as your final message.
  ```

- **When a session ends.** Read `last_message.md` (the E.7 report), the "Current milestone" line of
  `docs/PROGRESS.md`, and the open needs. Send one milestone message: what changed in three plain lines, whether
  the milestone is complete, the open needs as links, and the buttons **Continue**, **Pause build** and **Send the
  full report** (the report goes as a scrubbed Markdown document). Then `ARMED(next)`, or `HOLD` if the report
  names a blocker that only the user can clear, or `DONE` after the last milestone.
- **Failures.** A session that ends within 5 minutes with an error, or reports a usage limit, goes to `BACKOFF`:
  for a usage limit, until the reset time parsed from the error text (record the exact strings in `docs/PLAN.md`
  during M0), otherwise 10 minutes, doubling. Three consecutive failures create a need: "The build is stuck: <first
  line of the error>. [Retry] [Pause build]".
- **Restart safety.** After a wrapper restart, a running `smatsprint-codex-<n>` unit is re-adopted, never launched
  twice; a finished one is processed exactly once (its `ended_at` file is the marker).
- **What it never does.** Edit code, answer a need, run a check that changes anything, call an LLM other than by
  launching the next Codex session, or launch a session while another is active.

### N.9 The M0 bootstrap, in order

1. Phase 0 probes (Part E.8); no user action is needed for them.
2. The need store, the CLI and the **send-only** notifier. Until the programme's bot exists, the notifier sends
   through the shared DGIST bot with `sendMessage` only, prefixed `[SMAT-Sprint build]`. That bot is long-polled by
   `dgist-course-telegram.service` (checked 2026-09-23), so the programme never calls `getUpdates` or `setWebhook`
   on it. Messages sent this way carry no buttons; they say that a new code will arrive automatically if one expires.
3. **Need 1 (phone): GitHub login for this programme** (N.7), with automatic reissue (at most 3). While it is open:
   build the bridge and the wrapper against the fake backend (N.11), and the Phase 0 plan.
4. When `gh_auth` passes: create the private repository `mushfique-dgist/smat-sprint-lab` (the name was free on
   2026-09-23), push the skeleton, create `gh-pages` with only `index.html` ("dashboard not built yet"),
   `drop.html`, `drop-key.json`, `privacy.html` and `.nojekyll`, and enable Pages (D.3). Check `pages_live`.
5. **Need 2 (phone): create the programme's own bot.** Steps: open https://t.me/BotFather, send `/newbot`, name it
   "SMAT Sprint", choose a username ending in `_bot` (suggest one), copy the token BotFather shows; open the drop link
   (in the message), paste, tap Encrypt, tap "Submit new issue"; then open the new bot and tap Start. Check
   `bot_owner_verified`: the token passes `getMe` **and** the new bot has received `/start` from the owner chat id.
   PC fallback in the same message: `sprintctl secret set telegram-bot-token`.
6. Start `smatsprint-bridge.service` on the new bot. Its first message: "Connected. From now on I ask here, with
   buttons." From here on every need goes through the bridge. The DGIST bot is not used again except as a fallback
   before Gmail if the programme's bot token is revoked.
7. Run the N.11 suite against the real bot once: one need with a Done button that the user taps (phone), one
   reply, one stale-button press.
8. Install and arm the wrapper (`sprintctl build arm --next M1`), end the M0 session with the E.7 report. The
   wrapper sends the milestone message and launches M1 as soon as its launch rule holds.

### N.10 Needs after Codex has left (registered codes)

The programme uses the same protocol. Each code has a template, its buttons and its check in
`bridge/templates/`; the dashboard's Needs panel mirrors the open ones. At minimum:

| Code | Kind | Buttons / reply |
|---|---|---|
| `token_expiring` (a dashboard device token within 14 days; the bot token revoked; the drop key rotated) | phone | Done |
| `vast_credit_low` | phone | Done (check: credit) · Pause Vast work |
| `drive_quota_low`, `drive_token_dead` | phone | Done (check: `rclone about`) |
| `queue_empty` | phone | one button per pre-planned evergreen option (Part C.4), plus "Wait" |
| `ladder_crossed` | phone | information; at L3/L4: "Start Phase 2 matrix" · "Strengthen to 5 seeds" · "Later" |
| `paper_gate_decision` | phone | the paper path and venue options (Part G.7) |
| `sandbox_idle_stopped` | phone | information · "Restart it" |
| `location_event` (move, backup or evacuation finished or failed) | phone | information, or the D.4 buttons |
| `lease_cap_reached`, `vast_instance_wont_die`, `vast_instance_wont_start` | phone | the D.2 options |
| `polite_pause_long` | phone | "Keep waiting" · "Move to Vast" |
| `disk_floor` | phone | the prune options of D.7 with sizes |
| `gate_epoch_opened` | phone | information |
| `build_stuck` | phone | Retry · Pause build |
| `root_needed` | pc | the one line to type, and why user space was not enough |
| `unexpected` | phone | "Pause" · "Keep running"; the exact error text and the component |

A unit test asserts that every need raised anywhere in `control/`, `runner/`, `bridge/` and `codexwrap/` uses a
registered code.

### N.11 Tests (fake Telegram backend first, real bot once)

A fake Bot API server (in-process HTTP) implements `getUpdates` with real offset semantics (and 409 when two
pollers overlap), `sendMessage`, `editMessageText`, `editMessageReplyMarkup`, `answerCallbackQuery`,
`deleteMessage`, `sendDocument` and `getMe`, and can be told to fail, hang, delay, reorder or redeliver. Every
scenario below is a test, and every one must pass before the bridge is trusted:

- a Done press with a passing check resolves once; with a failing check it replies with the check's sentence and
  stays open; a Done press on a need without a check resolves it;
- Later snoozes and re-sends exactly once; Skip only on skippable needs;
- an expired device code is reissued automatically, the old message is edited, the nonce rotates, a press on the
  old button gets the stale-button answer, and the reissue stops at `max`;
- text replies for yes/no, pick-one, code and text; an ambiguous reply gets the help message; a 5,000-character
  reply is truncated and stored as data;
- a message from a wrong chat id, from a group chat, forwarded from the owner, or sent by a bot: no reply, no
  effect, counted, and one alert after 20 in an hour;
- a duplicate delivery of the same update id has no second effect; a crash between applying and committing the
  offset, followed by a restart, has no second effect; a restart of the unit in the middle of a device-code flow
  resumes the flow;
- 409 Conflict stops polling, alerts by Gmail, and resumes after the back-off without fighting;
- Telegram down for 30 minutes: needs and alerts go out by Gmail;
- a secret-looking message from the owner is deleted and not logged; an outgoing message containing a token-like
  string is withheld and alerted by Gmail without its content;
- rate limiting holds under a storm of 100 alerts;
- `/pause` and `/resume` travel through the command channel, are acknowledged only after the controller confirms,
  and appear in the Ledger panel with their reason;
- secret drop: a sealed-box round trip; a drop for a closed need, a wrong kind, or a replayed ciphertext is
  rejected; a malformed issue body is ignored; no secret appears in any log, status file, ledger row, journal
  excerpt or git object (scan);
- wrapper: a session ends → one message → the blocking need resolves → exactly one next session starts; Continue
  pressed twice launches once; a wrapper restart during a session re-adopts the running unit; a usage-limit exit
  backs off until the parsed reset time; three failures raise `build_stuck`.

After the programme's bot exists, run the real-bot smoke once (N.9 step 7), and record the result in
`tests/bridge_report.md`.

### N.12 What the bridge, the drop and the wrapper never do

Read or poll any bot but the programme's own; send to any chat but the owner's private chat; send a token, key or
password; ask for a password; run a shell, a path or a command taken from a message; accept a long-lived secret by
chat; launch two Codex sessions; keep a Codex session alive to wait; set a thread goal or use goal mode; touch the
forge's `~/.config/gh`, `~/.config/ugrp-forge/`, its units or its bot.
