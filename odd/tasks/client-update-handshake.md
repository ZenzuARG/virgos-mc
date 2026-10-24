# Client update handshake
Objective: enforce the installed Virgos-MC client release at login and produce a refreshed installer.
Delivery: inline implementation with runtime validation; repository has no Git checkout, so commits are not available.

## Specs

### S1 — Client release handshake
User requirement: "implementemos el handshake de actualización"
Acceptance: the server publishes one generated client requirement manifest; the Códice sends a client fingerprint during login; the server accepts the current fingerprint and rejects stale, malformed, or missing client handshakes deterministically.
Checks: build the server and Códice artifacts; run protocol-level tests for current, stale, and malformed fingerprints.

### S2 — Actionable disconnect message
User requirement: "el mensaje de desconexión"
Acceptance: a rejected connection receives a Spanish message that says the client must be updated and identifies the expected release/installer without exposing secrets or requiring console access.
Checks: assert the message for stale and missing Códice paths.

### S3 — Refreshed installer
User requirement: "después generá el instalador nuevo"
Acceptance: the generated installer bundles the new Códice and its release manifest, passes archive integrity checks, and records a new hash in the release metadata.
Checks: run the client release builder and inspect the ZIP/MRPack contents.

### S4 — Compatibility validation
User requirement: "validá cliente actualizado, cliente viejo y cliente sin Códice"
Acceptance: updated client connects, old client receives the update message, and a client without Códice receives the same actionable message; server remains healthy after each probe.
Checks: run isolated protocol probes against the live server or deterministic harness without mutating world data.

## Tasks
- T1 (S1-S2): implement the release manifest, login handshake, validation, timeout, and disconnect UX — route inline — complete (Gradle compile/check passed).
- T2 (S3): rebuild the Códice and installer metadata — route inline — complete (installerVersion 11, ZIP/MRPack hashes refreshed).
- T3 (S4): run current/stale/absent client validation and full server checks — route inline — complete (gate tests, live probe, audit, and delivery validation passed).

## Log
- L1: "Dale, implementemos el handshake de actualización y el mensaje de desconexión; después generá el instalador nuevo y validá cliente actualizado, cliente viejo y cliente sin Códice."
- L2: Implemented `2.0.0-r11` handshake with a ten-second missing-client timeout; current, stale, and missing-client gate cases pass deterministic checks.
- L3: Refreshed `dist/Virgos-MC-2.0.0-instalar.zip` and `.mrpack`; the live server reaches `Done` and reports protocol probe `OK`.
