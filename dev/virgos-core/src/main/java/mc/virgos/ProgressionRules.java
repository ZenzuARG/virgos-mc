package mc.virgos;

import java.util.List;
import java.util.Map;
import java.util.function.Predicate;

/** Personal achievements are checked at use time, so gifts cannot bypass them. */
public final class ProgressionRules {
    private final Map<String,List<String>> iron;
    private final Map<Integer,List<String>> ars;

    public ProgressionRules(Map<String,List<String>> iron, Map<Integer,List<String>> ars) {
        this.iron=Map.copyOf(iron);this.ars=Map.copyOf(ars);
        for(String rarity:List.of("COMMON","UNCOMMON","RARE","EPIC","LEGENDARY"))
            if(!iron.containsKey(rarity))throw new IllegalArgumentException("Missing Iron rarity: "+rarity);
        if(!ars.keySet().containsAll(List.of(1,2,3,99)))throw new IllegalArgumentException("Missing Ars tiers");
    }

    public List<String> missingIron(String rarity, Predicate<String> earned) {
        var required=iron.get(rarity);
        if(required==null)throw new IllegalArgumentException("Unknown spell rarity: "+rarity);
        return required.stream().filter(id->!earned.test(id)).toList();
    }

    public List<String> missingArs(int tier, Predicate<String> earned) {
        var required=ars.get(tier);
        if(required==null)throw new IllegalArgumentException("Unknown glyph tier: "+tier);
        return required.stream().filter(id->!earned.test(id)).toList();
    }
}
