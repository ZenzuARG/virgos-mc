package mc.virgos;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.BossEvent;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.living.LivingDamageEvent;
import net.minecraftforge.event.entity.living.LivingHealEvent;
import net.minecraftforge.event.entity.living.LivingDropsEvent;
import net.minecraftforge.event.entity.living.LivingExperienceDropEvent;
import net.minecraftforge.event.entity.player.PlayerInteractEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.registries.ForgeRegistries;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.*;

/** One physical arena, individual first-clear credit, no loot farming or inventory replacement. */
public final class Expeditions {
    private static final String TAG="virgos_encounter";
    private record Definition(String title,int minimum,List<String> requirements,List<String> mobs) {}
    private static final Map<String,Definition> DEFINITIONS=Map.of(
        "resonancia",new Definition("Resonancia de las profundidades",2,List.of("explorador"),List.of("minecraft:husk","minecraft:stray","minecraft:ravager")),
        "forja",new Definition("La forja arcana",2,List.of("especialista","resonancia"),List.of("minecraft:stray","minecraft:vindicator","minecraft:ravager")),
        "umbral",new Definition("Guardián del umbral",3,List.of("especialista","forja"),List.of("minecraft:vindicator","minecraft:ravager","minecraft:ravager")));
    private final Set<UUID> queue=new LinkedHashSet<>(),mobs=new HashSet<>();
    private final Map<UUID,Long> activity=new HashMap<>();
    private final Map<UUID,Vec3> positions=new HashMap<>();
    private final Map<UUID,Set<String>> pendingAwards=new HashMap<>();
    private final ServerBossEvent bar=new ServerBossEvent(Component.literal("Expedición Virgos"),BossEvent.BossBarColor.PURPLE,BossEvent.BossBarOverlay.PROGRESS);
    private MinecraftServer server;
    private Path journal;
    private BlockPos center;
    private List<BlockPos> seals=List.of();
    private int radius;
    private boolean enabled,storageReady;
    private String queuedKind,runKind,runId;
    private long queueExpires;
    private CoopEncounter encounter;
    private JsonObject lastResult=new JsonObject();
    private final DamageBudget damageBudget=new DamageBudget(),healBudget=new DamageBudget();
    private final Map<String,double[]> limits=new HashMap<>();
    private final Map<String,Integer> supplies=new HashMap<>();
    private long coolingUntil;
    private boolean phaseCleared;
    private double guardianHealth=900;

    public void initialize(MinecraftServer server) {
        this.server=server;enabled=false;storageReady=false;
        journal=server.getWorldPath(LevelResource.ROOT).resolve("virgos-expeditions-state.json");
        try {
            if(Files.exists(journal)) {
                var saved=JsonParser.parseString(Files.readString(journal)).getAsJsonObject();
                if(saved.get("schema").getAsInt()!=1)throw new IllegalStateException("Unknown expedition journal schema");
                for(var entry:saved.getAsJsonObject("pendingAwards").entrySet()) {
                    Set<String> awards=new HashSet<>();
                    for(var id:entry.getValue().getAsJsonArray()) {
                        String value=id.getAsString();
                        if(!DEFINITIONS.containsKey(value))throw new IllegalStateException("Unknown pending recognition");
                        awards.add(value);
                    }
                    pendingAwards.put(UUID.fromString(entry.getKey()),awards);
                }
                if(saved.has("activeRun")) {
                    lastResult=saved.getAsJsonObject("activeRun");
                    lastResult.addProperty("result","aborted_by_restart");
                    VirgosCore.LOG.info("Virgos: interrupted expedition cancelled; its tagged enemies will be removed on load");
                }else if(saved.has("lastResult"))lastResult=saved.getAsJsonObject("lastResult");
            }
            storageReady=true;save();loadArena();
        }catch(Exception error){storageReady=false;VirgosCore.LOG.error("Virgos: expedition storage/config unavailable",error);}
    }

    private void loadArena() throws Exception {
        enabled=false;
        var config=JsonParser.parseString(Files.readString(Path.of("config/virgos/expeditions.json"))).getAsJsonObject();
        if(config.get("schema").getAsInt()!=1)throw new IllegalArgumentException("Unknown arena schema");
        for(String kind:DEFINITIONS.keySet()) {
            var rule=config.getAsJsonObject("balance").getAsJsonObject(kind);
            double[] values={rule.get("damagePerSecond").getAsDouble(),rule.get("damageBurst").getAsDouble(),rule.get("healingPerSecond").getAsDouble()};
            for(double value:values)if(!Double.isFinite(value)||value<1||value>100)throw new IllegalArgumentException("Invalid combat budget");
            limits.put(kind,values);
        }
        guardianHealth=config.get("guardianHealth").getAsDouble();
        if(!Double.isFinite(guardianHealth)||guardianHealth<300||guardianHealth>5000)throw new IllegalArgumentException("Invalid guardian health");
        center=position(config.getAsJsonArray("center"));radius=config.get("radius").getAsInt();
        if(radius<20 || radius>64)throw new IllegalArgumentException("Invalid arena radius");
        List<BlockPos> locations=new ArrayList<>();
        for(var location:config.getAsJsonArray("seals"))locations.add(position(location.getAsJsonArray()));
        if(locations.size()!=3 || new HashSet<>(locations).size()!=3)throw new IllegalArgumentException("Three different seals are required");
        for(var a:locations) {
            if(a.distManhattan(center)>radius+8)throw new IllegalArgumentException("Seal outside arena");
            for(var b:locations)if(!a.equals(b)&&a.distSqr(b)<100)throw new IllegalArgumentException("Seals too close together");
        }
        seals=List.copyOf(locations);
        if(!config.get("enabled").getAsBoolean())return;
        String build=config.get("requiredBuild").getAsString();
        if(!build.matches("[a-z0-9_-]{1,64}"))throw new IllegalArgumentException("Invalid build name");
        var marker=server.getWorldPath(LevelResource.ROOT).resolve("virgos-build-"+build+"-state.json");
        if(!Files.exists(marker)||!JsonParser.parseString(Files.readString(marker)).getAsJsonObject().get("complete").getAsBoolean())
            throw new IllegalStateException("Arena construction must finish before enabling expeditions");
        for(var seal:seals)if(!server.overworld().getBlockState(seal).is(Blocks.LODESTONE))throw new IllegalStateException("Missing lodestone seal");
        enabled=true;
        VirgosCore.LOG.info("Virgos: expedition arena enabled at {}",center);
    }

    private static BlockPos position(com.google.gson.JsonArray a){if(a.size()!=3)throw new IllegalArgumentException("Invalid position");return new BlockPos(a.get(0).getAsInt(),a.get(1).getAsInt(),a.get(2).getAsInt());}
    private long now(){return server.overworld().getGameTime();}
    private boolean inside(ServerPlayer player){return player.serverLevel()==server.overworld()&&Math.abs(player.getX()-center.getX())<=radius&&Math.abs(player.getZ()-center.getZ())<=radius&&Math.abs(player.getY()-center.getY())<=10;}
    private boolean valid(ServerPlayer player){return player!=null&&!(player instanceof FakePlayer)&&player.isAlive()&&!player.isCreative()&&!player.isSpectator()&&VirgosCore.AUTH.authenticated(player)&&inside(player);}
    private void tell(ServerPlayer player,String message){player.sendSystemMessage(Component.literal("§6Virgos §r"+message));}
    private void broadcast(String message){if(encounter!=null)for(UUID id:encounter.members()){var player=server.getPlayerList().getPlayer(id);if(player!=null)tell(player,message);}}

    public LiteralArgumentBuilder<CommandSourceStack> commands() {
        var root=Commands.literal("expedicion").executes(context->{
            var player=context.getSource().getPlayer();if(player==null||!VirgosCore.AUTH.authenticated(player))return 0;
            tell(player,enabled?"Arena: "+center.getX()+", "+center.getY()+", "+center.getZ()+". Llegá caminando y elegí /virgos expedicion unirse resonancia|forja|umbral. Luego: /virgos expedicion iniciar. Durante los sellos, todos deben tocar uno y mantener clic derecho en sellos separados. /virgos expedicion salir abandona.":"Las expediciones están en preparación.");return 1;});
        var join=Commands.literal("unirse");
        for(String kind:List.of("resonancia","forja","umbral"))join.then(Commands.literal(kind).executes(context->join(context.getSource(),kind)));
        root.then(join);
        root.then(Commands.literal("iniciar").executes(context->start(context.getSource())));
        root.then(Commands.literal("aportar").executes(context->supply(context.getSource())));
        root.then(Commands.literal("estado").executes(context->{
            var p=context.getSource().getPlayer();if(p==null||!VirgosCore.AUTH.authenticated(p))return 0;
            if(encounter==null){tell(p,queue.isEmpty()?"Arena libre. Reunite con tus amigos en 672, 78, 1048.":"Grupo preparando "+queuedKind+": "+queue.size()+" participantes. Tu inscripción: "+queue.contains(p.getUUID()));}
            else {
                tell(p,DEFINITIONS.get(runKind).title+" · ronda "+encounter.round()+"/3 · "+(encounter.paused()?"En pausa":encounter.stage()==CoopEncounter.Stage.SEALS?"Activación de sellos":"Combate")+" · Participás: "+encounter.members().contains(p.getUUID()));
                if(runKind.equals("forja")&&encounter.members().contains(p.getUUID()))tell(p,"Aportes de esta ronda: "+supplies+" / "+requiredSupplies()+".");
            }
            return 1;
        }));
        root.then(Commands.literal("salir").executes(context->{
            var player=context.getSource().getPlayer();if(player==null||!VirgosCore.AUTH.authenticated(player))return 0;
            queue.remove(player.getUUID());
            if(encounter!=null&&encounter.members().contains(player.getUUID()))encounter.abort(player.getScoreboardName()+" abandonó la expedición.");
            tell(player,"Saliste del grupo de expedición.");return 1;}));
        root.then(Commands.literal("recargar").requires(source->source.hasPermission(2)).executes(context->{
            if(encounter!=null)return 0;
            try{loadArena();context.getSource().sendSuccess(()->Component.literal("Arena habilitada="+enabled),false);return 1;}
            catch(Exception error){context.getSource().sendFailure(Component.literal(error.getMessage()));return 0;}}));
        return root;
    }

    private int join(CommandSourceStack source,String kind) {
        var player=source.getPlayer();if(player==null||!VirgosCore.AUTH.authenticated(player))return 0;
        if(!enabled||!storageReady){tell(player,"La arena todavía no está disponible.");return 0;}
        if(encounter!=null){tell(player,"Hay una expedición en curso. Esperá a que termine.");return 0;}
        if(!valid(player)){tell(player,"Reunite vivo y en supervivencia dentro de la arena.");return 0;}
        for(String id:DEFINITIONS.get(kind).requirements)if(!Progression.earned(player,"virgos:"+id)){tell(player,"Te falta el reconocimiento "+id+" del códice.");return 0;}
        if(now()>queueExpires){queue.clear();queuedKind=null;}
        if(!queue.isEmpty()&&!kind.equals(queuedKind)){tell(player,"El grupo está preparando "+queuedKind+". Esperá o uníte a esa expedición.");return 0;}
        if(queue.size()>=8&&!queue.contains(player.getUUID())){tell(player,"El grupo está completo.");return 0;}
        if(queue.isEmpty())queueExpires=now()+6000;
        queuedKind=kind;queue.add(player.getUUID());
        for(UUID id:queue){var member=server.getPlayerList().getPlayer(id);if(member!=null)tell(member,player.getScoreboardName()+" se unió a "+kind+" ("+queue.size()+"/8, mínimo "+DEFINITIONS.get(kind).minimum+").");}
        return 1;
    }

    private int start(CommandSourceStack source) {
        var player=source.getPlayer();if(player==null||!VirgosCore.AUTH.authenticated(player))return 0;
        if(!enabled||!storageReady||encounter!=null||!queue.contains(player.getUUID())||now()>queueExpires)return 0;
        var definition=DEFINITIONS.get(queuedKind);
        if(queue.size()<definition.minimum){tell(player,"Faltan participantes: mínimo "+definition.minimum+".");return 0;}
        for(UUID id:queue) {
            var member=server.getPlayerList().getPlayer(id);
            if(!valid(member)){tell(player,"Todos deben estar presentes, vivos y autenticados.");return 0;}
            for(String requirement:definition.requirements)if(!Progression.earned(member,"virgos:"+requirement))return 0;
        }
        runKind=queuedKind;runId=UUID.randomUUID().toString();
        encounter=new CoopEncounter(queue,definition.minimum,3,160,now());
        damageBudget.clear();healBudget.clear();supplies.clear();coolingUntil=0;phaseCleared=false;
        for(UUID id:queue){var member=server.getPlayerList().getPlayer(id);bar.addPlayer(member);activity.put(id,now());positions.put(id,member.position());}
        queue.clear();queuedKind=null;
        try{save();}catch(Exception error){encounter.abort("No se pudo guardar el inicio de la expedición.");VirgosCore.LOG.error("Expedition start save failed",error);}
        broadcast("Comienza "+definition.title+". Todos deben tocar un sello y luego sostener "+definition.minimum+" sellos separados durante ocho segundos. Son tres rondas de sellos y combate.");
        explainPhase();return 1;
    }

    public void tick(MinecraftServer server) {
        if(!storageReady||server.getTickCount()%2!=0)return;
        if(encounter==null&&server.getTickCount()%20==0)deliverAwards();
        if(encounter==null){if(!queue.isEmpty()&&now()>queueExpires){queue.clear();queuedKind=null;}return;}
        Set<UUID> active=new HashSet<>();
        for(UUID id:encounter.members()) {
            var player=server.getPlayerList().getPlayer(id);
            if(valid(player)) {
                Vec3 previous=positions.get(id);
                if(previous==null||previous.distanceToSqr(player.position())>.04){activity.put(id,now());positions.put(id,player.position());}
                if(now()-activity.getOrDefault(id,0L)<=600)active.add(id);
            }
        }
        for(UUID id:mobs) {
            var entity=server.overworld().getEntity(id);
            if(entity==null){encounter.abort("Un enemigo dejó de estar disponible. Podés volver a intentarlo.");break;}
            if(entity instanceof Mob mob)mob.setNoAi(encounter.paused()||encounter.stage()==CoopEncounter.Stage.SEALS||phaseCleared);
            if(entity.position().distanceToSqr(Vec3.atCenterOf(center))>radius*radius)entity.teleportTo(center.getX()+.5,center.getY()+1,center.getZ()+.5);
        }
        var previous=encounter.stage();encounter.tick(now(),active,phaseCleared?0:mobs.size());
        if(previous==CoopEncounter.Stage.COMBAT&&encounter.stage()==CoopEncounter.Stage.SEALS){supplies.clear();explainPhase();}
        if(previous!=CoopEncounter.Stage.COMBAT&&encounter.stage()==CoopEncounter.Stage.COMBAT)spawnWave();
        if(encounter.stage()==CoopEncounter.Stage.COMPLETE){finish(true);return;}
        if(encounter.stage()==CoopEncounter.Stage.ABORTED){finish(false);return;}
        String phase=encounter.paused()?"Falta un participante activo":encounter.stage()==CoopEncounter.Stage.SEALS?"Sellos "+Math.round(encounter.charge()*100)+"%":"Enemigos: "+mobs.size();
        bar.setName(Component.literal(DEFINITIONS.get(runKind).title+" · Ronda "+encounter.round()+"/3 · "+phase));
        bar.setProgress((encounter.round()-1+(encounter.stage()==CoopEncounter.Stage.SEALS?encounter.charge()*.5f:.5f))/3f);
    }

    private void spawnWave() {
        var definition=DEFINITIONS.get(runKind);
        if(runKind.equals("umbral")&&!mobs.isEmpty()) {
            phaseCleared=false;
            for(UUID id:mobs)if(server.overworld().getEntity(id) instanceof Mob mob){mob.setNoAi(false);mob.setTarget(server.getPlayerList().getPlayer(encounter.members().iterator().next()));}
            encounter.combatStarted(mobs.size());broadcast("Guardián liberado: fase "+encounter.round()+"/3.");return;
        }
        int amount=encounter.round()==3?Math.max(1,encounter.members().size()/2):encounter.members().size()+1;
        String type=definition.mobs.get(encounter.round()-1);
        if(runKind.equals("umbral")){amount=1;type="minecraft:ravager";}
        for(int i=0;i<amount;i++) {
            var entity=ForgeRegistries.ENTITY_TYPES.getValue(new ResourceLocation(type)).create(server.overworld());
            if(!(entity instanceof Mob mob)){encounter.abort("No se pudo crear la oleada.");break;}
            double angle=Math.PI*2*i/amount;
            mob.moveTo(center.getX()+.5+Math.cos(angle)*9,center.getY()+1,center.getZ()+.5+Math.sin(angle)*9,0,0);
            mob.getPersistentData().putString(TAG,runId);mob.setPersistenceRequired();mob.setCanPickUpLoot(false);
            // create() does not run natural-spawn equipment initialization.
            if(type.equals("minecraft:stray"))mob.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND,new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.BOW));
            if(type.equals("minecraft:vindicator"))mob.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND,new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.IRON_AXE));
            mob.setItemSlot(net.minecraft.world.entity.EquipmentSlot.HEAD,new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.IRON_HELMET));
            mob.setCustomName(Component.literal("§d"+definition.title+" · "+encounter.round()));
            var health=mob.getAttribute(Attributes.MAX_HEALTH);
            if(health!=null){health.setBaseValue(health.getBaseValue()*(1+(encounter.members().size()-2)*.15));mob.setHealth(mob.getMaxHealth());}
            if(runKind.equals("umbral")&&health!=null){health.setBaseValue(guardianHealth*(1+(encounter.members().size()-3)*.2));mob.setHealth(mob.getMaxHealth());}
            mob.setTarget(server.getPlayerList().getPlayer(encounter.members().iterator().next()));
            if(server.overworld().addFreshEntity(mob))mobs.add(mob.getUUID());
        }
        if(encounter.stage()==CoopEncounter.Stage.COMBAT) {
            if(mobs.size()!=amount)encounter.abort("No se pudo preparar la oleada completa.");
            else encounter.combatStarted(mobs.size());
        }
        broadcast("Sellos abiertos. Derroten a la oleada y manténganse dentro de la arena.");
        if(runKind.equals("forja")){coolingUntil=now()+120;broadcast("Refrigeración: un compañero toca cualquier sello cada seis segundos para mantener vulnerables a los enemigos.");}
    }

    public void activity(ServerPlayer player) {
        if(encounter!=null&&encounter.members().contains(player.getUUID())&&valid(player))activity.put(player.getUUID(),now());
    }

    @SubscribeEvent(priority=EventPriority.HIGHEST,receiveCanceled=true)
    public void seal(PlayerInteractEvent.RightClickBlock event) {
        if(encounter==null||!(event.getEntity() instanceof ServerPlayer player)||!valid(player)||!encounter.members().contains(player.getUUID()))return;
        if(event.getHand()!=net.minecraft.world.InteractionHand.MAIN_HAND||!player.getMainHandItem().isEmpty())return;
        int index=seals.indexOf(event.getPos());
        if(index<0||player.distanceToSqr(Vec3.atCenterOf(event.getPos()))>25)return;
        if(runKind.equals("forja")&&encounter.stage()==CoopEncounter.Stage.COMBAT){coolingUntil=now()+120;activity(player);event.setCancellationResult(net.minecraft.world.InteractionResult.SUCCESS);event.setCanceled(true);return;}
        if(runKind.equals("forja")&&!supplied())return;
        if(runKind.equals("resonancia"))index=switch(encounter.round()){case 1->index<2?index:-1;case 2->index==1?0:index==2?1:-1;default->index==0?0:index==2?1:-1;};
        if(index<0||index>=encounter.minimum())return;
        if(encounter.press(player.getUUID(),index,now())){activity.put(player.getUUID(),now());event.setCancellationResult(net.minecraft.world.InteractionResult.SUCCESS);event.setCanceled(true);}
    }
    @SubscribeEvent(priority=EventPriority.HIGHEST)
    public void damage(LivingAttackEvent event) {
        var victim=event.getEntity();var attacker=event.getSource().getEntity();
        if(attacker instanceof Projectile projectile)attacker=projectile.getOwner();
        if(victim.getPersistentData().contains(TAG)) {
            if(encounter==null||encounter.stage()!=CoopEncounter.Stage.COMBAT||encounter.paused()||phaseCleared||(runKind.equals("forja")&&now()>coolingUntil)||!(attacker instanceof ServerPlayer player)||!valid(player)||!encounter.members().contains(player.getUUID()))event.setCanceled(true);
            else activity.put(player.getUUID(),now());
        }else if(attacker!=null&&attacker.getPersistentData().contains(TAG)&&(!(victim instanceof ServerPlayer player)||encounter==null||encounter.paused()||encounter.stage()!=CoopEncounter.Stage.COMBAT||!encounter.members().contains(player.getUUID())))event.setCanceled(true);
    }
    @SubscribeEvent(priority=EventPriority.LOWEST)
    public void balanceDamage(LivingDamageEvent event){
        if(encounter==null||!event.getEntity().getPersistentData().contains(TAG)||!(event.getSource().getEntity() instanceof ServerPlayer player))return;
        double[] rule=limits.get(runKind);float amount=damageBudget.accept(player.getUUID(),event.getAmount(),now(),rule[0],rule[1]);
        if(runKind.equals("umbral")&&encounter.round()<3){
            amount=GuardianPhases.limit(event.getEntity().getHealth(),event.getEntity().getMaxHealth(),encounter.round(),amount);
            if(GuardianPhases.complete(event.getEntity().getHealth(),event.getEntity().getMaxHealth(),encounter.round(),amount)){phaseCleared=true;if(event.getEntity() instanceof Mob mob)mob.setNoAi(true);}
        }
        event.setAmount(amount);
    }
    @SubscribeEvent(priority=EventPriority.LOWEST)
    public void balanceHealing(LivingHealEvent event){
        if(encounter==null||!(event.getEntity() instanceof ServerPlayer p)||!encounter.members().contains(p.getUUID())||!valid(p))return;
        double rate=limits.get(runKind)[2];event.setAmount(healBudget.accept(p.getUUID(),event.getAmount(),now(),rate,rate));
    }
    private Map<String,Integer> requiredSupplies(){return switch(encounter.round()){
        case 1->Map.of("create:iron_sheet",8);case 2->Map.of("create:brass_sheet",4);default->Map.of("create:precision_mechanism",1);};}
    private boolean supplied(){return requiredSupplies().entrySet().stream().allMatch(e->supplies.getOrDefault(e.getKey(),0)>=e.getValue());}
    private int supply(CommandSourceStack source){
        var p=source.getPlayer();if(p==null||encounter==null||!runKind.equals("forja")||encounter.stage()!=CoopEncounter.Stage.SEALS||!valid(p)||!encounter.members().contains(p.getUUID()))return 0;
        int donated=0;
        for(var e:requiredSupplies().entrySet()){
            int need=e.getValue()-supplies.getOrDefault(e.getKey(),0);var item=ForgeRegistries.ITEMS.getValue(new ResourceLocation(e.getKey()));
            for(var stack:p.getInventory().items)if(need>0&&stack.is(item)&&!stack.hasTag()){int take=Math.min(need,stack.getCount());stack.shrink(take);need-=take;donated+=take;supplies.merge(e.getKey(),take,Integer::sum);}
        }
        p.getInventory().setChanged();p.containerMenu.broadcastChanges();server.getPlayerList().saveAll();activity(p);
        broadcast("Suministros de ronda "+encounter.round()+": "+supplies+" / "+requiredSupplies()+". Se consumen incluso si se cancela la expedición.");return donated;
    }
    private void explainPhase(){
        switch(runKind){
            case "resonancia"->broadcast("Sellos activos: "+switch(encounter.round()){case 1->"oeste y este";case 2->"este y norte";default->"oeste y norte";}+".");
            case "forja"->broadcast("Antes de activar oeste y este, aporten al grupo "+requiredSupplies()+" con /virgos expedicion aportar. Los materiales se consumen, incluso al abandonar.");
            case "umbral"->broadcast("Los tres sellos liberan la fase "+encounter.round()+" del Guardián. Cada tercio de vida vuelve a cerrar su barrera.");
        }
    }
    @SubscribeEvent(priority=EventPriority.LOWEST)
    public void death(LivingDeathEvent event){if(event.getEntity().getPersistentData().contains(TAG))mobs.remove(event.getEntity().getUUID());}
    @SubscribeEvent
    public void drops(LivingDropsEvent event){if(event.getEntity().getPersistentData().contains(TAG))event.setCanceled(true);}
    @SubscribeEvent
    public void xp(LivingExperienceDropEvent event){if(event.getEntity().getPersistentData().contains(TAG))event.setDroppedExperience(0);}
    @SubscribeEvent
    public void loadEntity(EntityJoinLevelEvent event){if(!event.getLevel().isClientSide&&event.getEntity().getPersistentData().contains(TAG)&&!event.getEntity().getPersistentData().getString(TAG).equals(runId))event.setCanceled(true);}

    private void save() throws Exception {
        JsonObject data=new JsonObject();data.addProperty("schema",1);data.add("pendingAwards",VirgosCore.JSON.toJsonTree(pendingAwards));data.add("lastResult",lastResult);
        if(encounter!=null&&encounter.stage()!=CoopEncounter.Stage.COMPLETE&&encounter.stage()!=CoopEncounter.Stage.ABORTED) {
            JsonObject active=new JsonObject();active.addProperty("id",runId);active.addProperty("kind",runKind);active.add("participants",VirgosCore.JSON.toJsonTree(encounter.members()));data.add("activeRun",active);
        }
        Path temporary=journal.resolveSibling(journal.getFileName()+".tmp");Files.writeString(temporary,VirgosCore.JSON.toJson(data));
        Files.move(temporary,journal,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);
    }
    private void finish(boolean victory) {
        if(victory)for(UUID id:encounter.finishers())pendingAwards.computeIfAbsent(id,ignored->new HashSet<>()).add(runKind);
        lastResult=new JsonObject();lastResult.addProperty("id",runId);lastResult.addProperty("kind",runKind);lastResult.addProperty("result",victory?"complete":encounter.abortReason());lastResult.add("participants",VirgosCore.JSON.toJsonTree(encounter.members()));
        try{save();}catch(Exception error){VirgosCore.LOG.error("Could not persist expedition result; retrying",error);return;}
        broadcast(victory?"¡Expedición completada! Tu reconocimiento personal se entrega una sola vez; reclamá la recompensa del códice.":"Expedición cancelada: "+encounter.abortReason()+". Podés volver a prepararla.");
        for(UUID id:mobs)for(var level:server.getAllLevels()){var entity=level.getEntity(id);if(entity!=null)entity.discard();}
        mobs.clear();activity.clear();positions.clear();bar.removeAllPlayers();encounter=null;runId=null;runKind=null;
        deliverAwards();
    }
    private void deliverAwards() {
        if(pendingAwards.isEmpty())return;
        var iterator=pendingAwards.entrySet().iterator();boolean changed=false;
        while(iterator.hasNext()) {
            var entry=iterator.next();var player=server.getPlayerList().getPlayer(entry.getKey());
            if(player==null||!VirgosCore.AUTH.authenticated(player))continue;
            for(String id:entry.getValue()) {
                var advancement=server.getAdvancements().getAdvancement(new ResourceLocation("virgos",id));
                if(advancement==null)return;
                for(String criterion:player.getAdvancements().getOrStartProgress(advancement).getRemainingCriteria())player.getAdvancements().award(advancement,criterion);
            }
            player.getAdvancements().save();iterator.remove();changed=true;
        }
        if(changed)try{save();}catch(Exception error){VirgosCore.LOG.error("Could not checkpoint delivered expedition awards; replay is idempotent",error);}
    }
    public void stopping(){if(encounter!=null){encounter.abort("Reinicio del servidor");finish(false);}queue.clear();bar.removeAllPlayers();}
    public String status(){return "arena="+enabled+"; expedición="+(encounter==null?"libre":runKind+"/"+encounter.stage());}
}
