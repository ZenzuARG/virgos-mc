# KubeJS generated-resource startup race
Objective: Fix the observed null generated-resource stream and verify a real public server restart without launching a Minecraft client.
Branch: codex/project-cleanup-and-docs; baseline d0cc041; delivery ask-on-risk (local work-unit commits only); forecast about 300 authored lines; runner Gradle checkKubeJsGeneratedStreams/check/jar and managed public restart.

## Specs
### S1 — Correct the startup failure
User request: "Arreglá también el fallo de arranque de KubeJS y comprobá que el servidor reinicie bien. No abras Minecraft si no hace falta."
Acceptance: Reproduce the installed KubeJS lazy-cache invalidation race; serialize generated-resource fetch/stream construction/forget without replacing resource contents, hiding supplier failures or disabling datapacks. Verify the injected guard activates during actual server startup.
Checks: Deterministic installed-bytecode RED/GREEN probe; stream/cache regression tests; full Gradle check and jar.

### S2 — Verify the public restart and preserve release identity
User constraint: "Acordate de armar el release correctamente y que el servidor tome la version correcta, siempre tenemos ese fallo"
Acceptance: Verified backup precedes deployment; public server reaches Done and answers readiness checks with the corrected Core. No Minecraft client is launched. Record hashes and rollback evidence.
Implementation assumption: Server-only patch 3.0.7 retains the already verified client release 3.0.6 and installer 25; no new client installation is needed for this server-side guard.
Checks: Release/hash preflight; managed stop/backup/start; activation marker, datapack/script loading, server thread/readiness and absence of the recorded failure.

## Tasks
- T1 · S1 · inline · code verified / activation pending · Risk: item 4 (shared-cache concurrency); independent verifier after own checks; commit pending.
- T2 · S2 · inline · pending · Risk: item 5 (server release/deployment); commit pending.

## Log
- L1 (2026-11-17): "Arreglá también el fallo de arranque de KubeJS y comprobá que el servidor reinicie bien. No abras Minecraft si no hace falta."
- L2: Current allowAsyncStreams=false was not overwritten. Installed code gates recipe parallel streams only, not vanilla resource opens. GeneratedData wraps Lazy.get then forgets file-backed entries; Lazy.forget clears value before cached. Concurrent opens can observe null. Prior failed boot evidence: .lab/reports/3.0.6-startup-failure.log. The specific failing resource ID was not logged.
- L3: Mapping found no external invalidator of the same generated cache. Debug size reads are disabled and occur before publication; concurrent export remains outside this startup-only guard. Preserve every datapack and normal cache-forgetting semantics. No client launched.

- L4: RED forced the installed Lazy invalidation window and reproduced ByteArrayInputStream null-buffer NPE. GREEN checkKubeJsGeneratedStreams/check/jar; packaged-helper independent probe PASS, counterfactual without only the monitor FAIL, restored packaged helper PASS. Bytecode wiring verified, require1 exact descriptor. Every existing gameplay class is byte-identical to deployed3.0.6; only two classes were added and manifest/mixin configuration changed. No Minecraft client launched. Runtime activation remains required before completion.
