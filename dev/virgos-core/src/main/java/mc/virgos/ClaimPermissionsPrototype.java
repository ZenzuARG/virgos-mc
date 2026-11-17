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

/** In-game Spanish claim permissions UI backed by Open Parties and Claims. */
public final class ClaimPermissionsPrototype {
    private final ClaimPermissionService service;

    public ClaimPermissionsPrototype(ClaimPermissionService service) {
        this.service = java.util.Objects.requireNonNull(service, "Claim permission service");
    }

    public int open(CommandSourceStack source) {
        ServerPlayer player = source.getPlayer();
        if (!available(player)) return 0;
        ClaimPermissionService.Context context = service.current(player);
        if (context == null) {
            player.sendSystemMessage(Component.literal("Parate dentro de una parcela tuya para administrar sus permisos."));
            return 0;
        }
        openOverview(player);
        return 1;
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
        return true;
    }

    private void openOverview(ServerPlayer player) {
        ClaimPermissionService.Context context = service.current(player);
        if (context == null) { player.closeContainer(); player.sendSystemMessage(Component.literal("La parcela ya no está disponible.")); return; }
        player.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, Items.MAP, "§6Permisos de mi parcela", "§7" + context.claimName());
            put(icons, 10, Items.GOLD_BLOCK, "§eFamilia", "§7Confianza alta");
            put(icons, 12, Items.EMERALD_BLOCK, "§aAmigos", "§7Pueden usar tu base");
            put(icons, 14, Items.LIGHT_BLUE_WOOL, "§bVisitantes", "§7Sólo entrar y mirar");
            put(icons, 16, Items.PLAYER_HEAD, "§dExcepciones por jugador", "§7Permisos especiales");
            put(icons, 22, Items.BARRIER, "§cCerrar", "§7Volver al juego");
            return new ChestMenu(MenuType.GENERIC_9x3, id, inventory, icons, 3) {
                @Override public void clicked(int slot, int button, ClickType click, Player actor) {
                    if (!valid(actor) || click != ClickType.PICKUP || button != 0) return;
                    if (slot == 10) openGroup((ServerPlayer) actor, ClaimPermissionService.Group.FAMILY);
                    else if (slot == 12) openGroup((ServerPlayer) actor, ClaimPermissionService.Group.FRIENDS);
                    else if (slot == 14) openGroup((ServerPlayer) actor, ClaimPermissionService.Group.VISITORS);
                    else if (slot == 16) openExceptionPicker((ServerPlayer) actor);
                    else if (slot == 22) actor.closeContainer();
                }
                @Override public ItemStack quickMoveStack(Player actor, int slot) { return ItemStack.EMPTY; }
                @Override public boolean stillValid(Player actor) { return valid(actor); }
                private boolean valid(Player actor) { return actor == player && available((ServerPlayer) actor) && service.current((ServerPlayer) actor) != null; }
            };
        }, Component.literal("Permisos · " + context.claimName())));
    }

    private void openGroup(ServerPlayer player, ClaimPermissionService.Group group) {
        ClaimPermissionService.Context context = service.current(player);
        if (context == null) { player.closeContainer(); return; }
        player.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, group == ClaimPermissionService.Group.FAMILY ? Items.GOLD_BLOCK : group == ClaimPermissionService.Group.FRIENDS ? Items.EMERALD_BLOCK : Items.LIGHT_BLUE_WOOL,
                "§6Grupo: " + group.label, "§7" + service.members(context, group).size() + " jugadores");
            ClaimPermissionService.Permission[] permissions = ClaimPermissionService.Permission.values();
            for (int i = 0; i < permissions.length; i++) {
                ClaimPermissionService.Permission permission = permissions[i];
                boolean enabled = service.isGroupEnabled(context, group, permission);
                put(icons, 10 + i, permissionIcon(permission), (enabled ? "§a✓ " : "§c✗ ") + permission.label, enabled ? "§7Permitido para este grupo" : "§7Bloqueado para este grupo");
            }
            put(icons, 19, Items.NAME_TAG, "§fAdministrar integrantes", "§7Agregar o quitar jugadores");
            put(icons, 22, Items.ARROW, "§eVolver a grupos", "§7Elegir otra categoría");
            put(icons, 24, Items.PAPER, "§fVista previa", "§7Ver los permisos efectivos");
            put(icons, 26, Items.BARRIER, "§cCerrar", "§7Volver al juego");
            return new ChestMenu(MenuType.GENERIC_9x3, id, inventory, icons, 3) {
                @Override public void clicked(int slot, int button, ClickType click, Player actor) {
                    if (!valid(actor) || click != ClickType.PICKUP || button != 0) return;
                    ServerPlayer target = (ServerPlayer) actor;
                    if (slot >= 10 && slot < 10 + permissions.length) {
                        ClaimPermissionService.Permission selected = permissions[slot - 10];
                        boolean changed = service.setGroupPermission(context, group, selected, !service.isGroupEnabled(context, group, selected));
                        target.sendSystemMessage(Component.literal(changed ? "§aPermiso actualizado y guardado." : "§cNo se pudo guardar el permiso."));
                        openGroup(target, group);
                    } else if (slot == 19) openMemberPicker(target, group);
                    else if (slot == 22) openOverview(target);
                    else if (slot == 24) preview(target, context, group);
                    else if (slot == 26) target.closeContainer();
                }
                @Override public ItemStack quickMoveStack(Player actor, int slot) { return ItemStack.EMPTY; }
                @Override public boolean stillValid(Player actor) { return valid(actor); }
                private boolean valid(Player actor) { return actor == player && available((ServerPlayer) actor) && service.current((ServerPlayer) actor) != null; }
            };
        }, Component.literal("Permisos · " + group.label)));
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

    private void openMemberPicker(ServerPlayer player, ClaimPermissionService.Group group) {
        openMemberPicker(player, group, 0);
    }

    private void openMemberPicker(ServerPlayer player, ClaimPermissionService.Group group, int requestedPage) {
        ClaimPermissionService.Context context = service.current(player);
        if (context == null) { player.closeContainer(); return; }
        var candidates = memberCandidates(player.getUUID(), VirgosCore.PROFILES.knownPlayers(),
            player.server.getPlayerList().getPlayers().stream().map(ServerPlayer::getGameProfile).toList());
        int page = Math.max(0, Math.min(requestedPage, Math.max(0, (candidates.size() - 1) / 7)));
        var players = candidates.subList(page * 7, Math.min(candidates.size(), page * 7 + 7));
        player.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, Items.NAME_TAG, "§6Integrantes · " + group.label, "§7Clic para agregar o quitar");
            for (int i = 0; i < players.size(); i++) {
                com.mojang.authlib.GameProfile target = players.get(i);
                boolean included = service.members(context, group).contains(target.getId());
                put(icons, 10 + i, Items.PLAYER_HEAD, (included ? "§a✓ " : "§c✗ ") + target.getName(), included ? "§7Pertenece al grupo" : "§7No pertenece al grupo");
            }
            if (page > 0) put(icons, 18, Items.ARROW, "§ePágina anterior", "§7Ver más jugadores");
            if ((page + 1) * 7 < candidates.size()) put(icons, 20, Items.ARROW, "§ePágina siguiente", "§7Ver más jugadores");
            put(icons, 22, Items.ARROW, "§eVolver al grupo", "§7Guardar y volver");
            put(icons, 26, Items.BARRIER, "§cCerrar", "§7Volver al juego");
            return new ChestMenu(MenuType.GENERIC_9x3, id, inventory, icons, 3) {
                @Override public void clicked(int slot, int button, ClickType click, Player actor) {
                    if (!valid(actor) || click != ClickType.PICKUP || button != 0) return;
                    ServerPlayer editor = (ServerPlayer) actor;
                    if (slot >= 10 && slot < 10 + players.size()) {
                        com.mojang.authlib.GameProfile target = players.get(slot - 10);
                        boolean included = service.members(context, group).contains(target.getId());
                        boolean saved = service.setMember(context, group, target, !included);
                        editor.sendSystemMessage(Component.literal(saved ? "§aIntegrantes actualizados." : "§cNo se pudo guardar el integrante."));
                        openMemberPicker(editor, group, page);
                    } else if (slot == 18 && page > 0) openMemberPicker(editor, group, page - 1);
                    else if (slot == 20 && (page + 1) * 7 < candidates.size()) openMemberPicker(editor, group, page + 1);
                    else if (slot == 22) openGroup(editor, group);
                    else if (slot == 26) editor.closeContainer();
                }
                @Override public ItemStack quickMoveStack(Player actor, int slot) { return ItemStack.EMPTY; }
                @Override public boolean stillValid(Player actor) { return valid(actor); }
                private boolean valid(Player actor) { return actor == player && available((ServerPlayer) actor) && service.current((ServerPlayer) actor) != null; }
            };
        }, Component.literal("Integrantes · " + group.label)));
    }

    private void openExceptionPicker(ServerPlayer player) {
        ClaimPermissionService.Context context = service.current(player);
        if (context == null) { player.closeContainer(); return; }
        List<ServerPlayer> players = player.server.getPlayerList().getPlayers().stream().filter(p -> !p.getUUID().equals(player.getUUID())).limit(7).toList();
        player.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, Items.PLAYER_HEAD, "§dExcepciones individuales", "§7Elegí un jugador conectado");
            for (int i = 0; i < players.size(); i++) put(icons, 10 + i, Items.PLAYER_HEAD, "§f" + players.get(i).getGameProfile().getName(), "§7Configurar permisos especiales");
            put(icons, 22, Items.ARROW, "§eVolver a grupos", "§7Elegir otra categoría");
            put(icons, 26, Items.BARRIER, "§cCerrar", "§7Volver al juego");
            return new ChestMenu(MenuType.GENERIC_9x3, id, inventory, icons, 3) {
                @Override public void clicked(int slot, int button, ClickType click, Player actor) {
                    if (!valid(actor) || click != ClickType.PICKUP || button != 0) return;
                    ServerPlayer editor = (ServerPlayer) actor;
                    if (slot >= 10 && slot < 10 + players.size()) openIndividual(editor, context, players.get(slot - 10));
                    else if (slot == 22) openOverview(editor);
                    else if (slot == 26) editor.closeContainer();
                }
                @Override public ItemStack quickMoveStack(Player actor, int slot) { return ItemStack.EMPTY; }
                @Override public boolean stillValid(Player actor) { return valid(actor); }
                private boolean valid(Player actor) { return actor == player && available((ServerPlayer) actor) && service.current((ServerPlayer) actor) != null; }
            };
        }, Component.literal("Excepciones individuales")));
    }

    private void openIndividual(ServerPlayer editor, ClaimPermissionService.Context context, ServerPlayer target) {
        editor.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, Items.PLAYER_HEAD, "§dPermisos de " + target.getGameProfile().getName(), "§7Permitir · denegar · heredar");
            ClaimPermissionService.Permission[] permissions = ClaimPermissionService.Permission.values();
            for (int i = 0; i < permissions.length; i++) {
                ClaimPermissionService.Permission permission = permissions[i];
                ClaimPermissionService.Decision decision = service.individualDecision(context, target.getUUID(), permission);
                String status = decision == null ? "§7Heredado" : decision == ClaimPermissionService.Decision.ALLOW ? "§aPermitido" : "§cDenegado";
                put(icons, 10 + i, permissionIcon(permission), status + " · " + permission.label, "§7Clic para cambiar");
            }
            put(icons, 22, Items.ARROW, "§eVolver a jugadores", "§7Elegir otra persona");
            put(icons, 26, Items.BARRIER, "§cCerrar", "§7Volver al juego");
            return new ChestMenu(MenuType.GENERIC_9x3, id, inventory, icons, 3) {
                @Override public void clicked(int slot, int button, ClickType click, Player actor) {
                    if (!valid(actor) || click != ClickType.PICKUP || button != 0) return;
                    ServerPlayer owner = (ServerPlayer) actor;
                    if (slot >= 10 && slot < 10 + permissions.length) {
                        ClaimPermissionService.Permission selected = permissions[slot - 10];
                        ClaimPermissionService.Decision old = service.individualDecision(context, target.getUUID(), selected);
                        ClaimPermissionService.Decision next = old == null ? ClaimPermissionService.Decision.ALLOW : old == ClaimPermissionService.Decision.ALLOW ? ClaimPermissionService.Decision.DENY : null;
                        boolean changed = service.setIndividual(context, target, selected, next);
                        owner.sendSystemMessage(Component.literal(changed ? "§aExcepción individual guardada." : "§cNo se pudo guardar la excepción."));
                        openIndividual(owner, context, target);
                    } else if (slot == 22) openExceptionPicker(owner);
                    else if (slot == 26) owner.closeContainer();
                }
                @Override public ItemStack quickMoveStack(Player actor, int slot) { return ItemStack.EMPTY; }
                @Override public boolean stillValid(Player actor) { return valid(actor); }
                private boolean valid(Player actor) { return actor == editor && available((ServerPlayer) actor) && service.current((ServerPlayer) actor) != null; }
            };
        }, Component.literal("Excepción · " + target.getGameProfile().getName())));
    }

    private void preview(ServerPlayer player, ClaimPermissionService.Context context, ClaimPermissionService.Group group) {
        StringBuilder text = new StringBuilder("§6Vista previa · ").append(group.label).append("§r: ");
        for (ClaimPermissionService.Permission permission : ClaimPermissionService.Permission.values()) {
            if (service.isGroupEnabled(context, group, permission)) text.append(permission.label).append(", ");
        }
        player.sendSystemMessage(Component.literal(text.toString()));
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
