package mc.virgos;

import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraftforge.event.entity.living.LivingDamageEvent;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.registries.ForgeRegistries;
import java.util.*;

/** First-clear bonuses complement the original shared drops, never clone them. */
public final class BossRewards {
    private static final Map<String,String> BOSSES=Map.of(
        "cataclysm:ender_guardian","guardian", "cataclysm:netherite_monstrosity","monstruosidad",
        "cataclysm:the_harbinger","heraldo", "cataclysm:ignis","ignis",
        "cataclysm:ancient_remnant","remanente", "cataclysm:maledictus","maledictus",
        "mowziesmobs:ferrous_wroughtnaut","forjado", "minecraft:ender_dragon","dragon");
    private static final class Credit {float damage;int support;long first,last,lastSupport=-1000;}
    private final Map<UUID,Map<UUID,Credit>> credits=new HashMap<>();
    private final Map<UUID,LivingEntity> bosses=new HashMap<>();
    private boolean eligible(LivingEntity entity){return !entity.getPersistentData().contains("virgos_encounter")&&BOSSES.containsKey(String.valueOf(ForgeRegistries.ENTITY_TYPES.getKey(entity.getType())));}
    private Credit credit(LivingEntity boss,ServerPlayer p){
        bosses.put(boss.getUUID(),boss);var c=credits.computeIfAbsent(boss.getUUID(),x->new HashMap<>()).computeIfAbsent(p.getUUID(),x->new Credit());
        long now=p.server.overworld().getGameTime();if(c.first==0)c.first=now;c.last=now;return c;
    }
    @SubscribeEvent(priority=EventPriority.LOWEST)
    public void damage(LivingDamageEvent e){
        if(e.getAmount()<=0)return;
        if(eligible(e.getEntity())&&e.getSource().getEntity() instanceof ServerPlayer p&&valid(p,e.getEntity()))credit(e.getEntity(),p).damage+=Math.min(e.getAmount(),e.getEntity().getHealth());
        else if(e.getEntity() instanceof ServerPlayer p&&e.getSource().getEntity() instanceof LivingEntity boss&&eligible(boss)&&valid(p,boss))credit(boss,p).support++;
    }
    private boolean valid(ServerPlayer p,LivingEntity boss){return p.isAlive()&&!p.isCreative()&&!p.isSpectator()&&p.level()==boss.level()&&p.distanceToSqr(boss)<=40*40&&VirgosCore.AUTH.authenticated(p);}
    public void support(ServerPlayer p){
        // Only already engaged bosses qualify; distant casting cannot create an encounter.
        for(var boss:bosses.values())if(boss.isAlive()&&valid(p,boss)&&(!(boss instanceof Mob mob)||mob.getTarget()!=null)){
            var c=credit(boss,p);long now=p.server.overworld().getGameTime();
            if(now-c.lastSupport>=60){c.support++;c.lastSupport=now;}
        }
    }
    @SubscribeEvent(priority=EventPriority.LOWEST)
    public void death(LivingDeathEvent e){
        var boss=e.getEntity();if(!eligible(boss))return;
        var entries=credits.remove(boss.getUUID());bosses.remove(boss.getUUID());if(entries==null)return;
        String id=BOSSES.get(String.valueOf(ForgeRegistries.ENTITY_TYPES.getKey(boss.getType())));
        for(var entry:entries.entrySet()){
            var p=boss.getServer().getPlayerList().getPlayer(entry.getKey());var c=entry.getValue();long now=boss.getServer().overworld().getGameTime();
            if(p!=null&&valid(p,boss)&&now-c.last<=1200&&now-c.first>=60&&(c.damage>=boss.getMaxHealth()*.01||c.support>=3))CommunityProjects.award(p,"jefe_"+id);
        }
    }
    public void tick(MinecraftServer server){
        var gone=bosses.entrySet().stream().filter(e->e.getValue().isRemoved()).map(Map.Entry::getKey).toList();
        for(var id:gone){bosses.remove(id);credits.remove(id);}
    }
}
