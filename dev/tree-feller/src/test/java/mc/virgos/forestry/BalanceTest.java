package mc.virgos.forestry;

public final class BalanceTest {
    public static void main(String[] args) {
        if (Balance.cost(123, 0, bound -> 0) != 123) throw new AssertionError("one damage per log");
        if (Balance.cost(123, 3, bound -> 1) != 0) throw new AssertionError("Unbreaking may prevent every point");
        final int[] calls = {0};
        int result = Balance.cost(8, 3, bound -> { if (bound != 4) throw new AssertionError("vanilla denominator"); return calls[0]++ % bound; });
        if (result != 2 || calls[0] != 8) throw new AssertionError("independent per-log rolls");
        System.out.println("Balance PASS: per-log damage and vanilla Unbreaking");
    }
}
