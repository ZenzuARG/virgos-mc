package mc.virgos.forestry;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Collections;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.UUID;

/** Server-thread-confined durable intent, not an inventory of grantable items. */
public final class Journal {
    public record Group(String id, String owner, String world, String material,
                        int unreserved, List<String> pending, List<String> alternatives,
                        boolean selected, int required) {
        public Group(String id, String owner, String world, String material, int unreserved, List<String> pending) {
            this(id, owner, world, material, unreserved, pending, List.of(material), true, Math.max(unreserved, pending.size()));
        }
    }
    private final Path file;
    private final Map<String, String> rows = new TreeMap<>();
    private boolean healthy = true;

    public Journal(Path file) {
        this.file = file;
        try {
            if (Files.exists(file)) {
                String text = Files.readString(file);
                // v1 snapshots had no version prefix. Reading never rewrites or discards their pending intents.
                if (text.startsWith("forestry-journal-v2\n")) text = text.substring("forestry-journal-v2\n".length());
                int newline = text.indexOf('\n');
                if (newline < 0 || !text.substring(0, newline).equals(digest(text.substring(newline + 1)))) {
                    throw new IOException("Invalid forestry journal checksum");
                }
                for (String line : text.substring(newline + 1).split("\n")) {
                    if (line.isEmpty()) continue;
                    String[] pair = line.split("\t", -1);
                    if (pair.length != 2 || rows.put(decode(pair[0]), decode(pair[1])) != null) {
                        throw new IOException("Invalid duplicate journal row");
                    }
                }
                for (String key : rows.keySet()) {
                    if (!key.startsWith("placed:") && !key.startsWith("group:")) throw new IOException("Unknown row");
                    if (key.startsWith("placed:") && !"1".equals(rows.get(key))) throw new IOException("Invalid marker");
                }
                groups(); // Validate every record before exposing healthy state.
            }
        } catch (Exception error) {
            healthy = false;
        }
    }

    public boolean healthy() { return healthy; }
    public boolean knownPlaced(String position) { return rows.containsKey("placed:" + position); }

    public void markPlaced(String position, boolean placed) throws IOException {
        markPlaced(Map.of(position, placed));
    }

    public void markPlaced(Map<String, Boolean> changes) throws IOException {
        requireHealthy();
        Map<String, String> next = new TreeMap<>(rows);
        changes.forEach((position, placed) -> {
            if (placed) next.put("placed:" + position, "1");
            else next.remove("placed:" + position);
        });
        if (!next.equals(rows)) commit(next);
    }

    public String prepare(String owner, String world, String material, List<String> positions) throws IOException {
        return prepareGroup(owner, world, material, positions, List.of(material), true);
    }

    /** v2: retain declared alternatives until the operation's first valid own drop chooses one. */
    public String prepareDeclared(String owner, String world, String fallback, List<String> positions,
                                  List<String> alternatives) throws IOException {
        return prepareGroup(owner, world, fallback, positions, alternatives, false);
    }
    private String prepareGroup(String owner, String world, String material, List<String> positions,
                                List<String> alternatives, boolean selected) throws IOException {
        if (!healthy || positions.isEmpty() || positions.size() != new java.util.HashSet<>(positions).size()
                || alternatives.isEmpty() || !alternatives.contains(material)
                || alternatives.size() != new java.util.HashSet<>(alternatives).size()) return null;
        for (Group existing : groups()) {
            if (existing.world().equals(world) && existing.pending().stream().anyMatch(positions::contains)) return null;
        }
        String id = UUID.randomUUID().toString();
        put(new Group(id, owner, world, material, positions.size(), List.copyOf(positions),
                      List.copyOf(alternatives), selected, positions.size()));
        return id;
    }

    /** Persist the coherent choice/deduction before the caller exposes any remaining drop. */
    public int reserve(String id, String material, int amount) throws IOException {
        requireHealthy();
        Group group = find(id);
        if (group == null || amount <= 0 || !group.alternatives().contains(material)
                || (group.selected() && !group.material().equals(material))) return 0;
        int used = Math.min(amount, group.unreserved());
        if (used > 0) put(new Group(id, group.owner(), group.world(), material,
            group.unreserved() - used, group.pending(), group.alternatives(), true, group.required()));
        return used;
    }

    /** End-of-loot or restart fallback: select the declared minimum without granting an item. */
    public void seal(String id) throws IOException {
        requireHealthy();
        Group group = find(id);
        if (group != null && !group.selected()) put(new Group(id, group.owner(), group.world(), group.material(),
            group.unreserved(), group.pending(), group.alternatives(), true, group.required()));
    }

    /** Already-present correct saplings count as completion, never as an item grant. */
    public void complete(String id, String position) throws IOException {
        requireHealthy();
        Group group = find(id);
        if (group == null || !group.pending().contains(position)) return;
        List<String> pending = new ArrayList<>(group.pending());
        pending.remove(position);
        Map<String, String> next = new TreeMap<>(rows);
        if (pending.isEmpty()) next.remove("group:" + id);
        else next.put("group:" + id, value(new Group(id, group.owner(), group.world(), group.material(),
                                                   group.unreserved(), pending, group.alternatives(), group.selected(), group.required())));
        commit(next);
    }

    public List<Group> groups() {
        List<Group> result = new ArrayList<>();
        for (Map.Entry<String, String> entry : rows.entrySet()) {
            if (!entry.getKey().startsWith("group:")) continue;
            String[] parts = entry.getValue().split(";", -1);
            if (parts.length != 5 && parts.length != 9) throw new IllegalStateException("Invalid group version");
            List<String> pending = List.of(parts[4].split("/", -1));
            int remaining = Integer.parseInt(parts[3]);
            List<String> alternatives = parts.length == 5 ? List.of(parts[2]) : List.of(parts[5].split(",", -1));
            if (parts.length == 9 && !parts[8].equals("2")) throw new IllegalStateException("Unknown group schema");
            boolean selected = parts.length == 5 || parts[6].equals("1");
            if (parts.length == 9 && !(parts[6].equals("0") || parts[6].equals("1"))) throw new IllegalStateException("Invalid selection");
            int required = parts.length == 5 ? Math.max(remaining, pending.size()) : Integer.parseInt(parts[7]);
            if (remaining < 0 || required < 1 || remaining > required || pending.isEmpty() || pending.size() > required
                    || alternatives.isEmpty() || !alternatives.contains(parts[2])
                    || alternatives.size() != new java.util.HashSet<>(alternatives).size()) {
                throw new IllegalStateException("Invalid reservation");
            }
            for (String position : pending) {
                if (!position.matches("-?[0-9]+,-?[0-9]+,-?[0-9]+")) throw new IllegalStateException("Invalid position");
            }
            result.add(new Group(entry.getKey().substring(6), parts[0], parts[1], parts[2], remaining, pending, alternatives, selected, required));
        }
        return Collections.unmodifiableList(result);
    }

    private Group find(String id) {
        return groups().stream().filter(group -> group.id().equals(id)).findFirst().orElse(null);
    }
    private void put(Group group) throws IOException {
        Map<String, String> next = new TreeMap<>(rows);
        next.put("group:" + group.id(), value(group));
        commit(next);
    }
    private static String value(Group group) {
        List<String> fields = new ArrayList<>(group.alternatives());
        fields.addAll(List.of(group.owner(), group.world(), group.material()));
        for (String field : fields) {
            if (field.isBlank() || field.contains(";") || field.contains(",") || field.contains("\n")) throw new IllegalArgumentException("Invalid field");
        }
        return String.join(";", group.owner(), group.world(), group.material(),
                           Integer.toString(group.unreserved()), String.join("/", group.pending()),
                           String.join(",", group.alternatives()), group.selected() ? "1" : "0", Integer.toString(group.required()), "2");
    }
    private void requireHealthy() throws IOException {
        if (!healthy) throw new IOException("Forestry persistence unavailable; refusing mutation");
    }
    private void commit(Map<String, String> next) throws IOException {
        requireHealthy();
        StringBuilder body = new StringBuilder();
        next.forEach((key, value) -> body.append(encode(key)).append('\t').append(encode(value)).append('\n'));
        byte[] bytes = ("forestry-journal-v2\n" + digest(body.toString()) + "\n" + body).getBytes(StandardCharsets.UTF_8);
        Path temporary = file.resolveSibling(file.getFileName() + ".pending");
        try {
            Files.createDirectories(file.toAbsolutePath().getParent());
            try (FileChannel channel = FileChannel.open(temporary, StandardOpenOption.CREATE,
                    StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.WRITE)) {
                ByteBuffer buffer = ByteBuffer.wrap(bytes);
                while (buffer.hasRemaining()) channel.write(buffer);
                channel.force(true);
            }
            // Do not degrade to a non-atomic overwrite on an unsupported filesystem.
            Files.move(temporary, file, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            rows.clear();
            rows.putAll(next);
        } catch (IOException error) {
            healthy = false;
            throw error;
        }
    }
    private static String encode(String value) {
        return Base64.getUrlEncoder().withoutPadding().encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }
    private static String decode(String value) {
        return new String(Base64.getUrlDecoder().decode(value), StandardCharsets.UTF_8);
    }
    private static String digest(String value) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8)));
        } catch (java.security.NoSuchAlgorithmException impossible) {
            throw new AssertionError(impossible);
        }
    }
}
