package mc.virgos;
import com.google.gson.*;
import java.util.UUID;
public final class CommunityLedgerTest {
    private static final String PLAYER=UUID.randomUUID().toString(), RECEIPT=UUID.randomUUID().toString();
    private static JsonObject pending(){
        return JsonParser.parseString("{\"schema\":1,\"projects\":{\"cocina\":{}},\"pending\":{\""+PLAYER+"\":{\"id\":\""+RECEIPT+"\",\"project\":\"cocina\",\"amount\":32}}}").getAsJsonObject();
    }
    private static void require(boolean result,String message){if(!result)throw new AssertionError(message);}
    private static void reject(JsonObject state){try{CommunityLedger.validate(state);throw new AssertionError("Corrupt journal accepted");}catch(IllegalArgumentException expected){}}
    public static void main(String[] args){
        var before=pending();CommunityLedger.validate(before);
        var committed=CommunityLedger.settle(before,PLAYER,RECEIPT);
        require(committed.getAsJsonObject("projects").getAsJsonObject("cocina").get(PLAYER).getAsInt()==32,"Saved inventory credited");
        require(before.getAsJsonObject("pending").has(PLAYER),"Plan leaves original intact if persistence fails");
        require(CommunityLedger.settle(committed,PLAYER,RECEIPT).equals(committed),"Recovery is idempotent");
        var uncommitted=CommunityLedger.settle(before,PLAYER,"");
        require(uncommitted.getAsJsonObject("projects").getAsJsonObject("cocina").size()==0,"Unsaved inventory not credited");
        require(uncommitted.getAsJsonObject("pending").size()==0,"Uncommitted checkpoint cleared");
        var corrupt=pending();corrupt.getAsJsonObject("pending").getAsJsonObject(PLAYER).addProperty("amount",-1);reject(corrupt);
        corrupt=pending();corrupt.getAsJsonObject("pending").getAsJsonObject(PLAYER).addProperty("amount",31.5);reject(corrupt);
        corrupt=pending();corrupt.getAsJsonObject("pending").getAsJsonObject(PLAYER).addProperty("project","unknown");reject(corrupt);
        corrupt=pending();corrupt.getAsJsonObject("projects").getAsJsonObject("cocina").addProperty(PLAYER,64);reject(corrupt);
        corrupt=pending();corrupt.getAsJsonObject("projects").getAsJsonObject("cocina").addProperty("not-a-uuid",32);reject(corrupt);
        corrupt=pending();corrupt.getAsJsonObject("pending").add(UUID.randomUUID().toString(),corrupt.getAsJsonObject("pending").get(PLAYER).deepCopy());reject(corrupt);
        System.out.println("Community ledger: saved/unsaved recovery, idempotence, write failure isolation and six corrupt inputs passed");
    }
}
