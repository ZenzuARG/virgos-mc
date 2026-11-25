# Objective: optimization phase 2
Branch: codex/project-cleanup-and-docs
Delivery: server-side only; no client release; preserve online-mode=false
Test runner: PowerShell validation, Python backup fixture, health reports, controlled runtime audit

## Specs

S1. "Lleva a cabo los 4 puntos a optimizar" — clean stale partial backups, review/fix Playit flow without breaking public access, run maintenance/restore/health verification, and measure gameplay before/after tuning.
S2. "me gustaria agrandar un poco la distancia de vision, a 12 chunks aunque sea, la de simulacion a 9 puede ser" — set server view-distance=12 and simulation-distance=9, then verify the live server and health metrics.
S3. "server-side" — do not require a new client release for this phase; preserve online-mode=false.
S4. Preserve world/player data and make reversible backups before destructive cleanup or config changes.
S5. Do not claim performance success from configuration alone; record measured TPS, tick latency, memory, entities, and backup outcome.

## Tasks
- T1 (S1,S4): Inventory and quarantine stale `.partial` backups — inline; catalogued 11 stale partials (72,985,703,286 bytes), preserved a manifest, removed the incomplete artifacts after confirming verified full backups, and added 24-hour automatic partial retention cleanup — status: complete — commit: pending
- T2 (S1,S3): Audit Playit control/tunnel health and apply only safe server-side changes — inline; control channel shows resets, but public Minecraft protocol check returned OK on `virgos-mc.playit.plus:64083` with protocol 763 and 0/10 players; no tunnel change justified — status: complete (no-op) — commit: pending
- T3 (S1,S4,S5): Run controlled maintenance/restore/health workflow — inline; current health snapshot written at `.runtime/health/20261125T133640Z.json`, and the isolated restore drill report remains PASS with 147,542 blocks and zero route findings — status: complete — commit: pending
- T4 (S2,S5): Change distances to 12/9 and verify runtime metrics — inline; server.properties now 12/9, startup confirms both values, TPS remains 20, memory 2.3/7.1 GB (31%), 105 entities and 1 item — status: complete — commit: pending
- T5 (S1-S5): Final audit, retention/backup verification, and report — inline; latest backup verified 11,946 files, no `.partial` artifacts remain, public Playit protocol check OK, server PID 19704 active, and online-mode=false preserved — status: complete — commit: pending

Risk: item 1 (view/simulation distance and backup retention change persisted world/operational behavior); assessment pending after commit.

## Log
L1. Lleva a cabo los 4 puntos a optimizar, y me gustaria agrandar un poco la distancia de vision, a 12 chunks aunque sea, la de simulacion a 9 puede ser, que te parece?
