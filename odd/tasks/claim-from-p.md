# Claim from the P menu
Objective: Add a Spanish claim action to the existing in-game P permissions entry, preserving native claim authorization.
Branch: codex/project-cleanup-and-docs; delivery: local implementation, no deployment or publication; runner: Java17 Gradle offline checks. Forecast: ~300 authored lines.

## Specs
S1. “Sí, integrá «Reclamar parcela» en el menú de P para que podamos reclamar y configurar los permisos desde el mismo lugar, todo en español.” Acceptance: free land opens Spanish claim action, successful personal claim opens existing permissions; owned land keeps permissions; foreign/unavailable land cannot be claimed by this menu.
S2. “Probalo sin abrir Minecraft si no hace falta.” Acceptance: deterministic free/owned/foreign/unavailable/stale-location/auth/native-failure checks, focused test and full check/build; independent verifier for Risk item2 (claims/authorization). No client, live claims, server restart, deployment or GitHub mutation in scope.

## Tasks
- T1 [S1,S2] inline (one cohesive behavior; no writer trigger): regression tests RED, safe claim adapter/menu and Spanish help; complete (RED -> GREEN; focused and full checks PASS); commit 1269996f150dd84c17d3ce48b6914f8fdc365a42.
- T2 [S1,S2] independent verifier (Risk item2): focused and full offline checks, scratch audit; complete (independent PASS, no blockers).

## Log
L1. “Sí, integrá «Reclamar parcela» en el menú de P para que podamos reclamar y configurar los permisos desde el mismo lugar, todo en español. Probalo sin abrir Minecraft si no hace falta.”
L2. Map: P invokes virgos permisos. current() null conflates free, foreign and unavailable; add typed lookup. Delegate only native player-source oclaims claim, never elevated manager API. Recheck original dimension/chunk, authentication and personal mode before claiming; open permissions only on fresh own-claim result. Test classpath currently loses cached OpenPAC fallback, so reuse dependency in tests. Installed public release remains untouched.
L3. Pure test RED: Successful native claim opens permissions assertion failed against stub. GREEN after guarded flow; focus Gradle checkClaimPermissions PASS1m42s. Full offline check jar codexJar PASS2m2s,29actionabletasks (independent verifier), extra adversarial scratch probesPASS. Existing permission/native-ID tests remainPASS. Parent reran public puremain successfully. No rendered/live-world GUI execution; noMinecraft launched.
L4. First Gradle invocation had an unquoted PowerShell -D split; aborted only verified own wrapper/daemon and reran with quoted JVM args. Effective1GiB heap andoneworker confirmed. Unrelated VSCode/JVM processes untouched. New builtCore21d3e46679976604dccf2ed917028944d3f3a909dacecd69ca768d02d29630eb; installedCore remainsb3663855c65555fac0805d603e1d56563b9469578bb6b3005693d56d6dd14cc5. No deployment or publication. Risk: item2 (claims authorization); independent verifierPASS. Rollback: remove new claim-entry flow/menu adapter/tests and restore previous manual/guide instructions; native permissions/persisted format unchanged.
L5. Source committed locally as1269996f150dd84c17d3ce48b6914f8fdc365a42. Native committed assessment vsffe2737: medium, review_duefalse/under_budget (no native review started). Independent authorization verifierPASS stands. No push/release/deployment; publicserver and GitHubinstaller26 unchanged.
