# Claim permissions prototype
Objective: Add an in-game Spanish prototype screen for parcel permissions, using Virgos Core menus and keeping the web panel administrator-only.
Branch: codex/project-cleanup-and-docs · Delivery: inline work unit · Test runner: Gradle compileJava

## Specs

### S1 — In-game entry point
Authorized scope: Add `/virgos permisos` and a button from the existing Virgos menu.
Acceptance: An authenticated player can open a Spanish parcel-permissions prototype from inside the game; unauthenticated access remains blocked.
Checks: Gradle compileJava; command registration readback.

### S2 — Understandable permission screen
Authorized scope: Show a parcel title, group cards for Familia, Amigos, Visitantes, and an individual-exceptions entry with Spanish labels and short explanations.
Acceptance: The first screen communicates what each group is for without exposing technical permission nodes.
Checks: Gradle compileJava; source readback.

### S3 — Interactive prototype controls
Authorized scope: Open a group detail screen and toggle common actions (storage, machines, doors, building, breaking, animals) in a per-session prototype state; provide a back action and an explicit prototype status.
Acceptance: Clicking a group opens its controls, toggles change visible state, and the UI clearly says changes are prototype-only until persistence is wired.
Checks: Gradle compileJava; focused source inspection.

### S4 — Persisted claim permissions
Authorized scope: Replace session-only toggles with an adapter backed by Open Parties and Claims, resolving the claim at the player's current position and failing closed when no claim or native API is available.
Acceptance: Permission changes survive menu close, reconnect, and server restart; no-claim and unavailable-API cases do not mutate data.
Checks: Adapter unit tests; Forge QA for owner, friend, visitor, individual override, reconnect, and no-claim cases.

### S5 — Public rollout safety
Authorized scope: Rebuild and hash the Core artifact, run existing regression QA plus the new permissions matrix, create a verified backup, and deploy only through the repository's release path.
Acceptance: The public server starts with the new artifact and rollback evidence; existing world/player data and credentials remain preserved.
Checks: Gradle check/jar/codexJar; package validation; isolated lab QA; deployment preflight.

## Tasks
- T1 · S1-S3 · inline · complete · commit: 4b72d9a
- T2 · S4 · inline · complete · commit: e659137
- T3 · S5 · inline · partial · commit: pending (public startup verified; interactive permission smoke test pending)

## Log
- L2 (2026-11-16): Added `/virgos permisos`, a 3-screen chest-menu prototype, and a Virgos menu entry. Gradle `compileJava` passed with existing deprecation warnings.
- L3 (2026-11-16): "Puli todo el sistema, analizalo de punta a punta y lo implementamos y probamos en el servidor publico, pero por eso mismo quiero que este bien pulido todo, asi lo implementamos de una vez, luego hare pruebas y ajustamos cosas"
- L4 (2026-11-16): Public deployment is authorized for the server represented by this workspace using the local authenticated session, but only after artifact rebuild, backup, isolated QA, and release preflight.
- L5 (2026-11-16): Added a native Open Parties and Claims adapter, persisted claim policy JSON, group membership editing, individual allow/deny/inherit exceptions, and option synchronization. `compileJava` and `check jar` passed; public rollout remains pending because the live server currently has a connected player.
- L6 (2026-11-16): Built and deployed the locked Core artifact after a verified public backup. Startup reached `Done`, the runtime reported release 3.0.4, and the main-claim `subConfigIndex=-1` bug was fixed. Automated interactive UI verification remains partial because the QA client hit death-screen/handshake limitations; no claim permission data was left behind by the test.
- L1 (2026-11-16): "Sí, hagámoslo exclusivamente dentro del juego y dejemos el panel web sólo para administradores. Empecemos por el prototipo de la pantalla de permisos de parcelas."
