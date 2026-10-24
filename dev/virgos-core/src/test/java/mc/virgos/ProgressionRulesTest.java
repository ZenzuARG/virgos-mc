package mc.virgos;

import java.util.List;
import java.util.Map;
import java.util.Set;

/** Dependency-free policy regression tests, run by checkProgression. */
public final class ProgressionRulesTest {
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args) {
        var policy=new ProgressionRules(Map.of(
            "COMMON",List.of(),"UNCOMMON",List.of(),"RARE",List.of("explorador"),
            "EPIC",List.of("especialista"),"LEGENDARY",List.of("maestro")),
            Map.of(1,List.of(),2,List.of("explorador"),3,List.of("especialista"),99,List.of("maestro")));
        check(policy.missingIron("COMMON",id->false).isEmpty(),"A new player must be able to cast basic spells");
        check(policy.missingIron("RARE",id->false).equals(List.of("explorador")),"Rare gift must not bypass personal rank");
        check(policy.missingIron("EPIC",Set.of("especialista")::contains).isEmpty(),"Personal specialty unlocks epic");
        check(policy.missingIron("LEGENDARY",Set.of("maestro")::contains).isEmpty(),"Personal mastery unlocks legendary");
        check(policy.missingArs(1,id->false).isEmpty(),"Basic glyphs must remain available");
        check(policy.missingArs(3,Set.of("especialista")::contains).isEmpty(),"Personal specialty unlocks tier three");
        check(policy.missingArs(3,id->false).equals(List.of("especialista")),"Another identity retains its own requirement");
        boolean unknown=false;
        try{policy.missingArs(4,id->true);}catch(IllegalArgumentException expected){unknown=true;}
        check(unknown,"An unknown future tier must not silently bypass the policy");
        System.out.println("PASS: 8 personal spell progression checks");
    }
}
