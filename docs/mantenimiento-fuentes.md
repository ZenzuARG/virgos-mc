# Fuentes y reconstrucción de Virgos-MC

La copia privada `backups/virgos-v2-fuentes-*.zip` complementa los respaldos de partida de `backups/full`. Conserva scripts, plantillas del instalador, locks, configuración del paquete, diseños del spawn, fuentes Java, el JAR publicado y los insumos locales del parche de Playit. `sources-manifest.json` registra tamaño y SHA256 de cada entrada; `.lab/v2/source-archive.json` registra la verificación del ZIP completo. Se genera con `scripts/archive-v2-sources.py`.

Para recuperar la partida hacen falta también una copia completa verificada y Java/bibliotecas de la plataforma. No extraigas las fuentes encima del servidor activo. Trabajá en otra carpeta y compará los cambios antes de desplegarlos.

## Virgos Core

Con Java 17 y Python 3.11 o posterior disponibles, desde la raíz del proyecto:

```powershell
$env:JAVA_HOME = 'D:\proyectos\mc-server\.runtime\jdk-17.0.20.1+1'
$env:GRADLE_USER_HOME = 'D:\proyectos\mc-server\.cache\gradle'
.\dev\virgos-core\gradlew.bat -p dev\virgos-core check build codexJar
```

El wrapper fija Gradle 8.8 y `gradle.properties` fija Minecraft, Forge y la versión propia. La primera reconstrucción requiere Internet para las dependencias de Gradle/Forge. El ZIP conserva el JAR de Voice Chat usado para compilar en la ruta esperada. En esta instalación, con las dependencias presentes, `--offline check` fue satisfactorio.

Los JAR publicados son `virgos_core-2.0.0.jar` y `virgos_codex-2.0.0.jar`; sus SHA256 están en `pack/custom-artifacts.lock.json`. Un JAR recompilado puede tener otro hash por las fechas de empaquetado: no reemplazar el publicado ni actualizar el lock sin validar el nuevo resultado. Los hashes de la candidata v2 y las pruebas públicas están en `.lab/v2/acceptance.json` y `.lab/v2/final.json`. El archivo privado incluye también el parche de CoreProtect, su original y `scripts/PatchCoreProtect.java`.

## Parche de Playit

`dev/playit-udp-fix/build.ps1` compila `PatchCompanion.java` con Java 17 y ASM 9.9.1. El archivo de fuentes conserva el original de Companion y ambos JAR de ASM en las rutas que espera ese script. El parche verifica el SHA512 original, exige exactamente una sustitución y produce `pack/local/playit_companion-forge-0.1.2-virgos.1.jar`.

La reconstrucción aislada de cierre produjo exactamente el SHA256 fijado en `versions.lock.json`; informe `playit-rebuild-v1.json`. El original sólo cambia en una clase, más una nota de procedencia. `deploy.py` se reserva para un despliegue deliberado con el servidor detenido; no hace falta ejecutarlo para comprobar o archivar fuentes.

## Instalador

`scripts/build-client-release.py` usa `templates/`, los locks y `pack/client-overrides`. Requiere las descargas fijadas en `.cache/pack/downloads` y los instaladores Java/Forge que comprueba por hash. Esas descargas se pueden recuperar mediante la preparación del paquete; no forman parte de esta copia de fuentes. El ZIP para amigos se conserva tal como fue probado en `dist/` dentro del archivo privado.

Para la entrega vigente, compartí `dist/Virgos-MC-2.0.0-instalar.zip`. Los clientes no necesitan Gradle, las fuentes ni los respaldos del servidor.
