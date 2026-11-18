# Pre-release flow audit and completeness pass
Branch: `codex/project-cleanup-and-docs`; delivery: inline reviewable work units; runner: Python unittest, PowerShell validation, Gradle checks, and bounded QA scripts.
Objective: audit every player-facing release flow before the next release, fix confirmed regressions, and verify the shipped client/server experience is complete.

## Specs

### S1 — Audit all player-facing flows
User request: "Espera, antes de mandar otro release, arreglemos mas problemas o bugs de este estilo, revisa todo los flujos, y verifique que este todo presente y la experiencia sea completa"

Authorized scope: inspect authentication, commands, menu/guide navigation, quests/codex, keybindings, client packaging/update, server startup, and release validation. Preserve worlds, player data, backups, credentials, runtime evidence, and unrelated pre-existing edits.

Acceptance: every audited flow has concrete evidence, gaps are classified as fixed, pending, or not reproducible, and no release is claimed until the required checks pass.

Checks: bounded source/test inventory, focused regression tests, client/server artifact inspection, and applicable offline validation.

### S2 — Fix confirmed regressions without release publication
Authorized scope: implement only confirmed bugs discovered during S1; keep changes reviewable and do not publish, push, restart the public server, or overwrite release locks without a separate user request.

Acceptance: each fix has a regression check and a documented root cause; existing behavior outside the request remains unchanged.

Checks: RED/GREEN where a runnable deterministic test exists, focused tests, module compilation, and `git diff --check`.

### S3 — Release readiness decision
Acceptance: produce a concise readiness report listing completed checks, failed or unavailable proof, remaining blockers, and the exact artifacts that would need rebuilding before a release.

Checks: release metadata and installed artifact consistency, client/server jar freshness, and release validation scripts where they are safe and offline.

## Tasks
- T1 [S1] inline — map player-facing flows, release artifacts, and existing QA coverage; status DONE (Python suite, Gradle checks, artifact/lock inventory, command/guide scan); commit N/A
- T2 [S1,S2] inline — reproduce and fix confirmed command/menu/client-control regressions; status DONE (stale TLauncher fixture and Windows TreeFeller license pin fixed; previous menu/backpack fixes preserved); commit N/A
- T3 [S1,S3] inline — verify packaged artifacts, installer/update paths, and release metadata; status DONE (candidate 3.0.3 metadata, custom-artifact locks, staged installer/MRPack, and published 2.2.2 pointer intentionally separated); commit N/A
- T4 [S2,S3] inline — run focused and applicable full checks; status DONE (96 Python tests pass/3 skips, DH prepare/build checks pass, 16 TLauncher checks pass, release validation and local protocol ping pass); runtime client QA and post-restart log scan pass; commit N/A
- T5 [S3] inline — write readiness report and next-step blockers; status DONE (release-ready locally, not published); commit N/A

## Log
L1. User: "Espera, antes de mandar otro release, arreglemos mas problemas o bugs de este estilo, revisa todo los flujos, y verifique que este todo presente y la experiencia sea completa"
L2. Existing uncommitted fixes from the previous session must be preserved: TownServices menu flow, BackpackKeyGuardMixin, and their regression test.
L3. Full Python coverage initially exposed two real readiness defects: the TLauncher fixture still requested retired 5120 MB memory, and the TreeFeller release pin rejected Windows CRLF license bytes even though the frozen hash is LF-normalized.
L4. Fixed TLauncher test inputs to the supported 8192 MB minimum; 16 TLauncher checks pass.
L5. TreeFeller release validation now normalizes GPL license line endings for pin/archive comparisons and emits LF-normalized license artifacts; 91 Python tests pass with 3 environment-dependent skips.
L6. Virgos Core Gradle `check` passed (20 actionable tasks) and DH compatibility Gradle `check` passed (10 actionable tasks). Client standard lock is 2.2.7-r21 with 130/133 files present; 3 missing entries are optional, but required `virgos_codex` and `virgos_dh_compat` hashes do not match the lock and must be rebuilt/reinstalled before any release.
L7. Release metadata is not aligned for publication: `pack/current-release.json` is 2.2.2, `pack/candidates/current.json` points to 3.0.3, and the working tree has uncommitted source/artifact changes. No release or restart was performed.
L8. Local server protocol ping is healthy (`1.20.1`, protocol 763, 2/10 players) and `validar-entrega.ps1` reports `OK` with 129 components, but `logs/latest.log` records repeated `Slot 48 greater than inventory slot count` errors while Librero was testing the backpack flow. This confirms the deployed client still contains the old guard and the fix cannot be considered verified until the rebuilt client artifact is installed and retested.
L9. Startup/runtime logs also retain non-fatal advisories: offline/insecure mode, an Iron's Spellbooks HTTP timeout, unknown DH generator warnings for Twilight Forest, TreeFeller unknown materials, and Ketting unknown entity types. These require classification before release; no blind config or mod changes were made.
L10. Rebuilt local artifacts after the source fixes: `dev/virgos-core/build/libs/virgos_core-2.0.0.jar`, `virgos_codex-2.0.0.jar`, and `dev/dh-compat/build/libs/virgos_dh_compat-0.1.0.jar`. The rebuilt jars remain unstaged and were not copied into `mods` or `client/standard/mods`.
L11. With explicit user authorization, the public server was restarted through `run-public.cjs` using a temporary custom-artifact lock and the rebuilt server jars; an isolated QA client used the rebuilt client jars. `/virgos menu` opened, a menu item click closed the menu and routed to the guide flow, and two distinct Sophisticated Backpacks were opened by hovering each inventory slot and pressing B. Pressing B again inside BackpackScreen did not nest or corrupt the menu.
L12. During that runtime QA, no new `Slot 48 greater than inventory slot count` errors appeared after the candidate startup. One unrelated Lootr missing-loot-table error remained (`incendium:steam/rare`) and is pending classification. The QA account was logged out; the public server remains up with Librero as the only player.
L13. Added `incendium:steam/rare` aliases in the live KubeJS data and release override, targeting the existing `incendium:pipeline/rare` table. `/reload` was tested and failed with Ketting's `CraftServer.reload` null-world error, so a clean public restart was required.
L14. After the clean restart and verified backup, post-start runtime scan found zero `ERROR`, `Exception`, Lootr, `incendium:steam/rare`, unresolved-loot, or failed-handler lines; the public `list` command reports 0/10 players online. The focused alias regression test passes.
L15. TreeFeller's `COPPER_AXE` warning was traced to the generated plugin `tools` list; Minecraft 1.20.1 has no Bukkit material with that name. Added a narrow override and startup normalizer that removes only the exact unsupported entry while preserving the rest of the config.
L16. The normalizer runs before validation in both `scripts/iniciar.ps1` and `scripts/run-public.cjs`; focused TreeFeller config tests pass and the independent verifier found no blockers.
L17. After the public restart and automatic backup, the latest post-start log segment contains zero `COPPER_AXE`, TreeFeller unknown-material, Lootr, error, exception, or failure matches. Remaining warnings are the known offline voice-chat and ModernFix startup advisories; publication metadata remains unreconciled.
L18. The candidate release is now coherently staged as 3.0.3: rebuilt DH patched artifact `3aca79ff…` is installed on both server and standard client, root and candidate custom-artifact locks agree, and the fresh installer/MRPack contain client release `3.0.3` with 130 required and 3 optional files.
L19. `pack/current-release.json` remains the published 2.2.2 record by design; rewriting it before publication would falsely mark the candidate as published. `pack/candidates/current.json` and `pack/candidates/3.0.3/release.json` are the authoritative local release-ready metadata.
L20. After restarting with the patched DH artifact, protocol ping remains healthy (`1.20.1`, protocol 763, 0/10 players) and the post-start log again contains zero errors, exceptions, Lootr failures, `COPPER_AXE`, or unknown-material lines. The only startup warnings are the known offline voice-chat and ModernFix advisories.
L21. The first standalone DH compatibility check was invoked with the patched runtime JAR and correctly rejected it as an unrecognized native DH input; rerunning the check with the pinned upstream compile input passed all 10 actionable tasks. The release preparation check itself already passed with the patched output.
L22. The independent release verifier initially found missing local sources for the candidate lock; staging all four locked JARs under `pack/candidates/3.0.3/artifacts/` resolved that blocker. A second read-only verification passed candidate source resolution, hashes/sizes, archive manifests, and clean runtime-log checks.
L23. User explicitly authorized replacing the existing remote `v3.0.3`; commit `18e7cd5` was pushed, the tag was force-updated, and GitHub Actions run `42832728454` completed successfully, including the publish step. The public server remains on the verified 3.0.3 runtime.
