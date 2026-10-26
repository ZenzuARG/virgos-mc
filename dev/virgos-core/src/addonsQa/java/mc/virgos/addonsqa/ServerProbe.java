package mc.virgos.addonsqa;

import com.google.gson.*;
import com.mojang.logging.LogUtils;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.server.ServerLifecycleHooks;
import java.nio.file.*;
import java.lang.management.ManagementFactory;

/** Universal test-only artifact. No client imports, commands, world writes or arbitrary evaluation. */
@Mod("virgos_addons_qa")
public final class ServerProbe {
    private static final Gson JSON = new GsonBuilder().setPrettyPrinting().create();
    private final SampleWindow sample = new SampleWindow();
    private int line, polls;
    private long tickStart, sampleStart, cpuStart;
    private String sampleId;
    private Path folder;
    private boolean diagnosed;
    public ServerProbe() { MinecraftForge.EVENT_BUS.register(this); }
    private boolean allowed(MinecraftServer server) {
        try {
            Path cwd = Path.of("").toRealPath();
            boolean valid = server != null && LabGuard.allowedCanonical(cwd, server.isDedicatedServer(),
                server.getPort(), server.getWorldData().getLevelName());
            // Also pin the actual storage path, not only its displayed level name.
            valid &= server != null && server.getWorldPath(net.minecraft.world.level.storage.LevelResource.ROOT)
                .toRealPath().equals(cwd.resolve("virgos_world").toRealPath());
            Path target = cwd.resolve("virgos-addons-qa");
            valid &= !Files.isSymbolicLink(target) && (!Files.exists(target) || target.toRealPath().equals(target));
            if (valid) { folder = target; return true; }
        } catch (Exception ignored) { }
        if (!diagnosed) { LogUtils.getLogger().warn("Addons QA disabled: not an exact dedicated lab role/port/world"); diagnosed = true; }
        return false;
    }
    @SubscribeEvent
    public void tick(TickEvent.ServerTickEvent event) {
        MinecraftServer server = ServerLifecycleHooks.getCurrentServer();
        if (!allowed(server)) return;
        if (event.phase == TickEvent.Phase.START) { tickStart = System.nanoTime(); return; }
        long now = System.nanoTime();
        try {
            if (sampleId != null) {
                sample.add(now-tickStart);
                if (sample.expired(now)) finish(sampleId, server);
            }
            if (++polls % 20 != 0) return;
            Path commands = folder.resolve("commands.jsonl");
            if (!Files.exists(commands)) return;
            if (Files.isSymbolicLink(commands) || !commands.toRealPath().getParent().equals(folder) || Files.size(commands)>1_048_576)
                throw new IllegalArgumentException("unsafe or oversized request file");
            var lines = Files.readAllLines(commands);
            if (line >= lines.size()) return;
            var request = JsonParser.parseString(lines.get(line++)).getAsJsonObject();
            String id = request.get("id").getAsString();
            if (!LabGuard.id(id)) throw new IllegalArgumentException("invalid correlation id");
            try {
                switch (request.get("action").getAsString()) {
                    case "sample_start" -> {
                        if (sampleId != null) throw new IllegalStateException("sample already active");
                        sample.start(integer(request.get("seconds")), now);
                        sampleId=id; sampleStart=now; cpuStart=cpu();
                        var ack = new JsonObject(); ack.addProperty("id",id); ack.addProperty("status","sampling");
                        write(id+"-started",ack);
                    }
                    case "sample_stop" -> {
                        if (sampleId == null) throw new IllegalStateException("no active sample");
                        finish(id,server);
                    }
                    case "snapshot_blocks" -> snapshot(id,request,server);
                    default -> throw new IllegalArgumentException("unknown typed action");
                }
            } catch (Exception error) {
                var result=new JsonObject();result.addProperty("id",id);result.addProperty("error",error.toString());write(id,result);
            }
        } catch (Exception error) { LogUtils.getLogger().warn("Addons QA request rejected: {}",error.toString()); }
    }
    private void finish(String id, MinecraftServer server) throws Exception {
        var result=JSON.toJsonTree(sample.summary()).getAsJsonObject();
        result.addProperty("id",id);result.addProperty("sampleId",sampleId);
        result.addProperty("boundary","Forge ServerTickEvent START to END; excludes tick pacing/sleep");
        // Reciprocal interval is not server FPS; retain only duration statistics.
        result.remove("averageFps");
        double elapsed=(System.nanoTime()-sampleStart)/1e9;
        result.addProperty("elapsedSeconds",elapsed);result.addProperty("processCpuSeconds",(cpu()-cpuStart)/1e9);
        result.addProperty("processCpuCores",(cpu()-cpuStart)/1e9/elapsed);
        result.addProperty("heapUsedBytes",Runtime.getRuntime().totalMemory()-Runtime.getRuntime().freeMemory());
        result.addProperty("heapMaxBytes",Runtime.getRuntime().maxMemory());
        result.addProperty("nativeAverageTickMsControl",server.getAverageTickTime());
        write(id,result); sampleId=null;
    }
    private void snapshot(String id, JsonObject request, MinecraftServer server) throws Exception {
        var positions=request.getAsJsonArray("positions");
        if (positions.size()<1 || positions.size()>256) throw new IllegalArgumentException("positions must be 1..256");
        // Validate every position first: rejected requests never load even an earlier chunk.
        for (var value:positions) { var p=value.getAsJsonArray(); if(p.size()!=3)throw new IllegalArgumentException("xyz required");LabGuard.position(integer(p.get(0)),integer(p.get(1)),integer(p.get(2))); }
        var rows=new JsonArray(); var level=server.overworld();
        for (var value:positions) {
            var p=value.getAsJsonArray();var pos=new BlockPos(integer(p.get(0)),integer(p.get(1)),integer(p.get(2)));
            if (!level.hasChunkAt(pos)) throw new IllegalStateException("fixture chunk not loaded; observation will not load it");
            var row=new JsonObject();row.add("position",p);var state=level.getBlockState(pos);
            row.addProperty("block",BuiltInRegistries.BLOCK.getKey(state.getBlock()).toString());row.addProperty("state",state.toString());
            var be=level.getBlockEntity(pos);if(be!=null)row.addProperty("blockEntityNbt",be.saveWithFullMetadata().toString());rows.add(row);
        }
        var result=new JsonObject();result.addProperty("id",id);result.add("blocks",rows);write(id,result);
    }
    private static int integer(JsonElement value) {
        if(!value.isJsonPrimitive() || !value.getAsJsonPrimitive().isNumber())throw new IllegalArgumentException("integer required");
        try { return value.getAsBigDecimal().intValueExact(); }
        catch(ArithmeticException invalid) { throw new IllegalArgumentException("integer required",invalid); }
    }
    private static long cpu() { return ((com.sun.management.OperatingSystemMXBean)ManagementFactory.getOperatingSystemMXBean()).getProcessCpuTime(); }
    private void write(String id, JsonObject value) throws Exception {
        if (!id.matches("[A-Za-z0-9_-]{1,64}")) throw new IllegalArgumentException("invalid output id");
        Files.createDirectories(folder);
        Path target=folder.resolve(id+".json"), temp=folder.resolve(id+".tmp");
        if (Files.exists(target,LinkOption.NOFOLLOW_LINKS)||Files.exists(temp,LinkOption.NOFOLLOW_LINKS))throw new IllegalStateException("id already used");
        Files.writeString(temp,JSON.toJson(value),StandardOpenOption.CREATE_NEW);
        Files.move(temp,target,StandardCopyOption.ATOMIC_MOVE);
    }
}
