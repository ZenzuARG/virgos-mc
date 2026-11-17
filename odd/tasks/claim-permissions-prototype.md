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

### S6 — Automated end-to-end proof
User request: "Arreglá la prueba automatizada y verificá de punta a punta que el menú abra, permita agregar jugadores, guardar permisos de cofres y persista todo después de reconectar."
Acceptance: Two QA accounts exercise the real UI and chest protection before/after reconnect; assert saved membership and permissions; report failures honestly and restore temporary claims/blocks.
Checks: focused regression tests, Gradle check, real Forge client E2E and independent security verification.

### S7 — Correct the parcel shortcut
User report: "En uno de los clientes el menu de P no cambio y en el otro sale el menu de jugadores original de minecraft, o algo parecido, pero no permite modificar permisos de nada"
Acceptance: P opens the Spanish parcel permission action, migrating both observed old defaults while preserving unrelated personal controls.
Checks: shipped-policy migration regression; client build; real client shortcut probe.

## Tasks
- T1 · S1-S3 · inline · complete · commit: 4b72d9a
- T2 · S4 · inline · reopened (runtime defects found) · commit: e659137
- T3 · S5 · inline · partial · commit: pending (public startup verified; interactive permission smoke test pending)

- T5 · S7 · inline · in progress · Risk: item 5 (client artifact delivery)
- T4 · S6 · inline · in progress · Risk: items 1, 2, 5 (persistent authorization and deployment) · independent verifier required

## Log
- L2 (2026-11-16): Added `/virgos permisos`, a 3-screen chest-menu prototype, and a Virgos menu entry. Gradle `compileJava` passed with existing deprecation warnings.
- L3 (2026-11-16): "Puli todo el sistema, analizalo de punta a punta y lo implementamos y probamos en el servidor publico, pero por eso mismo quiero que este bien pulido todo, asi lo implementamos de una vez, luego hare pruebas y ajustamos cosas"
- L4 (2026-11-16): Public deployment is authorized for the server represented by this workspace using the local authenticated session, but only after artifact rebuild, backup, isolated QA, and release preflight.
- L5 (2026-11-16): Added a native Open Parties and Claims adapter, persisted claim policy JSON, group membership editing, individual allow/deny/inherit exceptions, and option synchronization. `compileJava` and `check jar` passed; public rollout remains pending because the live server currently has a connected player.
- L6 (2026-11-16): Built and deployed the locked Core artifact after a verified public backup. Startup reached `Done`, the runtime reported release 3.0.4, and the main-claim `subConfigIndex=-1` bug was fixed. Automated interactive UI verification remains partial because the QA client hit death-screen/handshake limitations; no claim permission data was left behind by the test.
- L1 (2026-11-16): "Sí, hagámoslo exclusivamente dentro del juego y dejemos el panel web sólo para administradores. Empecemos por el prototipo de la pantalla de permisos de parcelas."

- L7: S6 requested automated proof. Found null service initialization, incorrect main-config resolution, false booleans treated as enabled, and a stale QA2 mod set. Prior startup-only evidence did not verify the UI.

- L8 (2026-11-16): S7 reproduced from saved controls: standard P is vanilla Social Interactions; secondary P is OPAC. No client parcel action exists. Closed both QA clients to free RAM. Public E2E remains failed at oversized console preflight, not proved.

- L9 (2026-11-16): S7 RED: P must open parcel permissions. GREEN: checkCodexKeys codexJar and full check. Independent artifact verification passed, SHA98af3f96a15aa7e3d6a9caba91e87f277a0467a28192d0fcf060938621ddc66a. Both observed legacy bindings migrate; custom modifiers and J survive. Runtime proof remains unavailable:4GiB QA1 stalled in allocation/GC and timed out after claiming, before menu. Both QA processes stopped; fixture unclaimed, blocks removed, force-load ticket removed. Public client release still3.0.4; new client shortcut NOT publicly distributed. Need agreed test RAM budget before further client launches.
