# Give each grouped response its own native payload identity

DH 3.3.3 encodes one payload before the grouped-request loop, then shares that
payload's buffer ID between fragment transfers and final responses. Sharing an ID
across distinct receiver instances works; two outstanding complete responses using
that ID in one receiver can replace each other's buffer and fail on consumption.
This conditional native hazard is reproduced, not established as the observed
laboratory failure's original cause.

## Narrow change

`GroupedFullDataPayloadMixin` changes only the `FullDataPayload` local at index 3
in `FullDataSourceRequestHandler.lambda$tick$0(DataSourceRequestGroup, Map.Entry)`.
It runs before the loop's single `ConcurrentMap.remove(Object)` invocation. Each
iteration therefore uses one new wrapper in **both** `sendInChunks` and the final
response's captured runnable. Changing only the sender argument would be wrong:
the final response would still identify the old buffer.

The wrapper uses `FullDataPayload.lastBufferId.getAndIncrement()`, exposed through
a static accessor. It reuses the already encoded `ByteBuf` and beacon list without
encoding, copying content, retaining/releasing buffers or moving reader indices.
Native `PendingTransfer` continues duplicating the buffer with an independent
reader index. Direct and partial-response call sites, wire format, authentication,
queue policy, retries, expiry and readiness are unchanged. The native integer
allocator's eventual wraparound semantics are also unchanged.

## Registration and proof

Register `FullDataPayloadIdAccessor` in the common `mixins` list so it can coexist
with the separate payload ownership mixin. Register `GroupedFullDataPayloadMixin`
in the dedicated `server` list. Retain the existing exact dependency pins and
required Mixin configuration; the injection explicitly requires one target.

Add a JavaExec task `checkGroupedPayloadIdentity`, depending on `testClasses`, with
`sourceSets.test.runtimeClasspath`, main class
`mc.virgos.dhcompat.GroupedPayloadIdentityTest`, and system property
`dh.compat.originalJar=file(dhJar.get()).absolutePath`; make `check` depend on it.

The focused test binds its selector, local slot, loop and two consumers to original
DH SHA-256 `a537a71171d935540b56b7598d0de2c106f6f5026336c713d89a1d9ea0ea14e3`.
It checks accessor/handler annotations, native `PendingTransfer` reader behavior,
same-receiver and distinct-receiver controls, native DTO encoding/decoding, repeated
consumption, byte immutability and one encoding per grouped source. The disabled
control (`-Ddh.compat.grouped.disabled=true`) fails the distinct-ID assertion.

Tests call the helper's package-private allocation adapter using the actual native
atomic counter because an ordinary JavaExec does not run Mixin. This is a
bytecode-bound selector plus native transfer/DTO test, **not** evidence that the
production transformer applied the mixin. Required-transform application and full
untraced laboratory acceptance remain runtime checks before promotion.
