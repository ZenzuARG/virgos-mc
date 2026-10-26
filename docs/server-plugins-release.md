# Server-only plugins in the controlled public trial

The provisional **2.2.0** release adds SkinsRestorer 15.12.6 and the guarded
TreeFeller 1.33.0-virgos.3 fork as server plugins, never client mods. The declared
repository asset URLs are **not evidence of publication or availability**.
No release, CI run or public deployment is performed by the source helpers.

## Offline build and staging

Use external directories, a local Java17 JDK and the six exact inputs listed by
`dev/tree-feller/UPSTREAM.json`. The cache filenames are:

- `TreeFeller-1.33.0.jar` and `TreeFeller-upstream-source.zip`.
- `forge-1.20.1-47.4.22-0.6.1-universal.jar`.
- `CoreProtect-CE-24.1.jar` (public compile-only provider).
- `bungeecord-chat-1.20-R0.1.jar` and `guava-31.1-jre.jar`.

```powershell
python -B scripts/build-tree-release.py --cache-root C:/external/tree-cache --output C:/external/new-tree-build --java-home C:/external/jdk17 --offline --plan
python -B scripts/build-tree-release.py --cache-root C:/external/tree-cache --output C:/external/new-tree-build --java-home C:/external/jdk17 --offline
python -B scripts/prepare-dh-release.py --metadata pack/candidates/2.2.0/release.json --cache-root C:/external/release-cache --inputs-dir C:/external/new-release-inputs --java-home C:/external/jdk17 --offline --tree-artifacts C:/external/new-tree-build
```

`--plan` verifies cached providers and prints the command without a JVM or output
write. `--offline` never downloads. Without `--offline`, only anonymous official
HTTPS providers are fetched; no GitHub session, token or environment proxy is
used. A missing/corrupt provider, linked path, source/patch/license mismatch or
output overlap fails closed. The existing fork builder caps its Java processes
at 256 MiB and produces the complete GPL source archive. The default build refuses
bytes that differ from the frozen .3 hashes. The hosted Linux/Temurin workflow
passes `--allow-platform-variant`: it still validates every input, class footprint,
CRC, source archive, license and output role, but records platform-specific artifact
hashes in its manifest. Java compiler patch level and OS toolchain details can alter
class bytes while leaving the validated behavior and source unchanged. A NEW external
copy restores exact pinned text bytes (GPL license LF; other text CRLF), without
editing the checkout; cross-platform/JDK-vendor byte identity remains unproven.

The anonymous full Ketting public download was verified: 6,365,185 bytes,
SHA256 `1614068a547d9c27d738d9d4b8d8f1ebb423afe150c810493242f4e1c2f9cf29`.
CI must pass the same full hash check, not rely on a HEAD response. This unit's build execution remains pending the shared
native diagnostic resource window; Python mock tests are not compiler proof.

## Release boundaries

| Surface | Guarantee |
| --- | --- |
| Raw administration lock | Obsolete DHSupport removed; Skins/Tree server-only pins added. |
| Runtime CoreProtect | Existing patched `1e0d93…` retained. Public `a2acef…` is compile-only and must never replace it. |
| Client custom roles | Codex, patched DH and compatibility only; Core stays server-side. No Tree, Skins, QA or traces. |
| Sources | Existing declared source entries are hash/size/path checked and preserved; DH and Tree GPL sources are merged without duplicates. |
| CI assets | Tree plugin, full GPL source ZIP and license are staged separately; sources also accompany client archives. |
| Local staging | Explicit `--tree-artifacts` uses verified external files, never the unpublished repository URL. Omitting it preserves prior candidate behavior. |

Skins configuration uses the actual 15.12.6 generated schema: player commands,
skulls, GUI commands, default permissions/default skins and forced premium skin
application are disabled; normal join restoration remains enabled. The update
sentinel disables automatic plugin replacement. No fixture names, cached skins,
accounts, databases, tokens, ops or whitelist are copied. This is matching-name
visual restoration, **not premium ownership verification or an AuthMe bypass**.

## Trial limitations and checks

Tree .3 inventories 64 modded sapling variants, with 54 static mappings and 10
explicit unresolved mappings/anchors. These are not approved exclusions or
complete modded-tree support. Actual native felling, claims, drops/durability,
species growth/replant and restart replay remain unproven; no guard was weakened
to make the public trial succeed. The parent operator owns coordinated DH
handoff, verified backup, saved-data preservation, rollback and public restart.

```powershell
python -B -m unittest discover -s tests -p test_tree_release_build.py -v
python -B -m unittest discover -s tests -p test_prepare_dh_release.py -v
```

These are isolated Python/mock boundaries. They do not publish, download a
private plugin, run games or establish native compatibility.
