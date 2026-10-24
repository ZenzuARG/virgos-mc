package mc.virgos;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** A per-player rolling token budget shared across targets, including area spells. */
public final class DamageBudget {
    private record Balance(double tokens,long tick){}
    private final Map<UUID,Balance> balances=new HashMap<>();
    public float accept(UUID player,float requested,long tick,double perSecond,double burst) {
        if(!Float.isFinite(requested)||requested<=0||perSecond<=0||burst<=0)return 0;
        var old=balances.getOrDefault(player,new Balance(burst,tick));
        double available=Math.min(burst,old.tokens+Math.max(0,tick-old.tick)*perSecond/20.0);
        float accepted=(float)Math.min(requested,available);
        balances.put(player,new Balance(Math.max(0,available-accepted),tick));
        return accepted;
    }
    public void clear(){balances.clear();}
}
