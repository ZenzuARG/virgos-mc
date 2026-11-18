package mc.virgos;

import java.util.List;

/** One immutable pagination implementation for members, exceptions and previews. */
public record ClaimMenuPage<T>(int index, int count, List<T> rows) {
    public static <T> ClaimMenuPage<T> of(List<T> all, int requested) {
        int count = Math.max(1, (all.size() + 6) / 7);
        int page = Math.max(0, Math.min(requested, count - 1));
        return new ClaimMenuPage<>(page, count, List.copyOf(all.subList(page * 7, Math.min(all.size(), page * 7 + 7))));
    }
}
