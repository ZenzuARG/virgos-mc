# Stage server-only skin restoration safely

SkinsRestorer is a laboratory candidate, not a released dependency. Displaying a
Mojang skin does not verify account ownership and must not replace AuthMe or
change the server's UUID or online-mode policy.

The exact isolated destination is
`D:/proyectos/mc-server-lab/create-addons-20261025/skins`. It is separate from the
six Create performance variants. No existing laboratory is modified in place.

An artifact manifest may optionally include:

```json
"serverPlugins": [{
  "filename": "SkinsRestorer-15.12.6.jar",
  "sha256": "a85b4a370f988741c9a38f4d0498262edacbf3220314790ac1c127461996359c"
}]
```

Only the source-pinned plugin name and hash are accepted. Preparation rejects
unknown, duplicate, linked, corrupted or dual-role inputs before creating the
destination. Plugins are copied only to `server/plugins`, never any client or
`mods` directory, and become part of the launcher's immutable hash inventory.
Manifests without this optional field retain their previous behavior.

Native acceptance still requires generated-config inspection, normal login with
a matching official nickname, actual skin/profile observations, reconnect and
restart persistence, and unchanged authentication/UUID behavior. Manual skin
selection or a successful server boot is not equivalent proof.

## Matching-name fixture

Append `--skin-fixture` to supported preparation only for the exact `skins`
destination with the pinned plugin present. Client2 then uses the public nickname
`Notch`, its offline UUID and token `0`; client1 remains `VirgosQA1`. The fixture is
recorded in the immutable preparation manifest and the whitelist contains only
these two names. Default preparation still uses `VirgosQA1`/`VirgosQA2`.

This is not a Microsoft login or account-ownership test. AuthMe configuration,
online-mode, operator permissions and authentication requirements are unchanged.
Register/login normally, then request `{"action":"audit_skin"}` through the local
QA queue. `profile-skin.json` records only the fixture player's public texture
property/signature, strictly validated decoded Mojang texture fields, and the
actual client skin resource/model. Unknown payload fields, non-Mojang URLs and
oversized values are rejected without logging their contents. No session or
credential properties are read. Existing camera key controls can show third-person
rendering without another gameplay action.
The public texture property comes from the local player's current network
PlayerInfo profile, so plugin property updates are observable; its name/UUID must
still match the local player's identity. Signatures are recorded, not RSA-verified.

Automatic matching-nickname restoration must be observed without `/skin set` or
another manual skin assignment. Repeat normal authentication and observations
after reconnect and restart. The old six performance laboratories retain their
original observer JARs; build a separate QA artifact for the future skin fixture.

The focused Python suite also tests the packaged Java public-texture boundary when
the observer artifact and its generated runtime classpath are explicitly supplied:

```powershell
$env:VIRGOS_QA_JAR = '<new-controls-QA.jar>'
$env:VIRGOS_QA_CLASSPATH_FILE = '<observer-build>/qa-runtime-classpath.txt'
python -B -m unittest discover -s tests -p test_dh_fullpack_lab.py
```

Use Java17 through `JAVA_HOME`. Without these artifact inputs, that Java boundary
probe is explicitly skipped rather than reported as verified. Its cases cover
legacy HTTP and HTTPS Mojang texture URLs, slim SKIN metadata, CAPE, unsigned and
signed observation, and rejection of duplicate/private fields, wrong hosts and
oversized values. Signature observation is not RSA or account-ownership proof.
