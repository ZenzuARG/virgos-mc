# Performance release 3.1
Objective: Publish the 3.1 release with its one-click installer, retaining current Codex and permission features.
Branch: codex/project-cleanup-and-docs; delivery: ask-on-risk, forecast <=400 authored lines; runner: Python unittest and isolated PowerShell installer fixtures, archive readback and independent verification.

## Specs
S1. "Okey, hagamos algo, si ya tenemos todo optimizado y solucionado, larguemos un release nuevo, misma solucion de 1 solo click para instalar el juego, pero implementar todo lo nuevo y los ajustes que hicimos" Include the tested Ocuwheel and ModernFix loading changes, existing DH2/.5 settings and accepted grass128/blades64; retain recipe sync workaround. Do not claim unmeasured FPS gains or distribute personal high shader settings.
S2. "No es necesario medir eso, va a mejorar levemente el rendimiento, apliquemoslo, y porque decis que no queres mezclar los cambios del codice y permisos? eso ya lo implementamos tengo entendido, hay que mantenerlo" Preserve implemented Codex and server permissions; do not downgrade or rebuild unrelated changes blindly. Preserve original client and existing personal shader/map data.
S3. "Bien, teniendo en cuenta todas las mejoras y ajustes, larguemos la version 3.1 que creo que el server va a quedar un rato largo en esta version, esta bastante solida" Technical package version3.1.0; preserve verified server compatibility without unrequested restart or migration. Publish to the discussed GitHub Releases destination ZenzuARG/virgos-mc using the existing CLI session only after verification.
S4. "Esta largada de version significa tambien crear el release con el instalador correspondiente" Deliver the published release and its corresponding one-click installer ZIP, not just metadata.

## Tasks
- T1 S1-S3 inline — pin candidate inputs and balanced seeds, preserve upgrade preferences; complete locally. Risk:item5 installer/dependencies. Mapping delegated read-only because release inputs exceed bounded inline evidence.
- T2 S1-S4 inline — focused regression, build reproducible package and isolated installer tests; complete (15 Python regressions; installer WindowsPowerShell5.1; controls/DH/memory passed). No live launcher/original install mutation.
- T3 S1-S4 independent verifier — inspect actual archives, upgrade/fresh install and wire compatibility; PASS, no new blockers. Risk:item5.
- T4 S3-S4 inline — scoped commit/review per native mode, publish new release/assets without overwriting existing release; pending (CLI not authenticated). No server rollout authorized.

## Log
L1. "Okey, hagamos algo, si ya tenemos todo optimizado y solucionado, larguemos un release nuevo, misma solucion de 1 solo click para instalar el juego, pero implementar todo lo nuevo y los ajustes que hicimos"
L2. "No es necesario medir eso, va a mejorar levemente el rendimiento, apliquemoslo, y porque decis que no queres mezclar los cambios del codice y permisos? eso ya lo implementamos tengo entendido, hay que mantenerlo"
L3. "Bien, teniendo en cuenta todas las mejoras y ajustes, larguemos la version 3.1 que creo que el server va a quedar un rato largo en esta version, esta bastante solida"
L4. "Esta largada de version significa tambien crear el release con el instalador correspondiente"
L5. Frozen installer27 Codex hash matches actual test and current built JAR;3.0.10 server parcel/permissions rollout records exist. Original client unchanged. Guided Codex task has offline proof, pending rendered proof. ModernFix Dynamic Resources smoke tested but GrassierGrass advisory remains; accepted oil artifact documented, no blanket bug-free claim.

L6. Package/wire identity decoupled without changing admission policy:3.1.0 package, installer28, wire3.0.6. RED new compatible identity rejected; GREEN15 packaging tests passed. Grass preservation RED failed then GREEN actual installer fixture passed. Existing behavior differential independently byte-identical versus5063792. No server or original-client mutation.
L7. Independent verifier PASS all local S1-S4 checks; published deliverable still pending. Actual ZIP382523127bytes SHA256dc3451c4b029723e8a9b70d09ccd7d125604da79d0decf7075df12b1392f9335. MRPack382489614bytes SHA256f5d2ff9e8f331b89d70c188b4db8aa4ffd58d4c38965c07a0827056bd504a124. Output: external system-temp virgos-release-3.1.0-r28. Existing global candidate consistency2failures and source-only WindowsPowerShell5.1 encoding fixture are unrelated; actual distributed BOM scripts pass.
L8. Portable GitHub CLI exists but reports no authenticated session. No GitHub mutation; no credentials from other channels inspected. Native high-risk assessment requires explicit untracked selection; use committed-only scoped unit to exclude unrelated work. Risk:item5 installer/dependencies. Rollback: remove candidate3.1.0, restore seed/template/builder changes; deployed server/data unchanged.

L9. Local release commit e326302; Windows source-byte preservation fix d98a202. Both LGPL notice blobs now match their original pinned SHA256 after disabling checkout conversion. No license whitespace was edited. Final UTF-8 guide normalization preserves unchanged copy. Rebuild final archives after that guide-only correction.

L10. Final output system-temp virgos-release-3.1.0-r28-final. After UTF-8 guide correction, installer differs only at LEEME.txt; MRPack byte-identical. ArchiveCRC and original pinned source hashes PASS. Final hashes are recorded in docs/releases/3.1.0-client-installer.json. Publication and native candidate review remain pending; GitHub session must be restored by user.

L11. User chose review (1). Exact granted START returned lens_context_budget_exceeded, mutation not_started; no authority exists and exact retry cannot work. Reduced new net candidate by removing duplicated full candidate mods lock and appending only the identical Ocuwheel entry to canonical pack/mods.lock.json. Existing entries byte-preserved; candidate build now uses canonical mods lock. No history rewrite. Rebuild hashes must match final verified archives before fresh native START.

L12. Complete native evidence also includes a changed canonical file, so finalized reduction uses a small additionalMods client-only pin in candidate metadata instead. Canonical mods lock restored exactly; builder accepts optional unique required-client additions and rejects collisions/nonclient entries before output. Two focused RED tests observed before implementation. This avoids reviewing or maintaining a duplicated10k-line base lock. No runtime dependency bytes changed.

L13.17packaging regressionsPASS; independent overlay verifierPASS (baseline omission byte-identical, all name collisions and nonclient/optional additions reject before mutation). Actual overlay output hashes equal finalZIP/MRPack. Canonical mods lock unchanged. Native target must be freshly preflighted for this reduced net candidate; prior target exceeded budget and had no authority.
