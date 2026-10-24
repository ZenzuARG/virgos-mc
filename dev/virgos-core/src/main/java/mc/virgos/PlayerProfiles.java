package mc.virgos;

import com.google.gson.*;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import mc.virgos.profile.ProfileProtocol;
import net.minecraft.commands.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.stats.Stats;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.registries.ForgeRegistries;
import java.nio.file.*;
import java.util.*;

/** Public gameplay summaries only; never includes inventory, bases or account data. */
public final class PlayerProfiles {
    private final Map<UUID,JsonObject> profiles=new HashMap<>();
    private final Map<UUID,Integer> lastRequest=new HashMap<>();
    private MinecraftServer server;
    private Path file;
    private boolean questWarning;
    public void initialize(MinecraftServer server){
        this.server=server;profiles.clear();lastRequest.clear();questWarning=false;
        file=server.getWorldPath(LevelResource.ROOT).resolve("virgos-profiles.json");
        try{
            if(Files.exists(file)){
                JsonObject saved=JsonParser.parseString(Files.readString(file)).getAsJsonObject();
                if(saved.get("schema").getAsInt()!=1)throw new IllegalStateException("Unknown profile schema");
                for(var entry:saved.getAsJsonObject("players").entrySet())profiles.put(UUID.fromString(entry.getKey()),entry.getValue().getAsJsonObject());
            }
        }catch(Exception error){VirgosCore.LOG.error("Could not load player profiles",error);}
    }
    private long stat(ServerPlayer player,ResourceLocation key){return Math.max(0,player.getStats().getValue(Stats.CUSTOM.get(key)));}
    @SuppressWarnings("unchecked") private void quests(ServerPlayer player,JsonObject result){
        try{
            var handler=Class.forName("earth.terrarium.heracles.common.handlers.quests.QuestHandler");
            Map<String,?> quests=(Map<String,?>)handler.getMethod("quests").invoke(null);
            Object progress=Class.forName("earth.terrarium.heracles.common.handlers.progress.QuestProgressHandler").getMethod("getProgress",MinecraftServer.class,UUID.class).invoke(null,server,player.getUUID());
            var complete=progress.getClass().getMethod("isComplete",String.class);
            var claimed=progress.getClass().getMethod("isClaimed",String.class,Class.forName("earth.terrarium.heracles.api.quests.Quest"));
            Map<String,int[]> chapters=new TreeMap<>();int done=0,rewards=0;
            for(var entry:quests.entrySet()){
                boolean finished=(Boolean)complete.invoke(progress,entry.getKey());
                if(finished){done++;if(!(Boolean)claimed.invoke(progress,entry.getKey(),entry.getValue()))rewards++;}
                Object display=entry.getValue().getClass().getMethod("display").invoke(entry.getValue());
                Map<String,?> groups=(Map<String,?>)display.getClass().getMethod("groups").invoke(display);
                for(String group:groups.keySet()){int[] counts=chapters.computeIfAbsent(group,k->new int[2]);counts[1]++;if(finished)counts[0]++;}
            }
            result.addProperty("quests",done);result.addProperty("questTotal",quests.size());result.addProperty("rewards",rewards);
            JsonArray rows=new JsonArray();chapters.forEach((name,count)->{JsonObject row=new JsonObject();row.addProperty("name",name);row.addProperty("done",count[0]);row.addProperty("total",count[1]);rows.add(row);});result.add("chapters",rows);
        }catch(Exception error){
            result.addProperty("quests",-1);result.addProperty("questTotal",0);result.addProperty("rewards",0);result.add("chapters",new JsonArray());
            if(!questWarning){VirgosCore.LOG.error("Profile quest progress unavailable",error);questWarning=true;}
        }
    }
    private JsonObject snapshot(ServerPlayer player){
        JsonObject result=new JsonObject();result.addProperty("name",player.getGameProfile().getName());result.addProperty("uuid",player.getUUID().toString());
        result.addProperty("updated",System.currentTimeMillis());result.addProperty("seconds",stat(player,Stats.PLAY_TIME)/20);
        result.addProperty("level",player.experienceLevel);
        result.addProperty("rank",Progression.earned(player,"virgos:maestro")?"Maestro":Progression.earned(player,"virgos:especialista")?"Especialista":Progression.earned(player,"virgos:explorador")?"Explorador":"Inicio");
        result.addProperty("deaths",stat(player,Stats.DEATHS));result.addProperty("mobs",stat(player,Stats.MOB_KILLS));
        result.addProperty("jumps",stat(player,Stats.JUMP));result.addProperty("fish",stat(player,Stats.FISH_CAUGHT));
        result.addProperty("distanceCm",stat(player,Stats.WALK_ONE_CM)+stat(player,Stats.SPRINT_ONE_CM)+stat(player,Stats.CROUCH_ONE_CM)+stat(player,Stats.SWIM_ONE_CM)+stat(player,Stats.WALK_ON_WATER_ONE_CM)+stat(player,Stats.WALK_UNDER_WATER_ONE_CM));
        long mined=0,crafted=0;
        for(var block:ForgeRegistries.BLOCKS)mined+=Math.max(0,player.getStats().getValue(Stats.BLOCK_MINED,block));
        for(var item:ForgeRegistries.ITEMS)crafted+=Math.max(0,player.getStats().getValue(Stats.ITEM_CRAFTED,item));
        result.addProperty("mined",mined);result.addProperty("crafted",crafted);
        JsonArray milestones=new JsonArray();for(String id:List.of("explorador","especialista","resonancia","forja","umbral","maestro"))if(Progression.earned(player,"virgos:"+id))milestones.add(id);result.add("milestones",milestones);
        quests(player,result);profiles.put(player.getUUID(),result);return result;
    }
    public void tick(){if(server!=null&&server.getTickCount()%1200==0){for(var player:server.getPlayerList().getPlayers())if(VirgosCore.AUTH.authenticated(player))snapshot(player);save();}}
    public void logout(ServerPlayer player){if(VirgosCore.AUTH.authenticated(player)){snapshot(player);save();}lastRequest.remove(player.getUUID());}
    public void stopping(){if(server==null)return;for(var player:server.getPlayerList().getPlayers())if(VirgosCore.AUTH.authenticated(player))snapshot(player);save();server=null;}
    private void save(){
        if(file==null)return;
        try{
            JsonObject players=new JsonObject();profiles.forEach((id,data)->players.add(id.toString(),data));JsonObject out=new JsonObject();out.addProperty("schema",1);out.add("players",players);
            Path temporary=file.resolveSibling("virgos-profiles.json.tmp");Files.writeString(temporary,VirgosCore.JSON.toJson(out));
            try{Files.move(temporary,file,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);}catch(AtomicMoveNotSupportedException ignored){Files.move(temporary,file,StandardCopyOption.REPLACE_EXISTING);}
        }catch(Exception error){VirgosCore.LOG.error("Could not save player profiles",error);}
    }
    public LiteralArgumentBuilder<CommandSourceStack> command(String name){
        return Commands.literal(name).executes(c->show(c.getSource(),null))
            .then(Commands.argument("jugador",StringArgumentType.word()).suggests((c,b)->SharedSuggestionProvider.suggest(profiles.values().stream().map(p->p.get("name").getAsString()),b)).executes(c->show(c.getSource(),StringArgumentType.getString(c,"jugador"))));
    }
    private int unavailable(CommandSourceStack source,ServerPlayer viewer,String message){
        source.sendFailure(net.minecraft.network.chat.Component.literal(message));
        if(ProfileProtocol.CHANNEL.isRemotePresent(viewer.connection.connection)){
            JsonObject error=new JsonObject();error.addProperty("error",message);
            ProfileProtocol.CHANNEL.send(PacketDistributor.PLAYER.with(()->viewer),new ProfileProtocol.Snapshot(error.toString()));
        }
        return 0;
    }
    public int show(CommandSourceStack source,String name){
        ServerPlayer viewer=source.getPlayer();if(viewer==null||server==null||!VirgosCore.AUTH.authenticated(viewer))return 0;
        int tick=server.getTickCount();Integer previous=lastRequest.put(viewer.getUUID(),tick);if(previous!=null&&tick-previous<10)return 0;
        if(name==null)name=viewer.getGameProfile().getName();
        if(!name.matches("[A-Za-z0-9_]{1,16}"))return unavailable(source,viewer,"Usá el nombre de Minecraft del jugador.");
        ServerPlayer target=server.getPlayerList().getPlayerByName(name);JsonObject data=null;
        if(target!=null&&VirgosCore.AUTH.authenticated(target))data=snapshot(target).deepCopy();
        else for(JsonObject stored:profiles.values())if(stored.get("name").getAsString().equalsIgnoreCase(name)){data=stored.deepCopy();break;}
        if(data==null)return unavailable(source,viewer,"Ese jugador todavía no tiene un perfil en este mundo.");
        data.addProperty("online",target!=null&&VirgosCore.AUTH.authenticated(target));
        JsonArray friends=new JsonArray();profiles.values().stream().sorted(Comparator.comparing(p->p.get("name").getAsString().toLowerCase(Locale.ROOT))).limit(64).forEach(p->friends.add(p.get("name").getAsString()));data.add("players",friends);
        if(ProfileProtocol.CHANNEL.isRemotePresent(viewer.connection.connection))ProfileProtocol.CHANNEL.send(PacketDistributor.PLAYER.with(()->viewer),new ProfileProtocol.Snapshot(data.toString()));
        else {long seconds=data.get("seconds").getAsLong();source.sendSuccess(net.minecraft.network.chat.Component.literal("§6"+data.get("name").getAsString()+"§r · "+data.get("rank").getAsString()+" · nivel XP "+data.get("level").getAsInt()+"\nTiempo: "+seconds/3600+" h "+seconds%3600/60+" min (incluye AFK)\nMisiones: "+data.get("quests").getAsInt()+" / "+data.get("questTotal").getAsInt()+" · muertes: "+data.get("deaths").getAsInt())::copy,false);}
        return 1;
    }
}
