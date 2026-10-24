# Branched Codex progression tree
Objective: Build a complete visual progression tree for Magic and Create, then extend the same tree UX to all quest groups without changing existing quest IDs or progress.
Branch: local runtime (no Git repository detected)
Delivery: inline incremental implementation; no quest data migration unless a later verified compatibility step authorizes it.
Test runner: Gradle/JUnit for Virgos Core; direct client artifact verification.

## Specs

S1. "armá el árbol de progreso ramificado completo para Magia y Create"
Acceptance: Magic and Create open in a dedicated lane-based tree view with visible branches, node status, scroll, and quest opening actions.

S2. "después extendelo al resto de las misiones sin romper el progreso existente"
Acceptance: every quest group uses the same tree view; existing Heracles quest IDs, dependencies, completion state and claim behavior remain unchanged.

## Tasks
- T1 S1 inline — implement generic tree screen and explicit Magic/Create lanes — completed
- T2 S2 inline — fallback lane grouping for remaining sections and preserve packets/IDs — completed
- T3 verification — compile/test/build jar and refresh installer bundle — completed

## Log
L1. User request: "Ahora llevemos el Códice al siguiente nivel: armá el árbol de progreso ramificado completo para Magia y Create, y después extendelo al resto de las misiones sin romper el progreso existente."
L2. The tree is client-side visual grouping over existing entries; no server quest JSON or IDs were changed.
L3. Magic has Iron’s Spellbooks, Ars Nouveau and Mastery lanes; Create has Power/Movement, Processing and Automation lanes; other groups derive lanes from quest ID prefixes.
L4. Client review found and fixed a reflection bug in TreeScreen: group positions must call the Heracles location's position accessor; without it the adapter silently fell back to the original screen. Lane classification now covers scuela_* Create/Magic IDs, branch completion counters, hover states and dependency labels.\nL5. Verification: :codexJar --rerun-tasks passed; installer bundle refreshed with SHA256 7184462c8ec9209959698d94d51d0fdb0b2b16fdb747c1d37cef102a1c73d098.
L6. Added lightweight client animations: fade-in overlay on Hub/Tree, pulsing branch connectors and hover emphasis without moving hitboxes; this keeps interaction stable while making navigation feel less static. Verification: :codexJar --rerun-tasks and 	est passed; installer SHA256 566a22d003f4af715b898dc095f81e928bd0606998ff147e6e283f1fa9602e3f.
L7. Static review without Minecraft found logic gaps: Hub routes overflowed narrow screens, Tree scroll range left the last node clipped, and generic groups could create too many columns. Added Hub route scrolling/visibility, exact Tree max-scroll/node visibility bounds, and a four-lane cap with an Otros lane for generic groups. Verified with :codexJar --rerun-tasks, 	est, JSON/group geometry assertions, and installer lock/hash validation.
