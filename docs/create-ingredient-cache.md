# Refresh client recipe ingredients after tag binding

Codex refreshes ordinary Forge ingredient caches after the client receives tags. This
repairs existing JEI synthetic deployer recipes that cached `Empty Tag: create:sandpaper`
before the server's valid sandpaper tag arrived. No recipe is hidden or replaced.

## Cache boundary

Forge's `Ingredient.invalidateAll()` advances an epoch; it does not eagerly clear
every Ingredient. Vanilla `getItems()` and ModernFix 5.27.88's strong/soft cache
fast paths do not check that epoch. A client packet tag event advances the epoch,
and a client-only `getItems` HEAD injection checks it before returning cached items.
Forge's virtual `invalidate()` clears vanilla caches and invokes ModernFix's
existing soft-reference clearing hook. `markValid()` prevents repeated clearing
within the same epoch. Custom Ingredient subclasses retain their original behavior.

The mixin uses Minecraft 1.20.1's pinned SRG selector without a refmap, like the
existing version-pinned Core mixins. Its required injection fails visibly if the
method disappears. The config's `client` list excludes dedicated servers, and the
event subscriber ignores the integrated server's `SERVER_DATA_LOAD` event.

Mixin reserves its configured package prefix for transformation classes. Only the
actual mixin belongs under `mc.virgos.codex.ingredient.mixin`; the ordinary Forge
subscriber stays outside that prefix. The wiring regression rejects ordinary
classes in the reserved prefix, preventing startup `IllegalClassLoadError`.

## Verification

Run from `dev/virgos-core` with Java 17 and the existing Voice Chat API available:

```powershell
./gradlew.bat --offline checkIngredientCache check codexJar
```

The focused test exercises actual Forge epoch changes for initial tags, reconnect,
and server-event isolation. A deterministic cache fixture runs the production HEAD
hook against strong/soft cache semantics, stable epochs, custom ingredients, and an
unrelated working control. It does not substitute for full-pack Mixin/JEI testing.

Before shipping, use an isolated full-pack client/server to verify the packaged
MixinConfigs manifest, successful mixin application with ModernFix, and all six
existing JEI sandpaper deploying ingredients on initial connection and reconnect.
Both real sandpaper tools must appear, without barrier placeholders; retain a
working unrelated ingredient control. Truly missing compatibility tags and synced
barrier items require separate recipe/data corrections and are not fixed here.

Rollback removes this Codex cache hook, its client event subscriber and mixin config
plus the Codex manifest entry; no world, server cache or persisted format changes.
