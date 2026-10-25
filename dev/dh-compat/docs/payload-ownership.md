# Completed requested-payload ownership

A completed DH 3.3.3 response must keep its assembled buffer alive while its native
compression callback waits in an executor queue. Unclaimed fragments still expire
under the unchanged native 30-second cache policy.

## Handoff

1. The original `CompletableFuture.handleAsync` callback and source future remain
   unchanged. Its executor is decorated, not replaced with a new completion stage.
2. Immediately before scheduling, a successful non-null response claims its existing
   buffer through an atomic native-map removal. The received payload holds a local,
   transient one-shot lease; nothing is serialized or stored in a global registry.
3. The exact native `ConcurrentMap.get` decode seam consumes that lease once. Native
   DTO decoding, application flags, exceptions and retries still run. Both native
   finally-removal sites skip map removal for a successfully claimed payload: its
   entry was already removed at handoff, and a replacement entry is not owned by it.
   Unclaimed partial decoding keeps the original native map removal.
4. Dependent cancellation and scheduling rejection discard pending lease references.
   Cancellation racing with claim publication marks the handoff terminal and
   immediately discards any late-published lease. Cancellation cannot revoke a lease
   from an already-running callback. Receiver close invalidates leases before later queued lookups, without changing native close.

No decompression moves onto the network thread. The addon does not read or mutate
buffer indices, retain/release reference counts, increase TTL, replay packets, alter
partial-update handlers, or bypass authentication/readiness. Native Guava cache
construction has no removal listener; its comment is not a buffer-release contract.

A missing buffer at handoff does not become a successful response: the original
lookup/failure path remains. A different receiver cannot consume an attached lease
or obtain a cleanup handle that can discard its owning receiver's buffer.
Leases depend on the existing one-receiver-per-`ClientNetworkState` session lifetime.
The separate grouped-transfer identity fix prevents ID reuse; it is not implemented here.

## Deterministic verification

`PayloadOwnershipTest` uses the original pinned `a537a711...` DH jar, real native DTO
encoding, the original native receiver decode body and a fake Guava ticker. Its map
adapter models the exact redirected lookup and finally-removal invocations. A held compression
executor reproduces the old failure after 31 seconds without sleeping. The same
fixture then checks successful decoding, one-shot ownership, owner isolation,
close, both rejection timings, null/error/cancellation callbacks and active-callback
cancellation using latches. Additional regressions hold cancellation inside claim
publication and replace an already-claimed buffer ID before decoding; the replacement
must survive both native finally sites. Bytecode assertions pin native get/remove
seams and the 30-second TTL.

This is not a full Minecraft Mixin application test. Client-only registration and
an isolated runtime integration test remain required. The deterministic expiry race
is reproduced; it is not asserted to be the cause of every earlier runtime failure.
