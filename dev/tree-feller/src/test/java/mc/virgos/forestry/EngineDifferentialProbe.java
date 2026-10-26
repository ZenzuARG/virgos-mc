package mc.virgos.forestry;

import com.thizthizzydizzy.treefeller.Option;
import java.util.ArrayList;
import java.util.HashMap;
import org.bukkit.block.Block;

/** Runs unchanged against both original and patched JARs. */
public final class EngineDifferentialProbe {
    public static void main(String[] args) {
        Option.REQUIRED_LOGS.globalValue = Option.REQUIRED_LOGS.load(4);
        Option.LEAF_BREAK_RANGE.globalValue = Option.LEAF_BREAK_RANGE.load(6);
        Option.PLAYER_LEAVES.globalValue = Option.PLAYER_LEAVES.load(false);
        Option.IGNORE_LEAF_DATA.globalValue = Option.IGNORE_LEAF_DATA.load(false);
        Option.MAX_LOGS.globalValue = Option.MAX_LOGS.load(250);
        System.out.println("required-logs=" + Option.REQUIRED_LOGS.globalValue);
        System.out.println("leaf-range=" + Option.LEAF_BREAK_RANGE.globalValue);
        System.out.println("player-leaves=" + Option.PLAYER_LEAVES.globalValue);
        System.out.println("ignore-leaf-data=" + Option.IGNORE_LEAF_DATA.globalValue);
        HashMap<Integer, ArrayList<Block>> logs = new HashMap<>();
        logs.put(0, new ArrayList<>(java.util.Collections.nCopies(553, (Block)null)));
        System.out.println("configured-250=" + Option.MAX_LOGS.checkTrunk(null, null, null, logs, null).isSuccess());
        Option.MAX_LOGS.globalValue = null;
        System.out.println("configured-null=" + (Option.MAX_LOGS.checkTrunk(null, null, null, logs, null) == null));
    }
}
