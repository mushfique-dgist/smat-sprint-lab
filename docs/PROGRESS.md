# Current milestone and task
M0 (Part N): build and verify the phone needs bridge, secret drop, build jail, launcher and wrapper.

# Done
- Handoff README, master prompt and research directions read in order; Part E.8 step 0 attempted.
- Isolated gh 2.101.0 copy checksum passed; GitHub device login succeeded as mushfique-dgist.
- Owner-only DGIST send module validates a positive private chat id; Telegram returned HTTP 400 chat not found. Gmail fallback sent the code to its configured single recipient.
- Live Phase 0 checks: 105 GB disk free, 24 GiB MemAvailable, RTX 5090 visible in shell and user unit; EGL rendered 64x64; bubblewrap canary saw CUDA and EGL; transient scope accepted BindsTo and After.

# Next
1. Finish Phase 0 probes, including the exact build-jail, browser, Codex and systemd checks.
2. Commit the spec snapshot and bootstrap documents.
3. Implement the need store, sprintctl CLI and send-only bridge, adopting the completed GitHub login as need 1.
4. Create the private repository and Pages secret-drop shell using only the isolated gh session.
5. Send the BotFather setup need through a verified phone route; build and test full bridge mode.
6. Build and test the jail, named-operation launcher and bounded session wrapper.
7. Arm the wrapper only after M0 tests, progress and end.json are complete.

# Detached jobs
- None. The transient GitHub login unit finished successfully.

# Open needs
- None in a durable need store yet. Telegram bootstrap route is broken: configured DGIST owner chat returns chat not found.

# Red tests / open bugs
- DGIST bot sendMessage to the configured positive owner chat returned HTTP 400 chat not found; no Telegram delivery was claimed.
- Server Codex CLI is 0.155.0-alpha.16.4, so the handoff's 0.153.4 command and jail assumptions need current-version canaries.
- Forge worker unit is failed; this project must leave it untouched.
