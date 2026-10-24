package mc.virgos;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraftforge.registries.ForgeRegistries;
import java.nio.file.*;
import java.util.*;

/** Donations use a write-ahead journal and a receipt saved with the consumed inventory. */
public final class CommunityProjects {
    private static final Map<String,CommunityLedger.Rule> PROJECTS=CommunityLedger.RULES;
    private MinecraftServer server;
    private Path file;
    private JsonObject state;
    private boolean ready;
    public void initialize(MinecraftServer server){
        this.server=server;file=server.getWorldPath(LevelResource.ROOT).resolve("virgos-community.json");
        try {
            if(Files.exists(file))state=JsonParser.parseString(Files.readString(file)).getAsJsonObject();
            else {state=new JsonObject();state.addProperty("schema",1);state.add("projects",new JsonObject());state.add("pending",new JsonObject());}
            CommunityLedger.validate(state);
            for(String key:PROJECTS.keySet())if(!state.getAsJsonObject("projects").has(key))state.getAsJsonObject("projects").add(key,new JsonObject());
            save();ready=true;
        }catch(Exception error){VirgosCore.LOG.error("Community journal unavailable",error);ready=false;}
    }
    private JsonObject donors(String project){return state.getAsJsonObject("projects").getAsJsonObject(project);}
    private int count(String project){return donors(project).entrySet().stream().mapToInt(e->e.getValue().getAsInt()).sum();}
    private void save() throws Exception {save(state);}
    private void save(JsonObject next) throws Exception {
        CommunityLedger.validate(next);
        var tmp=file.resolveSibling(file.getFileName()+".tmp");Files.writeString(tmp,VirgosCore.JSON.toJson(next));
        try(var channel=java.nio.channels.FileChannel.open(tmp,StandardOpenOption.WRITE)){channel.force(true);}
        Files.move(tmp,file,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
    }
    public LiteralArgumentBuilder<CommandSourceStack> commands(){
        var root=Commands.literal("pueblo").executes(context->{
            var p=context.getSource().getPlayer();if(p==null||!VirgosCore.AUTH.authenticated(p)||!ready)return 0;
            tell(p,"Proyectos del Bastión: aportes consumidos, al menos tres personas. /virgos pueblo aportar cocina|taller|caminos. Recompensas personales en el códice, también para recién llegados.");
            for(var e:PROJECTS.entrySet()){
                var donors=donors(e.getKey());int own=donors.has(p.getUUID().toString())?donors.get(p.getUUID().toString()).getAsInt():0;
                tell(p,e.getKey()+": "+count(e.getKey())+"/"+e.getValue().total()+" "+e.getValue().item()+"; tu aporte "+own+"/"+e.getValue().personalLimit()+"; por entrega "+e.getValue().batch()+".");
            }
            return 1;
        });
        var donate=Commands.literal("aportar");
        for(String key:PROJECTS.keySet())donate.then(Commands.literal(key).executes(context->donate(context.getSource(),key)));
        return root.then(donate);
    }
    private static void tell(ServerPlayer p,String text){p.sendSystemMessage(Component.literal("§6Bastión §r"+text));}
    private int donate(CommandSourceStack source,String key){
        var p=source.getPlayer();if(p==null||!VirgosCore.AUTH.authenticated(p)||!ready)return 0;
        if(p.isCreative()||p.isSpectator()||!p.isAlive()||p.serverLevel()!=server.overworld()||p.distanceToSqr(net.minecraft.world.phys.Vec3.atCenterOf(server.overworld().getSharedSpawnPos()))>80*80){tell(p,"Aportá en supervivencia dentro del Bastión.");return 0;}
        if(!Progression.earned(p,"virgos:explorador")){tell(p,"Completá primero Explorador en el códice.");return 0;}
        if(state.getAsJsonObject("pending").has(p.getUUID().toString())){tell(p,"Tu aporte anterior está pendiente de recuperación. Esperá antes de iniciar otro.");return 0;}
        for(var e:state.getAsJsonObject("pending").entrySet())if(e.getValue().getAsJsonObject().get("project").getAsString().equals(key)){tell(p,"Un aporte está pendiente de recuperación; esperá o avisá al administrador.");return 0;}
        var spec=PROJECTS.get(key);String uuid=p.getUUID().toString();var contributions=donors(key);
        int own=contributions.has(uuid)?contributions.get(uuid).getAsInt():0;
        int amount=Math.min(spec.batch(),Math.min(spec.personalLimit()-own,spec.total()-count(key)));
        if(amount<=0){tell(p,"Este proyecto está completo o ya alcanzaste tu aporte personal.");return 0;}
        var item=ForgeRegistries.ITEMS.getValue(new ResourceLocation(spec.item()));
        int available=p.getInventory().items.stream().filter(s->s.is(item)&&!s.hasTag()).mapToInt(s->s.getCount()).sum();
        if(available<amount){tell(p,"Necesitás "+amount+" de "+spec.item()+" sin personalizar. Se consumen al aportar.");return 0;}
        var transaction=new JsonObject();String receipt=UUID.randomUUID().toString();
        transaction.addProperty("id",receipt);transaction.addProperty("project",key);transaction.addProperty("amount",amount);
        state.getAsJsonObject("pending").add(uuid,transaction);
        try {
            save();
            int remaining=amount;
            for(var stack:p.getInventory().items)if(stack.is(item)&&!stack.hasTag()){int take=Math.min(remaining,stack.getCount());stack.shrink(take);remaining-=take;if(remaining==0)break;}
            p.getPersistentData().putString("virgos_donation_receipt",receipt);
            p.getInventory().setChanged();p.containerMenu.broadcastChanges();server.getPlayerList().saveAll();
            // Vanilla save logs IO errors instead of propagating them. Check the durable receipt
            // before publishing the donation, so a failed player save cannot mint resources.
            var playerFile=server.getWorldPath(LevelResource.PLAYER_DATA_DIR).resolve(uuid+".dat");
            var saved=net.minecraft.nbt.NbtIo.readCompressed(playerFile.toFile());
            if(!receipt.equals(saved.getCompound("ForgeData").getString("virgos_donation_receipt")))throw new IllegalStateException("Player receipt did not reach disk");
            settle(p);tell(p,"Aportaste "+amount+". "+key+": "+count(key)+"/"+spec.total()+".");return 1;
        }catch(Exception error){ready=false;VirgosCore.LOG.error("Donation checkpoint failed; journal retained",error);tell(p,"Aporte en recuperación. Avisá al administrador antes de repetirlo.");return 0;}
    }
    private void settle(ServerPlayer p) throws Exception {
        String uuid=p.getUUID().toString();var pending=state.getAsJsonObject("pending");if(!pending.has(uuid))return;
        var next=CommunityLedger.settle(state,uuid,p.getPersistentData().getString("virgos_donation_receipt"));
        save(next);state=next;
    }
    public void tick(){
        if(!ready)return;
        for(var p:server.getPlayerList().getPlayers())if(VirgosCore.AUTH.authenticated(p)){
            try{settle(p);}catch(Exception error){ready=false;VirgosCore.LOG.error("Donation recovery failed",error);return;}
            if(!Progression.earned(p,"virgos:explorador"))continue;
            for(var e:PROJECTS.entrySet())if(count(e.getKey())>=e.getValue().total())award(p,"pueblo_"+e.getKey());
        }
    }
    public static void award(ServerPlayer p,String id){
        var advancement=p.server.getAdvancements().getAdvancement(new ResourceLocation("virgos",id));
        if(advancement==null){VirgosCore.LOG.error("Missing Virgos advancement {}",id);return;}
        var progress=p.getAdvancements().getOrStartProgress(advancement);
        if(progress.isDone())return;
        for(String criterion:progress.getRemainingCriteria())p.getAdvancements().award(advancement,criterion);
        p.getAdvancements().save();
    }
    public String status(){return "pueblo="+ready;}
}
