# Three pinned Create addons for a controlled public trial

The production mod lock adds exactly three unmodified upstream JARs on both the
client and server. Existing entries, versions and download hashes are preserved.
This is package preparation, not proof that a public deployment has occurred.

| Addon | Published release | Declared mod version | Native evidence |
| --- | --- | --- | --- |
| Crafts & Additions | forge-1.20.1-1.3.3 | 1.20.1-1.3.3 | Bounded processing/energy/JEI trial passed |
| Bells & Whistles | 0.4.5-1.20.x, Create6 | 0.4.3-1.20.x | Functional trial pending |
| Enchantment Industry | 1.4.1 | 1.4.1-for-create-6.0.8 | Functional trial pending |

Bells deliberately retains its actual internal version rather than rewriting a
third-party JAR. The exact pinned files, primary download URLs, SHA-512, sizes,
Forge descriptors and dependency ranges are in `pack/mods.lock.json`. All three
fit the existing Create6.0.8/Forge47.4.22 dependency graph. Static compatibility
is not a whole-pack runtime or performance approval.

## Delivery boundary

- Build a new identity-matched client/server release and installer before cutover;
  existing clients do not acquire new mods merely by reconnecting.
- Keep the existing 8192MB client default. Never ship laboratory QA or packet traces.
- Preserve public worlds, player records, claims, AuthMe and all DH databases,
  server identity/configuration and generation checkpoints.
- Coordinate one backed-up cutover with the DH recovery task; do not overwrite
  its artifacts or advertise an unverified DH fix.
- Keep upstream notices and source references; these addon JARs are not re-licensed.

## Checks

```powershell
python -B -m unittest discover -s tests -p test_create_addons_release_lock.py -v
python -B -m unittest discover -s tests -p test_create_addons_artifacts.py -v
```

The release-lock test pins both sides and real descriptor identities. Preparation
also checked cached JAR CRC, both advertised hashes and actual descriptors. All
pre-existing parsed lock entries remain identical to the preserved baseline.
These checks do not establish successful public installation or gameplay.

To reproduce the original six-variant laboratory comparison after this production
lock changes, pass an explicit preserved **pre-addon** lock to the laboratory
artifact tool. The new production lock must not be described as the old baseline.
