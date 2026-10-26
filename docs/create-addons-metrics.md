# Comparable Create addon laboratory measurements

Use the two test-only observers with the same warmed fixture, camera, window,
FPS cap, graphics/DH settings and sample duration for every variant. They do not
place machines or change inventories. Public service activity remains a measured
covariate, never something these observers pause.

## Install and measure

`addonsQaJar` builds the universal `virgos_addons_qa` observer separately from
Core/Codex. The controls-only `qaJar` build supplies the existing client observer.
Neither belongs in a release. The server observer runs only from canonical
`D:/proyectos/mc-server-lab/create-addons-20261025/<variant>/server`, with dedicated
server, port `25575`, level name `virgos_world`, and its exact matching storage
path. Allowed variants: `baseline`, `crafts`, `bells`, `cei`, `combined`,
`baseline-after`. A wrong role/path/port/world logs a diagnostic and performs no
observer file writes or operations; its universal JAR has no client references.

1. Prepare the fixture through the normal lab console. Keep all observed blocks
   within inclusive x32..160, y60..100, z-32..96; keep their chunks loaded normally.
2. Warm the scene before sampling. Join/authenticate normally, close all screens,
   fix player position/yaw/pitch, window size, FPS cap and graphics settings.
   Start the client with `-Dvirgos.qa.render=true`.
3. Append independent JSON lines after each observer is running. Use a unique
   alphanumeric/underscore/hyphen correlation ID (1..48 characters). Never reuse
   IDs: outputs are atomic and existing files are not replaced.

Server requests go in `server/virgos-addons-qa/commands.jsonl`:

```json
{"id":"idle01","action":"sample_start","seconds":60}
{"id":"blocks01","action":"snapshot_blocks","positions":[[48,65,0],[49,65,0]]}
```

Create that request directory only inside the prepared role. The observer accepts
one request per second; the file is bounded to 1MiB. `sample_start` accepts integer
30..300 seconds and returns `<id>-started.json`, then automatically `<id>.json`
at completion. `{"id":"early01","action":"sample_stop"}` closes the current
window early and writes `early01.json` containing the original `sampleId`.
Archive the generated request file between JVM runs to avoid replaying old lines.

Client requests use the existing `client2/virgos-qa/commands.jsonl` protocol:

```json
{"id":"idle01","action":"sample_start","seconds":60}
```

Automatic completion creates `frames-idle01.json`. Early `sample_stop` requires a
new `id`. Sampling aborts with an error result if the scene/menu, position, camera,
window, render/simulation distance, FPS cap or VSync changes. It never changes
those settings. Existing actions and output files remain unchanged.

## Read the measurements correctly

| Output | Meaning |
| --- | --- |
| Server `count`, `averageMs`, `medianMs`, `p95Ms`, `maxMs` | Real Forge `ServerTickEvent.START` to `END` duration, **not** wall time including tick pacing/sleep. Includes observer overhead; use the same observer in all variants. |
| `nativeAverageTickMsControl` | Native engine rolling tick-time control, distinct from the sampled Forge boundary. |
| Client `sampleCount`, `averageFPS`, `medianFrameMs`, `p95FrameMs` | Consecutive rendered END timestamps in-game. FPS is interval count divided by measured interval time, not a configured target or smoothed title counter. |
| CPU/heap fields | Process CPU-time delta and CPU cores used over elapsed wall time; end-of-window heap used/max bytes. These are not OS RSS/private-memory counters. Collect OS metrics separately. |
| Client `settings` | Initial actual camera/position, pixel window, cap/VSync, graphics/render/simulation distance and focus state. Keep focus conditions comparable. |
| `blocks` | Actual registry ID, complete blockstate string and block-entity NBT string for up to256 loaded positions in the bounded fixture. No chunk loads, placement or arbitrary commands. |

Quantiles use nearest rank (ceil(n*q), one-based). Empty samples have zero values;
reject them as insufficient proof. Do not compare cold boot to warmed samples or
claim universal factory performance from a bounded workload. Repeat matched
baseline/variant/baseline-after windows and report noise and public-load covariates.

## Open current registered JEI recipes

The additive client action below uses JEI's public focus factory and recipes GUI,
not synthetic ingredients, tag seeding, cache replacement or Screen mouse helpers:

```json
{"action":"show_recipe","item":"create:polished_rose_quartz"}
```

It creates an OUTPUT item-stack focus and calls `IRecipesGui.show(IFocus)` on the
current runtime. Then use the existing screenshot action. A registered item with
no current recipes may legitimately display no results; this action is not a
recipe-integrity assertion. No JEI compile dependency was added.

## Check-only build

Use Java17 and the existing offline Forge cache. The focused `checkAddonsQa` task
pins nearest-rank statistics, reset, sampling/time/position/ID bounds and wrong
role/port/path denial; full `check` includes it. Build `addonsQaJar` with reobf.
For `qaJar`, use an external init script selecting only
`dev/dh-compat/qa/mc/virgos/qa/ClientProbe.java`, excluding trace classes and mixin
resources as in the existing controls-only lab flow. Keep all build scratch outside
the checkout. Native operation/performance remains pending until the parent runs
the isolated full-pack matrix; a successful build is not native acceptance.
