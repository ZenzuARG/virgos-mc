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

import java.util.EnumMap;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * First in-game permissions screen. This is intentionally a visual prototype:
 * it does not write Open Parties and Claims data until the interaction model is
 * approved and the native claim API is wired.
 */
public final class ClaimPermissionsPrototype {
    private enum Group {
        FAMILY("Familia", "Confianza alta", Items.GOLD_BLOCK),
        FRIENDS("Amigos", "Pueden usar tu base", Items.EMERALD_BLOCK),
        VISITORS("Visitantes", "Sólo entrar y mirar", Items.LIGHT_BLUE_WOOL);

        private final String label;
        private final String summary;
        private final Item icon;

        Group(String label, String summary, Item icon) {
            this.label = label;
            this.summary = summary;
            this.icon = icon;
        }
    }

    private enum Permission {
        STORAGE("Abrir almacenamiento", "Cofres, barriles y shulkers", Items.CHEST),
        MACHINES("Usar máquinas", "Hornos, tolvas y estaciones", Items.FURNACE),
        DOORS("Usar puertas y botones", "Puertas, trampillas y palancas", Items.OAK_DOOR),
        BUILD("Construir", "Colocar bloques", Items.BRICKS),
        BREAK("Romper", "Destruir bloques", Items.IRON_PICKAXE),
        ANIMALS("Interactuar con animales", "Alimentar, criar y usar", Items.WHEAT);

        private final String label;
        private final String summary;
        private final Item icon;

        Permission(String label, String summary, Item icon) {
            this.label = label;
            this.summary = summary;
            this.icon = icon;
        }
    }

    private final Map<UUID, EnumMap<Group, EnumSet<Permission>>> sessionState = new HashMap<>();

    public int open(CommandSourceStack source) {
        ServerPlayer player = source.getPlayer();
        if (!available(player)) return 0;
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

    private EnumMap<Group, EnumSet<Permission>> state(ServerPlayer player) {
        return sessionState.computeIfAbsent(player.getUUID(), ignored -> {
            EnumMap<Group, EnumSet<Permission>> initial = new EnumMap<>(Group.class);
            for (Group group : Group.values()) initial.put(group, EnumSet.noneOf(Permission.class));
            initial.get(Group.FAMILY).addAll(EnumSet.allOf(Permission.class));
            initial.get(Group.FRIENDS).addAll(EnumSet.of(Permission.STORAGE, Permission.MACHINES, Permission.DOORS));
            initial.get(Group.VISITORS).add(Permission.DOORS);
            return initial;
        });
    }

    private void openOverview(ServerPlayer player) {
        player.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, Items.MAP, "§6Permisos de mi parcela", "§7Prototipo · todavía no guarda cambios");
            put(icons, 10, Group.FAMILY.icon, "§eFamilia", "§7" + Group.FAMILY.summary);
            put(icons, 12, Group.FRIENDS.icon, "§aAmigos", "§7" + Group.FRIENDS.summary);
            put(icons, 14, Group.VISITORS.icon, "§bVisitantes", "§7" + Group.VISITORS.summary);
            put(icons, 16, Items.PLAYER_HEAD, "§dExcepciones por jugador", "§7Un permiso especial para una persona");
            put(icons, 22, Items.BARRIER, "§cCerrar", "§7Volver al juego");
            return new ChestMenu(MenuType.GENERIC_9x3, id, inventory, icons, 3) {
                @Override public void clicked(int slot, int button, ClickType click, Player actor) {
                    if (!valid(actor) || click != ClickType.PICKUP || button != 0) return;
                    if (slot == 10) openGroup((ServerPlayer) actor, Group.FAMILY);
                    else if (slot == 12) openGroup((ServerPlayer) actor, Group.FRIENDS);
                    else if (slot == 14) openGroup((ServerPlayer) actor, Group.VISITORS);
                    else if (slot == 16) openExceptions((ServerPlayer) actor);
                    else if (slot == 22) actor.closeContainer();
                }
                @Override public ItemStack quickMoveStack(Player actor, int slot) { return ItemStack.EMPTY; }
                @Override public boolean stillValid(Player actor) { return valid(actor); }
                private boolean valid(Player actor) { return actor == player && available((ServerPlayer) actor); }
            };
        }, Component.literal("Permisos de mi parcela")));
    }

    private void openGroup(ServerPlayer player, Group group) {
        player.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, group.icon, "§6Grupo: " + group.label, "§7" + group.summary);
            Permission[] permissions = Permission.values();
            for (int i = 0; i < permissions.length; i++) {
                Permission permission = permissions[i];
                boolean enabled = state(player).get(group).contains(permission);
                put(icons, 10 + i, permission.icon, (enabled ? "§a✓ " : "§c✗ ") + permission.label, "§7" + permission.summary);
            }
            put(icons, 22, Items.ARROW, "§eVolver a grupos", "§7Elegir otra categoría");
            put(icons, 24, Items.PAPER, "§fVista previa", "§7Ver qué puede hacer este grupo");
            put(icons, 26, Items.BARRIER, "§cCerrar", "§7Volver al juego");
            return new ChestMenu(MenuType.GENERIC_9x3, id, inventory, icons, 3) {
                @Override public void clicked(int slot, int button, ClickType click, Player actor) {
                    if (!valid(actor) || click != ClickType.PICKUP || button != 0) return;
                    if (slot >= 10 && slot < 10 + permissions.length) {
                        Permission selected = permissions[slot - 10];
                        EnumSet<Permission> enabled = state((ServerPlayer) actor).get(group);
                        if (!enabled.add(selected)) enabled.remove(selected);
                        openGroup((ServerPlayer) actor, group);
                    } else if (slot == 22) openOverview((ServerPlayer) actor);
                    else if (slot == 24) preview((ServerPlayer) actor, group);
                    else if (slot == 26) actor.closeContainer();
                }
                @Override public ItemStack quickMoveStack(Player actor, int slot) { return ItemStack.EMPTY; }
                @Override public boolean stillValid(Player actor) { return valid(actor); }
                private boolean valid(Player actor) { return actor == player && available((ServerPlayer) actor); }
            };
        }, Component.literal("Permisos · " + group.label)));
    }

    private void openExceptions(ServerPlayer player) {
        player.openMenu(new SimpleMenuProvider((id, inventory, ignored) -> {
            SimpleContainer icons = new SimpleContainer(27);
            put(icons, 4, Items.PLAYER_HEAD, "§dExcepciones por jugador", "§7Prototipo · falta conectar la lista de jugadores");
            put(icons, 11, Items.NAME_TAG, "§fElegir jugador", "§7Después podremos buscar una cuenta y cambiar un permiso");
            put(icons, 15, Items.PAPER, "§fVista previa individual", "§7Mostrar permisos efectivos de una persona");
            put(icons, 22, Items.ARROW, "§eVolver a grupos", "§7Elegir otra categoría");
            put(icons, 26, Items.BARRIER, "§cCerrar", "§7Volver al juego");
            return new ChestMenu(MenuType.GENERIC_9x3, id, inventory, icons, 3) {
                @Override public void clicked(int slot, int button, ClickType click, Player actor) {
                    if (!valid(actor) || click != ClickType.PICKUP || button != 0) return;
                    if (slot == 22) openOverview((ServerPlayer) actor);
                    else if (slot == 26) actor.closeContainer();
                    else if (slot == 11 || slot == 15) actor.sendSystemMessage(Component.literal("§eLas excepciones individuales se conectarán en el siguiente paso del prototipo."));
                }
                @Override public ItemStack quickMoveStack(Player actor, int slot) { return ItemStack.EMPTY; }
                @Override public boolean stillValid(Player actor) { return valid(actor); }
                private boolean valid(Player actor) { return actor == player && available((ServerPlayer) actor); }
            };
        }, Component.literal("Excepciones por jugador")));
    }

    private void preview(ServerPlayer player, Group group) {
        String actions = state(player).get(group).stream().map(permission -> permission.label).reduce((left, right) -> left + ", " + right).orElse("Nada todavía");
        player.sendSystemMessage(Component.literal("§6Vista previa · " + group.label + "§r: " + actions));
    }

    private static void put(SimpleContainer container, int slot, Item item, String title, String subtitle) {
        ItemStack stack = new ItemStack(item);
        stack.setHoverName(Component.literal(title + "\n§8" + subtitle));
        container.setItem(slot, stack);
    }
}
