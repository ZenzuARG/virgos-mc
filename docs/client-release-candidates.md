# Build a candidate without modifying the published release

The explicit candidate mode builds an installer ZIP, MRPack and `release.json`
in a separate external directory. It reads local verified inputs only: no downloads,
launcher access, public runtime commands or published metadata updates.

## Inputs and command

### Clean local/CI preparation

Select metadata through `pack/candidates/current.json`; do not rewrite the published
`pack/current-release.json` or root artifact locks to prepare a candidate. Build
Core/Codex with Java 17 and `-PbuildEpoch=0`, then prepare complete inputs:

```powershell
python -B scripts/fetch-locked-client-deps.py
# The fetch step is separate and network-enabled; omit it with a verified local cache.
& dev/virgos-core/gradlew.bat -p dev/virgos-core check jar codexJar -PbuildEpoch=0
python -B scripts/prepare-dh-release.py `
  --metadata pack/candidates/2.1.0/release.json --cache-root .cache `
  --inputs-dir <new-external-input-directory> --java-home <Java-17-JDK> --offline
```

`--java-home` defaults to `JAVA_HOME`. The preparer never downloads upstream inputs;
CI resolves `JAVA_HOME` to its canonical directory before invoking the preparer,
because hosted tool-cache JDK aliases can be symbolic links. Linked release
inputs, cache paths and output paths remain rejected.
`--offline` also prevents addon Gradle dependency resolution. It verifies both built
jars' embedded release/fingerprint, source identity, original DH, ASM and two pinned
source archives before any child build or output creation. The addon is checked and
built with the original DH as compile-only input; patch compilation uses external
system-temp scratch, retained and reported in the returned JSON for inspection.

The result contains `release.json`, `custom-artifacts.lock.json`, an administration
lock without DHSupport, `client-update.json`, and `artifacts/` with four jars plus
verified sources/licenses. No existing candidate directory's ignored jars are reused.
Modification sources include the patcher, addon main sources/resources and build
recipe; QA and tests are not distributed. Feed these generated locks to the explicit
builder below. Never copy the private lab's worlds, accounts, queues or QA driver.

Explicit candidate ZIP/MRPack entries have fixed timestamps, Unix file modes and
sorted order; repeated builds from identical bytes reproduce archive hashes even
when input file mtimes differ. Historical/default archive modes retain their prior
behavior. The release workflow obtains its version from the current-candidate
pointer, requires a matching `v<version>` publication tag, and never dispatches or
publishes merely by running this local recipe. Workflow dispatch without a release
tag is build-only. Remote publication still needs explicit authorization.

```powershell
python -B scripts/build-client-release.py `
  --release-metadata <candidate-directory>/release.json `
  --custom-lock <candidate-directory>/custom-artifacts.lock.json `
  --mods-lock <candidate-directory>/mods.lock.json `
  --downloads <read-only-mod-download-cache> `
  --runtime-cache <read-only-runtime-cache> `
  --output <new-external-output-directory>
```

All flags except `--mods-lock` are required together. Omit `--mods-lock` to use
`pack/mods.lock.json`. Do not mix these flags with historical `--candidate-v2` or
`--candidate-v12`. Invocations without explicit flags retain their existing behavior.

`--runtime-cache` uses the existing layout: the Java archive at its root and the
Forge installer under `pack/`; filenames/hashes come from `pack/client-runtime.lock.json`.
The mod download cache contains artifacts directly by locked filename. Inputs remain
read-only; candidate output must be new or empty, external to the source/public
checkout and disjoint from input/cache directories. Linked paths are rejected.
Candidate validation requires Python 3.11 or later for the standard-library TOML parser.

### Release metadata

```json
{
  "version": "2.1.0",
  "installer": 12,
  "clientRelease": "2.1.0-r12",
  "clientFingerprint": "virgos-client-2.1.0-r12"
}
```

Version must be a safe three-part release version, optionally with a prerelease
suffix. Installer must be a positive integer. Client release must equal the version
or begin with `<version>-`; fingerprint must equal `virgos-client-<clientRelease>`.
Minecraft/Forge remain pinned to 1.20.1/47.4.22 in the mod lock.

### Custom artifact lock

Use schema 1 with the existing `artifacts` list shape:

```json
{
  "schema": 1,
  "artifacts": [{
    "filename": "virgos_dh_compat-0.1.0.jar",
    "local_source": "artifacts/virgos_dh_compat-0.1.0.jar",
    "hash_algorithm": "sha256",
    "hash": "<verified-artifact-hash>",
    "sides": ["client", "server"],
    "mode": "required"
  }]
}
```

Candidate relative `local_source` paths resolve from the custom lock's directory,
not the checkout. Absolute local paths are also accepted; traversal is forbidden.
Legacy custom-lock resolution remains checkout-relative.

Exactly three required client roles must be supplied:

| Filename | Top-level Forge mod ID |
|---|---|
| `virgos_codex-<version>.jar` | `virgos_codex` |
| `DistantHorizons-3.3.3-1.20.1-fabric-forge.jar` | `distanthorizons`, version 3.3.3 |
| `virgos_dh_compat-<version>.jar` | `virgos_dh_compat` |

SHA-256 or SHA-512 hashes and actual `META-INF/mods.toml` identities are checked.
Duplicate/unexpected/optional roles, QA drivers and test packages are rejected.
The known DH internal test-renderer classes/shaders shipped in 3.3.3 are preserved;
they are upstream runtime diagnostics, not the Virgos QA driver. Server-only Core
entries are ignored by the client builder. An upstream DH download with the same
filename is replaced by the verified bundled artifact, never distributed twice.

Manifest project IDs are `virgos-codex`, `distant-horizons`, and `virgos-dh-compat`.
The installer accepts only those project/filename pairs, validates bundled hashes
before mutation and never downloads these components.

JAR bytes—including original licenses/notices—are bundled unchanged. The installer
uses `asistente/bundled/`; MRPack uses `overrides/mods/`. Bundled components are required
and have no network download URL. Preserve source/license notices when preparing the
pinned inputs; this builder neither invents nor strips them.

## Keep the patched client installed

The candidate must ship both `asistente/dh-client-settings.ps1` and the DH v5 seed
under `asistente/overrides/config/DistantHorizons.toml`. The builder rejects half-pairs;
default/historical selection semantics remain unchanged, but packages with the new
seed also include its requested helper. Packages with neither retain legacy behavior.

Before any download, mod replacement or lock write, the installer computes the DH
settings plan. It rejects unsupported/invalid configuration without mutation, preserves
personal v5 rendering values, and disables the native auto-updater so it cannot replace
the pinned patched JAR. The managed seed is not copied over existing settings while a
plan exists. Older-schema settings follow the helper's backup-and-v5-seed migration;
successful installation applies the plan through the existing atomic writer.

## Verification and handoff

Run `python -B -m unittest discover -s tests -p test_client_release_contents.py`.
The external synthetic tests verify metadata, rejection without output, bundled
identities, byte-preserved JARs and unchanged published inputs/caches. No runtime
compatibility or public promotion is implied by an archive test.

Pass the candidate artifacts and their `release.json` hashes to the isolated pack
verification phase. Updating published locks, promoting to main, stopping/upgrading
the server and uploading an installer remain separate authorized operations.
