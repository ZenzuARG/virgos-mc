# Prepare isolated Create addon inputs

These commands prepare laboratory artifacts only. They do not change approved pack
locks, the public service, worlds, DH progress or release identities. No optional
dependency, server plugin or SkinsRestorer is downloaded automatically.

## Fetch once

From the repository root, using Python 3.11 or newer:

```powershell
python scripts/prepare-create-addons-artifacts.py fetch --output-root D:/proyectos/mc-server-lab/create-addons-20261025
```

Only the three fixed Modrinth version IDs are selected. The tool verifies identity,
Forge 1.20.1 support, the exact primary CDN location and filename, size, both SHA512
and SHA1, outer/embedded JAR CRCs, and actual mandatory dependency ranges against
`pack/mods.lock.json`. The existing recursive descriptor inspector is reused without
executing the approved resolver's cache-creating module body. Unknown ranges,
ambiguous installed versions and missing mandatory dependencies fail closed.

`upstream/upstream.json` retains complete upstream responses, actual SHA256,
descriptors, the base lock hash and base inventory. Runtime compatibility remains
pending. Repeated fetches refuse to overwrite existing evidence.

## Prepare each variant before launching

After building the current observer, select its verified base artifact directory
and matching installed-input client directory containing the original DH JAR:

```powershell
python scripts/prepare-create-addons-artifacts.py variants --output-root D:/proyectos/mc-server-lab/create-addons-20261025 --base-artifacts <verified-DH-compat-QA-directory> --client-source <matching-client-inputs>
```

The output is `variant-artifacts/{baseline,crafts,bells,cei,combined,baseline-after}`.
Each directory carries an independently hash-verified `compat-manifest.json` and
unchanged copies of the selected DH, compatibility and QA inputs. Only its selected
addon JARs are added. No existing mods directory or immutable lab manifest is edited.

Use each directory as `--artifacts` for `prepare-dh-fullpack-lab.py`, with the same
named exact lab directory immediately under the authorized output root. The old
exact DH laboratory remains authorized; arbitrary siblings/descendants do not.
All original endpoint, link, overlap and launch-state guards remain active.
Run variants sequentially because they share loopback ports. Preserve previous
proof directories rather than reusing them.
The legacy `check-dh-fullpack-lab.py` remains restricted to its original lab;
the addon experiment's checker owns DH controls for the new variants.

## Verify

```powershell
python -m unittest discover -s tests -p test_create_addons_artifacts.py
python -m unittest discover -s tests -p "test_dh_fullpack*.py"
```

The tests use external temporary data, reject bad hashes before output creation,
cover strict ranges and missing dependencies, preserve baseline manifests, and
verify the exact destination allowlist. Native machine, recipe, reconnect, restart
and matched warmed performance proof are separate requirements before inclusion.
