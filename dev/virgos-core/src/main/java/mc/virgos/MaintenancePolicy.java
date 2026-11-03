package mc.virgos;

/** Pure scheduling rule. Active players always prevent an automatic restart. */
public record MaintenancePolicy(long intervalMillis,long idleMillis) {
    public MaintenancePolicy {
        if(intervalMillis<60_000||idleMillis<30_000)throw new IllegalArgumentException("Unsafe maintenance interval");
    }
    public boolean due(long now,long lastBackup,long emptySince,int players,boolean activitySinceBackup) {
        return players==0&&activitySinceBackup&&emptySince>=0&&now>=emptySince&&now>=lastBackup
            &&now-emptySince>=idleMillis&&now-lastBackup>=intervalMillis;
    }
    public boolean warningDue(long now,long lastBackup,int players,boolean activitySinceBackup,boolean alreadyWarned) {
        return players>0&&activitySinceBackup&&!alreadyWarned&&now>=lastBackup&&now-lastBackup>=intervalMillis;
    }
}
