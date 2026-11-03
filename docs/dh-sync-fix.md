# Distant Horizons: reparación de sincronización

## Causa encontrada

La semilla de cliente no habilitaba explícitamente la generación/sincronización remota y limitaba el radio LOD a 32 chunks. La configuración de servidor y cliente no estaba alineada; el cliente no conservaba un caché Distant_Horizons_server_data con datos del servidor.

## Cambio

- El servidor deja generatorPlan = DISABLED para que Chunky controle la generación de chunks faltantes; DH solo sirve el caché LOD persistido. El cliente mantiene generatorPlan = CHUNKS_ONLY para consumir los LOD remotos.
- Cliente: radio LOD: 256 chunks; la generación local queda desactivada (generationMaxChunkRadius = 0).
- Servidor: generatorPlan = DISABLED, chunkGeneratorMode = PRE_EXISTING_ONLY, radio realtime 256 y rate limits 16; esto evita el inyector de dimensiones no soportadas y conserva la entrega del caché.
- view-distance=8 y simulation-distance=6 no cambiaron.

## Evidencia aislada

Con DH 3.3.3 Forge 1.20.1 y login AuthMe normal, el cliente negoció serverReady=true, synchronizeOnLoad=true, maxSyncOnLoadDistance=625, generatorPlan=CHUNKS_ONLY; luego creó su base Distant_Horizons_server_data con 104 filas FullData, de las cuales 54 coincidieron byte a byte con filas del servidor. Antes del cambio el caché del cliente estaba ausente.

Fuente: .runtime/reports/dh-sync-fix-2026-11-03.json.
