package mc.virgos;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.nbt.TagParser;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraft.world.phys.AABB;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.GZIPInputStream;

/** Console-only construction tools. Nothing is regenerated automatically. */
public final class WorldTools {
    private JsonArray terrain;
    private int scanX, scanZ, radius, step, nextX, nextZ;
    private boolean survey;
    private JsonArray blocks;
    private List<BlockState> palette;
    private int index;
    private int refreshIndex;
    private JsonArray fills, blockEntities;
    private int fillIndex, fillX, fillY, fillZ;
    private boolean fillStarted;
    private long placed;
    private Path marker;
    private boolean complete;
    private String blueprintHash;

    public int scan(CommandSourceStack source, int x, int z, int range, int spacing) {
        if (terrain != null || blocks != null) {
            source.sendFailure(Component.literal("Hay una operación en curso."));
            return 0;
        }
        scanX = x; scanZ = z; radius = range; step = spacing;
        survey = false;
        nextX = x - range; nextZ = z - range;
        terrain = new JsonArray();
        source.sendSuccess(() -> Component.literal("Muestreo de terreno iniciado; resultado en virgos-reports/terrain.json."), false);
        return 1;
    }

    public int survey(CommandSourceStack source, int x, int z, int range, int spacing) {
        if ((2L * range / spacing + 1) * (2L * range / spacing + 1) > 20000) return 0;
        int result = scan(source, x, z, range, spacing);
        if (result == 1) survey = true;
        return result;
    }

    public int build(CommandSourceStack source) {
        return build(source,"bastion");
    }

    public int build(CommandSourceStack source, String name) {
        if (!name.matches("[a-z0-9_-]{1,64}")) return 0;
        if (blocks != null || terrain != null) return 0;
        marker = source.getServer().getWorldPath(LevelResource.ROOT).resolve(name.equals("bastion") ? "virgos-build-state.json" : "virgos-build-"+name+"-state.json");
        try {
            index = 0;
            Path blueprint = Path.of("config/virgos/"+name+".blocks.json.gz");
            blueprintHash = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(blueprint)));
            if (Files.exists(marker)) {
                JsonObject state = JsonParser.parseString(Files.readString(marker)).getAsJsonObject();
                if (state.get("complete").getAsBoolean()) {
                    source.sendFailure(Component.literal("El Bastión ya fue construido. No se sobrescribirá."));
                    return 0;
                }
                if (!blueprintHash.equals(state.get("blueprintSha256").getAsString()))
                    throw new IllegalStateException("Blueprint changed during an unfinished build");
                // Reapply idempotently after an interrupted build: the index may
                // be newer than the world's last durable chunk save.
                index = 0;
            }
            try (var reader = new InputStreamReader(new GZIPInputStream(Files.newInputStream(blueprint)), StandardCharsets.UTF_8)) {
                JsonObject data = JsonParser.parseReader(reader).getAsJsonObject();
                if(data.has("auditOnly")&&data.get("auditOnly").getAsBoolean())throw new IllegalArgumentException("Audit-only template cannot be used to build");
                palette = new ArrayList<>();
                for (var entry : data.getAsJsonArray("palette")) {
                    palette.add(BlockStateParser.parseForBlock(source.getLevel().holderLookup(Registries.BLOCK), entry.getAsString(), false).blockState());
                }
                blocks = data.getAsJsonArray("blocks");
                fills = data.has("fills") ? data.getAsJsonArray("fills") : new JsonArray();
                blockEntities = data.has("blockEntities") ? data.getAsJsonArray("blockEntities") : new JsonArray();
                long volume = 0;
                for (var entry : fills) {
                    JsonArray fill = entry.getAsJsonArray();
                    if (fill.size() != 7) throw new IllegalArgumentException("Invalid fill");
                    int x1=fill.get(0).getAsInt(), y1=fill.get(1).getAsInt(), z1=fill.get(2).getAsInt();
                    int x2=fill.get(3).getAsInt(), y2=fill.get(4).getAsInt(), z2=fill.get(5).getAsInt();
                    if (x1>x2 || y1>y2 || z1>z2 || y1 < -64 || y2>319 || Math.abs(x1)>29000000 || Math.abs(x2)>29000000 || Math.abs(z1)>29000000 || Math.abs(z2)>29000000 || fill.get(6).getAsInt()<0 || fill.get(6).getAsInt()>=palette.size()) throw new IllegalArgumentException("Invalid fill bounds");
                    volume += (x2-x1+1L)*(y2-y1+1L)*(z2-z1+1L);
                }
                if (volume > 15000000 || blocks.size()>2000000 || blockEntities.size()>20000) throw new IllegalArgumentException("Blueprint exceeds construction limits");
                for (var entry : blockEntities) TagParser.parseTag(entry.getAsJsonObject().get("nbt").getAsString());
                fillIndex=0; fillStarted=false; placed=0; refreshIndex=0;
                for (var entry : blocks) {
                    JsonArray block = entry.getAsJsonArray();
                    if (block.size() != 4 || Math.abs(block.get(0).getAsInt()) > 29000000 || Math.abs(block.get(2).getAsInt()) > 29000000 || block.get(1).getAsInt() < -64 || block.get(1).getAsInt() > 319 || block.get(3).getAsInt() < 0 || block.get(3).getAsInt() >= palette.size())
                        throw new IllegalArgumentException("Invalid blueprint block");
                }
                complete = false;
                saveProgress();
                source.sendSuccess(() -> Component.literal("Construcción iniciada: " + blocks.size() + " bloques; progreso guardado en el mundo."), false);
            }
            return 1;
        } catch (Exception exception) {
            blocks = null;
            VirgosCore.LOG.error("Invalid Bastion blueprint", exception);
            source.sendFailure(Component.literal("No se pudo cargar la plantilla del Bastión. Revisá el log."));
            return 0;
        }
    }

    public void tick(MinecraftServer server) {
        ServerLevel level = server.overworld();
        if (terrain != null) {
            // Limit work by elapsed time, including synchronous chunk generation.
            long start = System.nanoTime();
            for (int count = 0; count < 256 && System.nanoTime() - start < 8_000_000; count++) {
                int height;
                String biome;
                if (survey) {
                    var random = level.getChunkSource().randomState();
                    var generator = level.getChunkSource().getGenerator();
                    height = generator.getBaseHeight(nextX, nextZ, Heightmap.Types.WORLD_SURFACE_WG, level, random);
                    biome = generator.getBiomeSource().getNoiseBiome(nextX >> 2, height >> 2, nextZ >> 2, random.sampler()).unwrapKey().orElseThrow().location().toString();
                } else {
                    level.getChunk(nextX >> 4, nextZ >> 4);
                    height = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, nextX, nextZ);
                    biome = level.getBiome(new BlockPos(nextX, height, nextZ)).unwrapKey().orElseThrow().location().toString();
                }
                JsonArray point = new JsonArray();
                point.add(nextX); point.add(nextZ); point.add(height); point.add(biome.toString());
                terrain.add(point);
                nextZ += step;
                if (nextZ > scanZ + radius) { nextZ = scanZ - radius; nextX += step; }
                if (nextX > scanX + radius) {
                    try {
                        JsonObject report = new JsonObject();
                        report.addProperty("centerX", scanX); report.addProperty("centerZ", scanZ);
                        report.addProperty("radius", radius); report.addProperty("step", step);
                        report.addProperty("seed", level.getSeed()); report.add("terrain", terrain);
                        report.addProperty("survey", survey);
                        Files.createDirectories(Path.of("virgos-reports"));
                        Files.writeString(Path.of("virgos-reports/" + (survey ? "survey" : "terrain") + ".json"), VirgosCore.JSON.toJson(report));
                        VirgosCore.LOG.info("Virgos terrain scan complete: {} points", terrain.size());
                    } catch (Exception exception) { VirgosCore.LOG.error("Terrain export failed", exception); }
                    terrain = null;
                    break;
                }
            }
        }
        if (blocks != null) {
            long start = System.nanoTime();
            for (int count=0; count<3000 && fillIndex<fills.size() && System.nanoTime()-start<10_000_000; count++) {
                JsonArray fill=fills.get(fillIndex).getAsJsonArray();
                if (!fillStarted) { fillX=fill.get(0).getAsInt(); fillY=fill.get(1).getAsInt(); fillZ=fill.get(2).getAsInt(); fillStarted=true; }
                BlockPos position=new BlockPos(fillX,fillY,fillZ);
                BlockState state=palette.get(fill.get(6).getAsInt());
                if (level.getBlockState(position)!=state) level.setBlock(position,state,2|16);
                placed++;
                if (++fillY>fill.get(4).getAsInt()) {
                    fillY=fill.get(1).getAsInt();
                    if (++fillZ>fill.get(5).getAsInt()) {
                        fillZ=fill.get(2).getAsInt();
                        if (++fillX>fill.get(3).getAsInt()) { fillIndex++; fillStarted=false; }
                    }
                }
            }
            if (fillIndex<fills.size()) return;
            for (int count = 0; count < 1500 && index < blocks.size() && System.nanoTime() - start < 10_000_000; count++, index++) {
                JsonArray block = blocks.get(index).getAsJsonArray();
                level.setBlock(new BlockPos(block.get(0).getAsInt(), block.get(1).getAsInt(), block.get(2).getAsInt()), palette.get(block.get(3).getAsInt()), 2 | 16);
            }
            if (server.getTickCount() % 100 == 0) saveProgress();
            if (index >= blocks.size()) {
                // Bulk placement deliberately deferred neighbor updates. Once all
                // supports exist, connect panes/fences/stairs and validate supports.
                for (int count=0; count<1500 && refreshIndex<blocks.size() && System.nanoTime()-start<10_000_000; count++,refreshIndex++) {
                    JsonArray entry=blocks.get(refreshIndex).getAsJsonArray();
                    BlockPos position=new BlockPos(entry.get(0).getAsInt(),entry.get(1).getAsInt(),entry.get(2).getAsInt());
                    BlockState state=level.getBlockState(position);
                    if (!state.isAir()) level.setBlock(position,Block.updateFromNeighbourShapes(state,level,position),2);
                }
                if (refreshIndex<blocks.size()) return;
                for (var entry : blockEntities) {
                    try {
                        JsonObject value=entry.getAsJsonObject();
                        BlockPos position=new BlockPos(value.get("x").getAsInt(),value.get("y").getAsInt(),value.get("z").getAsInt());
                        var entity=level.getBlockEntity(position);
                        if (entity==null) throw new IllegalStateException("No block entity at "+position);
                        entity.load(TagParser.parseTag(value.get("nbt").getAsString()));
                        entity.setChanged();
                        level.sendBlockUpdated(position,level.getBlockState(position),level.getBlockState(position),3);
                    } catch (Exception exception) {
                        VirgosCore.LOG.error("Bastion block entity failed; construction remains incomplete",exception);
                        blocks=null;
                        return;
                    }
                }
                server.saveEverything(false, true, true);
                complete = true;
                saveProgress();
                VirgosCore.LOG.info("Virgos Bastion construction complete: {} blocks", index);
                blocks = null;
            }
        }
    }

    public void saveProgress() {
        if (marker == null) return;
        try {
            JsonObject state = new JsonObject();
            state.addProperty("index", index);
            state.addProperty("refreshed",refreshIndex);
            state.addProperty("complete", complete);
            state.addProperty("blueprintSha256", blueprintHash);
            Path temporary = marker.resolveSibling(marker.getFileName() + ".tmp");
            Files.writeString(temporary, VirgosCore.JSON.toJson(state));
            Files.move(temporary, marker, StandardCopyOption.REPLACE_EXISTING);
        } catch (Exception exception) { VirgosCore.LOG.error("Build progress save failed", exception); }
    }

    public int audit(CommandSourceStack source) {
        return audit(source,"bastion");
    }

    public int audit(CommandSourceStack source,String name) {
        if(!name.matches("[a-z0-9_-]{1,64}"))return 0;
        if (blocks!=null || terrain!=null) return 0;
        try (var reader=new InputStreamReader(new GZIPInputStream(Files.newInputStream(Path.of("config/virgos/"+name+".blocks.json.gz"))),StandardCharsets.UTF_8)) {
            var level=source.getLevel();
            var data=JsonParser.parseReader(reader).getAsJsonObject();
            JsonArray unsupported=new JsonArray(), missing=new JsonArray(), wrongBlocks=new JsonArray(), blocked=new JsonArray(), routeProblems=new JsonArray();
            int checked=0,naturalSoilChanges=0,naturalVineGrowth=0;
            for(var entry:data.getAsJsonArray("blocks")) {
                var b=entry.getAsJsonArray();
                BlockPos pos=new BlockPos(b.get(0).getAsInt(),b.get(1).getAsInt(),b.get(2).getAsInt());
                BlockState actual=level.getBlockState(pos);
                String expected=data.getAsJsonArray("palette").get(b.get(3).getAsInt()).getAsString().split("\\[")[0];
                if (!actual.isAir() && !actual.canSurvive(level,pos) && unsupported.size()<100) unsupported.add(pos.toShortString()+" "+actual);
                if (actual.isAir() && !expected.equals("minecraft:air") && missing.size()<100) missing.add(pos.toShortString()+" "+expected);
                boolean naturalSoilChange=(expected.equals("minecraft:grass_block")&&actual.is(net.minecraft.world.level.block.Blocks.DIRT))||(expected.equals("minecraft:dirt")&&actual.is(net.minecraft.world.level.block.Blocks.GRASS_BLOCK));
                boolean grownVine=expected.equals("minecraft:air")&&actual.is(net.minecraft.world.level.block.Blocks.VINE)&&actual.canSurvive(level,pos);
                if(naturalSoilChange)naturalSoilChanges++;
                else if(grownVine)naturalVineGrowth++;
                else if(!actual.isAir()&&!net.minecraftforge.registries.ForgeRegistries.BLOCKS.getKey(actual.getBlock()).toString().equals(expected)&&wrongBlocks.size()<100)wrongBlocks.add(pos.toShortString()+" expected="+expected+" actual="+actual);
                checked++;
            }
            if(data.has("walkChecks")) for(var entry:data.getAsJsonArray("walkChecks")) {
                var p=entry.getAsJsonArray();double x=p.get(0).getAsDouble()+.5,y=p.get(1).getAsDouble(),z=p.get(2).getAsDouble()+.5;
                if(!level.noCollision(null,new AABB(x-.3,y,z-.3,x+.3,y+1.8,z+.3)))blocked.add(p);
            }
            if(data.has("routes")) for(var entry:data.getAsJsonArray("routes")) {
                var route=entry.getAsJsonObject();
                JsonArray previous=null;
                for(var point:route.getAsJsonArray("points")) {
                    var p=point.getAsJsonArray();double x=p.get(0).getAsDouble(),y=p.get(1).getAsDouble(),z=p.get(2).getAsDouble();
                    String problem=null;
                    if(!level.noCollision(null,new AABB(x-.29,y+.01,z-.29,x+.29,y+1.81,z+.29)))problem="headroom";
                    else if(level.noCollision(null,new AABB(x-.29,y-.08,z-.29,x+.29,y-.01,z+.29)))problem="no_floor";
                    if(previous!=null && Math.abs(y-previous.get(1).getAsDouble())>1.01)problem="step_too_high";
                    if(problem!=null && routeProblems.size()<200) {
                        var failure=new JsonObject();failure.addProperty("route",route.get("name").getAsString());failure.add("point",p);failure.addProperty("problem",problem);routeProblems.add(failure);
                    }
                    previous=p;
                }
            }
            JsonObject report=new JsonObject();report.addProperty("checked",checked);
            report.add("unsupported",unsupported);report.add("missing",missing);report.add("blockedWalkChecks",blocked);
            report.add("wrongBlocks",wrongBlocks);
            report.addProperty("naturalSoilChanges",naturalSoilChanges);
            report.addProperty("naturalVineGrowth",naturalVineGrowth);
            report.add("routeProblems",routeProblems);
            Files.writeString(Path.of("virgos-reports/"+name+"-audit.json"),VirgosCore.JSON.toJson(report));
            final int totalChecked=checked;
            source.sendSuccess(()->Component.literal(name+": "+totalChecked+" bloques revisados; sin soporte="+unsupported.size()+"; ausentes="+missing.size()+"; distintos="+wrongBlocks.size()+"; pasos bloqueados="+blocked.size()+"; fallas de recorrido="+routeProblems.size()),false);
            return 1;
        }catch(Exception e){VirgosCore.LOG.error("Bastion audit failed",e);return 0;}
    }

    public String status() { return "terrain=" + (terrain != null) + "; fills="+fillIndex+"; visited="+placed+"; build=" + index + "; complete=" + complete; }
}
