package mc.virgos;

import java.util.List;
import java.util.stream.IntStream;

public final class ClaimMenuPageTest {
    public static void main(String[] args) {
        List<String> offline = IntStream.range(0, 24).mapToObj(i -> "KnownOffline" + i).toList();
        var visible = new java.util.ArrayList<String>();
        for (int i = 0; i < 4; i++) visible.addAll(ClaimMenuPage.of(offline, i).rows());
        if (!visible.equals(offline)) throw new AssertionError("Every offline player remains reachable after page one");
        if (ClaimMenuPage.of(offline, -3).index() != 0 || ClaimMenuPage.of(offline, 99).index() != 3)
            throw new AssertionError("Page requests must clamp safely");
        if (!ClaimMenuPage.of(List.of(), 5).rows().isEmpty() || ClaimMenuPage.of(List.of(), 5).index() != 0)
            throw new AssertionError("Empty selection remains usable");
        try { ClaimMenuPage.of(offline, 0).rows().clear(); throw new AssertionError("Pages must be immutable"); }
        catch (UnsupportedOperationException expected) { }
        System.out.println("Claim menu pages: all players, clamping and immutable snapshots PASS");
    }
}
