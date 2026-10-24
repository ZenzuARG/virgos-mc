package mc.virgos;
public final class MaintenancePolicyTest {
    public static void main(String[] args){
        var policy=new MaintenancePolicy(120_000,60_000);
        if(!policy.due(180_000,0,100_000,0,true))throw new AssertionError("Due checkpoint");
        if(policy.due(180_000,0,100_000,1,true))throw new AssertionError("Never restart with a player");
        if(policy.due(180_000,0,130_000,0,true))throw new AssertionError("Idle grace period");
        if(policy.due(180_000,100_000,100_000,0,true))throw new AssertionError("Minimum backup interval");
        if(policy.due(180_000,0,100_000,0,false))throw new AssertionError("No endless idle restart loop");
        if(policy.due(10,100_000,100_000,0,true))throw new AssertionError("Clock regression");
        System.out.println("Maintenance: six empty-server scheduling checks passed");
    }
}
