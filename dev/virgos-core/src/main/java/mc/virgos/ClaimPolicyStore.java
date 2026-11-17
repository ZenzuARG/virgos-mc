package mc.virgos;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
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
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.UUID;
import java.util.function.Consumer;
import java.util.function.Predicate;

/** Authoritative area policies; the previous permission file is read-only. */
public final class ClaimPolicyStore {
    public record Key(UUID owner, String dimension, int x, int z, String subId) {
        public Key {
            Objects.requireNonNull(owner);
            if (dimension == null || !dimension.matches("[a-z0-9_.-]+:[a-z0-9_./-]+")
                || subId == null || subId.isBlank() || subId.contains("|"))
                throw new IllegalArgumentException("Invalid parcel identity");
        }
        public String encoded() { return "parcel|" + owner + "|" + dimension + "|" + x + "|" + z + "|" + subId; }
        public String legacy() { return owner + ":" + subId; }
        public static Key decode(String raw) {
            String[] parts = raw.split("\\|", -1);
            if (parts.length != 6 || !parts[0].equals("parcel")) throw new IllegalArgumentException("Invalid parcel key");
            Key key = new Key(UUID.fromString(parts[1]), parts[2], Integer.parseInt(parts[3]), Integer.parseInt(parts[4]), parts[5]);
            if (!key.encoded().equals(raw)) throw new IllegalArgumentException("Noncanonical parcel key");
            return key;
        }
    }
    @FunctionalInterface public interface AtomicWriter { void write(Path path, String content) throws IOException; }
    private static final Gson JSON = new Gson();
    private final AtomicWriter writer;
    private volatile JsonObject document = empty(), legacy = new JsonObject();
    private Path file, legacyFile;
    private String currentHash, legacyHash;
    private volatile boolean healthy;
    private Exception failure;

    public ClaimPolicyStore() { this(ClaimPolicyStore::replace); }
    public ClaimPolicyStore(AtomicWriter writer) { this.writer = Objects.requireNonNull(writer); }
    public synchronized boolean load(Path current, Path old) {
        file = current;
        legacyFile = old;
        try {
            if (current.toAbsolutePath().normalize().equals(old.toAbsolutePath().normalize()))
                throw new IllegalArgumentException("Legacy and current files must be distinct");
            JsonObject next = Files.exists(current) ? parse(current) : empty();
            JsonObject defaults = Files.exists(old) ? parse(old) : new JsonObject();
            validate(next);
            for (var entry : defaults.entrySet()) {
                boolean record = entry.getValue().isJsonObject() && (entry.getValue().getAsJsonObject().has("groups")
                    || entry.getValue().getAsJsonObject().has("individuals"));
                if (!record && !entry.getKey().matches("[0-9a-fA-F-]{36}:.*")) continue;
                int separator = entry.getKey().indexOf(':');
                if (separator < 0) throw new IllegalArgumentException("Invalid legacy key");
                String owner = entry.getKey().substring(0, separator);
                if (!UUID.fromString(owner).toString().equalsIgnoreCase(owner)) throw new IllegalArgumentException("Invalid legacy owner");
                ClaimPolicyRules.validate(ClaimPolicyRules.requiredObject(entry.getValue()));
            }
            currentHash = hash(current);
            legacyHash = hash(old);
            document = next;
            legacy = defaults;
            healthy = true;
            failure = null;
            return true;
        } catch (Exception invalid) {
            healthy = false;
            failure = invalid;
            return false;
        }
    }
    public boolean healthy() { return healthy; }
    public Exception failure() { return failure; }
    public JsonObject snapshot() { return document.deepCopy(); }
    public JsonObject policy(Key key) {
        if (!healthy) return null;
        JsonObject value = policy(document, key);
        return value == null ? null : value.deepCopy();
    }
    public String areaId(Key key) {
        var value = document.getAsJsonObject("parcels").get(key.encoded());
        return value == null ? key.encoded() : value.getAsString();
    }
    public List<Key> areaMembers(Key key) {
        if (!document.getAsJsonObject("parcels").has(key.encoded())) return List.of(key);
        String id = areaId(key);
        List<Key> members = new ArrayList<>();
        document.getAsJsonObject("parcels").entrySet().forEach(entry -> {
            if (id.equals(entry.getValue().getAsString())) members.add(Key.decode(entry.getKey()));
        });
        return List.copyOf(members);
    }
    public boolean edit(Key key, Consumer<JsonObject> change) {
        return commit(next -> {
            JsonObject area = next.getAsJsonObject("areas").getAsJsonObject(ensureArea(next, key));
            if (!area.has("policy")) {
                area.remove("nativePolicy");
                area.add("policy", new JsonObject());
            }
            change.accept(area.getAsJsonObject("policy"));
        });
    }
    public boolean join(Key first, Key second, boolean keepFirst, Predicate<Key> owned) {
        if (!healthy || !first.owner().equals(second.owner()) || !first.dimension().equals(second.dimension())) return false;
        return commit(next -> {
            if (!owned.test(first) || !owned.test(second)) throw new IllegalStateException("Ownership changed");
            List<Key> members = new ArrayList<>(areaMembers(first));
            for (Key key : areaMembers(second)) if (!members.contains(key)) members.add(key);
            List<Key> live = members.stream().filter(owned).toList();
            String area = ensureArea(next, keepFirst ? first : second);
            for (Key key : live) next.getAsJsonObject("parcels").addProperty(key.encoded(), area);
        });
    }
    public boolean split(Key key) {
        return commit(next -> {
            JsonObject source = policy(next, key);
            String id = createArea(next, key, source == null ? null : source.deepCopy());
            next.getAsJsonObject("parcels").addProperty(key.encoded(), id);
        });
    }
    private synchronized boolean commit(Consumer<JsonObject> change) {
        if (!healthy) return false;
        try {
            if (!Objects.equals(currentHash, hash(file)) || !Objects.equals(legacyHash, hash(legacyFile))) {
                healthy = false;
                throw new IOException("Permission files changed outside the policy store");
            }
            JsonObject next = document.deepCopy();
            change.accept(next);
            validate(next);
            String content = JSON.toJson(next);
            String nextHash = digest(content.getBytes(StandardCharsets.UTF_8));
            writer.write(file, content);
            currentHash = nextHash;
            document = next;
            failure = null;
            return true;
        } catch (Exception rejected) {
            failure = rejected;
            return false;
        }
    }
    private JsonObject policy(JsonObject doc, Key key) {
        var binding = doc.getAsJsonObject("parcels").get(key.encoded());
        if (binding != null) return doc.getAsJsonObject("areas").getAsJsonObject(binding.getAsString()).getAsJsonObject("policy");
        var fallback = legacy.get(key.legacy());
        return fallback == null ? null : fallback.getAsJsonObject();
    }
    private String ensureArea(JsonObject next, Key key) {
        var binding = next.getAsJsonObject("parcels").get(key.encoded());
        if (binding != null) return binding.getAsString();
        JsonObject old = policy(next, key);
        String id = createArea(next, key, old == null ? null : old.deepCopy());
        next.getAsJsonObject("parcels").addProperty(key.encoded(), id);
        return id;
    }
    private static String createArea(JsonObject next, Key key, JsonObject policy) {
        String id = UUID.randomUUID().toString();
        JsonObject area = new JsonObject();
        area.addProperty("owner", key.owner().toString());
        area.addProperty("dimension", key.dimension());
        if (policy == null) area.addProperty("nativePolicy", true);
        else area.add("policy", policy);
        next.getAsJsonObject("areas").add(id, area);
        return id;
    }
    private static JsonObject empty() {
        JsonObject root = new JsonObject();
        root.addProperty("schema", 2);
        root.add("areas", new JsonObject());
        root.add("parcels", new JsonObject());
        return root;
    }
    private static JsonObject parse(Path path) throws IOException {
        return ClaimPolicyRules.requiredObject(JsonParser.parseString(Files.readString(path, StandardCharsets.UTF_8)));
    }
    private static void validate(JsonObject root) {
        if (!root.has("schema") || !root.get("schema").isJsonPrimitive()
            || !root.get("schema").getAsJsonPrimitive().isNumber() || !root.get("schema").getAsString().equals("2"))
            throw new IllegalArgumentException("Unsupported policy schema");
        JsonObject areas = ClaimPolicyRules.requiredObject(root.get("areas"));
        JsonObject parcels = ClaimPolicyRules.requiredObject(root.get("parcels"));
        for (var entry : areas.entrySet()) {
            UUID.fromString(entry.getKey());
            JsonObject area = ClaimPolicyRules.requiredObject(entry.getValue());
            ClaimPolicyRules.uuid(area.get("owner"));
            String dimension = ClaimPolicyRules.text(area.get("dimension"));
            if (!dimension.matches("[a-z0-9_.-]+:[a-z0-9_./-]+")) throw new IllegalArgumentException("Invalid area dimension");
            if (area.has("nativePolicy")) {
                var nativePolicy = area.get("nativePolicy");
                if (area.has("policy") || !nativePolicy.isJsonPrimitive()
                    || !nativePolicy.getAsJsonPrimitive().isBoolean() || !nativePolicy.getAsBoolean())
                    throw new IllegalArgumentException("Invalid native-only area policy");
            } else ClaimPolicyRules.validate(ClaimPolicyRules.requiredObject(area.get("policy")));
        }
        for (var entry : parcels.entrySet()) {
            Key key = Key.decode(entry.getKey());
            String id = ClaimPolicyRules.text(entry.getValue());
            JsonObject area = areas.has(id) ? areas.getAsJsonObject(id) : null;
            if (area == null || !key.owner().toString().equals(area.get("owner").getAsString())
                || !key.dimension().equals(area.get("dimension").getAsString()))
                throw new IllegalArgumentException("Invalid parcel area binding");
        }
    }
    private static String hash(Path path) throws IOException {
        return Files.exists(path) ? digest(Files.readAllBytes(path)) : null;
    }
    private static String digest(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
    }
    private static void replace(Path file, String content) throws IOException {
        Path parent = file.toAbsolutePath().getParent();
        Files.createDirectories(parent);
        Path temporary = Files.createTempFile(parent, file.getFileName() + ".", ".tmp");
        boolean committed = false;
        try {
            try (FileChannel channel = FileChannel.open(temporary, StandardOpenOption.WRITE)) {
                ByteBuffer bytes = StandardCharsets.UTF_8.encode(content);
                while (bytes.hasRemaining()) channel.write(bytes);
                channel.force(true);
            }
            Files.move(temporary, file, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            committed = true;
        } finally {
            if (!committed) Files.deleteIfExists(temporary);
        }
    }
}
