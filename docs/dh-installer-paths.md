# DH installer path checks

The installer inspects both the destination configuration and bundled defaults,
including existing parent directories, before replacing mods or writing the pack
lock. It queries native Windows metadata without following the inspected entry.

Ordinary files and the sixteen documented CloudFiles reparse tags are accepted.
Symbolic links, junctions, other name-surrogate tags, unknown reparse tags and
metadata-query failures remain rejected. A folder named `OneDrive` is not an
exception. This check does not provide a new race-free filesystem guarantee.

If installation is rejected, extract the ZIP into a normal local directory and
choose a local game directory without links. Do not remove reparse metadata or
disable OneDrive to bypass the check. The error identifies the rejected path.

## Verification

Run with Windows PowerShell 5.1:

```powershell
powershell.exe -NoProfile -File scripts/test-dh-cloud-paths.ps1
powershell.exe -NoProfile -File scripts/test-dh-client-settings.ps1
powershell.exe -NoProfile -File scripts/test-client-installer.ps1 -Package <external-fixture-package>
```

Cloud-tag fixtures are deterministic metadata simulations. They do not prove
operation with a real OneDrive provider; that check requires an actual synced
installation. Native ordinary paths, missing destinations and a real junction
are exercised without elevation. Test fixtures remain outside the worktree.
