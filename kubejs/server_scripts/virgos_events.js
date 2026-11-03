// Small, reversible seasonal/event layer. Gameplay balance remains in native
// configs; this script only announces the current activity and points players
// to the corresponding Heracles objective.
const SEASONAL_MESSAGE = 'Temporada Virgos: elegí una expedición y registrá el hallazgo en el Códice.'

PlayerEvents.loggedIn(event => {
  event.player.tell(Text.of('Bastión Virgos: revisá Heracles para la temporada y las expediciones activas.'))
})

ServerEvents.tick(event => {
  if (event.server.tickCount % 24000 !== 0) return
  event.server.runCommandSilent(`tellraw @a {"text":"${SEASONAL_MESSAGE}","color":"gold"}`)
})
