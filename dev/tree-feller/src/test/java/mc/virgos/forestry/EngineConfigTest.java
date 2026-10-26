package mc.virgos.forestry;

import com.thizthizzydizzy.treefeller.Option;
import java.util.ArrayList;
import java.util.HashMap;
import org.bukkit.block.Block;

public final class EngineConfigTest {
    public static void main(String[] args) {
        Forestry.configure(null);
        if (Option.MAX_LOGS.globalValue != null || Option.COOLDOWN.globalValue != null) throw new AssertionError("no arbitrary cap/cooldown");
        HashMap<Integer, ArrayList<Block>> blocks = new HashMap<>();
        blocks.put(0, new ArrayList<>(java.util.Collections.nCopies(553, (Block)null)));
        if (Option.MAX_LOGS.checkTrunk(null, null, null, blocks, null) != null) throw new AssertionError("null disables limit");
        Option.MAX_LOGS.globalValue = 0;
        if (Option.MAX_LOGS.checkTrunk(null, null, null, blocks, null).isSuccess()) throw new AssertionError("zero must not mean unlimited");
        Forestry.configure(null);
        if (Option.CASCADE.globalValue || Option.CUTTING_ANIMATION.globalValue || Option.SEND_BLOCK_BREAK_EVENTS.globalValue) throw new AssertionError("unsafe mode");
        if (!Option.DAMAGE_MULT.globalValue.equals(1d) || !Option.RESPECT_UNBREAKING.globalValue) throw new AssertionError("balanced cost");
        NativeGuard guard = new NativeGuard();
        if (guard.breaking(null, null, null) || guard.placing(null, null, null)) throw new AssertionError("missing native bridge fails closed");
        System.out.println("EngineConfig PASS: null cap, no cascade/synthetic events, balanced damage, absent bridge DENY");
    }
}
