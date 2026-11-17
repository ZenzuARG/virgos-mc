package mc.virgos;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.util.UUID;

public final class ClaimPolicyRulesTest {
    public static void main(String[] args) {
        UUID player = UUID.randomUUID();
        JsonObject policy = JsonParser.parseString("{\"groups\":{\"familia\":{\"members\":[{\"id\":\"" + player
            + "\"}],\"permissions\":{\"building\":true,\"storage\":true}},\"amigos\":{\"members\":[{\"id\":\""
            + player + "\"}],\"permissions\":{\"doors\":true}}},\"individuals\":{\"" + player
            + "\":{\"permissions\":{\"storage\":\"DENY\"}}}}").getAsJsonObject();
        ClaimPolicyRules.validate(policy);
        require(ClaimPolicyRules.effective(policy, player, "building").allowed(), "Building grant is independent");
        var storage = ClaimPolicyRules.effective(policy, player, "storage");
        require(!storage.allowed() && storage.source() == ClaimPolicyRules.Source.INDIVIDUAL, "Individual DENY wins over every group's storage grant");
        require(ClaimPolicyRules.effective(policy, player, "doors").allowed(), "Permissions from another group are included");
        require(!ClaimPolicyRules.effective(policy, UUID.randomUUID(), "storage").allowed(), "Unlisted visitors do not gain permissions");
        var decisions = policy.getAsJsonObject("individuals").getAsJsonObject(player.toString()).getAsJsonObject("permissions");
        decisions.remove("storage");
        var inherited = ClaimPolicyRules.effective(policy, player, "storage");
        require(inherited.allowed() && inherited.source() == ClaimPolicyRules.Source.GROUPS && inherited.groups().contains("familia"), "Inheritance and preview provenance use the same calculation");
        decisions.addProperty("machines", "ALLOW");
        require(ClaimPolicyRules.effective(policy, player, "machines").allowed(), "Individual ALLOW needs no group grant");
        decisions.addProperty("storage", "invalid");
        try { ClaimPolicyRules.validate(policy); throw new AssertionError("Invalid individual decisions must not load"); }
        catch (IllegalArgumentException expected) { }
        System.out.println("Claim policy rules: group union, independent categories, individual overrides and provenance PASS");
    }
    private static void require(boolean valid, String message) {
        if (!valid) throw new AssertionError(message);
    }
}
