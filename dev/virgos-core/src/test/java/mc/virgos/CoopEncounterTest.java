package mc.virgos;

import java.util.List;
import java.util.Set;
import java.util.UUID;

public final class CoopEncounterTest {
    private static final UUID A=new UUID(0,1),B=new UUID(0,2),C=new UUID(0,3);
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    private static CoopEncounter pair(){return new CoopEncounter(List.of(A,B),2,2,40,0);}
    public static void main(String[] args) {
        boolean rejected=false;
        try{new CoopEncounter(List.of(A,A),2,1,40,0);}catch(IllegalArgumentException expected){rejected=true;}
        check(rejected,"Two names with the same UUID cannot count as two people");
        var solo=pair();
        for(int t=1;t<=80;t++){solo.press(A,t%2,t);solo.tick(t,Set.of(A,B),1);}
        check(solo.stage()==CoopEncounter.Stage.SEALS,"A single identity cannot energize two seals");
        check(!solo.press(C,1,81),"Late entrant cannot contribute or receive credit");
        var run=pair();
        for(int t=1;t<=40;t++){run.press(A,0,t);run.press(B,1,t);run.tick(t,Set.of(A,B),0);}
        check(run.stage()==CoopEncounter.Stage.COMBAT,"Distinct players can complete seals together");
        run.tick(41,Set.of(A,B),0);
        check(run.stage()==CoopEncounter.Stage.COMBAT,"No empty-wave automatic win before spawning");
        run.combatStarted(3);
        run.tick(42,Set.of(A,B),1);
        check(run.stage()==CoopEncounter.Stage.COMBAT,"Remaining enemies prevent completion");
        run.tick(43,Set.of(A,B),0);
        check(run.round()==2 && run.stage()==CoopEncounter.Stage.SEALS,"Next round requires fresh cooperation");
        for(int t=44;t<=84;t++){run.press(A,0,t);run.press(B,1,t);run.tick(t,Set.of(A,B),0);}
        run.combatStarted(1);run.tick(85,Set.of(A),0);
        check(run.stage()==CoopEncounter.Stage.COMBAT && run.finishers().isEmpty(),"Disconnect at the final kill cannot award victory");
        run.tick(86,Set.of(A,B),0);
        check(run.stage()==CoopEncounter.Stage.COMPLETE && run.finishers().equals(Set.of(A,B)),"Only original active participants finish");
        var lost=pair();lost.tick(1,Set.of(A),0);lost.tick(201,Set.of(A),0);
        check(lost.stage()==CoopEncounter.Stage.ABORTED && lost.finishers().isEmpty(),"Disconnection or AFK eventually aborts without rewards");
        var failedSpawn=pair();
        for(int t=1;t<=40;t++){failedSpawn.press(A,0,t);failedSpawn.press(B,1,t);failedSpawn.tick(t,Set.of(A,B),0);}
        failedSpawn.combatStarted(0);
        check(failedSpawn.stage()==CoopEncounter.Stage.ABORTED,"Spawn failure must never grant completion");
        var extra=new CoopEncounter(List.of(A,B,C),2,1,40,0);
        for(int t=1;t<=40;t++){extra.press(A,0,t);extra.press(B,1,t);extra.tick(t,Set.of(A,B,C),0);}
        check(extra.stage()==CoopEncounter.Stage.SEALS,"An extra member must also contribute to each seal phase");
        var restart=pair();restart.abort("Reinicio del servidor");restart.tick(100,Set.of(A,B),0);
        check(restart.finishers().isEmpty(),"Restart cancellation cannot produce rewards");
        var three=new CoopEncounter(List.of(A,B,C),3,1,40,0);
        for(int t=1;t<=40;t++){three.press(A,0,t);three.press(B,1,t);three.press(C,2,t);three.tick(t,Set.of(A,B,C),0);}
        check(three.stage()==CoopEncounter.Stage.COMBAT,"Three-player expedition requires and accepts three simultaneous seals");
        System.out.println("PASS: 14 cooperative encounter checks");
    }
}
