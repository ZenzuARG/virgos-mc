# Virgos-MC 3.0.4 release

Objective: publish a clean patch release containing the menu diagnostics, Create/magic additions, and refreshed client package.
Branch: `codex/project-cleanup-and-docs`; delivery: `ask-on-risk`; test runner: Python unittest + offline Gradle checks.

## Specs

1. **S1 — Menu/auth behavior**: User request (verbatim): “Bien, implementemos todo y lancemos un release nuevo, prolijo”. The release must include the already-authorized fix that makes `/virgos menu` and `/virgos guia` explain AuthMe, client-handshake, and `/login` blocking states instead of failing silently. Acceptance: focused menu regression tests pass and the rebuilt server/client jars embed the current release identity.
2. **S2 — Content package**: Include the authorized Create expansion and conservative magic configuration already present in the working tree. Acceptance: lock, override, and compatibility tests pass and the release package contains no QA/runtime-private files.
3. **S3 — Release identity**: Prepare a new patch release `3.0.4` with a new installer revision and matching client release/fingerprint across source, candidate metadata, server update config, docs, and locks. Acceptance: candidate consistency and archive reproducibility checks pass.
4. **S4 — Publication**: Validate the release artifacts and prepare the exact tag/release inputs. Remote publication is pending explicit authorization for the GitHub destination and operation; no remote mutation is inferred from local release preparation.

## Tasks

- T1 [S1,S2] inline — reconcile current uncommitted feature changes and update release identity; status DONE; commits `d77ff2e`, `4d85c63`
- T2 [S3] inline — build deterministic Core/Codex and candidate installer/MRPack; status DONE; commit `4fde69d`
- T3 [S4] inline — run focused/full validation and stage release evidence; status DONE; commit `4fde69d`
- T4 [S4] inline — publish tag/release only after remote authorization; status DONE; tag `v3.0.4`, Actions run `43788209072`, release published

## Log

L1. User request: “Bien, implementemos todo y lancemos un release nuevo, prolijo”.
L2. Existing working tree already contains menu/guide diagnostics, Create addon locks/overrides, conservative Iron's Spells configs, and related tests from the prior authorized work; this release task packages those changes rather than widening gameplay scope.
L3. Release identity advanced from 3.0.3 to 3.0.4 with installer revision 24. Offline Gradle Core/Codex checks passed, deterministic installer/MRPack generation passed (133 required and 3 optional files), and the full Python suite passed 100 tests with 3 environment skips.
L4. Local TreeFeller rebuild was attempted but the machine has no Java 17 compiler; GitHub Actions remains the authoritative full release gate for that server-only artifact.
L5. User authorized GitHub publication to `origin`; branch and tag `v3.0.4` were pushed, Actions run `43788209072` completed successfully, and GitHub release `v3.0.4` was confirmed published with installer and MRPack assets.
L6. The live server was stopped with a verified automatic backup, restarted from the rebuilt core, and confirmed ready. Boot initially exposed an invalid `item` reference for `forge:gems/amethyst`; the override was corrected to a Forge tag, the focused recipe test passed, and a clean restart reported zero failed recipes.
