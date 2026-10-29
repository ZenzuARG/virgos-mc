# Make DH retrieval observable and backpack opening safe
Branch: `codex/create-addons-lab`; delivery: local source fix and validated client artifact before any public rollout; runner: Gradle assemble/check plus runtime log probes.

## Specs

S1. "Correji ambos errores, no des por sentado que funciona el DH en el servidor porque la realidad es que no esta funcionando, esos numeros que ves estan siempre estaticos y no avanzan, nunca reconstrute el lod". Acceptance: the client compatibility layer must ship the active retrieval-progress mixin, terminal remote retrievals must advance the native remaining estimate, and a server-backed session must prove Data/Mapping completion rather than relying on packet receipt alone.

S2. "y revisa bien la logica de la mochila, no quiero que este problema le ocurra a mas personas". Acceptance: B remains the backpack opener from world/player inventory, but pressing B while BackpackScreen is already open must not route a global menu slot index into the nested-backpack packet path; the fix must preserve authoritative player/backpack data and prevent the known transient slot mismatch.

## Tasks
- T1 [S1] inline, DONE, e957218: make remote retrieval progress terminal and verify client packaging/runtime mixin application.
- T2 [S2] inline, DONE, e957218: block unsafe nested B path and verify source build plus runtime behavior.
- T3 [S1,S2] inline, DONE, 380e810: package/lab validation, GitHub v2.2.3 publication, verified public backup, and public restart.

## Log
L1. User: "Correji ambos errores, no des por sentado que funciona el DH en el servidor porque la realidad es que no esta funcionando, esos numeros que ves estan siempre estaticos y no avanzan, nunca reconstrute el lod, y revisa bien la logica de la mochila, no quiero que este problema le ocurra a mas personas"
L2. Mapping evidence: native DH 3.3.3 does not decrement `estimatedTotalChunkCount`; the source mixin only handles SUCCESS and stale client artifacts lack the mixin. Backpack issue is a global BackpackScreen slot index (for example 193) being sent as a storage-local index during a repeated/nested B action.
L3. Replaced the success-only HEAD hook with a terminal-future hook that decrements on SUCCESS and failed terminal requests, ignores REQUIRES_SPLITTING until child requests finish, and deduplicates shared futures with a weak identity set. `assemble` passed; pinned native-bytecode checks remain unavailable because the local DH jar hash differs from the historical pinned fixture.
L4. Backpack guard now blocks B while BackpackScreen is open, preventing global menu indices such as 193 from being sent as storage-local indices. B remains available from world/player inventory.
L5. Installed rebuilt client addon SHA256 `4A8B4E1E977847FB...` after backing up the previous `6E871D0F963...` jar to `D:\proyectos\mc-server\.runtime\client-backups\20261028-dh-backpack-fix`; public server was not changed.
L6. Verification: `assemble` passed; `checkOrdering`, `checkChunkyReadiness`, and `checkChunkyLodServing` passed. The native `checkLevelPublication`, `checkPayloadOwnership`, and grouped-payload checks remain blocked by the repository's historical pinned-DH SHA mismatch, not by compilation. Review assessment for commit `e957218` returned medium/under_budget.
L7. Release/deployment: v2.2.3 was published by CI run 40798256192 from source tag `v2.2.3`; the public server was backed up with 8470 verified files, updated with Core SHA `a09133f3...` and DH compat SHA `4a8b4e1e...`, passed `validar-entrega.ps1`, and restarted with `Done (17.939s)`. Worlds, player data, and DH cache were preserved.
