package mc.virgos.forestry;

import java.util.function.IntUnaryOperator;

/** Vanilla item Unbreaking: independently ignore each damage point with level/(level+1) probability. */
public final class Balance {
    private Balance() {}
    public static int cost(int logs, int unbreaking, IntUnaryOperator random) {
        if (logs < 0 || unbreaking < 0 || unbreaking == Integer.MAX_VALUE) throw new IllegalArgumentException("Invalid durability input");
        int result = 0;
        for (int log = 0; log < logs; log++) if (random.applyAsInt(unbreaking + 1) == 0) result++;
        return result;
    }
}
