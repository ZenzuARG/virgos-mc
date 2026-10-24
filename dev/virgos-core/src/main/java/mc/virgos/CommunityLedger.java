package mc.virgos;

import com.google.gson.JsonObject;
import com.google.gson.JsonElement;
import java.util.*;

/** Validated immutable transition plans for donation recovery. No game APIs. */
public final class CommunityLedger {
    public record Rule(String item,int total,int batch,int personalLimit){}
    public static final Map<String,Rule> RULES;
    static {
        var rules=new LinkedHashMap<String,Rule>();
        rules.put("cocina",new Rule("minecraft:wheat",192,32,64));
        rules.put("taller",new Rule("create:andesite_alloy",192,32,64));
        rules.put("caminos",new Rule("create:track",384,64,128));
        RULES=Collections.unmodifiableMap(rules);
    }
    private static int integer(JsonElement value,int maximum) {
        if(value==null||!value.isJsonPrimitive()||!value.getAsJsonPrimitive().isNumber()||!value.getAsString().matches("0|[1-9][0-9]*"))throw new IllegalArgumentException("Invalid contribution number");
        long n=value.getAsLong();if(n>maximum)throw new IllegalArgumentException("Contribution exceeds limit");return (int)n;
    }
    private static void identity(String id){if(!UUID.fromString(id).toString().equals(id))throw new IllegalArgumentException("Invalid identity");}
    public static void validate(JsonObject state) {
        if(integer(state.get("schema"),1)!=1||!state.has("projects")||!state.has("pending"))throw new IllegalArgumentException("Invalid community journal");
        var projects=state.getAsJsonObject("projects");var pending=state.getAsJsonObject("pending");
        if(!RULES.keySet().containsAll(projects.keySet()))throw new IllegalArgumentException("Unknown community project");
        for(var e:projects.entrySet()){
            var rule=RULES.get(e.getKey());int total=0;
            for(var donor:e.getValue().getAsJsonObject().entrySet()){
                identity(donor.getKey());int n=integer(donor.getValue(),rule.personalLimit);
                if(n==0||n%rule.batch!=0)throw new IllegalArgumentException("Invalid donation batch");total+=n;
            }
            if(total>rule.total)throw new IllegalArgumentException("Project total exceeded");
        }
        var occupied=new HashSet<String>();
        for(var e:pending.entrySet()){
            identity(e.getKey());var tx=e.getValue().getAsJsonObject();identity(tx.get("id").getAsString());
            String key=tx.get("project").getAsString();var rule=RULES.get(key);
            if(rule==null||!occupied.add(key))throw new IllegalArgumentException("Invalid pending project");
            int amount=integer(tx.get("amount"),rule.batch);
            if(amount!=rule.batch)throw new IllegalArgumentException("Invalid pending amount");
            var donors=projects.getAsJsonObject(key);int total=0;
            if(donors!=null){for(var value:donors.entrySet())total+=value.getValue().getAsInt();
                if(donors.has(e.getKey())&&donors.get(e.getKey()).getAsInt()+amount>rule.personalLimit)throw new IllegalArgumentException("Pending personal cap exceeded");}
            if(total+amount>rule.total)throw new IllegalArgumentException("Pending project cap exceeded");
        }
    }
    public static JsonObject settle(JsonObject original,String player,String receipt) {
        validate(original);identity(player);
        var next=original.deepCopy();var pending=next.getAsJsonObject("pending");
        if(!pending.has(player))return next;
        var tx=pending.getAsJsonObject(player);
        if(tx.get("id").getAsString().equals(receipt)) {
            String project=tx.get("project").getAsString();
            if(!next.getAsJsonObject("projects").has(project))next.getAsJsonObject("projects").add(project,new JsonObject());
            var donors=next.getAsJsonObject("projects").getAsJsonObject(project);
            donors.addProperty(player,(donors.has(player)?donors.get(player).getAsInt():0)+tx.get("amount").getAsInt());
        }
        pending.remove(player);validate(next);return next;
    }
}
