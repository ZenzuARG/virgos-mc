# Observe native DH payload ownership without repairing the session

This is **QA-only instrumentation for pinned Distant Horizons 3.3.3**, not a fix.
Do not include these sources/resources in Codex, Core, patched DH or the production
compatibility addon. Final production proof must run without this trace.

## Private observer wiring

The parent-owned external QA build must compile:

- `dev/dh-compat/qa/mc/virgos/qa/DhPayloadTrace.java`
- `dev/dh-compat/qa/mc/virgos/qa/trace/*.java`

Include `dev/dh-compat/qa-resources/virgos_qa.mixins.json` at the QA JAR root and set
its manifest `MixinConfigs` attribute to `virgos_qa.mixins.json`. Preserve the existing
QA `META-INF/mods.toml` and observer source; do not compile a second ClientProbe.
The external init script owns source/resource paths and output placement. No project
Gradle file or production manifest is changed by this instrumentation.

Mixins use `@Pseudo`, string targets, `@Coerce Object` and reflection; they require
only the existing Forge/Mixin QA compile classpath, **not a DH compile dependency**.
All pinned method descriptors and seams use `require=1`, `remap=false`. The resource
lists them under `client`, so dedicated-server instrumentation is not installed.

Opt in only for the isolated private client:

```text
-Dvirgos.dh.trace=true
```

Default false performs no buffer-field inspection, thread startup or filesystem I/O.
When enabled, the only runtime output is the private working directory's
`virgos-qa/dh-payload-trace.jsonl`. Each JVM run has a numeric trace ID; append-only
history is distinguishable by that ID. Preserve the file with the corresponding logs.

## Observations and invariants

| Event | Observation |
|---|---|
| `receiver_session` | Numeric receiver/session identity binding |
| `fragment_arrival` | Native message ID, first flag, buffer writer-index metadata, cumulative received bytes |
| `native_compute_before` / `native_compute_return` | Existing native cache compute argument/result presence and object identity |
| `response_arrival` / `partial_arrival` | Final-message buffer/future IDs at native session entry |
| `compression_callback` | Native request-response callback start on its existing executor |
| `decode_start` / `native_cache_lookup` | Decode entry and the exact native lookup result |
| `native_remove_attempt` / `native_remove_return` | Before/after the native removal operation, including exceptional DTO paths |
| `decode_return` / `receiver_close` | Normal decode completion or receiver closure |

`receiver`, `session`, `objectId` are JVM identity hashes; they are not player IDs.
`buffer` and `future` are native protocol IDs. Unknown numeric fields use -1 or 0.
`flag` means first-fragment for `fragment_arrival`, presence for cache seams, and
non-null payload for response events. `bytes`/`total` are fragment metadata only;
no payload bytes, palettes, chunk positions, names, addresses or tokens are logged.

The native map is **never queried additionally**. The lookup observer returns the
identical `Objects.requireNonNull` argument, including null, so the same native NPE
still occurs. No ByteBuf content reads, index changes, retain/release, callback
rescheduling, retries, resends, cache TTL changes or authentication/readiness changes
are introduced. The fragment-size observation uses only the non-mutating writer-index
getter. Cache lambda observations inspect values already supplied by native compute.

## Bounds and interpretation

One daemon writer performs all filesystem work. Native callers use bounded `offer`,
never `put` or a writer join. Limits per process are five minutes, 12,000 event-budget
slots, 1,024 queued records, 2,048 tracked buffer counters and 64 receiver/session
bindings. Overflow drops observations, not native work. Summary lines report drops,
reflection failures, untracked counters and asynchronous I/O failures; summaries flush
approximately once per second. No shutdown hook extends VM lifetime.

Missing logs, nonzero drops/failures, unknown identities or exhausted bounds make a
negative inference **inconclusive**. A daemon may lose its final queued records at JVM
exit. `DhPayloadTrace.stats()` exposes metadata without any repair action if the parent
observer needs an explicit check.

Useful discriminators, only when coverage is complete:

- Assembled native entry and final response, then >30 seconds before compression
  callback and a null native lookup, without close/removal: expired queued payload.
- Non-first fragment with null native compute input/result: no retained first fragment.
- Repeated first fragment while a previous composite remains: replacement/reused ID.
- Prior successful removal of the same receiver/buffer before another decode: repeated consumption.

This trace does not by itself prove a pre-auth C2S drop; it observes the client side.
Do not infer packet loss or raise TTL merely from the existing exception wording.

## Pure checks

Compile `DhPayloadTrace.java` and `qa-tests/mc/virgos/qa/DhPayloadTraceTest.java` with
cached JDK 17 `javac --release 17 -d <external-temp-classes>`, then run
`mc.virgos.qa.DhPayloadTraceTest` from an external temporary working directory.
Tests cover disabled no-I/O, identity preservation, JSON escaping, record/duration/
queue bounds, visible loss/error counters and daemon ownership. They do not prove
Mixin application; the parent still compiles the actual offline QA JAR and validates
these seams in its private run.
