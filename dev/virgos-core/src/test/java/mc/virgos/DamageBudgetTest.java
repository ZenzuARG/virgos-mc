package mc.virgos;
import java.util.UUID;
public final class DamageBudgetTest {
    private static void eq(float actual,float wanted){if(Math.abs(actual-wanted)>.001)throw new AssertionError(actual+" != "+wanted);}
    public static void main(String[] args){
        var b=new DamageBudget();var a=UUID.randomUUID();var c=UUID.randomUUID();
        eq(b.accept(a,1000,0,20,10),10);eq(b.accept(a,20,0,20,10),0);
        eq(b.accept(a,20,5,20,10),5);eq(b.accept(c,20,5,20,10),10);
        eq(b.accept(a,100,1000,20,10),10);eq(b.accept(a,100,0,20,10),0);
        eq(b.accept(a,Float.NaN,1001,20,10),0);b.clear();eq(b.accept(a,100,1001,20,10),10);
        System.out.println("Damage budgets: burst, multi-target, regen, separate players and invalid amounts passed");
        eq(GuardianPhases.limit(480,480,1,10000),160);eq(GuardianPhases.limit(320,480,1,10000),0);
        eq(GuardianPhases.limit(320,480,2,10000),160);eq(GuardianPhases.limit(160,480,2,10000),0);
        eq(GuardianPhases.limit(160,480,3,10000),10000);eq(GuardianPhases.limit(400,480,1,24),24);
        if(!GuardianPhases.complete(322,480,1,2)||GuardianPhases.complete(400,480,1,24)||GuardianPhases.complete(10,480,3,24))throw new AssertionError("Phase transitions");
        System.out.println("Guardian: all three health phases and no-skipping checks passed");
    }
}
