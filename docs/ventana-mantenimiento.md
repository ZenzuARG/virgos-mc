# Ventana de mantenimiento: terreno y spawn

Este procedimiento es la única ruta autorizada para mutar el mundo público con
Chunky y promover la señalización v5. No se ejecuta mientras haya jugadores.

## Precondiciones

1. Tener un backup completo verificado (`backups/full/*.zip`).
2. Iniciar el servidor con `scripts/run-public.cjs` y esperar el mensaje de listo.
3. Confirmar `view-distance=8` y `simulation-distance=6`.
4. Confirmar `list` con cero jugadores.

## Orden de ejecución

```powershell
node scripts/health-report.cjs
python scripts/pregen-managed.py --world minecraft:overworld --center 672 752 --radius 768 --seconds 3600 --label spawn --confirm
python scripts/pregen-managed.py --world minecraft:overworld --center 672 600 --radius 512 --seconds 3600 --label north-route --confirm
python scripts/pregen-managed.py --world minecraft:overworld --center 672 1000 --radius 512 --seconds 3600 --label south-route --confirm
python scripts/pregen-managed.py --world minecraft:overworld --center 824 736 --radius 512 --seconds 3600 --label east-route --confirm
python scripts/pregen-managed.py --world minecraft:overworld --center 520 736 --radius 512 --seconds 3600 --label west-route --confirm
python scripts/pregen-managed.py --world minecraft:the_nether --center 0 0 --radius 768 --seconds 3600 --label nether --confirm
python scripts/pregen-managed.py --world minecraft:the_end --center 0 0 --radius 512 --seconds 3600 --label end --confirm
python scripts/pregen-managed.py --world aether:the_aether --center 0 0 --radius 512 --seconds 3600 --label aether --confirm
python scripts/pregen-managed.py --world twilightforest:twilight_forest --center 0 0 --radius 512 --seconds 3600 --label twilight --confirm
python scripts/promote-spawn-guidance.py --backup backups/full/<backup-verificado>.zip --confirm
```

Cada job debe terminar con `complete` o quedar documentado como pausado por
jugadores/tiempo. Si un job falla, se detiene la ventana y no se ejecutan los
siguientes. Los informes quedan en `.runtime/pregen/`, `.runtime/health/` y
`.runtime/spawn-promotion/`.

## Evidencia de la ventana ejecutada

El 3 de noviembre de 2026 se completaron los nueve jobs en producción con cero
jugadores: spawn (9.409 chunks), cuatro rutas (4.225 cada una), Nether (9.409)
y End/Aether/Twilight (4.225 cada uno). La promoción v5 verificó las nueve
estaciones mediante `data get block`; el health report posterior registró 20 TPS,
2,4/7,1 GB, 111 entidades, 8 ítems, 0 aldeanos y 0 minecarts.
