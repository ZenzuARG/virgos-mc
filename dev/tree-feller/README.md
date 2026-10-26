# Guarded server-only tree felling

Version `1.33.0-virgos.3` is a **laboratory candidate**, not a deployment approval. The retained `.1` piston and `.2` species artifacts remain diagnostic-only and unchanged. It patches pinned TreeFeller 1.33.0 rather than replacing its shape, leaf, drop, or tool engine. Players do not install anything. Do not add this JAR to a client or a Forge `mods` directory.

## Build locally

Requires Python 3.10+, a local Java **17 JDK**, and the exact existing inputs listed in `UPSTREAM.json`. No downloads or authenticated sessions are used by the builder. All outputs and compiler caches stay outside the repository; the output directory must not exist yet.

```powershell
$base = 'D:/proyectos/mc-server-lab/create-ingredients-20261025/verification-inputs-corrected/server'
$upstream = 'C:/Users/zulia/AppData/Local/Temp/virgos-tree-feller-source-sulhgdgt'
python -B dev/tree-feller/build.py `
  --upstream-jar "$upstream/TreeFeller-1.33.0.jar" `
  --source-zip "$upstream/source.zip" `
  --bukkit-api "$base/libraries/org/kettingpowered/server/forge/1.20.1-47.4.22-0.6.1/forge-1.20.1-47.4.22-0.6.1-universal.jar" `
  --coreprotect-api 'C:/Users/zulia/AppData/Local/Temp/virgos-ci-public-providers-4_3sj99b/CoreProtect-CE-24.1.jar' `
  --classpath "$base/libraries/net/md-5/bungeecord-chat/1.20-R0.1/bungeecord-chat-1.20-R0.1.jar" `
  --classpath "$base/libraries/com/google/guava/guava/31.1-jre/guava-31.1-jre.jar" `
  --compatibility-jar 'C:/Users/zulia/AppData/Local/Temp/virgos-t10-freeze-v6r0ekk7/candidate/TreeFeller-1.33.0-virgos.2.jar' `
  --jdk 'D:/proyectos/mc-server/.runtime/jdk-17.0.20.1+1' `
  --output "$env:TEMP/tree-feller-verification/candidate" --tests
python -B -m unittest discover -s dev/tree-feller/tests -v
```

Choose a fresh external output path for each build. `--help` documents every argument. `evidence.json`, compiler logs, `differential.json`, `journal-differential.json`, `catalog-differential.json` and `tests.json` remain with that output. The builder validates input SHA-256, source contexts, ZIP CRC/paths, Java version, original nested class footprint, and the narrow overlay allowlist. Annotation processors are disabled. It never invokes upstream's manifest `Main-Class` config generator.

The output contains a deterministic plugin JAR and a corresponding-source ZIP containing the full patched upstream source, complete fork source/patches/tests/build instructions, the original pinned source/JAR inputs, pins and GPLv3 license. Publish both together if this candidate is later approved. Upstream authorship and license are retained; this fork is GPL-3.0. `UPSTREAM.json` records the tag commit and anonymous official release/source URLs. Nothing here authorizes publishing or public-server installation.

The strict compile-only CoreProtect provider is the [official public CoreProtect-CE-24.1 JAR](https://cdn.modrinth.com/data/Lu3KuzdV/versions/3sehX6Sg/CoreProtect-CE-24.1.jar), SHA-256 `a2acef7c06ef201355cef07d591a6055dfed358ad768faaaaaf4e276865ecc97`, Artistic-2.0 ([source](https://github.com/PlayPro/CoreProtect)). Its referenced `CoreProtect.class` and `CoreProtectAPI.class` were checked byte-identical to the patched runtime provider; their exact fingerprints are enforced in `UPSTREAM.json`. This JAR is **not bundled**. Do not replace the actual patched runtime plugin SHA `1e0d93e1cc719cffb243b3b37a3e1c3ed2d9a37e65e31ab9b2d6b00ed740e8b7`; the material utility fix is runtime-specific. The previous `.1` and `.2` artifacts/source archives remain untouched.

## Enforced behavior

| Boundary | Behavior |
|---|---|
| Authentication | Existing Core `AUTH.authenticated` is called on the server thread; absent/error/offline actors deny. No AuthMe configuration, identity or permissions are changed. |
| Claims | Actual OPAC operation checks use the existing game classloader, real actor/axe and block position. `true` means **deny**. Every trunk, affected leaf and decoration is checked before cost/world/loot changes and again immediately before each break. Proposed sapling states are checked before felling and immediately before placement. No synthetic break event or full-pass grant is used. |
| History | Persisted direct Bukkit placement markers deny known player-built logs, including multi-place and piston moves. Successful removal is observed on the next tick before clearing a direct marker; a later Forge cancellation cannot erase it. Growth events clear stale direct markers only after observing the proposed new log on the next tick. Piston movement of every supported log—including healthy UNKNOWN/naturally grown sources—temporarily denies in-flight destinations, retains conservative source markers and records observed destination markers on the next tick. Existing known-source tracking is preserved for other forms. CoreProtect must be healthy and return a successful lookup. Historical rows without a verified direct-vs-growth discriminator are **UNKNOWN**, not buildings; the existing natural-shape engine remains authoritative under confirmed policy 2. API/query failure is never UNKNOWN. |
| Shape and neighbors | Existing upstream shape/leaf-distance engine remains. Each accepted candidate must match actual declared trunk/foliage/`Option.SAPLING`, pinned family/growth metadata and observed distinguishing foliage. A shared wood or generic oak leaf is not enough to select another species. Mature-root geometry and required planting layout are separate fields; accepted `ROOT_GRID` families retain their proven matching square layouts. Unresolved core/buttress anchors cannot authorize an operation. There is no universal 2×2 assumption. Multiple separate root footprints are rejected, not cascaded. Unresolved families are reported and not accelerated. |
| Balance | One durability point per log before vanilla item Unbreaking's independent per-point probability; unbreakable/creative semantics remain upstream. The same sampled cost is used for eligibility and execution. No new cooldown or total-log cap: the upstream nullable limit is set to `null`, **not zero**. Existing finite spatial detection range and natural-shape requirements remain. |
| Safe engine mode | Cascade, animation, falling-block behaviors, synthetic break events, partial felling, stacked tools, block conversion and inventory sapling consumption are disabled. The minimum fallback is owned by the journal, not upstream's unpersisted `Sapling`. Reload enforces this profile; unsupported in-memory mode changes refuse operations. Other engine settings remain upstream. |
| Replant | A durable declared-seed-alternative/owner/world/root reservation is written before felling. The first valid own drop selects the group's coherent seed; only matching drops are deducted before item-entity creation, up to the required planting count. Other alternatives remain physical loot. No valid drops selects the declared fallback; any shortfall becomes only the minimum planting fallback, never an item grant. No inventory saplings are read. Patched legacy `Sapling.place` always refuses, closing direct, inventory and timeout bypasses; its old public placement API is intentionally disabled in this fork. |
| Deferred retry | Once per second on the server thread; no chunk force-load. All pending footprint cells must be authorized and supported air or a supported correct existing sapling. Obstruction, denied claims, offline actor or unloaded chunk defer without overwriting. Journal completion is durable per position; existing correct saplings complete intents after a crash without spawning duplicate items. Disconnect/restart do not discard pending intents. |
| Persistence | Explicit `forestry-journal-v2` checksummed deterministic snapshots, forced writes and atomic replacement; no non-atomic fallback. V1 files are read without rewriting; legacy selected materials, pending positions and provenance markers remain intact. The first accepted mutation writes a v2 snapshot, preserving all other rows. Unknown versions/corruption deny, never discard. Old `.1` cannot read v2: retain the file on rollback, do not replace this plugin with the unguarded/old implementation. Corruption/write failures disable accelerated operations. The journal never represents inventory items that can be withdrawn. |

All proposed seed states use actual `BlockData.isSupported` against the real target/soil and mandatory OPAC placement checks before felling and immediately before planting. No vanilla-only soil whitelist or guessed mod soil name grants permission.

The first guarded refusal emits a bounded diagnostic; repeated identical refusals do not flood the log. A native bridge marked `UNAVAILABLE:*` is a runtime blocker, never permission to skip the guard.

## Declared species and honest coverage

`resources/catalog.json` inventories all **64** installed non-potted `*_sapling` resource variants with exact source-JAR SHA-256, resource/class paths and content hashes. `catalog.tsv` is the pinned runtime projection. This inventory is not an exhaustive count of fungi or other vegetation and is not native acceptance.

| Source | Inventory | Static mapping/grow path ready for runtime binding |
|---|---:|---:|
| Regions Unexplored | 33 | 30 |
| Aether | 2 | 2 |
| Deep Aether | 6 | 6 |
| Alex's Caves | 3 | 1 |
| Ars Nouveau | 4 | 0 |
| Twilight Forest | 10 | 9 |
| Quark | 6 | 6 |

The **10 explicit gaps** are RU `baobab`, `kapok`, `redwood`; Alex `ancient`, `thornwood`; all four Ars `{blue,green,purple,red}_archwood`; and Twilight `hollow_oak` (all IDs use their mod namespace and `_sapling` suffix; complete literal IDs/reasons are in the catalog). Ars seed minimum is resolved, but a faithful anchor within its mature core/buttresses remains unresolved. Ultra/custom growth, unknown trunk/foliage links, and shared hollow/ordinary-oak morphology are not guessed. Statically inherited grow paths do not prove the natural mature tree's anchor geometry: large/wide/terraced specimens still need fixtures. These gaps prevent claiming full S7 acceptance.

Catalog schema 2 keeps `mature_widths`/legacy `widths` separate from `planting_widths`, with an explicit `anchor_mode`. Ars `MagicTree` grows from **one** seed, while `MagicTrunkPlacer` produces a 2×2 core plus buttress roots. Its minimum metadata is therefore **one**, not four; the planting anchor among those roots is still `UNRESOLVED_ARS_BUTTRESS`. These four profiles are not activated, and no arbitrary corner or four-seed fallback is used. Mature root counts never directly become journal requirements: only a resolved planting-position list reaches the existing journal helper.

The six Quark families have explicit constructor-chain evidence through `Zeta-1.0-31.jar` (`PassthroughTreeGrower` and `ZetaSaplingBlock`), with cross-JAR origin hashes on each reference. Their source-backed one-seed candidates use `ROOT_GRID`. This closes six static mapping gaps, not native growth acceptance.

Runtime binding enumerates actual injected `Material.getKey()` values, rejects duplicate/unresolved keys, and checks block-data/item round trips. It never invents enum spellings. Only bound, declared profiles are installed into upstream detection. `Forestry.coverage()` reports every family as a gap, `UNRESOLVED_BINDING:*`, or `BOUND_UNPROVEN_NATIVE`; unmatched preconfigured tree declarations are also listed explicitly; the last label is deliberately **not PASS**. The bindings and actual modded soils must be observed on Ketting before acceptance.

Upstream's actual azalea declaration retains `AZALEA` and `FLOWERING_AZALEA` despite `OAK_LOG` trunks. Shared-wood mod foliage remains distinct (magnolia colours, roseroot colours and similar families); no log-name-to-seed fallback exists. Missing material bindings preserve/defer old journal intents rather than silently substituting a vanilla seed. V1 intents retain their exact old material because their original lost foliage identity cannot safely be reconstructed.

Reproduce/check the pinned catalog using exact local sources and a fresh external output directory:

```powershell
python -B dev/tree-feller/tests/catalog_resources.py --mods-root "$base/mods" --output "$env:TEMP/tree-catalog-recheck"
```

Compare both generated files byte-for-byte with `resources/`; source changes, count changes or missing evidence require review, not automatic acceptance. The generator executes no mod code or downloads.

## Focused proof boundaries

- `DeclaredSpeciesTest`: observed semantic RED on the old oak inference, then GREEN using the actual pinned upstream azalea config and `Tree/Option.SAPLING` public metadata.
- `AlternativeJournalTest`: own-valid-drop-first, preserved alternatives, coherent choice, minimum-only deduction, declared fallback, persisted restart choice and rejected-byte invariants.
- `LegacyJournalTest`: v1 read/reject byte stability and accepted v2 write preserving pending intents/markers. `JournalDifferentialProbe` compares old public operation outputs/state against the pinned `.2` JAR; omitting `--compatibility-jar` records explicit SKIPPED differential results. `CatalogCompatibilityProbe` also compares the prior constructor, vanilla identities and accessors against `.2`.
- `PlantingLayoutTest`/Python layout regression: observed RED for missing Ars mature/one-seed separation and missing Quark/Zeta association, then GREEN. Verifies Ars mature-four/seed-one metadata **and denial of unresolved anchors**, six Quark one-seed candidates, unchanged spruce layouts, and minimum-only use of the existing journal. It is not an Ars executed-felling proof.
- `CatalogTest`/Python resource tests: exact inventory, distinguishing foliage, arbitrary seed/trunk mismatch rejection, source/resource hashes and explicit gaps. These tests cannot establish native registry binding or sapling growth.
- `PistonProvenanceTest`: shared selection seam for both handlers; UNKNOWN supported trunks acquire manipulated provenance, known-source behavior remains. The independent event probe lacked mapped `net.minecraft.world.level.Level`, so real piston cancellation/restart proof is still pending.

## Required native acceptance (not supplied by unit tests)

Use only a newly prepared isolated laboratory variant and normal AuthMe login. Preserve public service/worlds/DH and all client/release locks. Add the candidate to `server/plugins` only, with the existing CoreProtect/Core/OPAC versions; no client overlay.

- Own claim, unclaimed land, other claim, team/exception cases; unauthenticated actor; disabled/missing/erroring Core/OPAC/CoreProtect. A rejected real felling must leave blocks, axe, loot, journal and player data unchanged. Exercise a denied leaf/decoration, not just the clicked log.
- Naturally grown and old unknown-history trees; future player-built/piston-moved logs; growth attributed to a planter must not be classified as manual construction. Include adjacent trees and verify the second trunk is untouched.
- All supported species, real dark-oak/jungle/spruce 2Ã—2 footprints, insufficient inventory saplings, zero/partial/excess natural sapling drops and Unbreaking tools. Count final loot plus planted minimum; do not use `/give` as executed felling proof.
- Denied/obstructed planting, disconnect and server restart with pending intents, then clear the obstruction/restore the actor's permission. Verify eventual species-correct placement, no item duplication and unchanged UUID/pack/DH state. Exercise crash-after-placement-before-completion in an isolated fixture.
- Measure real large-tree/CoreProtect lookup and synchronous persistence cost. No arbitrary cap was introduced to hide performance issues. Verify actual CraftBukkitâ†”Forge classloader/reflection signatures on Ketting; compile success does not prove this bridge.

Historical provenance ambiguity is the explicitly accepted policy-2 tradeoff. Species/growth gaps are not an approved release exclusion. The plugin cannot infer that a healthy old log row was direct construction when the API does not distinguish it from natural growth. Custom/plugin-generated placements that emit no Bukkit placement event likewise remain shape-classified UNKNOWN. Native runtime and performance proof remain **UNPROVEN** until separately observed.

## Rollback boundary

Remove only this candidate from the isolated lab `plugins` directory. Retain `plugins/TreeFeller/forestry-journal.tsv` and pending intents as evidence; do not silently delete them or deploy the upstream unguarded plugin as a fallback. No AuthMe, client locks, public files or shared pack pins belong to this unit.

Risk: items 1/2/3/4/5 (world/loot persistence, authentication/claims, deferred ordering and server-plugin delivery).
