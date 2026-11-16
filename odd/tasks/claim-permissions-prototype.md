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

## Tasks
- T1 · S1-S3 · inline · complete · commit: d1830b5

## Log
- L2 (2026-11-16): Added `/virgos permisos`, a 3-screen chest-menu prototype, and a Virgos menu entry. Gradle `compileJava` passed with existing deprecation warnings.
- L1 (2026-11-16): "Sí, hagámoslo exclusivamente dentro del juego y dejemos el panel web sólo para administradores. Empecemos por el prototipo de la pantalla de permisos de parcelas."
