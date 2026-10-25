# Verify the full gameplay pack without touching the public server

Preparation creates a fresh, loopback-only laboratory at
`D:/proyectos/mc-server-lab/dh-fullpack-20261024`. It never launches Minecraft,
downloads dependencies, copies public worlds/accounts/databases, or publishes artifacts.
Both command-line tools reject any other destination. Do not use existing public launch scripts.

## Prepare

From the authorized source snapshot, run Python with `-B`:

```powershell
python -B scripts/prepare-dh-fullpack-lab.py `
  --pack-source C:/Users/zulia/.codex/worktrees/dh-fullpack-lab/mc-server `
  --artifacts <external-verified-artifacts-directory> `
  --lab D:/proyectos/mc-server-lab/dh-fullpack-20261024 `
  --java-server D:/proyectos/mc-server/.runtime/jdk-21.0.12.1+1-jre/bin/java.exe `
  --java-client D:/proyectos/mc-server/.runtime/jdk-17.0.20.1+1-jre/bin/java.exe
```

`--server-source` and `--client-source` default to the installed server and client.
Only selected gameplay inputs are read. The destination must not exist and must not
overlap any source. Symlinks/junctions, missing dependencies and invalid artifact
hashes are rejected before destination creation. An I/O failure during copying can
leave an incomplete lab; preserve it for inspection rather than rerunning into it.

### Artifact contract

The artifact directory must contain `compat-manifest.json`:

```json
{
  "schema": 1,
  "originalDhSha256": "<installed-original-DH-sha256>",
  "artifacts": [
    {"filename": "DistantHorizons-3.3.3-1.20.1-fabric-forge.jar", "sha256": "<patched-sha256>"},
    {"filename": "virgos_dh_compat-0.1.0.jar", "sha256": "<addon-sha256>"},
    {"filename": "virgos_local_qa-2.0.0.jar", "sha256": "<observer-only-QA-sha256>"}
  ]
}
```

QA is optional during preparation, but required for client observation and graceful
client timeouts. Names beginning `virgos_local_qa-` are installed only on clients;
other verified artifacts are installed on both sides. The compatibility addon and
patched DH are mandatory. No original release lock is modified.

## Isolation and selection

| Input | Lab policy |
|---|---|
| Installed server/client mod jars | Preserve actual installed sets except declared substitutions below |
| Playit / DiscordSRV | Excluded external infrastructure; no tunnels or bot credentials |
| DHSupport 0.14 | Replaced by native DH 3.3.3 and verified compatibility artifact |
| AuthMe / LuckPerms / CoreProtect / DecentHolograms | Preserve plugin jars, generate fresh local configuration and databases |
| Configuration | Explicit gameplay config directory/extension policy in `dh_fullpack_lab/policy.py`; exclude credential names and network/backup integration configs |
| KubeJS / defaultconfigs | Canonical defaults, then selected installed runtime files |
| World | Fresh normal `virgos_world`, seed 42; only canonical world serverconfig templates copied |
| Client assets/libraries | Referenced read-only from installed cache; natives and writable game directories copied separately |

`lab-manifest.json` records hashes, omissions, source selection and every conflicting
canonical/runtime override. Precedence is **canonical < selected runtime < lab safety**.
The preparer rejects known production tunnel/webhook endpoints in selected text inputs.
It does not recursively copy any plugin data directory, launcher profile or public world.
Installed resource packs outside the canonical UI override and shader packs are not copied.

Safety overrides bind Minecraft to `127.0.0.1:25575`, voice chat to loopback UDP
24455, disable RCON/query, restrict the whitelist to offline `VirgosQA1`/`VirgosQA2`,
and disable maintenance/clean-stop/scheduled backups. AuthMe sessions are disabled;
registration and release validation still need real runtime proof with fake accounts.
Plugin update/metrics settings are generated locally, not inherited from public files;
this is not an OS-level outbound-network sandbox.

Two independent client directories allow cold-cache versus reconnect tests. The
previous measured ~2.3 GiB dependency lower bound needs another ~0.67 GiB for the
second client mod copy, plus new worlds, DH data, logs and builds. No capacity or
performance claim follows from these sizes or the configured heaps.

## Run and observe

```powershell
python -B scripts/run-dh-fullpack-lab.py --lab D:/proyectos/mc-server-lab/dh-fullpack-20261024 --role server
python -B scripts/run-dh-fullpack-lab.py --lab D:/proyectos/mc-server-lab/dh-fullpack-20261024 --role client
```

Run roles in separate foreground terminals. `client2` uses `VirgosQA2` and an independent
cache. Heaps are 4 GiB server / 8 GiB client. Boot timeout is at most 300 seconds;
lifetime at most 1200 seconds, followed by a 30-second graceful-stop allowance.
The runner records only its newly spawned child and never discovers or controls public PIDs.
An unfinished process record refuses relaunch and requires manual inspection.

Append local server commands to `server/commands.txt` **after** its runner starts.
Clients use observer actions in `<client>/virgos-qa/commands.jsonl`; endpoints are
restricted to `127.0.0.1:25575`. Use `stop` or `{"action":"quit"}` for an early
clean exit. Timeouts are failed runs, not proof of successful validation.

On each client/client2 restart, the runner archives the previous command queue and
top-level observer JSON into `virgos-qa/history/<runId>/`, clears queued actions
before spawning its own child, and marks audit results pending. Append new client
actions only after the runner starts; an old successful audit is never current proof.
Startup readiness requires the actual title screen or an in-game fake QA player;
connection/loading screens are not proof. `LoadingErrorScreen` records its observed
status in `runner-failure.json`, requests a normal quit immediately and returns failure,
with the existing bounded own-child termination fallback. No screenshot, UI click or
network repair action is invented automatically; logs and prior evidence remain available.

The runner rechecks immutable prepared jars/dependencies/argument arrays and safety
properties before launch. It also rejects links/junctions anywhere in the writable
lab footprint, including worlds, generated configs, caches and client saves, not
only immutable inputs. Canonical and runtime overlay selections use the same
sensitive-name/database exclusions; legitimate gameplay binaries and resource-pack
ZIP files retain their format-specific copy policy.
It records `process.json`, `console.log` and observer JSON.
These files are observations, not an assertion that authentication or DH worked.

## Acceptance evidence still required

- First cold PLAY and DH readiness without QA networking repairs.
- Fresh fake registration/login, valid release acceptance and invalid/missing release rejection.
- Remote LOD download without visiting the fixture; compare Data **and Mapping**.
- Offline cached refresh, live material/geometry changes, restart persistence and identical-input no-op control.
- No public runtime writes, production commands, tunnels or credentials.

Run policy tests with `python -B -m unittest discover -s tests -p test_dh_fullpack_lab.py`.
Rollback removes only the isolated tooling/compatibility unit and its lab; no public
installation or stored data is part of this change.

## Normal-action data-flow proof

With the verified server and a fresh `client2` running, use `python scripts/check-dh-fullpack-lab.py --lab D:/proyectos/mc-server-lab/dh-fullpack-20261024 --role client2`. It uses only the observer command queue, deliberate normal AuthMe registration/login of disposable QA names, read-only SQLite snapshots, bounded changes to the sixteen-chunk fixture, and normal reconnect/quit actions. It never repairs networking or marks DH ready. The fresh laboratory permits a bounded 120-second login/registration grace for the full pack's cold JEI/bootstrap work; password and release validation remain required. These are not production credentials or production settings.

Proof requires an absent actual vanilla chunk (getChunk with creation disabled; ClientLevel.hasChunk always returns true), Data plus Mapping identity, material/geometry/live/reconnect updates and the original palette regression/no-op controls. Results are under the laboratory's `proof/` directory. A stopped process or missing proof yields PARTIAL, not a compatibility claim.
