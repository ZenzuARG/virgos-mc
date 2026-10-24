package mc.virgos;

import com.google.gson.*;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import net.minecraft.commands.*;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.TagParser;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.*;
import net.minecraft.world.item.*;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraftforge.registries.ForgeRegistries;
import java.nio.file.*;

/** Eight physical player shops. Reservations precede creation and survive moving a shop. */
public final class TownServices {
    private MinecraftServer server;
    private JsonObject config, reservations;
    private Path file;
    private boolean ready;
    public void initialize(MinecraftServer value) {
        server=value;ready=false;
        try {
            config=JsonParser.parseString(Files.readString(Path.of("config/virgos/services.json"))).getAsJsonObject();
            file=server.getWorldPath(LevelResource.ROOT).resolve("virgos-market.json");
            reservations=Files.exists(file)?JsonParser.parseString(Files.readString(file)).getAsJsonObject():new JsonObject();
            var used=new java.util.HashSet<Integer>();
            for(var entry:reservations.entrySet()) {
                java.util.UUID.fromString(entry.getKey());int id=entry.getValue().getAsInt();
                if(id<1||id>8||!used.add(id))throw new IllegalStateException("Invalid market reservation");
            }
            ready=true;
        }catch(Exception e){VirgosCore.LOG.error("Town services unavailable; reservations locked",e);}
    }
    private void reserve(String uuid,int id) throws Exception {
        var next=reservations.deepCopy();next.addProperty(uuid,id);
        var tmp=file.resolveSibling(file.getFileName()+".tmp");Files.writeString(tmp,VirgosCore.JSON.toJson(next));
        try(var channel=java.nio.channels.FileChannel.open(tmp,StandardOpenOption.WRITE)){channel.force(true);}
        Files.move(tmp,file,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);reservations=next;
    }
    public LiteralArgumentBuilder<CommandSourceStack> commands() {
        return Commands.literal("mercado").executes(c->PlayerGuide.show(c.getSource(),"mercado"))
            .then(Commands.literal("reservar").then(Commands.argument("puesto",IntegerArgumentType.integer(1,8))
                .executes(c->claim(c.getSource(),IntegerArgumentType.getInteger(c,"puesto")))));
    }
    public LiteralArgumentBuilder<CommandSourceStack> adminCommands() {
        return Commands.literal("servicios").requires(s->s.hasPermission(2))
            .then(Commands.literal("instalar").executes(c->install(c.getSource())));
    }
    private int claim(CommandSourceStack source,int id) {
        ServerPlayer p=source.getPlayer();if(p==null||!VirgosCore.AUTH.authenticated(p)||!ready)return 0;
        try {
            var a=config.getAsJsonArray("stalls").get(id-1).getAsJsonArray();
            var pos=new BlockPos(a.get(0).getAsInt(),a.get(1).getAsInt(),a.get(2).getAsInt());
            if(p.serverLevel()!=server.overworld()||p.distanceToSqr(pos.getX()+.5,pos.getY(),pos.getZ()+.5)>36) {
                source.sendFailure(Component.literal("Acercate al puesto "+id+" del mercado: "+pos.toShortString()+"."));return 0;
            }
            String uuid=p.getUUID().toString();
            if(reservations.has(uuid)&&reservations.get(uuid).getAsInt()!=id) {
                source.sendFailure(Component.literal("Ya reservaste el puesto "+reservations.get(uuid)+". Un puesto por persona."));return 0;
            }
            for(var entry:reservations.entrySet())if(!entry.getKey().equals(uuid)&&entry.getValue().getAsInt()==id) {
                source.sendFailure(Component.literal("Este puesto ya está reservado."));return 0;
            }
            var be=server.overworld().getBlockEntity(pos);
            if(be==null||!ForgeRegistries.BLOCKS.getKey(be.getBlockState().getBlock()).toString().equals("lightmanscurrency:shelf_oak"))
                throw new IllegalStateException("Shop missing; request administrator restoration");
            var trader=be.getClass().getMethod("getTraderData").invoke(be);
            if(trader!=null) {
                Object owner=trader.getClass().getMethod("getOwner").invoke(trader);
                if(!(Boolean)owner.getClass().getMethod("isMember",Player.class).invoke(owner,p)) {
                    source.sendFailure(Component.literal("El puesto tiene otro propietario; no se modificó."));return 0;
                }
            }
            if(!reservations.has(uuid))reserve(uuid,id);
            if(trader==null) {
                be.getClass().getMethod("initialize",Player.class,ItemStack.class).invoke(be,p,new ItemStack(be.getBlockState().getBlock()));
                trader=be.getClass().getMethod("getTraderData").invoke(be);
                var direction=Class.forName("io.github.lightman314.lightmanscurrency.api.traders.trade.TradeDirection");
                for(Object trade:(java.util.List<?>)trader.getClass().getMethod("getTradeData").invoke(trader))
                    trade.getClass().getMethod("setTradeType",direction).invoke(trade,direction.getField("BARTER").get(null));
                trader.getClass().getMethod("markTradesDirty").invoke(trader);
            }
            server.saveEverything(false,true,true);
            source.sendSuccess(()->Component.literal("§aPuesto "+id+" reservado. Clic derecho para abrirlo; usá su almacén para configurar TRUEQUE y depositar mercadería. /virgos guia mercado"),false);
            return 1;
        }catch(Exception e){VirgosCore.LOG.error("Market reservation could not finish",e);source.sendFailure(Component.literal("No se pudo preparar el puesto. La reserva se conserva; avisá al administrador."));return 0;}
    }
    private int install(CommandSourceStack source) {
        if(!ready)return 0;
        try {
            int created=0;
            for(var element:config.getAsJsonArray("npcs")) {
                var data=TagParser.parseTag(element.getAsString());
                var pos=data.getList("Pos",6);
                server.overworld().getChunk(new BlockPos((int)pos.getDouble(0),(int)pos.getDouble(1),(int)pos.getDouble(2)));
                if(server.overworld().getEntity(data.getUUID("UUID"))!=null)continue;
                var entity=EntityType.loadEntityRecursive(data,server.overworld(),e->e);
                if(entity==null||!server.overworld().addFreshEntity(entity))throw new IllegalStateException("NPC creation failed");
                created++;
            }
            server.saveEverything(false,true,true);final int count=created;
            source.sendSuccess(()->Component.literal("Servicios: "+count+" NPC creados; los existentes se conservaron."),true);return 1;
        }catch(Exception e){VirgosCore.LOG.error("NPC installation failed",e);return 0;}
    }
    public static int menu(CommandSourceStack source) {
        var p=source.getPlayer();if(p==null||!VirgosCore.AUTH.authenticated(p))return 0;
        String[] topics={"inicio","progreso","bases","mercado","encargos","fotografia","navegacion","musica","expediciones"};
        Item[] items={Items.BOOK,Items.COMPASS,Items.OAK_DOOR,Items.EMERALD,Items.PAPER,Items.SPYGLASS,Items.OAK_BOAT,Items.NOTE_BLOCK,Items.IRON_SWORD};
        String[] labels={"Primeros pasos","Mi progreso","Proteger mi base","Mercado y trueque","Encargos sin apuro","Fotografía","Viajes en barco","Música en grupo","Expediciones cooperativas"};
        p.openMenu(new SimpleMenuProvider((id,inventory,player)->{
            var icons=new SimpleContainer(27);
            for(int i=0;i<topics.length;i++){var item=new ItemStack(items[i]);item.setHoverName(Component.literal("§6"+labels[i]));icons.setItem(9+i,item);}
            return new ChestMenu(MenuType.GENERIC_9x3,id,inventory,icons,3) {
                @Override public void clicked(int slot,int button,ClickType click,Player actor) {
                    if(actor!=p||!VirgosCore.AUTH.authenticated(p))return;
                    if(click==ClickType.PICKUP&&button==0&&slot>=9&&slot<18){p.closeContainer();PlayerGuide.show(p.createCommandSourceStack(),topics[slot-9]);}
                }
                @Override public ItemStack quickMoveStack(Player actor,int slot){return ItemStack.EMPTY;}
                @Override public boolean stillValid(Player actor){return actor==p&&VirgosCore.AUTH.authenticated(p);}
            };
        },Component.literal("Virgos · Pueblo y aventuras")));return 1;
    }
}
