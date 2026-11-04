# Shared authoritative Distant Horizons LOD

Objective: make the server LOD the shared baseline while preserving client-side exploration updates.
Branch: current working branch; delivery remains uncommitted until end-to-end QA passes.
Test runner: `dev/virgos-core/gradlew.bat -p dev/dh-compat` plus fresh public QA client/database probes.

## Specs

1. **S1 — New-client baseline**: "el cliente nuevo tiene que poder descargar el lod de todo el mundo"
   Acceptance: a fresh client receives server DH session configuration and server-owned LOD data before local generation; `serverReady=true` and fresh cache rows are present.
2. **S2 — Existing-client merge**: "el cliente viejo tiene que poder actualizar el lod generando mundo por su cuenta, osea explorando, y tambien tiene que poder sincronizar/descargar el lod del servidor"
   Acceptance: an existing cache remains usable, server updates are applied, and local exploration fills only missing/stale regions without overwriting newer server data.
3. **S3 — Shared convergence**: "todos tendrian la misma version de lod o el mismo lod y lo estarian actualizando conjuntamente"
   Acceptance: reconnecting clients converge on the server snapshot for equal coordinates; server payloads win conflicts by version/session freshness.

## Tasks

- T1 — Map native DH handshake and payload ownership; route: inline; status: complete; evidence: client sends SessionConfig/RequestLevelInit with no server response; native server state queues messages until player registration.
- T2 — Remove the premature server-side constructor config send and restore native request/response negotiation; route: inline; status: complete; commit: pending.
- T5 — Permit only the two native DH handshake messages through the pre-auth payload guard; route: inline; status: complete; commit: pending.
- T3 — Implement server-first merge policy and regression probes; route: inline; status: pending; commit: pending.
- T4 — Fresh/old client end-to-end QA and release packaging; route: inline; status: partial; commit: pending.

## Log

- L1: "Okey continuemos solucionando esto, recorda, el cliente nuevo tiene que poder descargar el lod de todo el mundo, y el cliente viejo tiene que poder actualizar el lod generando mundo por su cuenta, osea explorando, y tambien tiene que poder sincronizar/descargar el lod del servidor, ya que otros usuarios tambien van a estar actualizandolo, de esta forma todos tendrian la misma version de lod o el mismo lod y lo estarian actualizando conjuntamente, que te parece? es posible?"
- Current evidence: public QA connects but `client/standard/virgos-qa/dh-audit.json` reports `serverReady=false`; server logs show the player is disconnected after login timeout.
- 2026-11-04: Official client debug log confirmed `SessionConfigMessage` and `RequestLevelInitMessage` were sent, but no server response arrived. The custom `DhServerPlayerStateMixin` constructor send was removed; the native `SessionConfigMessage` handler remains authoritative.
- 2026-11-04: Rebuilt the compatibility addon successfully, restarted the public server, and confirmed DH initializes as `SERVER_ONLY`; the installed official client still had the previous addon hash, so a new 3.0.3 installer was built externally with the corrected 31416-byte addon. Client reconnect verification remains pending.
- 2026-11-04: The official client was synchronized in place with the corrected addon after backing up the previous jar; both client and server now report SHA256 `450674...`. A fresh client connection is still required to verify `serverReady=true` and LOD row growth.
- 2026-11-04: Root cause identified: AuthBridge intercepted every pre-auth custom payload and swallowed DH's `distant_horizons:msg` session-config and level-init request before AuthMe login. The guard now permits only DH protocol version 16 message IDs 4 and 3, each once, with a bounded payload; all other DH messages remain blocked.
- 2026-11-04: Core tests pass and the public server was restarted with the patched core jar. The prior client connection was necessarily dropped by the restart; reconnect verification is pending.
- 2026-11-04: Reconnect still showed no LevelInit/serverReady response. The pre-auth gate was too narrow for DH's follow-up negotiation/request sequence, so it now permits the bounded protocol-16 DH channel (read-only LOD negotiation/data requests) before AuthMe; tests pass and the server was restarted again.
- 2026-11-04: The broader gate still produced no client acknowledgement. AuthBridge was manually invoking `payload.handle()`, which bypasses Forge's native SimpleChannel dispatch. DH payloads now pass directly through Netty's native pipeline; core tests pass and the public server was restarted again at 19:28.
