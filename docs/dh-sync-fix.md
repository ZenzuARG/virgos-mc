# Distant Horizons: reparación de sincronización

## Causa encontrada

La semilla de cliente no habilitaba explícitamente la generación/sincronización remota y limitaba el radio LOD a 32 chunks. La configuración de servidor y cliente no estaba alineada; el cliente no conservaba un caché Distant_Horizons_server_data con datos del servidor.

## Cambio

- El servidor mantiene enableDistantGeneration = true y generatorPlan = CHUNKS_ONLY con chunkGeneratorMode = PRE_EXISTING_ONLY: DH puede enviar los LOD persistidos y solo procesa chunks que ya existen; Chunky sigue siendo responsable de pregenerar el terreno. El cliente mantiene enableDistantGeneration = true para solicitar y guardar los LOD remotos.
- Cliente: radio LOD: 256 chunks; la generación local queda desactivada (generationMaxChunkRadius = 0).
- Servidor: generatorPlan = CHUNKS_ONLY, chunkGeneratorMode = PRE_EXISTING_ONLY, radio realtime 256 y rate limits 16; el modo preexistente evita generar dimensiones nuevas y mantiene activa la entrega del caché.
- view-distance=8 y simulation-distance=6 no cambiaron.

## Evidencia aislada

Con DH 3.3.3 Forge 1.20.1 y login AuthMe normal, el cliente negoció serverReady=true, synchronizeOnLoad=true, maxSyncOnLoadDistance=625, generatorPlan=CHUNKS_ONLY; luego creó su base Distant_Horizons_server_data con 104 filas FullData, de las cuales 54 coincidieron byte a byte con filas del servidor. Antes del cambio el caché del cliente estaba ausente.

Fuente: .runtime/reports/dh-sync-fix-2026-11-03.json.
