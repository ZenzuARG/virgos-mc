package mc.virgos;
/** Shared by the live damage event and deterministic phase-boundary checks. */
public final class GuardianPhases {
    public static float floor(float maximum,int round){return round>=3?0:maximum*(3-round)/3f;}
    public static float limit(float health,float maximum,int round,float damage){return round>=3?damage:Math.min(damage,Math.max(0,health-floor(maximum,round)));}
    public static boolean complete(float health,float maximum,int round,float damage){return round<3&&health-damage<=floor(maximum,round)+.01f;}
}
