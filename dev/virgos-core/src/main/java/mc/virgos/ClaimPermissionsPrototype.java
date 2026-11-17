package mc.virgos;

import net.minecraft.commands.CommandSourceStack;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import java.util.List;
import java.util.function.IntConsumer;
import com.mojang.authlib.GameProfile;
import net.minecraft.world.entity.player.Inventory;

/** In-game Spanish claim permissions UI backed by Open Parties and Claims. */
public final class ClaimPermissionsPrototype {
    private final ClaimPermissionService service;

    public ClaimPermissionsPrototype(ClaimPermissionService service) {
        this.service = java.util.Objects.requireNonNull(service, "Claim permission service");
    }

    public int open(CommandSourceStack source) {
        ServerPlayer player = source.getPlayer();
        if (!available(player)) return 0;
        var target = service.claimTarget(player);
        switch (target.state()) {
            case FREE -> openClaimEntry(player, target);
            case OWNED -> openOverview(player);
            case OTHER -> player.sendSystemMessage(Component.literal("Esta parcela pertenece a otra persona. No puedes reclamarla ni modificar sus permisos."));
            case UNAVAILABLE -> player.sendSystemMessage(Component.literal("No se pudo consultar la parcela. Inténtalo de nuevo más tarde."));
        }
        return target.state() == ClaimEntryFlow.State.FREE || target.state() == ClaimEntryFlow.State.OWNED ? 1 : 0;
    }

    private void openClaimEntry(ServerPlayer player, ClaimEntryFlow.Target target) {
        player.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, Items.MAP, "§6Parcela sin reclamar", "§7Parcela: " + target.x() + ", " + target.z());
            put(icons, 13, Items.GRASS_BLOCK, "§aReclamar parcela", "§7Protege este terreno y abre sus permisos");
            put(icons, 22, Items.BARRIER, "§cCerrar", "§7No se reclamará ningún terreno");
            return new ChestMenu(MenuType.GENERIC_9x3, id, inventory, icons, 3) {
                @Override public void clicked(int slot, int button, ClickType click, Player actor) {
                    if (actor != player || click != ClickType.PICKUP || button != 0) return;
                    if (slot == 22) { player.closeContainer(); return; }
                    if (slot != 13) return;
                    // A delayed or repeated packet must not reclaim after this screen has closed.
                    if (player.containerMenu != this) return;
                    var result = service.claimHere(player, target, () -> available(player));
                    player.closeContainer();
                    switch (result) {
                        case OWNED -> {
                            player.sendSystemMessage(Component.literal("Parcela reclamada. Ya puedes configurar sus permisos."));
                            if (available(player)) openOverview(player);
                        }
                        case STALE -> player.sendSystemMessage(Component.literal("La parcela o tu ubicación cambió. Pulsa P de nuevo para revisar el terreno actual."));
                        case DENIED -> player.sendSystemMessage(Component.literal("No se puede reclamar ahora. Inicia sesión y utiliza el modo de reclamación personal, sin modo administrativo ni suplantación."));
                        case FAILED -> player.sendSystemMessage(Component.literal("No se pudo reclamar la parcela. Revisa tu límite de parcelas y las restricciones de la zona. Los permisos no se han abierto."));
                    }
                }
                @Override public ItemStack quickMoveStack(Player actor, int slot) { return ItemStack.EMPTY; }
                @Override public boolean stillValid(Player actor) {
                    return actor == player && available(player) && target.sameChunk(service.claimTarget(player));
                }
            };
        }, Component.literal("Reclamar parcela")));
    }

    private boolean available(ServerPlayer player) {
        if (player == null) return false;
        if (!VirgosCore.AUTH.ready()) {
            player.sendSystemMessage(Component.literal("AuthMe está en mantenimiento; los permisos quedan bloqueados."));
            return false;
        }
        if (VirgosCore.UPDATE_GATE == null || !VirgosCore.UPDATE_GATE.accepted(player)) {
            player.sendSystemMessage(Component.literal("Actualizá el paquete Virgos-MC antes de abrir los permisos."));
            return false;
        }
        if (!VirgosCore.AUTH.authenticated(player)) {
            player.sendSystemMessage(Component.literal("Usá /login primero para abrir los permisos."));
            return false;
        }
        if (!service.ready()) {
            player.sendSystemMessage(Component.literal("La configuración de permisos necesita revisión; no se aplicarán cambios."));
            return false;
        }
        return true;
    }


    private ClaimPermissionService.Context context(ServerPlayer player) {
        if (!available(player)) { player.closeContainer(); return null; }
        var context = service.current(player);
        if (context == null) {
            player.closeContainer();
            player.sendSystemMessage(Component.literal("La parcela ya no está disponible. Pulsa P de nuevo."));
        }
        return context;
    }

    private ChestMenu locked(int id, Inventory inventory, SimpleContainer icons, ServerPlayer owner,
                             ClaimPermissionService.Context context, IntConsumer action) {
        return new ChestMenu(MenuType.GENERIC_9x3, id, inventory, icons, 3) {
            private boolean valid(Player actor) {
                return actor == owner && owner.containerMenu == this && available(owner) && service.sameContext(owner, context);
            }
            @Override public void clicked(int slot, int button, ClickType click, Player actor) {
                if (valid(actor) && click == ClickType.PICKUP && button == 0) action.accept(slot);
            }
            @Override public boolean stillValid(Player actor) { return valid(actor); }
            @Override public ItemStack quickMoveStack(Player actor, int slot) { return ItemStack.EMPTY; }
        };
    }

    private void openOverview(ServerPlayer player) {
        var context = context(player);
        if (context == null) return;
        player.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            int chunks = service.areaMembers(context).size();
            put(icons, 4, Items.MAP, "§6Permisos del área · " + chunks + " chunk(s)",
                !service.protectionEnabled(context) ? "§cProtección general desactivada; revisa las reglas del servidor"
                    : service.hasPolicy(context) ? "§7Los chunks unidos comparten estos ajustes" : "§eSin reglas propias: al editar se activará este panel");
            put(icons, 10, Items.GOLD_BLOCK, "§eFamilia", "§7Configurar permisos e integrantes");
            put(icons, 12, Items.EMERALD_BLOCK, "§aAmigos", "§7Configurar permisos e integrantes");
            put(icons, 14, Items.LIGHT_BLUE_WOOL, "§bVisitantes", "§7Los grupos no conceden permisos por su nombre");
            put(icons, 16, Items.PLAYER_HEAD, "§dExcepciones por jugador", "§7Permitir, denegar o heredar; también desconectados");
            put(icons, 20, Items.OAK_FENCE, "§eUnir o separar parcelas", "§7Estar pegadas no las une automáticamente");
            put(icons, 22, Items.BARRIER, "§cCerrar", "§7Los cambios se guardan con cada clic");
            put(icons, 24, Items.PAPER, "§fVista previa por jugador", "§7Combina grupos y excepciones individuales");
            return locked(id, inventory, icons, player, context, slot -> {
                if (slot == 10) openGroup(player, ClaimPermissionService.Group.FAMILY);
                else if (slot == 12) openGroup(player, ClaimPermissionService.Group.FRIENDS);
                else if (slot == 14) openGroup(player, ClaimPermissionService.Group.VISITORS);
                else if (slot == 16) openExceptionPicker(player);
                else if (slot == 20) openAreas(player);
                else if (slot == 24) openPlayers(player, null, PlayerView.PREVIEW, 0);
                else if (slot == 22) player.closeContainer();
            });
        }, Component.literal("Permisos del área")));
    }

    private void openGroup(ServerPlayer player, ClaimPermissionService.Group group) {
        var context = context(player);
        if (context == null) return;
        player.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, Items.NAME_TAG, "§6Grupo: " + group.label,
                "§7" + service.members(context, group).size() + " integrantes · se suman permisos entre grupos");
            var permissions = ClaimPermissionService.Permission.values();
            for (int i = 0; i < permissions.length; i++) {
                var permission = permissions[i];
                boolean enabled = service.isGroupEnabled(context, group, permission);
                put(icons, 10 + i, permissionIcon(permission), (enabled ? "§a✓ " : "§c✗ ") + permission.label,
                    permission == ClaimPermissionService.Permission.BUILDING
                        ? "§cPermite destruir bloques y contenedores; solo para personas de confianza"
                        : enabled ? "§7Concedido por este grupo" : "§7No concedido por este grupo; revisa otros grupos y excepciones");
            }
            put(icons, 19, Items.NAME_TAG, "§fAdministrar integrantes", "§7Agregar o quitar jugadores conocidos");
            put(icons, 22, Items.ARROW, "§eVolver al área", "§7Cada cambio se guarda automáticamente");
            put(icons, 24, Items.PAPER, "§fVista previa por jugador", "§7Permisos del panel y su origen");
            put(icons, 26, Items.BARRIER, "§cCerrar", "§7Volver al juego");
            return locked(id, inventory, icons, player, context, slot -> {
                if (slot >= 10 && slot < 10 + permissions.length) {
                    var permission = permissions[slot - 10];
                    report(player, service.setGroupPermission(context, group, permission,
                        !service.isGroupEnabled(context, group, permission)), "Permiso actualizado y guardado.");
                    openGroup(player, group);
                } else if (slot == 19) openPlayers(player, group, PlayerView.MEMBERS, 0);
                else if (slot == 22) openOverview(player);
                else if (slot == 24) openPlayers(player, null, PlayerView.PREVIEW, 0);
                else if (slot == 26) player.closeContainer();
            });
        }, Component.literal("Grupo · " + group.label)));
    }

    static List<com.mojang.authlib.GameProfile> memberCandidates(java.util.UUID owner,
            List<com.mojang.authlib.GameProfile> known, List<com.mojang.authlib.GameProfile> online) {
        var players = new java.util.LinkedHashMap<java.util.UUID, com.mojang.authlib.GameProfile>();
        java.util.stream.Stream.concat(known.stream(), online.stream())
            .filter(profile -> profile.getId() != null && !profile.getId().equals(owner)
                && profile.getName() != null && !profile.getName().isBlank())
            .forEach(profile -> players.put(profile.getId(), profile));
        return players.values().stream().sorted(java.util.Comparator
            .comparing(com.mojang.authlib.GameProfile::getName, String.CASE_INSENSITIVE_ORDER)
            .thenComparing(profile -> profile.getId().toString())).toList();
    }


    private enum PlayerView { MEMBERS, EXCEPTIONS, PREVIEW }

    private void openExceptionPicker(ServerPlayer player) { openPlayers(player, null, PlayerView.EXCEPTIONS, 0); }

    private void openPlayers(ServerPlayer player, ClaimPermissionService.Group group, PlayerView view, int requested) {
        var context = context(player);
        if (context == null) return;
        var known = new java.util.ArrayList<>(VirgosCore.PROFILES.knownPlayers());
        known.addAll(service.storedPlayers(context));
        var candidates = memberCandidates(player.getUUID(), known,
            player.server.getPlayerList().getPlayers().stream().map(ServerPlayer::getGameProfile).toList());
        var page = ClaimMenuPage.of(candidates, requested);
        String title = view == PlayerView.MEMBERS ? "Integrantes · " + group.label
            : view == PlayerView.EXCEPTIONS ? "Excepciones individuales" : "Vista previa por jugador";
        player.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, Items.NAME_TAG, "§6" + title,
                "§7Conocidos y desconectados · página " + (page.index() + 1) + "/" + page.count());
            if (page.rows().isEmpty())
                put(icons, 13, Items.PAPER, "§7No hay jugadores para elegir", "§7Deben haber ingresado al servidor al menos una vez");
            for (int i = 0; i < page.rows().size(); i++) {
                var target = page.rows().get(i);
                boolean member = view == PlayerView.MEMBERS && service.members(context, group).contains(target.getId());
                put(icons, 10 + i, Items.PLAYER_HEAD, (member ? "§a✓ " : "§f") + target.getName(),
                    view == PlayerView.MEMBERS ? "§7Clic para agregar o quitar" : "§7Clic para ver al jugador");
            }
            if (page.index() > 0) put(icons, 18, Items.ARROW, "§ePágina anterior", "§7Ver más jugadores");
            if (page.index() + 1 < page.count()) put(icons, 20, Items.ARROW, "§ePágina siguiente", "§7Ver más jugadores");
            put(icons, 22, Items.ARROW, "§eVolver", "§7Los cambios ya están guardados");
            put(icons, 26, Items.BARRIER, "§cCerrar", "§7Volver al juego");
            return locked(id, inventory, icons, player, context, slot -> {
                if (slot >= 10 && slot < 10 + page.rows().size()) {
                    var target = page.rows().get(slot - 10);
                    if (view == PlayerView.MEMBERS) {
                        boolean included = service.members(context, group).contains(target.getId());
                        report(player, service.setMember(context, group, target, !included), "Integrantes actualizados.");
                        openPlayers(player, group, view, page.index());
                    } else if (view == PlayerView.EXCEPTIONS) openIndividual(player, target, page.index());
                    else openPreview(player, target, page.index());
                } else if (slot == 18 && page.index() > 0) openPlayers(player, group, view, page.index() - 1);
                else if (slot == 20 && page.index() + 1 < page.count()) openPlayers(player, group, view, page.index() + 1);
                else if (slot == 22) {
                    if (view == PlayerView.MEMBERS) openGroup(player, group);
                    else openOverview(player);
                } else if (slot == 26) player.closeContainer();
            });
        }, Component.literal(title)));
    }

    private void openIndividual(ServerPlayer owner, GameProfile target, int page) {
        var context = context(owner);
        if (context == null) return;
        owner.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, Items.PLAYER_HEAD, "§dPermisos de " + target.getName(), "§7Heredar → permitir → denegar");
            var permissions = ClaimPermissionService.Permission.values();
            for (int i = 0; i < permissions.length; i++) {
                var permission = permissions[i];
                var decision = service.individualDecision(context, target.getId(), permission);
                String status = decision == null ? "§7Heredado" : decision == ClaimPermissionService.Decision.ALLOW ? "§aPermitido" : "§cDenegado";
                put(icons, 10 + i, permissionIcon(permission), status + " · " + permission.label,
                    explanation(service.effectivePermission(context, target.getId(), permission)));
            }
            put(icons, 22, Items.ARROW, "§eVolver a jugadores", "§7También puedes editar desconectados");
            put(icons, 26, Items.BARRIER, "§cCerrar", "§7Volver al juego");
            return locked(id, inventory, icons, owner, context, slot -> {
                if (slot >= 10 && slot < 10 + permissions.length) {
                    var permission = permissions[slot - 10];
                    var old = service.individualDecision(context, target.getId(), permission);
                    var next = old == null ? ClaimPermissionService.Decision.ALLOW
                        : old == ClaimPermissionService.Decision.ALLOW ? ClaimPermissionService.Decision.DENY : null;
                    report(owner, service.setIndividual(context, target, permission, next), "Excepción guardada.");
                    openIndividual(owner, target, page);
                } else if (slot == 22) openPlayers(owner, null, PlayerView.EXCEPTIONS, page);
                else if (slot == 26) owner.closeContainer();
            });
        }, Component.literal("Excepción · " + target.getName())));
    }

    private void openPreview(ServerPlayer owner, GameProfile target, int page) {
        var context = context(owner);
        if (context == null) return;
        owner.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, Items.PLAYER_HEAD, "§6Vista previa · " + target.getName(),
                service.protectionEnabled(context) ? "§7Permisos del panel; además se aplican las restricciones del servidor"
                    : "§cLa protección general está desactivada: este panel no la activa");
            var permissions = ClaimPermissionService.Permission.values();
            for (int i = 0; i < permissions.length; i++) {
                var permission = permissions[i];
                var effective = service.effectivePermission(context, target.getId(), permission);
                put(icons, 10 + i, permissionIcon(permission),
                    (service.hasPolicy(context) ? effective.allowed() ? "§aPermitido · " : "§cDenegado · " : "§7Reglas generales · ") + permission.label,
                    service.hasPolicy(context) ? explanation(effective) : "§7Este chunk aún no tiene reglas del panel");
            }
            put(icons, 22, Items.ARROW, "§eVolver a jugadores", "§7Vista de solo lectura");
            put(icons, 26, Items.BARRIER, "§cCerrar", "§7Volver al juego");
            return locked(id, inventory, icons, owner, context, slot -> {
                if (slot == 22) openPlayers(owner, null, PlayerView.PREVIEW, page);
                else if (slot == 26) owner.closeContainer();
            });
        }, Component.literal("Vista previa · " + target.getName())));
    }

    private void openAreas(ServerPlayer player) {
        var context = context(player);
        if (context == null) return;
        var neighbors = service.neighboringAreas(context);
        int size = service.areaMembers(context).size();
        player.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, Items.MAP, "§6Área de " + size + " chunk(s)", "§7Unir o separar no libera terrenos ni cambia su dueño");
            for (int i = 0; i < neighbors.size(); i++) {
                var other = neighbors.get(i);
                put(icons, 10 + i, Items.OAK_FENCE, "§eUnir con chunk " + other.parcel().x() + ", " + other.parcel().z(),
                    "§7Área vecina de " + service.areaMembers(other).size() + " chunk(s); elegirás qué permisos conservar");
            }
            if (neighbors.isEmpty()) put(icons, 13, Items.PAPER, "§7No hay otra área propia al lado", "§7Sitúate en el borde junto al área que quieres unir");
            put(icons, 20, size > 1 ? Items.SHEARS : Items.GRAY_DYE,
                size > 1 ? "§eSeparar este chunk" : "§7Este chunk ya es independiente",
                "§7Al separar se conservan la protección y los permisos actuales");
            put(icons, 22, Items.ARROW, "§eVolver al área", "§7La unidad mínima es un chunk de 16 × 16");
            put(icons, 26, Items.BARRIER, "§cCerrar", "§7Volver al juego");
            return locked(id, inventory, icons, player, context, slot -> {
                if (slot >= 10 && slot < 10 + neighbors.size()) confirmJoin(player, neighbors.get(slot - 10));
                else if (slot == 20 && size > 1) {
                    report(player, service.splitParcel(player, context), "Chunk separado; sus permisos actuales se conservaron.");
                    openOverview(player);
                } else if (slot == 22) openOverview(player);
                else if (slot == 26) player.closeContainer();
            });
        }, Component.literal("Unir o separar parcelas")));
    }

    private void confirmJoin(ServerPlayer player, ClaimPermissionService.Context selected) {
        var current = context(player);
        if (current == null) return;
        player.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, Items.MAP, "§6Elegir los permisos del área unida", "§eLos ajustes del área no elegida serán reemplazados");
            put(icons, 10, Items.EMERALD_BLOCK, "§aConservar los de esta área", "§7Compartir grupos, excepciones y permisos actuales");
            put(icons, 16, Items.GOLD_BLOCK, "§eConservar los del área vecina", "§7Compartir grupos, excepciones y permisos de la otra área");
            put(icons, 22, Items.ARROW, "§cCancelar", "§7No se guardará ningún cambio");
            return locked(id, inventory, icons, player, current, slot -> {
                if (slot == 10 || slot == 16) {
                    report(player, service.joinAreas(player, current, selected, slot == 10),
                        "Áreas unidas; ahora comparten sus permisos.");
                    openOverview(player);
                } else if (slot == 22) openAreas(player);
            });
        }, Component.literal("Confirmar unión de áreas")));
    }

    private static String explanation(ClaimPolicyRules.Effective effective) {
        String origin = switch (effective.source()) {
            case INDIVIDUAL -> "excepción individual";
            case DEFAULT -> "sin concesiones de grupos";
            case GROUPS -> "grupos " + String.join(", ", effective.groups());
        };
        return "§7" + (effective.allowed() ? "Permitido" : "Denegado") + " por " + origin;
    }

    private static void report(ServerPlayer player, boolean saved, String success) {
        player.sendSystemMessage(Component.literal(saved ? "§a" + success : "§cNo se guardaron cambios. La parcela pudo cambiar o el archivo no se pudo escribir."));
    }

    private static Item permissionIcon(ClaimPermissionService.Permission permission) {
        return switch (permission) {
            case STORAGE -> Items.CHEST;
            case MACHINES -> Items.FURNACE;
            case DOORS -> Items.OAK_DOOR;
            case BUILDING -> Items.BRICKS;
        };
    }

    private static void put(SimpleContainer container, int slot, Item item, String title, String subtitle) {
        ItemStack stack = new ItemStack(item);
        stack.setHoverName(Component.literal(title + "\n§8" + subtitle));
        container.setItem(slot, stack);
    }
}
