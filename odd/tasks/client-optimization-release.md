# Objective: client optimization release
Branch: codex/project-cleanup-and-docs
Delivery: candidate build first; server wire identity retained; publication requires separate explicit remote approval
Test runner: Python unittest + client packaging tests + isolated archive readback

## Specs

S1. "quiero hacerla valer, quiero implementar varias mejoras" — create a meaningful client release with multiple tested improvements, not a cosmetic version bump.
S2. "recorda que tenemos que pushear una version nueva" — prepare a new client release candidate; do not publish remotely until destination/operation approval is explicit.
S3. Keep the compatible server wire identity and `online-mode=false`; no client update is required for server-only changes.
S4. Include the verified client improvements: Ocuwheel, Distant Horizons compatibility/settings, ModernFix dynamic resources, and the Sophisticated Backpacks B-key unbind.
S5. Preserve existing personal client data and provide reproducible installer/MRPack artifacts.

## Tasks
- T1 (S3): Set server simulation-distance back to 6 while retaining view-distance=12 — inline; runtime config applied, effective on next restart; current server restarted and confirmed 6/12 — status: complete — commit: runtime ignored config
- T2 (S1,S4): Prepare client defaults/policy delta and candidate metadata — inline; retain tested Ocuwheel/DH/ModernFix stack, include backpack-key fix, reduce client entity scaling to 0.75, disable cloud rendering, and set biome blending to 0 — status: complete — commit: pending
- T3 (S1,S5): Build reproducible installer and MRPack candidate — inline; external candidate output `C:\Users\zulia\AppData\Local\Temp\virgos-release-3.2.0` — status: complete — commit: pending
- T4 (S1,S5): Run package/archive/installer tests and verify hashes — inline; 17 release-content tests pass, installer test passes, keybinding script passes; one unrelated Java source-shape test remains pre-existing — status: complete — commit: pending
- T5 (S2): Prepare publication handoff without remote mutation — inline — status: pending — commit: pending

## Log
L1. quiero hacerla valer, quiero implementar varias mejoras
L2. recorda que tenemos que pushear una version nueva pero quiero hacerla valer, quiero implementar varias mejoras
