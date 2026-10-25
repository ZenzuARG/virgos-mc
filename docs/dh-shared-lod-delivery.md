# Shared Distant Horizons terrain

The server serves saved LODs to new and returning clients without requiring them
to visit the terrain first. Normal Minecraft chunks are not sent at the full LOD
distance. Clients still download and render progressively within their selected
LOD render radius; the whole database is not pushed immediately on login.

## Managed settings

- Server: origin boundary 625 chunks (approximately 10 km), request/sync distance 625,
  live updates 256, and 16 generation/sync requests per second. `PRE_EXISTING_ONLY`
  avoids generating missing Minecraft terrain in response to ordinary requests.
  The server-only compatibility guard preserves cached serving during Chunky
  only in this mode; other DH generation modes retain native mutual exclusion.
- Client: no local origin boundary; the server remains authoritative. Fresh
  profiles render 256 chunks (approximately 4 km), rather than forcing 10-km
  rendering on every computer. Players may adjust the render radius.
- Updated installers migrate the previous pack defaults: origin boundary 32 to 0,
  and render radius 32 to 256. Other personal values and comments are preserved.
  Current-schema files are backed up before any change; repeated migration is a
  no-op. Updating only the packaged seed does not migrate existing profiles.

## Persistence and recovery

Use a normal `stop`, wait for Java and the managed backup to finish, and verify
the backup before changing public files. Generated LODs remain in the world’s
SQLite database. Never copy a live database alone without its WAL, or delete
client/server caches as a repair.

`PRE_EXISTING_ONLY` also applies to DH's own pre-generator: it does **not** fill
missing world terrain. First generate actual missing chunks with the already
installed Chunky mod, centered at 0,0 with a circular 10000-block radius. Existing
world chunks are retained. Do not run two large generators concurrently.

After actual chunk generation, use DH's import sweep over the same coverage to
fill any remaining LOD processing gaps:

```text
forge:dh pregen start overworld 0 0 625
```

The traversal percentage may restart; fully generated saved sections are reused.
This is not a durability guarantee for forced termination or power loss.

## Regression proof

The isolated full-pack proof uses a fixture 1024 blocks from spawn, beyond the old
512-block boundary. A normal teleport places the QA viewer 256 blocks away,
also outside that origin boundary, without visiting the fixture. This avoids
starving the fixture behind a cold cache's nearest-first request backlog.
It checks native authentication, fresh cached download during active Chunky while
the corresponding vanilla chunk is absent, live material/geometry updates,
offline changes refreshed on reconnect, and persistence after clean client exit.

An updated installer/MRPack must be distributed before already-installed users
receive the migration. Source-only changes do not update their running clients.

## Current verification status (2026-10-25)

The exact 2.1.1-r13 candidate passed 18 native checks with 8 GiB on each side:
fresh remote download, live material/geometry changes, offline reconnect refresh,
persistent cache, and observed Chunky activity throughout every phase. The normal
client screenshot shows the remote emerald LOD while its vanilla chunk is absent.
See the [verification record](releases/2.1.1-verification.json) and
[captured frame](releases/2.1.1-dh-remote.png).

An earlier check incorrectly required a palette change even when a known material
changed only the column data. The corrected check compares both components and
still requires exact server/client convergence. A below-policy 6-GiB test also
exhausted memory; the shipped 8-GiB policy passed. Existing non-DH resource-model
log advisories remain, so this is not a zero-error certification for every mod.

Publication and the public r13 client gate remain separate rollout steps. The
complete 10-km region is still being created; cache availability is progressive.
