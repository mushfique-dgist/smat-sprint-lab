# Current milestone and task
M0 (Part N): finish the phone bridge and bounded builder bootstrap. CPU-only setup continues while another autoresearch occupies the GPU.

# Done
- Read the handoff README first, followed E.8 step 0 for GitHub login, then read the full master prompt from Page one and 02_RESEARCH_DIRECTIONS.md. No goal mode or subagents.
- Isolated gh 2.101.0 passed checksum and logged in as mushfique-dgist. Need 1 was resolved by an independent gh_auth check.
- Private mushfique-dgist/smat-sprint-lab repository, deploy key, and public Pages drop shell are live. The Pages branch contains only public shell assets.
- Need 2 was delivered to the configured single-recipient Gmail fallback after the DGIST bot returned HTTP 400 chat not found for the configured positive owner id. Its encrypted phone drop passed browser/PyNaCl checks; the corrected message with the PC fallback was sent again through Gmail.
- Send-only bridge, fixed-operation launcher, and bounded wrapper run from the pinned svc-2 service worktree. The wrapper's launch state is in state/codexwrap/state.json; any M0 continuation runs in the CPU-only jail. Full bot mode is gated by full_test_passed.json.
- CPU-only build jail passed foreign-secret, process, user-bus, no-GPU, read-only-state, and writable-spool canaries. A real Codex builder-mode-1 canary returned CHECKED using the private Codex home without changing shared config.
- Browser/PyNaCl sealed-box round trip, known vector, stale fingerprint refusal, private-issue intake, owner checks, scrubber checks, full-bridge fake callback/reply cases, wrapper bootstrap/recovery cases, and 10,000 unique need IDs passed.
- The nearest AGENTS.md and a fresh rendered prompt were checked; the context audit passed. Foreign services and shared Codex config remain untouched.

# Next
1. Finish CPU fake-backend cases for full bridge, outage and crash paths. Full bot mode remains gated until that and real phone smoke pass.
2. Process the encrypted bot token and verify the owner's private /start when the phone drop arrives. The corrected need is already on the configured phone email route.
3. Complete remaining launcher and wrapper controls, release protocol, and N.11 adversarial cases. Keep all work CPU-only until GPU admission is safe.
4. Defer final CUDA-in-jail and science GPU canaries until GPU admission is safe; no GPU job is running for SMAT-Sprint.

# Detached jobs
- None. The bridge, launcher and unarmed wrapper are persistent user services, not detached experiment jobs.

# Open needs
- n-20260926-build-5d0b: create the programme bot on the phone and submit its token through the live encrypted Pages drop. The configured Gmail route is aurnab0001@gmail.com.

# Red tests / open bugs
- DGIST bot sendMessage to the configured positive owner id returned HTTP 400 chat not found. Telegram delivery is unverified; Gmail is the current phone route.
- The own bot has not been created or started, so real full-mode smoke cannot pass yet. The bridge remains send-only.
- N.11 is not yet complete: full outage/crash matrix, commands, reissue scheduling and real bot cases remain. Full mode is not trusted or enabled.
- A foreign autoresearch process is occupying the GPU. Final CUDA-in-jail and scientific acceptance remain open, with no GPU use from this project.
- The running services are pinned to svc-2. The first-session report and end.json precede the one-time M0 arm operation.
