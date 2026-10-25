# Pinned Distant Horizons lifecycle and transfer fixes

This Forge addon fixes client initialization races for **Minecraft 1.20.1,
Forge 47.4.22 and Distant Horizons 3.3.3**, plus dedicated-server Chunky provider
readiness on **Ketting Forge 47.4.22-0.6.1 with Chunky 1.3.146**. It changes
ordering and transient buffer ownership, not authentication, packet permissions or terrain data. Client fixes
remain client-only; the Chunky guard is dedicated-server-only.

## Build and check offline

From the repository root, using the existing Gradle wrapper and Java 17:

```powershell
$env:JAVA_HOME = '<Java 17 JDK directory>'
& dev/virgos-core/gradlew.bat -p dev/dh-compat --offline check jar '-PdhJar=<original DH 3.3.3 jar>'
```

The output is `build/libs/virgos_dh_compat-0.1.0.jar` inside this module.
The supplied DH jar is compile-only and is never bundled. The offline build
requires the existing ForgeGradle 6.0.54, Forge and Mixin caches.

## What changes

| Injection | Ordering guarantee |
| --- | --- |
| `Connection.m_129520_` | Its single `ChannelConfig.setAutoRead(false)` call runs on the same channel event loop, ahead of that caller's queued packet send. Existing on-loop calls stay immediate. |
| `DhClientWorld.<init>` | Capture the initial `ClientNetworkState.sendConfigMessage()` instead of sending before the world is published. |
| `SharedApi.setDhWorld` return | Send the captured configuration once, only when this world is the published world, after native thread-pool setup has completed. |
| Full four-argument `DhClientLevel` constructor return | Publish the wrapper reference, then register native partial-update handlers once, only after provider/module/repository/renderer initialization succeeds. The delegating constructor and null-network branch retain their native behavior. |
| Requested-source async handoff | Claim a completed buffer before executor scheduling and consume it once within its original receiver lifetime. Unclaimed fragments keep their native expiry. |
| Grouped server response iteration | Allocate each response wrapper from the native ID sequence before both fragment sending and final-message capture, sharing the immutable encoded bytes without recompression. |
| Dedicated-server `AbstractChunkyAccessor.tryRunFirstTimeSetup` head | Defer the exact Forge accessor while the installed Chunky provider reports its expected unloaded state, before native code sets `listenerBound`. Native subsequent calls bind the listener normally once ready. |

There is no polling, forced read enable, fake session readiness, pool prewarming,
retry loop, replay of gameplay packets, or authentication bypass. Other normal
DH configuration messages are unchanged.

The client-level fix defers only the two native publication calls; it neither
constructs the client module early nor changes `close()`. A partial update could
previously invoke `updateDataSourcesAsync` while `clientside` was still null.
Normal full-source responses retain the native session/request queues and decoder;
completed requested buffers use transient payload-local ownership during the
executor handoff, not this partial-update subscription. Messages received
before the level subscribes are not buffered or replayed by this addon. The
initial snapshot must retrieve current server state through normal requests;
this is an end-to-end laboratory requirement, not a claim that every prebinding
partial push is harmless. Unclaimed fragment-buffer expiry remains unchanged.

See [completed payload ownership](docs/payload-ownership.md) and
[grouped response identities](docs/grouped-payload-identity.md) for the native
regressions, cancellation/close controls and precise version boundary. These
mechanisms reproduce with the original receiver and DTO code; reproducing them
does not establish which caused an earlier intermittent full-pack failure.
Full untraced laboratory acceptance remains mandatory.

The Chunky probe calls only the public provider getter through reflection, so
Chunky remains an optional dependency. It runs only for the installed Forge
accessor before its listener is bound. Only the getter's exact
`IllegalStateException("Chunky is not loaded.")` is treated as not ready;
unexpected provider failures propagate. No listener flag is forged and the
generation-progress hook is retained. There are no new version upgrades.

## Version boundary and verification

Targets were inspected with `javap -c -p` in the installed 1.20.1 SRG client and
the original DH 3.3.3 jar. The client target contains exactly one `setAutoRead`
invocation in `m_129520_`, before its event-loop `execute`. DH's constructor
sends configuration before `SharedApi.setDhWorld` stores `currentWorld` and
calls `ThreadPoolUtil.setupThreadPools`.

Runtime SRG names are intentionally explicit with `remap=false`; no annotation
processor or refmap is required. Every injector requires one match and the
Mixin configuration is required, so incompatible layouts fail instead of
silently disabling a fix. Dependency versions are exact pins, not broad ranges.
Forge has separate side-specific pins: client `[47.4.22]`, dedicated server
`[47.4.22-0.6.1]`; optional server Chunky is pinned to `[1.3.146]`.

`checkOrdering` runs deterministic FIFO, already-on-loop, publication-order,
and once-only tests. These tests prove the shared ordering primitives, not
Mixin application or end-to-end networking; the parent laboratory run must
verify actual injection and cold/cached full-pack connections. Remove only
this addon jar to roll back its fixes; it has no persistent configuration.
`checkChunkyReadiness` additionally exercises unloaded-provider deferral,
normal retry binding once, the already-ready control, and unexpected-error
propagation using a test-only provider fixture. Full-pack server startup remains
an integration check, not a claim made by that fixture.

`checkLevelPublication` requires the original SHA-256-pinned DH jar. Using
cached test-only ASM, it extracts the real constructor's publication/module
order and reproduces immediate callback delivery before `clientside` exists.
It then checks deferred publication, complete-field visibility, once-only and
delegated constructors, null-network and failed-construction controls, native
close ownership and the compiled mixin's exact client-only injection selectors.
This is a bytecode-bound deterministic fixture, not actual Mixin application;
the parent cold-cache laboratory run must still prove runtime integration and
fresh snapshot retrieval. The separate missing-buffer failure is not declared
resolved by these constructor checks.

## Pinned laboratory artifacts

`build-artifacts.py --help` describes the offline builder. Supply the original DH jar, this addon jar, cached ASM jar, Java 17 JDK and an external output directory. The builder accepts only the SHA-256-pinned DH 3.3.3 input, never edits installed artifacts, adds the alias-safe semantic merge comparator, and writes a deterministic dependency jar plus `compat-manifest.json`. An optional observer-only QA jar is client-only. Unknown dependencies and overlapping output paths fail before build output is created.

The merge regression and identical-input controls must both pass. Changing palette identifiers is not equivalent to changing block or biome meaning. Data checksums alone omit that mapping and are insufficient freshness evidence.

The observer source under `qa/` contains audits/actions only: no channel-read repair, DH config resend, readiness mutation or authentication bypass. Full-pack proof must use this observer rather than the earlier temporary recovery driver. Production release locks and installers are intentionally unchanged.
