# Bounded captured mining in the laboratory QA client

`capture_attack` is an opt-in **test-only input fixture**, not proof that a server
accepted a break, a claim permission, or TreeFeller operation. Never ship this QA
artifact with a client release.

## Quick path

1. Use a normally joined, authenticated laboratory player on exactly
   `127.0.0.1:25575`. Focus the Minecraft window, close screens, and establish the
   actual crosshair block before requesting input.
2. Append one command to the existing `virgos-qa/commands.jsonl` queue:

   ```json
   {"action":"capture_attack","id":"oak-1","x":48,"y":64,"z":48,"ticks":40}
   ```

3. Read `virgos-qa/capture-input.json`, then independently inspect the server's
   actual blocks, tool damage, inventory/loot, permissions and replant ledger.
   The receipt always reports `serverEventProven:false`.

## Input ownership

The action rejects before input when the endpoint, focus, live connected player,
screen or actual `BLOCK` hit differs from its preconditions. Coordinates and ticks
must be exact integers. Requested held-input duration is 1–100 client ticks, **in addition to one idle
warmup client tick**, with an independent
10-second monotonic wall deadline checked on ticks and rendered frames. The
unique request ID is 1–48 ASCII letters, digits, underscores or hyphens; replayed
IDs and simultaneous captures are rejected without changing the active lease.
The session accepts at most 256 unique capture IDs.

A successful request first acquires Minecraft's mouse with attack **up** and no
queued attack click. The receipt reports `state:"warmup"`, `armed:false`. One full
natural Minecraft client tick then runs idle input handling. Only the subsequent
`ClientTick.END` rechecks the actual `BLOCK` target, focus, connection, live player
and native capture before issuing one `KeyMapping.click` and attack-key down.
The receipt becomes `state:"armed"`, `armed:true`; only subsequent held ticks
consume the requested duration. Render callbacks observe safety/deadlines but
**cannot arm**. A target change before arming cancels without any attack click.

This ordering lets normal Minecraft `continueAttack(false)` clear the guard set
by `grabMouse`; the fixture never writes the private guard or simulates a reset.
The native evidence establishes successful capture but not that this diagnosis
was the exclusive reason no break occurred. The correction still needs native
mining/claim/replant verification.

It does **not** invoke game-mode destruction, send a custom
packet, manufacture a block event, or alter permissions. Target equality gates
both acquisition and arming; it is not continuously required after a block disappears.

During the explicit lease only, the ordinary ten-tick background mouse release
and show/hide behavior are suppressed. All default behavior remains unchanged
without a capture. The existing held-key slot is shared, not independently held
by two owners. Existing held input prevents starting a capture. Other input
commands cancel capture before proceeding; screenshot/audit commands may observe
it. `capture_cancel` cancels explicitly. Old `hold` still clamps 1–200 ticks and
does not synthesize an initial click.

Completion, lost focus/capture, a screen transition, death, disconnect, changed
endpoint, action/input error, receipt-write failure and shutdown release attack
and mouse. Cleanup also drains the capture's unconsumed initial attack click.
An I/O failure cannot keep inputs held. No receipt is created until a capture
was actually requested; receipts contain no player names or credentials.

## Verification

```powershell
python -B -m unittest discover -s tests -p test_qa_capture_input.py -v
```

The Python runner compiles/runs the pure `CaptureLease` public interface using
Java17, capped at 256 MiB, in a retained external TEMP directory. Set
`VIRGOS_QA_JAVA_HOME` only when the documented local JDK path is unavailable.
It models the mapped grab/guard/idle/initial-click ordering and checks a full
idle tick before arming, render-only non-arming, 40 held ticks separate from
warmup, fresh target rejection, wall timeout, rejection without
input mutation, duplicate requests and all modeled interruption/cleanup paths.
The integration check pins actual END-tick versus render routing and action wiring; it does not initialize
Minecraft or prove native capture, classloading, mining, claims or replanting.
Native checks remain mandatory before claiming functional acceptance.

Controls-only builds must include `ClientProbe.java` **and** `CaptureLease.java`,
exclude trace/mixin classes and retain all existing QA resources/skin schema.
Build into a new external directory; preserve the old pinned QA JAR and lab.
