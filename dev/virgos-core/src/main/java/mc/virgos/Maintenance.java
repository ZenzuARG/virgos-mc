package mc.virgos;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import java.nio.file.*;
import java.time.Instant;

/** The wrapper backs up only after Minecraft and all plugin databases have closed. */
public final class Maintenance {
    private MaintenancePolicy policy;
    private boolean enabled,managed,played,requested;
    private long lastBackup,emptySince=-1;
    private MinecraftServer server;
    public void initialize(MinecraftServer server) {
        this.server=server;enabled=false;managed=false;played=false;requested=false;
        try {
            Path config=Path.of("config/virgos/maintenance.json");
            if(!Files.exists(config))return;
            var c=JsonParser.parseString(Files.readString(config)).getAsJsonObject();
            if(c.get("schema").getAsInt()!=1)throw new IllegalArgumentException("Unknown maintenance schema");
            policy=new MaintenancePolicy(c.get("intervalMinutes").getAsLong()*60_000,c.get("idleMinutes").getAsLong()*60_000);
            enabled=c.get("enabled").getAsBoolean();
            Path run=Path.of(".runtime/active-run.json");
            if(Files.exists(run)) {
                var state=JsonParser.parseString(Files.readString(run)).getAsJsonObject();
                managed=state.has("checkpointSupport")&&state.get("checkpointSupport").getAsBoolean()&&!state.has("finished");
            }
            lastBackup=System.currentTimeMillis();
            Path record=Path.of(".runtime/last-backup.json");
            if(Files.exists(record))lastBackup=Instant.parse(JsonParser.parseString(Files.readString(record)).getAsJsonObject().get("completed").getAsString()).toEpochMilli();
            VirgosCore.LOG.info("Virgos: maintenance enabled={}, wrapper support={}",enabled,managed);
        }catch(Exception e){enabled=false;VirgosCore.LOG.error("Virgos: maintenance unavailable",e);}
    }
    public void tick() {
        if(!enabled||!managed||requested)return;
        int players=server.getPlayerCount();long now=System.currentTimeMillis();
        if(players>0){played=true;emptySince=-1;return;}
        if(emptySince<0)emptySince=now;
        if(policy.due(now,lastBackup,emptySince,players,played))request(null);
    }
    public int request(CommandSourceStack source) {
        if(!managed||requested){if(source!=null)source.sendFailure(Component.literal("Iniciá con iniciar.bat o el controlador gestionado para usar el respaldo con reinicio."));return 0;}
        if(server.getPlayerCount()!=0){if(source!=null)source.sendFailure(Component.literal("El respaldo completo espera a que no haya jugadores. No se expulsó a nadie."));return 0;}
        try {
            var record=new JsonObject();record.addProperty("schema",1);record.addProperty("requestedAt",Instant.now().toString());record.addProperty("reason","full-backup");
            record.addProperty("world",server.getWorldData().getLevelName());
            Path temp=Path.of(".runtime/checkpoint-request.json.tmp");Files.writeString(temp,VirgosCore.JSON.toJson(record));
            Files.move(temp,Path.of(".runtime/checkpoint-request.json"),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);
            requested=true;
            VirgosCore.LOG.info("Virgos: empty-server checkpoint requested; clean shutdown, full backup, then restart");
            server.halt(false);return 1;
        }catch(Exception e){VirgosCore.LOG.error("Virgos: checkpoint request failed; server remains online",e);return 0;}
    }
    public String status(){return "respaldoAuto="+(enabled&&managed)+"; respaldoMin="+Math.max(0,(System.currentTimeMillis()-lastBackup)/60_000);}
}
