package mc.virgos.qa;

import com.google.gson.*;
import com.mojang.logging.LogUtils;
import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.gui.screens.ConnectScreen;
import net.minecraft.client.multiplayer.ServerData;
import net.minecraft.client.multiplayer.resolver.ServerAddress;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

/** Test driver is a separate artifact; it is never part of the friends' pack. */
@Mod("virgos_qa")
public final class ClientProbe {
    private static final Gson JSON = new GsonBuilder().setPrettyPrinting().create();
    private final Path folder = Path.of("virgos-qa");
    private int line;
    private int ticks;
    private KeyMapping heldKey;
    private int heldTicks;
    private int pendingScreenshot;
    private final java.util.Set<String> allowedServers=java.util.Set.of("127.0.0.1:25575");

    public ClientProbe() { MinecraftForge.EVENT_BUS.register(this); }

    @SubscribeEvent
    public void tick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) return;
        if(heldKey!=null && --heldTicks<=0){heldKey.setDown(false);heldKey=null;}
        if(++ticks % 10 != 0) return;
        Minecraft client = Minecraft.getInstance();
        long nativeWindow = client.getWindow().getWindow();
        if (Boolean.getBoolean("virgos.qa.render")) {
            org.lwjgl.glfw.GLFW.glfwSetWindowAttrib(nativeWindow, org.lwjgl.glfw.GLFW.GLFW_FOCUS_ON_SHOW, org.lwjgl.glfw.GLFW.GLFW_FALSE);
            org.lwjgl.glfw.GLFW.glfwShowWindow(nativeWindow);
        } else org.lwjgl.glfw.GLFW.glfwHideWindow(nativeWindow);
        client.mouseHandler.releaseMouse();
        // The QA window stays in the background while tests drive Minecraft's
        // own input/UI code. Do not open PauseScreen merely on loss of focus.
        client.options.pauseOnLostFocus=false;
        try {
            Files.createDirectories(folder);
            JsonObject status = new JsonObject();
            status.addProperty("screen", client.screen == null ? "game" : client.screen.getClass().getName());
            status.addProperty("screenTitle", client.screen == null ? "" : client.screen.getTitle().getString());
            if(client.screen!=null&&client.screen.getClass().getName().endsWith("LoadingErrorScreen")){
                var diagnostic=new JsonObject();
                for(var field:client.screen.getClass().getDeclaredFields()){
                    if(!java.util.Collection.class.isAssignableFrom(field.getType()))continue;
                    field.setAccessible(true);diagnostic.addProperty(field.getName(),String.valueOf(field.get(client.screen)));
                }
                status.add("loadingDiagnostic",diagnostic);
            }

            status.addProperty("line", line);
            status.addProperty("fps", Minecraft.getInstance().getFps());
            status.addProperty("width", client.getWindow().getGuiScaledWidth());
            status.addProperty("height", client.getWindow().getGuiScaledHeight());
            if (client.player != null) {
                status.addProperty("name", client.player.getGameProfile().getName());
                status.addProperty("uuid", client.player.getUUID().toString());
                status.addProperty("health", client.player.getHealth());
                status.addProperty("flying", client.player.getAbilities().flying);
                status.addProperty("mayfly", client.player.getAbilities().mayfly);
                status.addProperty("yaw", client.player.getYRot());
                status.addProperty("pitch", client.player.getXRot());
                status.addProperty("windowActive",client.isWindowActive());
                status.addProperty("attackStrength",client.player.getAttackStrengthScale(0));
                status.addProperty("handsBusy",client.player.isHandsBusy());
                status.addProperty("usingItem",client.player.isUsingItem());
                try {
                    status.addProperty("betterCombatEnabled",Class.forName("net.bettercombat.client.BetterCombatClient").getField("ENABLED").getBoolean(null));
                    Object attributes=Class.forName("net.bettercombat.logic.WeaponRegistry").getMethod("getAttributes",net.minecraft.world.item.ItemStack.class).invoke(null,client.player.getMainHandItem());
                    status.addProperty("betterCombatWeapon",attributes!=null);
                    status.addProperty("upswingTicks",(Integer)client.getClass().getMethod("getUpswingTicks").invoke(client));
                    status.addProperty("comboCount",(Integer)client.getClass().getMethod("getComboCount").invoke(client));
                    var hand=client.getClass().getDeclaredMethod("getCurrentHand");hand.setAccessible(true);
                    status.addProperty("currentAttackHand",String.valueOf(hand.invoke(client)));
                    var miss=client.getClass().getDeclaredField("f_91078_");miss.setAccessible(true);status.addProperty("missTime",miss.getInt(client));
                }catch(ReflectiveOperationException ignored){}
                status.addProperty("x", client.player.getX()); status.addProperty("y", client.player.getY()); status.addProperty("z", client.player.getZ());
                JsonArray inventory = new JsonArray();
                for (var stack : client.player.getInventory().items) if (!stack.isEmpty()) inventory.add(BuiltInRegistries.ITEM.getKey(stack.getItem()) + " x" + stack.getCount());
                status.add("inventory", inventory);
            }
            Files.writeString(folder.resolve("status.json"), JSON.toJson(status));
            Path commands = folder.resolve("commands.jsonl");
            if (!Files.exists(commands)) return;
            var lines = Files.readAllLines(commands);
            if (line >= lines.size()) return;
            String raw = lines.get(line++).strip();
            if (raw.isEmpty()) return;
            JsonObject command = JsonParser.parseString(raw).getAsJsonObject();
            String action = command.get("action").getAsString();
            // Never automate gameplay on any external server.
            var current = client.getCurrentServer();
            if (current != null && !allowedServers.contains(current.ip)) throw new IllegalStateException("QA restricted to Virgos-owned endpoints");
            switch (action) {
                case "connect" -> {
                    if (!(client.screen instanceof TitleScreen)) throw new IllegalStateException("Connect only from title screen");
                    String endpoint=Files.exists(folder.resolve("endpoint.txt"))?Files.readString(folder.resolve("endpoint.txt")).strip():"127.0.0.1:25575";
                    if(!allowedServers.contains(endpoint))throw new IllegalArgumentException("Unsupported QA endpoint");
                    ServerData data = new ServerData("Virgos QA", endpoint, false);
                    ConnectScreen.startConnecting(client.screen, client, ServerAddress.parseString(data.ip), data, false);
                }
                case "command" -> {
                    if (client.player == null) throw new IllegalStateException("Not joined");
                    client.player.connection.sendCommand(command.get("value").getAsString());
                }
                case "chat" -> {
                    if (client.player == null) throw new IllegalStateException("Not joined");
                    client.player.connection.sendChat(command.get("value").getAsString());
                }
                case "key" -> {
                    String name = command.get("name").getAsString();
                    boolean found = false;
                    for (KeyMapping key : client.options.keyMappings) if (key.getName().equals(name)) {
                        KeyMapping.click(key.getKey()); found = true;
                    }
                    if (!found) throw new IllegalArgumentException("Unknown key " + name);
                }
                case "hold" -> {
                    if(client.screen!=null || client.player==null)throw new IllegalStateException("Hold only in game");
                    if(heldKey!=null)heldKey.setDown(false);
                    String name=command.get("name").getAsString();
                    heldTicks=Math.max(1,Math.min(200,command.get("ticks").getAsInt()));
                    heldKey=null;
                    for(KeyMapping key:client.options.keyMappings)if(key.getName().equals(name)){heldKey=key;key.setDown(true);}
                    if(heldKey==null)throw new IllegalArgumentException("Unknown key "+name);
                }
                case "use" -> {
                    if(client.player==null || client.gameMode==null || client.screen!=null)throw new IllegalStateException("Use only in game");
                    if(client.hitResult instanceof net.minecraft.world.phys.BlockHitResult hit)
                        client.gameMode.useItemOn(client.player,net.minecraft.world.InteractionHand.MAIN_HAND,hit);
                    else client.gameMode.useItem(client.player,net.minecraft.world.InteractionHand.MAIN_HAND);
                }
                case "attack" -> {
                    if(client.player==null || client.gameMode==null || client.screen!=null)throw new IllegalStateException("Attack only in game");
                    if(client.hitResult instanceof net.minecraft.world.phys.BlockHitResult hit)
                        client.gameMode.startDestroyBlock(hit.getBlockPos(),hit.getDirection());
                    else if(client.hitResult instanceof net.minecraft.world.phys.EntityHitResult hit) {
                        client.gameMode.attack(client.player,hit.getEntity());
                        client.player.swing(net.minecraft.world.InteractionHand.MAIN_HAND);
                    }
                }
                case "combat" -> {
                    if(client.player==null||client.screen!=null)throw new IllegalStateException("Combat only in game");
                    var type=Class.forName("net.bettercombat.api.WeaponAttributes");
                    var attributes=Class.forName("net.bettercombat.logic.WeaponRegistry").getMethod("getAttributes",net.minecraft.world.item.ItemStack.class).invoke(null,client.player.getMainHandItem());
                    if(attributes==null)throw new IllegalStateException("Not a Better Combat weapon");
                    var method=client.getClass().getDeclaredMethod("startUpswing",type);method.setAccessible(true);method.invoke(client,attributes);
                }
                case "keys" -> {
                    JsonObject keys = new JsonObject();
                    for (KeyMapping key : client.options.keyMappings) keys.addProperty(key.getName(), key.getKey().getName());
                    Files.writeString(folder.resolve("keys.json"), JSON.toJson(keys));
                }
                case "bind" -> {
                    String name = command.get("name").getAsString();
                    boolean found = false;
                    for (KeyMapping key : client.options.keyMappings) if (key.getName().equals(name)) {
                        key.setKey(InputConstants.getKey(command.get("key").getAsString())); found = true;
                    }
                    if (!found) throw new IllegalArgumentException("Unknown key " + name);
                    KeyMapping.resetMapping();
                    client.options.save();
                }
                case "click" -> {
                    if (client.screen == null) throw new IllegalStateException("No screen");
                    double x = command.get("x").getAsDouble(), y = command.get("y").getAsDouble();
                    int button = command.has("button") ? command.get("button").getAsInt() : 0;
                    client.screen.mouseClicked(x, y, button);
                    client.screen.mouseReleased(x, y, button);
                }
                case "audit_loading" -> {
                    if(client.screen==null)throw new IllegalStateException("No screen");
                    var result=new JsonObject();result.addProperty("screen",client.screen.getClass().getName());
                    for(var field:client.screen.getClass().getDeclaredFields()){
                        if(!java.util.Collection.class.isAssignableFrom(field.getType())&&!Throwable.class.isAssignableFrom(field.getType()))continue;
                        field.setAccessible(true);Object value=field.get(client.screen);
                        result.addProperty(field.getName(),String.valueOf(value));
                    }
                    Files.writeString(folder.resolve("loading-audit.json"),JSON.toJson(result));
                }
                case "inspect_screen" -> {
                    if(client.screen==null)throw new IllegalStateException("No screen");
                    JsonArray widgets=new JsonArray();
                    for(var child:client.screen.children())if(child instanceof net.minecraft.client.gui.components.AbstractWidget widget){
                        JsonObject row=new JsonObject();row.addProperty("type",widget.getClass().getName());row.addProperty("text",widget.getMessage().getString());row.addProperty("x",widget.getX());row.addProperty("y",widget.getY());row.addProperty("width",widget.getWidth());row.addProperty("height",widget.getHeight());row.addProperty("visible",widget.visible);row.addProperty("active",widget.active);widgets.add(row);
                    }
                    Files.writeString(folder.resolve("screen.json"),JSON.toJson(widgets));
                }
                case "type" -> {if(client.screen==null)throw new IllegalStateException("No screen");for(char c:command.get("value").getAsString().toCharArray())client.screen.charTyped(c,0);}
                case "scroll" -> {if(client.screen==null)throw new IllegalStateException("No screen");client.screen.mouseScrolled(command.get("x").getAsDouble(),command.get("y").getAsDouble(),command.get("amount").getAsDouble());}
                case "scale" -> {client.options.guiScale().set(command.get("value").getAsInt());client.options.save();client.resizeDisplay();}
                case "look" -> {
                    if (client.player == null) throw new IllegalStateException("Not joined");
                    client.player.setYRot(command.get("yaw").getAsFloat());
                    client.player.setXRot(command.get("pitch").getAsFloat());
                }
                case "close" -> {
                    if(client.screen!=null)client.screen.onClose();
                    if(client.level!=null){client.setScreen(null);client.mouseHandler.grabMouse();}
                }
                case "screenshot" -> pendingScreenshot=line;
                case "probe_dh_merge" -> {
                    var shared=Class.forName("com.seibel.distanthorizons.core.api.internal.SharedApi");
                    var world=shared.getMethod("getAbstractDhWorld").invoke(null);
                    Object level=((Iterable<?>)world.getClass().getMethod("getAllLoadedLevels").invoke(world)).iterator().next();
                    var provider=level.getClass().getField("remoteDataSourceProvider").get(level);
                    var repo=provider.getClass().getField("repo").get(provider);
                    var wrapper=level.getClass().getMethod("getLevelWrapper").invoke(level);
                    Path base=client.gameDirectory.toPath().getParent();
                    Path oldPath=((java.io.File)repo.getClass().getField("databaseFile").get(repo)).toPath();
                    if(command.has("fixture")&&command.get("fixture").getAsBoolean())oldPath=base.resolve("probe-inputs/old-diamond.sqlite");
                    Path newPath=command.has("same")&&command.get("same").getAsBoolean()?oldPath:base.resolve("server/virgos_world/data/DistantHorizons.sqlite");
                    if(command.has("fixture")&&command.get("fixture").getAsBoolean()&&!(command.has("same")&&command.get("same").getAsBoolean()))newPath=base.resolve("probe-inputs/new-emerald.sqlite");
                    try(var oldSource=(AutoCloseable)labReadSource(repo,wrapper,oldPath);var newSource=(AutoCloseable)labReadSource(repo,wrapper,newPath)) {
                        var result=new JsonObject();
                        result.add("before",labColumnSemantics(oldSource));result.add("incoming",labColumnSemantics(newSource));result.addProperty("fullBefore",labFullDigest(oldSource));result.addProperty("fullIncoming",labFullDigest(newSource));
                        boolean changed=(Boolean)oldSource.getClass().getMethod("updateFromDataSource",oldSource.getClass()).invoke(oldSource,newSource);
                        result.addProperty("reportedChanged",changed);result.add("after",labColumnSemantics(oldSource));result.addProperty("fullAfter",labFullDigest(oldSource));
                        Files.writeString(folder.resolve("merge-probe.json"),JSON.toJson(result));
                    }
                }
                case "read_dh_section" -> {
                    var shared=Class.forName("com.seibel.distanthorizons.core.api.internal.SharedApi");
                    var world=shared.getMethod("getAbstractDhWorld").invoke(null);
                    var position=Class.forName("com.seibel.distanthorizons.core.pos.DhSectionPos");
                    byte detail=position.getField("SECTION_MINIMUM_DETAIL_LEVEL").getByte(null);
                    long encoded=(Long)position.getMethod("encode",byte.class,int.class,int.class).invoke(null,detail,4,0);
                    for(Object level:(Iterable<?>)world.getClass().getMethod("getAllLoadedLevels").invoke(world)){
                        var provider=level.getClass().getField("remoteDataSourceProvider").get(level);
                        provider.getClass().getMethod("get",long.class).invoke(provider,encoded);
                    }
                }
                case "audit_dh" -> {
                    var result=new JsonObject();
                    result.addProperty("windowVisible", org.lwjgl.glfw.GLFW.glfwGetWindowAttrib(nativeWindow, org.lwjgl.glfw.GLFW.GLFW_VISIBLE) != 0);
                    result.addProperty("windowFocused", org.lwjgl.glfw.GLFW.glfwGetWindowAttrib(nativeWindow, org.lwjgl.glfw.GLFW.GLFW_FOCUSED) != 0);
                    result.addProperty("windowIconified", org.lwjgl.glfw.GLFW.glfwGetWindowAttrib(nativeWindow, org.lwjgl.glfw.GLFW.GLFW_ICONIFIED) != 0);
                    result.addProperty("fps",Minecraft.getInstance().getFps());
                    result.addProperty("heapUsedMiB",(Runtime.getRuntime().totalMemory()-Runtime.getRuntime().freeMemory())/1048576);
                    result.addProperty("dhLoaded",net.minecraftforge.fml.ModList.get().isLoaded("distanthorizons"));
                    var remoteChunk=client.level==null?null:client.level.getChunkSource().getChunk(16,0,net.minecraft.world.level.chunk.ChunkStatus.FULL,false);
                    result.addProperty("remoteVanillaChunkPresent",remoteChunk!=null&&!(remoteChunk instanceof net.minecraft.world.level.chunk.EmptyLevelChunk));
                    result.addProperty("remoteChunkClass",remoteChunk==null?"null":remoteChunk.getClass().getName());
                    result.addProperty("modCount",net.minecraftforge.fml.ModList.get().getMods().size());
                    if(net.minecraftforge.fml.ModList.get().isLoaded("distanthorizons")) {
                        var shared=Class.forName("com.seibel.distanthorizons.core.api.internal.SharedApi");
                        result.add("debug",JSON.toJsonTree(shared.getMethod("getDebugMenuString").invoke(shared.getField("INSTANCE").get(null))));
                        var world=shared.getMethod("getAbstractDhWorld").invoke(null);
                        if(world!=null) {
                            var network=world.getClass().getField("networkState").get(world);
                            result.addProperty("serverReady",(Boolean)network.getClass().getMethod("isReady").invoke(network));
                            result.addProperty("serverTimeOffset",(Long)network.getClass().getMethod("getServerTimeOffset").invoke(network));
                            var config=network.getClass().getField("sessionConfig").get(network);
                            var settings=new JsonObject();
                            for(String name:java.util.List.of("getSynchronizeOnLoad","getMaxSyncOnLoadDistance","getSyncOnLoginRateLimit","getGeneratorPlan"))settings.add(name,JSON.toJsonTree(config.getClass().getMethod(name).invoke(config)));
                            result.add("negotiated",settings);
                            var levels=new JsonArray();
                            for(Object level:(Iterable<?>)world.getClass().getMethod("getAllLoadedLevels").invoke(world)) {
                                var row=new JsonObject();row.addProperty("level",level.toString());
                                try {
                                    var wrapper=level.getClass().getMethod("getLevelWrapper").invoke(level);
                                    row.addProperty("levelWrapperClass",wrapper.getClass().getName());
                                    row.addProperty("wrapperReferencesLevel",wrapper.getClass().getMethod("getDhLevel").invoke(wrapper)==level);
                                    row.addProperty("shouldDoWorldGen",(Boolean)level.getClass().getMethod("shouldDoWorldGen").invoke(level));
                                    var mc=level.getClass().getDeclaredField("MC_CLIENT");mc.setAccessible(true);
                                    var currentWrapper=mc.get(null).getClass().getMethod("getWrappedClientLevel").invoke(mc.get(null));
                                    row.addProperty("currentWrapperSame",currentWrapper==wrapper);
                                    row.addProperty("currentWrapperReferencesLevel",currentWrapper!=null&&currentWrapper.getClass().getMethod("getDhLevel").invoke(currentWrapper)==level);
                                    var moduleField=level.getClass().getDeclaredField("clientside");moduleField.setAccessible(true);var module=moduleField.get(level);
                                    row.addProperty("modulePresent",module!=null);
                                    if(module!=null){var ref=(java.util.concurrent.atomic.AtomicReference<?>)module.getClass().getField("ClientRenderStateRef").get(module);row.addProperty("renderStatePresent",ref.get()!=null);}
                                } catch(ReflectiveOperationException observationError){row.addProperty("observationError",observationError.toString());}
                                var f=level.getClass().getDeclaredField("syncOnLoadRequestQueue");f.setAccessible(true);var queue=f.get(level);
                                row.addProperty("waiting",(Integer)queue.getClass().getMethod("getWaitingTaskCount").invoke(queue));
                                row.addProperty("inProgress",(Integer)queue.getClass().getMethod("getInProgressTaskCount").invoke(queue));
                                levels.add(row);
                            }
                            result.add("levels",levels);

                        }
                        var api=Class.forName("com.seibel.distanthorizons.core.api.internal.ClientApi");
                        result.addProperty("rendererDisabledByException",api.getField("rendererDisabledBecauseOfExceptions").getBoolean(api.getField("INSTANCE").get(null)));
                    }
                    Files.writeString(folder.resolve("dh-audit.json"),JSON.toJson(result));
                }
                case "slots" -> {
                    if(client.player==null)throw new IllegalStateException("Not joined");
                    var rows=new JsonArray();
                    for(var slot:client.player.containerMenu.slots) {
                        var row=new JsonObject();row.addProperty("slot",slot.index);row.addProperty("x",slot.x);row.addProperty("y",slot.y);
                        row.addProperty("item",slot.getItem().save(new net.minecraft.nbt.CompoundTag()).toString());rows.add(row);
                    }
                    var snapshot=new JsonObject();snapshot.add("slots",rows);snapshot.addProperty("menu",client.player.containerMenu.getClass().getName());
                    snapshot.addProperty("carried",client.player.containerMenu.getCarried().save(new net.minecraft.nbt.CompoundTag()).toString());
                    Files.writeString(folder.resolve("slots.json"),JSON.toJson(snapshot));
                }
                case "slot" -> {
                    if(client.player==null||client.gameMode==null)throw new IllegalStateException("Not joined");
                    client.gameMode.handleInventoryMouseClick(client.player.containerMenu.containerId,command.get("slot").getAsInt(),command.get("button").getAsInt(),net.minecraft.world.inventory.ClickType.valueOf(command.get("type").getAsString()),client.player);
                }
                case "audit_recipes" -> {
                    if(client.player==null || client.getConnection()==null)throw new IllegalStateException("Not joined");
                    var result=new JsonObject();
                    var internal=Class.forName("mezz.jei.common.Internal");
                    result.addProperty("jeiSynced",(Boolean)internal.getMethod("hasClientSyncedRecipes").invoke(null));
                    result.addProperty("jeiFallback",(Boolean)internal.getMethod("hasClientFallbackRecipes").invoke(null));
                    result.add("recipes",JSON.toJsonTree(client.getConnection().getRecipeManager().getRecipes().stream().map(recipe->recipe.getId().toString()).sorted().toList()));
                    Files.writeString(folder.resolve("recipes-audit.json"),JSON.toJson(result));
                }
                case "disconnect" -> {
                    if (client.level != null) client.level.disconnect();
                    client.clearLevel();
                    client.setScreen(new TitleScreen());
                }
                case "quit" -> client.stop();
                default -> throw new IllegalArgumentException("Unknown action: " + action);
            }
        } catch (Exception exception) {
            LogUtils.getLogger().error("Virgos QA action failed", exception);
            try { Files.writeString(folder.resolve("last-error.json"), JSON.toJson(Map.of("line", line, "error", exception.toString()))); }
            catch (Exception ignored) { }
        }
    }

    @SubscribeEvent
    public void rendered(TickEvent.RenderTickEvent event) {
        if(event.phase!=TickEvent.Phase.END || pendingScreenshot==0)return;
        Minecraft client=Minecraft.getInstance();
        int number=pendingScreenshot;pendingScreenshot=0;
        Screenshot.grab(client.gameDirectory,"virgos-qa-"+number+".png",client.getMainRenderTarget(),result->LogUtils.getLogger().info("QA screenshot: {}",result.getString()));
    }

    private Object labReadSource(Object repo,Object wrapper,Path path)throws Exception {
        Class.forName("dh_sqlite.JDBC");
        try(var db=java.sql.DriverManager.getConnection("jdbc:dh_sqlite:"+path.toAbsolutePath().toUri()+"?mode=ro");var statement=db.createStatement()) {
            statement.execute("PRAGMA query_only=ON");
            try(var rows=statement.executeQuery("SELECT * FROM FullData WHERE DetailLevel=0 AND PosX=4 AND PosZ=0")) {
                if(!rows.next())throw new IllegalStateException("Probe target missing");
                var dto=(AutoCloseable)repo.getClass().getMethod("convertResultSetToDto",java.sql.ResultSet.class).invoke(repo,rows);
                try(dto){return dto.getClass().getMethod("createDataSource",Class.forName("com.seibel.distanthorizons.core.wrapperInterfaces.world.ILevelWrapper"),Class.forName("com.seibel.distanthorizons.core.enums.EDhDirection")).invoke(dto,wrapper,null);}
            }
        }
    }
    private JsonArray labColumnSemantics(Object source)throws Exception {
        var result=new JsonArray();var mapping=source.getClass().getField("mapping").get(source);
        var values=(it.unimi.dsi.fastutil.longs.LongArrayList)source.getClass().getMethod("getColumnAtRelPos",int.class,int.class).invoke(source,0,0);
        var util=Class.forName("com.seibel.distanthorizons.core.util.FullDataPointUtil");
        for(long value:values){int id=(Integer)util.getMethod("getId",long.class).invoke(null,value);var block=mapping.getClass().getMethod("getBlockStateWrapper",int.class).invoke(mapping,id);var row=new JsonObject();row.addProperty("packed",value);row.addProperty("block",(String)block.getClass().getMethod("getSerialString").invoke(block));var biome=mapping.getClass().getMethod("getBiomeWrapper",int.class).invoke(mapping,id);row.addProperty("biome",(String)biome.getClass().getMethod("getSerialString").invoke(biome));result.add(row);}
        return result;
    }

    private String labFullDigest(Object source)throws Exception {
        var digest=java.security.MessageDigest.getInstance("SHA-256");var mapping=source.getClass().getField("mapping").get(source);
        var util=Class.forName("com.seibel.distanthorizons.core.util.FullDataPointUtil");long mask=util.getField("ID_MASK").getLong(null);
        for(int x=0;x<64;x++)for(int z=0;z<64;z++){
            var values=(it.unimi.dsi.fastutil.longs.LongArrayList)source.getClass().getMethod("getColumnAtRelPos",int.class,int.class).invoke(source,x,z);
            digest.update(java.nio.ByteBuffer.allocate(4).putInt(values==null?-1:values.size()).array());if(values==null)continue;
            for(long value:values){int id=(Integer)util.getMethod("getId",long.class).invoke(null,value);digest.update(java.nio.ByteBuffer.allocate(8).putLong(value&~mask).array());
                for(String name:java.util.List.of("getBiomeWrapper","getBlockStateWrapper")){var wrapper=mapping.getClass().getMethod(name,int.class).invoke(mapping,id);var text=(String)wrapper.getClass().getMethod("getSerialString").invoke(wrapper);digest.update(text.getBytes(java.nio.charset.StandardCharsets.UTF_8));digest.update((byte)0);}
            }
        }
        return java.util.HexFormat.of().formatHex(digest.digest());
    }

}
