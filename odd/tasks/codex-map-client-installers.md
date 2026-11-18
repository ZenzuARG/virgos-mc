# Build the complete Virgos-MC client installers with the updated Códice and surface map

Branch: `codex/project-cleanup-and-docs`. Delivery strategy: ask-on-risk; forecast: approximately 310 authored lines. Test runners: Python unittest and PowerShell offline installer fixtures.

## Specs

- S1 — “Quiero que salga con los instaladores qué veníamos usando pero con los ajustes”: reuse the existing Windows assistant and MRPack format with the verified Códice update, retaining compatibility with the active 3.0.6 client gate.
- S2 — “Agregá el mapa de la M como mapa separado sin pisar los de los chicos”: distribute the surface map with both packages; install it without replacing or activating a player map. Windows assists automatically; MRPack includes the map in an inactive folder with instructions, independent of third-party launcher overwrite behavior.
- S3 — “manteniendo el acceso al perfil y el progreso, los que ya tengan avance reconozcamoslo automaticamente”: package the already verified Códice JAR unchanged. No server modifications or restart.
- S4 — “Recorda mantener el jnstalador lo mas fácil de utilizar, mis amigos no son duchos” and “Así ellos tienen una solución confiable y robusta de 1 click para instalar todo”: guide Windows users to one primary install or repair action. Reuse the saved launcher when it is still usable, detect the only initialized launcher on first use, and do not choose between two launchers or silently switch an existing one.

## Tasks

- [x] T1 S1–S3 | inline release packaging/installer, independent verifier PASS for items 1 and 5.
- [x] T2 S1–S4 | built and verified both complete local installers. Publication and Discord are separate pending steps.
- [x] T3 S4 | inline launcher selection and one primary action. RED missing selector; GREEN with 47 PowerShell installer checks, preview, and eight independently exercised UI states.

## Log

- L1: “Ese es el instalador final? O como un parche? Quiero que salga con los instaladores qué veníamos usando pero con los ajustes”
- The published ZIP is a manual overlay, not the complete installer. Existing Windows ZIP and MRPack contain the prior Códice.
- User added S4 before publication on 2026-11-17 (local time). Packaging checks for initial S1–S3 passed (13 focused Python tests and 42 PowerShell fixture checks, including independently on 5.1); S4 changes the ZIP candidate bytes.
- Final artifacts are `Virgos-MC-3.0.6-instalar.zip` (382,522,106 B, SHA256 `8b9db15e2b552fce1dc1db81acdc4f51dc873ea3cf847a54df5ff048c2481d7b`) and `Virgos-MC-3.0.6.mrpack` (382,489,168 B, SHA256 `bd0046f3deb432b59b67362f17d46303085ed20d7f369cb9d879264eda4ccd44`). Both retain the 3.0.6 client identity and embed the verified Códice and 1284 map tiles.
- Windows PowerShell 5.1 installer fixtures, eight memory regression tests, 13 focused packaging tests and the independent actual assistant/map probes passed. The complete Python suite ran 104 tests (98 passed, three skipped, two failures and one error); the same three failures reproduced in a narrow scratch containing only unchanged prior Códice/release paths. No game or real launcher installation was executed.
