package mc.virgos.forestry;

import com.thizthizzydizzy.treefeller.DetectedTree;
import com.thizthizzydizzy.treefeller.FellBehavior;
import com.thizthizzydizzy.treefeller.Option;
import com.thizthizzydizzy.treefeller.TreeFeller;
import com.thizthizzydizzy.treefeller.compat.TreeFellerCompat;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.coreprotect.CoreProtect;
import net.coreprotect.CoreProtectAPI;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.block.BlockState;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import org.bukkit.event.block.BlockMultiPlaceEvent;
import org.bukkit.event.block.BlockPistonExtendEvent;
import org.bukkit.event.block.BlockPistonRetractEvent;
import org.bukkit.event.world.StructureGrowEvent;
import org.bukkit.inventory.ItemStack;

/** Mandatory integration, deliberately outside upstream's optional compatibility catch-and-continue. */
public final class Forestry implements Listener {
    private record Operation(String group, Set<String> approved) {}
    private static Forestry instance;
    private static final Catalog CATALOG = loadCatalog();
    private static MaterialBindings bindings;
    private static final Map<com.thizthizzydizzy.treefeller.Tree, Catalog.Definition> definitions = new IdentityHashMap<>();
    private static final Set<com.thizthizzydizzy.treefeller.Tree> injected = java.util.Collections.newSetFromMap(new IdentityHashMap<>());
    private static final Map<String, String> coverage = new java.util.LinkedHashMap<>();
    private static Catalog loadCatalog() {
        try { return new Catalog(); }
        catch (IOException error) { throw new ExceptionInInitializerError(error); }
    }
    public static Map<String, String> coverage() { return Map.copyOf(coverage); }
    private static String registryKey(Material material) { return material.getKey().toString(); }
    private static List<String> keys(List<Material> materials) { return materials.stream().map(Forestry::registryKey).toList(); }
    private static Set<String> seedKeys(Set<Material> materials) {
        return materials.stream().map(Forestry::registryKey).collect(java.util.stream.Collectors.toUnmodifiableSet());
    }
    private static boolean refused;
    private final TreeFeller plugin;
    private final NativeGuard guard = new NativeGuard();
    private final Journal journal;
    private final Map<DetectedTree, Operation> operations = new IdentityHashMap<>();
    private boolean healthy = true;
    private final Map<String, Integer> moving = new java.util.HashMap<>();

    private Forestry(TreeFeller plugin) {
        this.plugin = plugin;
        journal = new Journal(plugin.getDataFolder().toPath().resolve("forestry-journal.tsv"));
        healthy = journal.healthy() && bindings != null;
    }
    public static void enable(TreeFeller plugin) {
        instance = new Forestry(plugin);
        Bukkit.getPluginManager().registerEvents(instance, plugin);
        Bukkit.getScheduler().runTaskTimer(plugin, instance::retry, 20L, 20L);
        if (!instance.healthy) plugin.getLogger().severe("Forestry journal unavailable; all accelerated felling refused");
    }
    private static final Map<DetectedTree, Integer> costs = new IdentityHashMap<>();
    public static void begin() { costs.clear(); }
    public static int durability(DetectedTree tree, int logs, ItemStack axe) {
        return costs.computeIfAbsent(tree, ignored -> Balance.cost(logs,
            axe.getEnchantmentLevel(org.bukkit.enchantments.Enchantment.DURABILITY),
            bound -> java.util.concurrent.ThreadLocalRandom.current().nextInt(bound)));
    }
    public static void resetDenied() { refused = false; }
    public static boolean denied() { return refused; }
    private boolean ready() { return Bukkit.isPrimaryThread() && healthy && journal.healthy(); }
    private static String position(Block block) { return block.getX() + "," + block.getY() + "," + block.getZ(); }
    private static String key(Block block) { return block.getWorld().getUID() + ":" + position(block); }

    /** Enforced safe engine mode; no delayed falling entities or synthetic break events. */
    @SuppressWarnings({"unchecked", "rawtypes"})
    private static void fixed(Option option, Object value) {
        option.globalValue = value;
        option.toolValues.clear();
        option.treeValues.clear();
    }
    public static void configure(TreeFeller plugin) {
        fixed(Option.CASCADE, false);
        fixed(Option.CUTTING_ANIMATION, false);
        fixed(Option.LOG_BEHAVIOR, FellBehavior.BREAK);
        fixed(Option.LEAF_BEHAVIOR, FellBehavior.BREAK);
        fixed(Option.SEND_BLOCK_BREAK_EVENTS, false);
        fixed(Option.ALLOW_PARTIAL, false);
        fixed(Option.ALLOW_PARTIAL_TOOL, false);
        fixed(Option.LEAVE_STUMP, false);
        fixed(Option.DAMAGE_MULT, 1d);
        fixed(Option.RESPECT_UNBREAKING, true);
        fixed(Option.RESPECT_UNBREAKABLE, true);
        fixed(Option.STACKED_TOOLS, false);
        fixed(Option.MAX_LOGS, null); // 0 means reject every tree in upstream, not unlimited.
        fixed(Option.COOLDOWN, null);
        fixed(Option.USE_INVENTORY_SAPLINGS, false);
        fixed(Option.SPAWN_SAPLINGS, 0); // The durable ledger owns minimum fallback, never upstream's ephemeral Sapling.
        fixed(Option.BLOCK_CONVERSIONS, new java.util.HashMap<Material, Material>());
        if (plugin != null) bindCatalog(plugin);
    }
    private static void bindCatalog(TreeFeller plugin) {
        definitions.clear();
        TreeFeller.trees.removeAll(injected);
        injected.forEach(tree -> Option.SAPLING.treeValues.remove(tree));
        injected.clear();
        coverage.clear();
        try { bindings = new MaterialBindings(); }
        catch (RuntimeException | LinkageError error) {
            bindings = null;
            CATALOG.definitions().forEach(value -> coverage.put(value.id(), "UNRESOLVED_BINDING:" + error.getClass().getSimpleName()));
            plugin.getLogger().severe("Forestry registry unavailable; accelerated felling disabled");
            return;
        }
        List<com.thizthizzydizzy.treefeller.Tree> additions = new ArrayList<>();
        for (Catalog.Definition value : CATALOG.definitions()) {
            if (!value.status().equals("READY_STATIC") || !value.anchorResolved()) {
                coverage.put(value.id(), value.status().equals("READY_STATIC") ? "UNRESOLVED_ANCHOR:" + value.anchorMode() : value.status());
                continue;
            }
            try {
                for (String key : value.trunks()) bindings.block(key, false);
                for (String key : value.foliage()) bindings.block(key, false);
                for (String key : value.seeds()) bindings.block(key, true);
                coverage.put(value.id(), "BOUND_UNPROVEN_NATIVE");
                if (!value.id().startsWith("minecraft:")) {
                    var tree = new com.thizthizzydizzy.treefeller.Tree(
                        new ArrayList<>(value.trunks().stream().map(key -> bindings.block(key, false)).toList()),
                        new ArrayList<>(value.foliage().stream().map(key -> bindings.block(key, false)).toList()));
                    Option.SAPLING.treeValues.put(tree, new HashSet<>(value.seeds().stream().map(key -> bindings.block(key, true)).toList()));
                    definitions.put(tree, value);
                    additions.add(tree);
                    injected.add(tree);
                }
            } catch (RuntimeException | LinkageError error) {
                coverage.put(value.id(), "UNRESOLVED_BINDING:" + error.getClass().getSimpleName());
            }
        }
        int configured = 0;
        for (var tree : TreeFeller.trees) {
            String entry = "configured:" + configured++;
            try {
                Set<String> seeds = seedKeys(declaredSeeds(null, tree));
                Catalog.Definition value = CATALOG.find(keys(tree.trunk), keys(tree.leaves), seeds);
                if (value != null && "BOUND_UNPROVEN_NATIVE".equals(coverage.get(value.id()))) definitions.put(tree, value);
                else coverage.put(entry, "UNRESOLVED_DECLARATION: trunks=" + keys(tree.trunk) + "; foliage=" + keys(tree.leaves) + "; seeds=" + seeds);
            } catch (RuntimeException | LinkageError error) {
                coverage.put(entry, "UNRESOLVED_BINDING:" + error.getClass().getSimpleName());
            }
        }
        // More-specific mod foliage definitions must be considered before generic shared-wood vanilla definitions.
        TreeFeller.trees.addAll(0, additions);
        plugin.getLogger().info("Forestry declared-family coverage (binding is not native acceptance): " + coverage);
    }
    private boolean safeMode(DetectedTree tree) {
        var tool = tree.tool;
        var kind = tree.tree;
        return !Option.CASCADE.get(tool, kind) && !Option.CUTTING_ANIMATION.get(tool, kind)
            && Option.LOG_BEHAVIOR.get(tool, kind) == FellBehavior.BREAK
            && Option.LEAF_BEHAVIOR.get(tool, kind) == FellBehavior.BREAK
            && !Option.SEND_BLOCK_BREAK_EVENTS.get(tool, kind)
            && !Option.ALLOW_PARTIAL.get(tool, kind) && !Option.ALLOW_PARTIAL_TOOL.get(tool, kind)
            && !Option.LEAVE_STUMP.get(tool, kind) && Option.BLOCK_CONVERSIONS.get(tool, kind).isEmpty()
            && Double.valueOf(1d).equals(Option.DAMAGE_MULT.globalValue)
            && !Option.DAMAGE_MULT.toolValues.containsKey(tool) && !Option.DAMAGE_MULT.treeValues.containsKey(kind)
            && Option.RESPECT_UNBREAKING.get(tool, kind) && Option.RESPECT_UNBREAKABLE.get(tool, kind)
            && !Option.STACKED_TOOLS.get(tool, kind) && Option.SPAWN_SAPLINGS.get(tool, kind) == 0;
    }
    private boolean historyAvailable(Block log) {
        if (journal.knownPlaced(key(log)) || moving.containsKey(key(log))) return false;
        org.bukkit.plugin.Plugin plugin = Bukkit.getPluginManager().getPlugin("CoreProtect");
        if (!(plugin instanceof CoreProtect core) || !plugin.isEnabled()) return false;
        CoreProtectAPI api = core.getAPI();
        // Healthy rows without a verified direct-origin discriminator remain UNKNOWN under policy 2.
        // In particular, a username on a growth row is not evidence of a player-built log.
        return api != null && api.isEnabled() && api.blockLookup(log, Integer.MAX_VALUE) != null;
    }
    /** Declared seed selection seam used by the species-fidelity regression. */
    public static Set<Material> declaredSeeds(com.thizthizzydizzy.treefeller.Tool tool,
                                             com.thizthizzydizzy.treefeller.Tree tree) {
        Set<Material> declared = Option.SAPLING.get(tool, tree);
        return declared == null ? Set.of() : Set.copyOf(declared);
    }
    private static List<Block> roots(DetectedTree tree, Set<Material> seeds) {
        List<Block> roots = new ArrayList<>();
        for (var level : tree.trunk.values()) for (Block log : level) {
            if (tree.tree.trunk.contains(log.getRelative(0, -1, 0).getType())) continue;
            // Query the actual proposed state/soil, not a vanilla GRASS whitelist or guessed mod soil name.
            if (seeds.stream().allMatch(seed -> Bukkit.createBlockData(seed).isSupported(log))) roots.add(log);
        }
        return roots;
    }
    private static boolean footprint(List<Block> roots, List<Integer> widths) {
        if (roots.isEmpty()) return false;
        int y = roots.get(0).getY();
        int minX = roots.stream().mapToInt(Block::getX).min().orElseThrow();
        int minZ = roots.stream().mapToInt(Block::getZ).min().orElseThrow();
        Set<String> actual = roots.stream().map(Forestry::position).collect(java.util.stream.Collectors.toSet());
        for (int width : widths) {
            if ((long)width * width != roots.size()) continue;
            Set<String> expected = new HashSet<>();
            for (int x = 0; x < width; x++) for (int z = 0; z < width; z++) expected.add((minX + x) + "," + y + "," + (minZ + z));
            if (actual.equals(expected)) return true;
        }
        return false;
    }
    private static List<Block> plantingPositions(List<Block> matureRoots, Catalog.Definition definition) {
        if (!definition.anchorResolved() || !footprint(matureRoots, definition.widths())) return List.of();
        int width = (int)Math.sqrt(matureRoots.size());
        // ROOT_GRID is the proven legacy layout. Do not guess a corner within an Ars buttress/core shape.
        if (definition.minimumPlantsFor(width) != matureRoots.size()) return List.of();
        return List.copyOf(matureRoots);
    }
    /** Candidate discrimination happens inside upstream detection so a shared-wood mismatch can try the next tree. */
    public static boolean definitionMatches(DetectedTree tree) {
        Catalog.Definition value = definitions.get(tree.tree);
        if (value == null || !value.accepts(keys(tree.tree.trunk), keys(tree.tree.leaves), seedKeys(declaredSeeds(tree.tool, tree.tree)))) return false;
        return value.observed(tree.leaves.values().stream().flatMap(List::stream)
            .map(block -> registryKey(block.getType())).collect(java.util.stream.Collectors.toSet()));
    }
    public static boolean prepare(DetectedTree tree, Player player, ItemStack axe, Set<Block> affected) {
        try {
            if (instance == null || !instance.ready() || player == null || !instance.safeMode(tree)) return reject();
            Catalog.Definition definition = definitions.get(tree.tree);
            Set<Material> seeds = declaredSeeds(tree.tool, tree.tree);
            Set<String> seedKeys = seedKeys(seeds);
            if (definition == null || !definitionMatches(tree)) return reject();
            List<Block> roots = roots(tree, seeds);
            List<Block> planting = plantingPositions(roots, definition);
            if (planting.isEmpty()) return reject();
            for (var level : tree.trunk.values()) for (Block log : level) {
                if (!tree.tree.trunk.contains(log.getType()) || !instance.historyAvailable(log)) return reject();
            }
            Set<String> approved = new HashSet<>();
            for (Block block : affected) {
                if (!instance.guard.breaking(player, axe, block)) return reject();
                approved.add(key(block));
            }
            for (Block root : planting) for (Material seed : seeds) {
                if (!Bukkit.createBlockData(seed).isSupported(root) || !instance.guard.placing(player, root, seed)) return reject();
            }
            String fallback = seedKeys.contains(definition.fallback()) ? definition.fallback() : seedKeys.stream().sorted().findFirst().orElseThrow();
            String group = instance.journal.prepareDeclared(player.getUniqueId().toString(), roots.get(0).getWorld().getUID().toString(),
                fallback, planting.stream().map(Forestry::position).toList(), seedKeys.stream().sorted().toList());
            if (group == null) return reject();
            tree.saplings.clear();
            instance.operations.put(tree, new Operation(group, Set.copyOf(approved)));
            return true;
        } catch (Exception | LinkageError error) {
            return reject();
        }
    }
    private static String lastReport = "";
    private static boolean reject() {
        refused = true;
        if (instance != null) {
            String report = "Forestry refused accelerated felling; mandatory policy/history/auth/claim check. Native bridge: " + instance.guard.diagnostic();
            if (!report.equals(lastReport)) instance.plugin.getLogger().warning(report);
            lastReport = report;
        }
        return false;
    }
    public static boolean beforeBreak(DetectedTree tree, Player player, ItemStack axe, Block block) {
        if (instance == null || !instance.ready()) return false;
        Operation operation = instance.operations.get(tree);
        return operation != null && operation.approved().contains(key(block)) && instance.guard.breaking(player, axe, block);
    }
    /** Called before the engine creates an item entity, after its original loot calculation. */
    public static boolean reserve(DetectedTree tree, ItemStack stack) {
        if (instance == null || !instance.ready()) return false;
        Operation operation = instance.operations.get(tree);
        if (operation == null) return false;
        try {
            int used = instance.journal.reserve(operation.group(), registryKey(stack.getType()), stack.getAmount());
            stack.setAmount(stack.getAmount() - used);
            return stack.getAmount() > 0;
        } catch (IOException error) {
            instance.healthy = false;
            refused = true;
            throw new IllegalStateException("Forestry reservation failed; aborting world mutation", error);
        }
    }
    public static void finish(DetectedTree tree) {
        if (instance == null) return;
        Operation operation = instance.operations.remove(tree);
        if (operation == null) return;
        try { instance.journal.seal(operation.group()); }
        catch (IOException error) { instance.healthy = false; refused = true; throw new IllegalStateException("Forestry fallback selection failed", error); }
    }
    private void retry() {
        if (!ready()) return;
        try {
            for (Journal.Group group : journal.groups()) {
                Player player = Bukkit.getPlayer(UUID.fromString(group.owner()));
                World world = Bukkit.getWorld(UUID.fromString(group.world()));
                if (player == null || world == null) continue;
                if (!group.selected()) journal.seal(group.id());
                Material material;
                try {
                    material = bindings.pending(group.material());
                    if (!CATALOG.seed(registryKey(material))) throw new IllegalArgumentException("Pending material is not a declared seed");
                }
                catch (RuntimeException | LinkageError unavailable) {
                    coverage.put("pending:" + group.id(), "UNRESOLVED_BINDING:" + group.material());
                    continue; // Preserve the original intent; never discard or substitute an unbound seed.
                }
                List<Block> pending = new ArrayList<>();
                boolean allowed = true;
                for (String point : group.pending()) {
                    String[] xyz = point.split(",");
                    int x = Integer.parseInt(xyz[0]), y = Integer.parseInt(xyz[1]), z = Integer.parseInt(xyz[2]);
                    if (!world.isChunkLoaded(x >> 4, z >> 4)) { allowed = false; break; }
                    Block block = world.getBlockAt(x, y, z);
                    if (!guard.placing(player, block, material)) { allowed = false; break; }
                    if (!Bukkit.createBlockData(material).isSupported(block)
                        || (block.getType() != material && !block.getType().isAir())) { allowed = false; break; }
                    pending.add(block);
                }
                if (!allowed) continue; // Whole footprint checked before its first placement.
                for (Block block : pending) {
                    if (block.getType() != material) {
                        // Recheck immediately; physics/listeners may alter later targets.
                        if (!guard.placing(player, block, material) || !block.getType().isAir()
                                || !Bukkit.createBlockData(material).isSupported(block)) break;
                        BlockState previous = block.getState();
                        block.setType(material, false);
                        TreeFellerCompat.addBlock(plugin, player, block, previous);
                    }
                    journal.complete(group.id(), position(block));
                }
            }
        } catch (Exception | LinkageError error) {
            healthy = false;
            plugin.getLogger().severe("Forestry persistence/retry failed; refusing further felling: " + error.getClass().getSimpleName());
        }
    }
    private static boolean trackedTrunk(Material material) {
        return CATALOG.trunk(registryKey(material)) || material.name().endsWith("_LOG");
    }
    private void marker(Block block, boolean placed) {
        if (!Bukkit.isPrimaryThread()) { healthy = false; return; }
        try { journal.markPlaced(key(block), placed); }
        catch (IOException error) { healthy = false; }
    }
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void placed(BlockPlaceEvent event) {
        if (event instanceof BlockMultiPlaceEvent multiple) {
            for (BlockState state : multiple.getReplacedBlockStates()) {
                if (trackedTrunk(state.getBlock().getType())) marker(state.getBlock(), true);
            }
        } else if (trackedTrunk(event.getBlockPlaced().getType())) marker(event.getBlockPlaced(), true);
    }
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void broken(BlockBreakEvent event) {
        Block block = event.getBlock();
        // Forge can still reject the removal after this Bukkit event. Observe the actual result next tick.
        Bukkit.getScheduler().runTask(plugin, () -> {
            if (!trackedTrunk(block.getType())) marker(block, false);
        });
    }
    /** Pure seam for the piston provenance rule; it does not grant felling permission. */
    public static boolean tracksMoved(Material material, boolean knownPlaced) {
        // Moving a naturally grown/UNKNOWN supported log makes its destination player-manipulated too.
        return knownPlaced || CATALOG.trunk(registryKey(material));
    }
    private void moved(List<Block> blocks, org.bukkit.block.BlockFace direction) {
        // Snapshot first: a pushed chain must not erase a marker written by its preceding log.
        Map<Block, Material> destinations = new java.util.LinkedHashMap<>();
        for (Block block : blocks) if (tracksMoved(block.getType(), journal.knownPlaced(key(block)))) destinations.put(block.getRelative(direction), block.getType());
        Set<String> inFlight = new HashSet<>();
        destinations.keySet().forEach(block -> inFlight.add(key(block)));
        inFlight.forEach(point -> moving.merge(point, 1, Integer::sum)); // Close the event-to-next-tick provenance window.
        Bukkit.getScheduler().runTask(plugin, () -> {
            Map<String, Boolean> changes = new java.util.LinkedHashMap<>();
            destinations.forEach((block, material) -> {
                if (block.getType() == material) changes.put(key(block), true);
            });
            // Retain source markers conservatively; a cancelled/moved identical log cannot erase provenance.
            // A subsequent real break or StructureGrowEvent clears stale source positions.
            try { journal.markPlaced(changes); }
            catch (IOException error) { healthy = false; }
            finally {
                inFlight.forEach(point -> moving.computeIfPresent(point, (key, count) -> count == 1 ? null : count - 1));
            }
        });
    }
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void pushed(BlockPistonExtendEvent event) { moved(event.getBlocks(), event.getDirection()); }
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void pulled(BlockPistonRetractEvent event) { moved(event.getBlocks(), event.getDirection().getOppositeFace()); }
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void grown(StructureGrowEvent event) {
        Map<Block, Material> grown = new java.util.LinkedHashMap<>();
        for (BlockState state : event.getBlocks()) {
            if (trackedTrunk(state.getType()) && !trackedTrunk(state.getBlock().getType())) {
                grown.put(state.getBlock(), state.getType());
            }
        }
        Bukkit.getScheduler().runTask(plugin, () -> grown.forEach((block, material) -> {
            // A cancelled growth event cannot remove a building marker either.
            if (block.getType() == material) marker(block, false);
        }));
    }
}
