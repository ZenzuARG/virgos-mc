# Project cleanup, optimization, and information refresh
Branch: `codex/project-cleanup-and-docs`; delivery: reviewable work-unit commits; runner: PowerShell, Gradle offline checks, repository scripts

## Specs

### S1 — Safe repository cleanup
User request: "Limpiemos un poco el proyecto, borremos cosas innecesarias, optimicemos codigo y actualicemos informacion"

Authorized scope: remove only generated or clearly disposable artifacts after checking they are not referenced by active task records or needed for the next offline build. Preserve live worlds, backups, `.runtime` rollback/evidence, credentials, mods, plugins, `.cache` dependency caches, `.atl` tool metadata, and the pre-existing `TownServices.java` edit. Acceptance: repository state is auditable; no live data or active user work is deleted; `git status`, reference scans, and cleanup manifest identify every removed path.

Checks: bounded inventory before/after; `git diff --check`; no server start or restart; no destructive cleanup of high-risk runtime data.

### S2 — Release and user-information reconciliation
Authorized scope: make README and player/source-maintenance information distinguish the published 2.2.2 state from the 3.0.3 release candidate. Do not promote 3.0.3, rewrite published locks, or claim release publication. Acceptance: version, installer, memory, and candidate-status instructions are truthful and link to durable tracked evidence.

Checks: `rg` scan for stale 2.0.0 claims in user-facing docs; JSON parse for release metadata; Markdown structural readback.

### S3 — Narrow TownServices optimization
Authorized scope: preserve the existing menu resilience fix while reducing repeated allocation of immutable topic/label metadata in `/virgos menu`; retain click validation, clickable chat fallback, and command behavior. Do not redesign commands or change player-visible wording.

Checks: focused Java/Gradle tests or offline `check` if no narrower runner exists; `git diff --check`; source readback; behavior-preserving inspection.

### S4 — Historical/ephemeral reference cleanup
Authorized scope: update only stale user-facing references that point to absent ephemeral evidence; retain historical task records and audit provenance. Acceptance: durable docs say when evidence is local/ignored instead of linking to paths readers cannot obtain.

Checks: bounded reference scan and Markdown readback.

## Tasks
- T1 [S1] inline — inventory and remove only approved disposable artifacts; status DONE (removed `.mixin.out/`, preserved high-risk/runtime data); commit N/A
- T2 [S2,S4] inline — reconcile README/player/source docs and stale ephemeral links; status DONE (published 2.2.2 separated from candidate 3.0.3; historical `.lab` evidence labeled local); commit N/A
- T3 [S3] inline — optimize TownServices metadata allocations while preserving the uncommitted fix; status DONE (static menu metadata preserves wording and fallback behavior); commit N/A
- T4 [S1-S4] inline — run focused checks, record cleanup manifest, and close work unit; status DONE (offline Gradle check passed); commit `d678887`

## Log
L1. User request: "Limpiemos un poco el proyecto, borremos cosas innecesarias, optimicemos codigo y actualicemos informacion"
L2. Read-only inventory found release metadata disagreement: published `pack/current-release.json` is 2.2.2, `pack/candidates/current.json` selects candidate 3.0.3, and `pack/deployed-release.json` is historical. Large runtime/data trees are high-risk and remain protected.
L3. Existing uncommitted `TownServices.java` menu resilience work must be preserved and verified before any optimization.
L4. T1 removed only ignored `.mixin.out/` build output. The incomplete 6.5 GB post-stop backup remains pending explicit cleanup; all world, backup, runtime, cache, artifact, report, and crash evidence was preserved.
L5. T2 updated README, player installation, source-maintenance, Discord, and implementation notes without promoting candidate 3.0.3 or rewriting release locks. T3 moved immutable menu metadata to a static record table; the uncommitted actor guard and clickable fallback remain intact.
L6. Offline Gradle `check` passed on 2026-11-05: 20 actionable tasks, including all Virgos Core checks and tests; only existing deprecation warnings were reported.
L7. Work-unit commit `d678887` created as `chore: clean project metadata and menu allocations`; the task document itself is closed in a follow-up documentation commit.
L8. User explicitly authorized deleting the incomplete `backups/full/virgos-20261105-102236-auto.zip.partial`; it was removed after confirming the path stayed inside the workspace. The verified prior backup remains intact.

Risk: none (the TownServices change preserves existing command wording, click behavior, and fallback output while moving immutable metadata to static storage).
