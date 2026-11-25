# Objective: stabilize server errors and compatibilities
Branch: codex/project-cleanup-and-docs
Delivery: incremental local fixes; online-mode=false preserved
Test runner: repository validation scripts plus focused log/config checks

## Specs

S1. "soluciona todos los problemas del servidor ya sean error o compatiblidades" — audit the current server state and resolve actionable errors/compatibility issues without changing unrelated user work.
S2. "online-mode=false" — preserve offline authentication because friends do not have premium accounts.
S3. Preserve player/world data and create reversible backups before data or runtime-state changes.
S4. Verify the running server after each runtime-affecting fix and report unresolved warnings honestly.

## Tasks
- T1 (S1-S4): Map current errors, warnings, configs, and runtime state — inline after explorer unavailable; evidence: latest.log has 0 ERROR lines, TreeFeller PALE_OAK/POPLAR warnings, historical InventoryView overflow — status: complete — commit: pending
- T2 (S1,S3,S4): Remove invalid TreeFeller declarations and verify startup — inline; removed unsupported PALE_OAK/POPLAR entries; startup no longer logs those warnings — status: complete — commit: pending
- T3 (S1,S4): Diagnose and fix InventoryView slot overflow with reproduction evidence — inline; root cause was Sophisticated Backpacks key B opening a mismatched menu; unbound key in client policy/default options; keybinding tests pass — status: complete — commit: pending
- T4 (S1,S4): Clean non-fatal recipe/tag compatibility warnings where behavior is unchanged — inline; reviewed and classified as cosmetic/optional integrations; no safe source change identified — status: complete (no-op) — commit: pending
- T5 (S1-S4): Final runtime/log audit and preserve online-mode=false — inline; `validar-entrega.ps1` passed, server PID 31944 responsive, latest.log has 0 ERROR, 0 TreeFeller invalid-tree warnings, 0 InventoryView overflows in current run, and `online-mode=false` — status: complete — commit: e60e7ba
- T6 (S1,S3,S4): Make clean-stop backups tolerate transient Windows file locks — inline; retry read-open up to 10 seconds before failing; lock simulation passed and full delivery validation passed — status: complete — commit: pending

Risk: item 3 (client key default changes affect the published client configuration contract); assessment: medium/under_budget, no native review due.

## Log
L1. soluciona todos los problemas del servidor ya sean error o compatiblidades
