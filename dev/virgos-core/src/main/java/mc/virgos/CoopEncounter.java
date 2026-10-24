package mc.virgos;

import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/** Deterministic encounter rules; world/auth/entity checks are supplied by the server.
 * Time is in server ticks. A run never accepts new members after it begins.
 */
public final class CoopEncounter {
    public enum Stage { SEALS, COMBAT, COMPLETE, ABORTED }
    private record Press(int seal,long at) {}
    private final Set<UUID> members;
    private final int minimum,rounds,chargeRequired;
    private final long started;
    private final Map<UUID,Press> presses=new HashMap<>();
    private final Set<UUID> contributors=new HashSet<>();
    private Stage stage=Stage.SEALS;
    private int round=1,charge;
    private long lastTick,invalidSince=-1;
    private boolean combatStarted;
    private String abortReason="";

    public CoopEncounter(Collection<UUID> participants,int minimum,int rounds,int chargeRequired,long now) {
        members=Set.copyOf(participants);
        if(members.size()!=participants.size())throw new IllegalArgumentException("Duplicate participant identity");
        if(minimum<2 || minimum>4 || members.size()<minimum || members.size()>8 || rounds<1 || rounds>8 || chargeRequired<20)
            throw new IllegalArgumentException("Invalid encounter setup");
        this.minimum=minimum;this.rounds=rounds;this.chargeRequired=chargeRequired;started=now;lastTick=now;
    }

    /** Each identity can energize only one seal at a time, even if packets alternate. */
    public boolean press(UUID player,int seal,long now) {
        if(stage!=Stage.SEALS || !members.contains(player) || seal<0 || seal>=minimum)return false;
        presses.put(player,new Press(seal,now));contributors.add(player);return true;
    }

    public void combatStarted(int spawned) {
        if(stage!=Stage.COMBAT || combatStarted)throw new IllegalStateException("No wave pending");
        if(spawned<=0){abort("No se pudo preparar la oleada.");return;}
        combatStarted=true;
    }

    /** valid means connected, authenticated, alive, inside the arena and active.
     * Missing members pause progress immediately, then abort after ten seconds.
     */
    public void tick(long now,Set<UUID> valid,int liveEnemies) {
        if(stage==Stage.COMPLETE || stage==Stage.ABORTED)return;
        if(now<lastTick)throw new IllegalArgumentException("Encounter clock moved backwards");
        int elapsed=(int)Math.min(20,now-lastTick);lastTick=now;
        if(now-started>20L*60*45){abort("Se agotó el tiempo de la expedición.");return;}
        if(!valid.containsAll(members)) {
            charge=0;presses.clear();
            if(invalidSince<0)invalidSince=now;
            if(now-invalidSince>=200)abort("Faltan participantes vivos, activos y autenticados en la arena.");
            return;
        }
        invalidSince=-1;
        if(stage==Stage.SEALS) {
            Set<Integer> lit=new HashSet<>();
            for(var entry:presses.entrySet())if(now-entry.getValue().at<=30)lit.add(entry.getValue().seal);
            if(lit.size()==minimum && contributors.containsAll(members))charge+=elapsed;
            else charge=0;
            if(charge>=chargeRequired){stage=Stage.COMBAT;charge=chargeRequired;combatStarted=false;}
        }else if(combatStarted && liveEnemies==0) {
            if(round==rounds)stage=Stage.COMPLETE;
            else {round++;stage=Stage.SEALS;charge=0;presses.clear();contributors.clear();combatStarted=false;}
        }
    }

    public void abort(String reason) {
        if(stage==Stage.COMPLETE || stage==Stage.ABORTED)return;
        abortReason=reason;stage=Stage.ABORTED;presses.clear();
    }
    public Stage stage(){return stage;}
    public int round(){return round;}
    public int minimum(){return minimum;}
    public float charge(){return Math.min(1f,charge/(float)chargeRequired);}
    public Set<UUID> members(){return members;}
    public boolean paused(){return invalidSince>=0;}
    public String abortReason(){return abortReason;}
    public Set<UUID> finishers(){return stage==Stage.COMPLETE?members:Set.of();}
}
