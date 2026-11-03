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
        if(!policy.warningDue(180_000,0,1,true,false))throw new AssertionError("Warn before idle restart");
        if(policy.warningDue(180_000,0,1,true,true))throw new AssertionError("Warn only once");
        if(policy.warningDue(180_000,0,0,true,false))throw new AssertionError("No warning after empty");
        System.out.println("Maintenance: nine scheduling checks passed");
    }
}
