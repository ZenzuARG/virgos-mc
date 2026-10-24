package mc.virgos;

import com.google.gson.JsonParser;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.entity.living.LivingEvent;
import net.minecraftforge.eventbus.api.Event;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Server-side spell limits integrated with Heracles' personal advancements.
 * Reflection isolates optional mod APIs; all Minecraft calls remain mapped.
 */
public final class Progression {
    private static final String IRON_EVENT="io.redspace.ironsspellbooks.api.events.SpellPreCastEvent";
    private static final String ARS_EVENT="com.hollingsworth.arsnouveau.api.event.SpellCastEvent";
    private ProgressionRules rules;
    private Method ironId,ironLevel,ironSpell,ironRarity,arsTier;
    private Method spellContainerIs,spellContainerGet,spellContainerAll,spellSlotSpell,spellId;
    private Method magicDataFor,magicDataCastingItem;
    private Field arsSpell,arsRecipe,arsTierValue;
    private final Map<UUID,Integer> lastNotice=new HashMap<>();
    private long blockedIron,blockedArs,allowedIron,allowedArs;
    private boolean ready;
    private final Map<String,String> titles=new HashMap<>();

    public void initialize(MinecraftServer server) {
        ready=false;
        try {
            var config=JsonParser.parseString(Files.readString(Path.of("config/virgos/progression.json"))).getAsJsonObject();
            if(config.get("schema").getAsInt()!=1)throw new IllegalArgumentException("Unknown progression schema");
            var iron=new HashMap<String,List<String>>();
            var ars=new HashMap<Integer,List<String>>();
            for(var entry:config.getAsJsonObject("ironSpellRarity").entrySet()) {
                List<String> requirements=new ArrayList<>();
                for(var id:entry.getValue().getAsJsonArray())requirements.add(id.getAsString());
                iron.put(entry.getKey(),List.copyOf(requirements));
            }
            for(var entry:config.getAsJsonObject("arsGlyphTier").entrySet()) {
                List<String> requirements=new ArrayList<>();
                for(var id:entry.getValue().getAsJsonArray())requirements.add(id.getAsString());
                ars.put(Integer.parseInt(entry.getKey()),List.copyOf(requirements));
            }
            for(var entry:config.getAsJsonObject("titles").entrySet())titles.put(entry.getKey(),entry.getValue().getAsString());
            for(var group:List.of(iron.values(),ars.values()))for(var ids:group)for(String id:ids) {
                if(server.getAdvancements().getAdvancement(new ResourceLocation(id))==null)
                    throw new IllegalArgumentException("Missing personal advancement "+id);
                if(!titles.containsKey(id))throw new IllegalArgumentException("Missing achievement title "+id);
            }
            rules=new ProgressionRules(iron,ars);
            Class<?> ironEvent=Class.forName(IRON_EVENT);
            ironId=ironEvent.getMethod("getSpellId");ironLevel=ironEvent.getMethod("getSpellLevel");
            ironSpell=Class.forName("io.redspace.ironsspellbooks.api.registry.SpellRegistry").getMethod("getSpell",String.class);
            Class<?> abstractSpell=Class.forName("io.redspace.ironsspellbooks.api.spells.AbstractSpell");
            ironRarity=abstractSpell.getMethod("getRarity",int.class);
            spellId=abstractSpell.getMethod("getSpellId");
            Class<?> spellContainer=Class.forName("io.redspace.ironsspellbooks.api.spells.ISpellContainer");
            spellContainerIs=spellContainer.getMethod("isSpellContainer",net.minecraft.world.item.ItemStack.class);
            spellContainerGet=spellContainer.getMethod("get",net.minecraft.world.item.ItemStack.class);
            spellContainerAll=spellContainer.getMethod("getAllSpells");
            spellSlotSpell=Class.forName("io.redspace.ironsspellbooks.api.spells.SpellSlot").getMethod("getSpell");
            Class<?> magicData=Class.forName("io.redspace.ironsspellbooks.api.magic.MagicData");
            magicDataFor=magicData.getMethod("getPlayerMagicData",net.minecraft.world.entity.LivingEntity.class);
            magicDataCastingItem=magicData.getMethod("getPlayerCastingItem");
            arsSpell=Class.forName(ARS_EVENT).getField("spell");
            arsRecipe=Class.forName("com.hollingsworth.arsnouveau.api.spell.Spell").getField("recipe");
            arsTier=Class.forName("com.hollingsworth.arsnouveau.api.spell.AbstractSpellPart").getMethod("getConfigTier");
            arsTierValue=Class.forName("com.hollingsworth.arsnouveau.api.spell.SpellTier").getField("value");
            ready=true;
            VirgosCore.LOG.info("Virgos: personal progression ready (Iron rarity + Ars glyph tiers)");
        }catch(Exception exception) {
            VirgosCore.LOG.error("Virgos: spell progression unavailable; casts will be refused",exception);
        }
    }

    public static boolean earned(ServerPlayer player,String id) {
        var advancement=player.server.getAdvancements().getAdvancement(new ResourceLocation(id));
        return advancement!=null && player.getAdvancements().getOrStartProgress(advancement).isDone();
    }

    private boolean allowed(ServerPlayer player,Event event) {
        if(!VirgosCore.AUTH.authenticated(player)) {
            if(event.isCancelable())event.setCanceled(true);
            return false;
        }
        if(!ready) {
            refuse(player,event,"La magia está en mantenimiento. Avisale al administrador.");
            return false;
        }
        return true;
    }

    private void refuse(ServerPlayer player,Event event,String message) {
        if(event.isCancelable())event.setCanceled(true);
        else throw new IllegalStateException("Expected a cancelable spell event");
        int tick=player.server.getTickCount();
        if(tick-lastNotice.getOrDefault(player.getUUID(),-100)>60) {
            player.sendSystemMessage(Component.literal("§e"+message));
            lastNotice.put(player.getUUID(),tick);
        }
    }

    private boolean require(ServerPlayer player,Event event,List<String> missing) {
        if(missing.isEmpty())return true;
        String names=String.join(", ",missing.stream().map(id->titles.getOrDefault(id,id)).toList());
        refuse(player,event,"Este hechizo requiere: "+names+". Revisá tu códice [J].");
        return false;
    }

    /**
     * A spell already installed in one of the player's books is an explicit player choice.
     * The codex still guides new unlocks, but it must not prevent a player from using a
     * spell they already learned. Reflection keeps this bridge optional at compile time.
     */
    private boolean hasSpellInBook(ServerPlayer player,String id) {
        try {
            for(var stack:player.getInventory().items)if(containerHasSpell(stack,id))return true;
            for(var stack:player.getInventory().armor)if(containerHasSpell(stack,id))return true;
            for(var stack:player.getInventory().offhand)if(containerHasSpell(stack,id))return true;
            Object data=magicDataFor.invoke(null,player);
            Object casting=magicDataCastingItem.invoke(data);
            return casting instanceof net.minecraft.world.item.ItemStack stack && containerHasSpell(stack,id);
        } catch(Exception ignored) {
            return false;
        }
    }

    private boolean containerHasSpell(net.minecraft.world.item.ItemStack stack,String id)throws Exception {
        if(stack==null || stack.isEmpty() || !spellContainerIs.invoke(null,stack).equals(Boolean.TRUE))return false;
        Object container=spellContainerGet.invoke(null,stack);
        Object spells=spellContainerAll.invoke(container);
        if(!(spells instanceof Object[] slots))return false;
        for(Object slot:slots) {
            Object spell=spellSlotSpell.invoke(slot);
            if(spell!=null && id.equals(spellId.invoke(spell)))return true;
        }
        return false;
    }

    @SubscribeEvent(priority=EventPriority.HIGHEST)
    public void iron(PlayerEvent event) {
        if(!event.getClass().getName().equals(IRON_EVENT) || !(event.getEntity() instanceof ServerPlayer player))return;
        if(!allowed(player,event)){blockedIron++;return;}
        try {
            String spellIdValue=(String)ironId.invoke(event);
            if(hasSpellInBook(player,spellIdValue)) {
                allowedIron++;VirgosCore.EXPEDITIONS.activity(player);VirgosCore.BOSSES.support(player);return;
            }
            Object spell=ironSpell.invoke(null,spellIdValue);
            String rarity=((Enum<?>)ironRarity.invoke(spell,ironLevel.invoke(event))).name();
            if(require(player,event,rules.missingIron(rarity,id->earned(player,id)))){allowedIron++;VirgosCore.EXPEDITIONS.activity(player);VirgosCore.BOSSES.support(player);}
            else blockedIron++;
        }catch(Exception exception) {
            blockedIron++;refuse(player,event,"No se pudo validar este hechizo. Avisale al administrador.");
            VirgosCore.LOG.error("Virgos: Iron spell progression validation failed",exception);
        }
    }

    @SubscribeEvent(priority=EventPriority.HIGHEST)
    public void ars(LivingEvent event) {
        if(!event.getClass().getName().equals(ARS_EVENT) || !(event.getEntity() instanceof ServerPlayer player))return;
        if(!allowed(player,event)){blockedArs++;return;}
        try {
            var missing=new LinkedHashSet<String>();
            for(Object part:(List<?>)arsRecipe.get(arsSpell.get(event))) {
                int tier=arsTierValue.getInt(arsTier.invoke(part));
                missing.addAll(rules.missingArs(tier,id->earned(player,id)));
            }
            if(require(player,event,List.copyOf(missing))){allowedArs++;VirgosCore.EXPEDITIONS.activity(player);VirgosCore.BOSSES.support(player);}else blockedArs++;
        }catch(Exception exception) {
            blockedArs++;refuse(player,event,"No se pudo validar este glifo. Avisale al administrador.");
            VirgosCore.LOG.error("Virgos: Ars spell progression validation failed",exception);
        }
    }

    public int describe(CommandSourceStack source) {
        ServerPlayer player=source.getPlayer();
        if(player==null || !VirgosCore.AUTH.authenticated(player))return 0;
        String rank=earned(player,"virgos:maestro")?"Maestro":earned(player,"virgos:especialista")?"Especialista":earned(player,"virgos:explorador")?"Explorador":"Inicio";
        StringBuilder text=new StringBuilder("§6Tu progreso: "+rank+"§r\n");
        for(String id:List.of("explorador","especialista","resonancia","forja","umbral","maestro"))
            text.append(earned(player,"virgos:"+id)?"§a✓ ":"§7○ ").append(titles.getOrDefault("virgos:"+id,id)).append("\n");
        String next=!earned(player,"virgos:explorador")?"J → reclamá la bienvenida y llevá un pico de hierro para activar Explorador.":
            !earned(player,"virgos:resonancia")?"Reuní dos Exploradores y completá Resonancia al sur del Bastión.":
            !earned(player,"virgos:especialista")?"J → completá UNA rama: Ingeniería Create, Hechicería Iron o Ars; reclamá Especialista.":
            !earned(player,"virgos:forja")?"Reuní dos Especialistas con Resonancia para completar Forja.":
            !earned(player,"virgos:umbral")?"Reuní tres Especialistas con Forja para completar Umbral.":
            !earned(player,"virgos:maestro")?"J → reclamá la recompensa de Umbral para activar Maestro.":
            "Elegí nuevos mods, proyectos, jefes o acompañá a quienes están empezando.";
        text.append("§ePróximo paso: ").append(next).append("\n");
        text.append("§fSi un hechizo ya está dentro de tu libro, podés lanzarlo: el códice no lo bloquea. Para aprender nuevos, abrí J → 04 · Magia y reclamá la misión que corresponda. /virgos guia magia explica el camino.");
        source.sendSuccess(()->Component.literal(text.toString()),false);
        return 1;
    }

    public String status(){return "progreso="+ready+"; Iron="+allowedIron+" permitidos/"+blockedIron+" bloqueados; Ars="+allowedArs+" permitidos/"+blockedArs+" bloqueados";}
    public void detach(UUID id){lastNotice.remove(id);}
}
