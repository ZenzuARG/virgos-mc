# Release 3.0.7 with installer 26
Objective: Publish verified server 3.0.7 and compatible client 3.0.6 installer 26 with forced zero mipmaps.
Branch: codex/project-cleanup-and-docs; delivery: single release; checks: Python client tests and packaged PowerShell CLI, no Minecraft.

## Specs
S1. “Dale, reconstruí el paquete con este ajuste y terminá el release de GitHub.” Scope: origin ZenzuARG/virgos-mc, existing local authenticated GitHub credential; exact verified assets only.
S2. “Verificá que incluya la versión correcta y que el instalador ponga mipmaps en 0 también en los clientes ya instalados, sin abrir Minecraft.” Acceptance: server3.0.7/Core pinned hash, client gate3.0.6, installer26; actual packaged CLI converts existing mipmaps4 to0 while preserving other settings; GitHub asset digests match.

## Tasks
- T1 [S1,S2] inline: prepare metadata and rebuild packages; complete; commit d5aac1d.
- T2 [S2] inline + independent verifier (Risk item5 release): verify archives and packaged upgrade; complete (14 client tests, selection RED/GREEN, independent full-lock CLI and PowerShell suite PASS).
- T3 [S1] inline: commit, publish explicit assets and read back remote identity/digests; complete; source/tag commit d5aac1d, GitHub release448174977.

## Log
L1. User request: “Dale, reconstruí el paquete con este ajuste y terminá el release de GitHub. Verificá que incluya la versión correcta y que el instalador ponga mipmaps en 0 también en los clientes ya instalados, sin abrir Minecraft.”
L2. Existing builder requires package version/clientRelease agreement. Keep client3.0.6, bump installer25 to26. Current server remains3.0.7. GitHub v3.0.7 absent (authenticated404); no remote tag. Manual publication uses existing Git credential, never exposes it. Forecast under200 authored lines beyond existing88-line mipmap change.
L3. Production installer26 SHA101a42292e5465e4ff79502249807fba9512774d5528c2f392013192aac833f2; MRPack90490ae3f5a4ef57fffdd51d1e6df634fc627029b9247beb1b3c910a7a697f3e. Independent actual original-manifest133-mod offline CLI PASS; existing4 to0, other preferences preserved, verify-only unchanged, repeat idempotent. One stale PowerShell fixture assertion corrected and rechecked PASS. Workflow selection RED then GREEN for separate client identity. Risk: item5 (installer/release/workflow). Native assess high/review_due due workflow shell source; publication pending native candidate choice.
L4. User confirmation: “1, revisá este cambio y después terminá de publicar el release en GitHub con el instalador 26, sin abrir Minecraft.”
L5. Native immutable reliability review approved with no findings; exact acknowledgement burned authority. Reviewed source commit d5aac1de826d9912427ab79a6b8abd74444e1847 pushed, exact v3.0.7 tag verified at same commit. Published https://github.com/ZenzuARG/virgos-mc/releases/tag/v3.0.7 at 2026-11-17T05:16:22Z; latest verified. Exactly four explicit assets uploaded and all remote SHA256 digests/sizes match local. No Minecraft launch or server restart. Rollback boundary: installer26 source/template changes and metadata; previous installer25 remains in historical release, server hotfix independent. GitHub Actions build not run or claimed; local deterministic build, suite and packaged CLI proof apply.
