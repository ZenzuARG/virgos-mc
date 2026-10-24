package mc.virgos.codex;

import com.mojang.logging.LogUtils;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ScreenEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.client.event.ClientPlayerNetworkEvent;
import net.minecraftforge.fml.common.Mod;
import mc.virgos.update.ClientRelease;
import mc.virgos.update.UpdateProtocol;
import java.lang.reflect.*;
import java.util.*;

@Mod("virgos_codex")
public final class VirgosCodex {
    public VirgosCodex() {
        mc.virgos.profile.ProfileProtocol.register(ProfileScreen::accept);
        UpdateProtocol.register(ignored -> {});
    }
    public static void openCodex(){pendingTree=true;group(savedGroup.isEmpty()?"01 · Empezar":savedGroup);}
    private static final String PREFIX="earth.terrarium.heracles.";
    private static boolean originalOnce;
    private static boolean pendingTree;
    private static String savedGroup="",savedQuery="";
    private static int savedPage, savedFilter;

    @Mod.EventBusSubscriber(modid="virgos_codex",value=Dist.CLIENT,bus=Mod.EventBusSubscriber.Bus.FORGE)
    public static final class Events {
        @SubscribeEvent public static void questBackground(ScreenEvent.Render.Pre event){
            if(event.getScreen().getClass().getName().startsWith(PREFIX+"client.screens.quest."))event.getGuiGraphics().fill(0,0,event.getScreen().width,event.getScreen().height,0xFF17242C);
        }
        @SubscribeEvent public static void opening(ScreenEvent.Opening event) {
            Screen screen=event.getNewScreen();
            if(screen==null || !screen.getClass().getName().equals(PREFIX+"client.screens.quests.QuestsScreen"))return;
            if(originalOnce){originalOnce=false;return;}
            try {
                if(pendingTree){pendingTree=false;event.setNewScreen(new TreeScreen(screen));}
                else event.setNewScreen(new HubScreen(screen));
            }
            catch(Exception error){LogUtils.getLogger().error("Virgos codex: retaining Heracles screen after adapter failure",error);}
        }
        @SubscribeEvent public static void loggingIn(ClientPlayerNetworkEvent.LoggingIn event) {
            UpdateProtocol.CHANNEL.sendToServer(new UpdateProtocol.ClientHello(ClientRelease.RELEASE, ClientRelease.FINGERPRINT));
        }
    }
    private static Object call(Object target,String method)throws Exception{return target.getClass().getMethod(method).invoke(target);}
    private static Object field(Object target,String name)throws Exception{
        for(Class<?> c=target.getClass();c!=null;c=c.getSuperclass()){
            try{Field f=c.getDeclaredField(name);f.setAccessible(true);return f.get(target);}catch(NoSuchFieldException ignored){}
        }
        throw new NoSuchFieldException(name);
    }
    private static void send(String name,Class<?>[] types,Object... values) {
        try {
            Object packet=Class.forName(PREFIX+"common.network.packets."+name).getConstructor(types).newInstance(values);
            Object channel=Class.forName(PREFIX+"common.network.NetworkHandler").getField("CHANNEL").get(null);
            for(Method method:channel.getClass().getMethods())if(method.getName().equals("sendToServer")&&method.getParameterCount()==1&&method.getParameterTypes()[0].isInstance(packet)){method.invoke(channel,packet);return;}
            throw new NoSuchMethodException("sendToServer");
        }catch(Exception error){LogUtils.getLogger().error("Virgos codex request failed",error);}
    }
    private static void group(String name){send("groups.OpenGroupPacket",new Class<?>[]{String.class,boolean.class},name,false);}
    private static void openTree(String name){savedGroup=name;pendingTree=true;group(name);}
    private record Entry(String id,String title,String subtitle,String status,ItemStack icon,int x,int y){}
    private static final class QuestRowButton extends Button {
        QuestRowButton(int x,int y,int width,OnPress action){super(x,y,width,40,Component.empty(),action,DEFAULT_NARRATION);}
        // Text and state are rendered once by the list; keep Button's narration/input.
        @Override public void renderWidget(GuiGraphics graphics,int mouseX,int mouseY,float tick){}
    }
    private static final class RouteButton extends Button {
        RouteButton(int x,int y,int width,int height,OnPress action){super(x,y,width,height,Component.empty(),action,DEFAULT_NARRATION);}
        @Override public void renderWidget(GuiGraphics graphics,int mouseX,int mouseY,float tick){}
    }

    /** A calm landing page: choose a route before opening the dense quest list. */
    private static final class HubScreen extends Screen {
        private final Screen original;
        private final List<String> groups;
        private final Map<String,int[]> progress=new LinkedHashMap<>();
        private final List<Button> routeButtons=new ArrayList<>();
        private int left,top,panelW,panelH,columns,introTicks,routeScroll;

        @SuppressWarnings("unchecked") HubScreen(Screen original)throws Exception {
            super(Component.literal("Códice de Virgos-MC"));this.original=original;
            Object content=field(original,"content");
            groups=List.copyOf((List<String>)Class.forName(PREFIX+"client.handlers.ClientQuests").getMethod("groups").invoke(null));
            Class<?> client=Class.forName(PREFIX+"client.handlers.ClientQuests");
            Map<String,?> statuses=(Map<String,?>)call(content,"quests");
            for(String name:groups)progress.put(name,new int[]{0,0});
            for(var row:statuses.entrySet()){
                Optional<?> found=(Optional<?>)client.getMethod("get",String.class).invoke(null,row.getKey());
                if(found.isEmpty())continue;
                Object display=call(call(found.get(),"value"),"display");
                Map<String,?> locations=(Map<String,?>)call(display,"groups");
                for(String name:groups)if(locations.containsKey(name)){
                    int[] counts=progress.get(name);counts[0]++;
                    if(row.getValue().toString().equals("COMPLETED_CLAIMED"))counts[1]++;
                }
            }
        }
        @Override protected void init(){
            panelW=Math.min(920,width-24);panelH=Math.min(570,height-24);left=(width-panelW)/2;top=(height-panelH)/2;
            columns=panelW>=560?2:1;routeButtons.clear();
            addRenderableWidget(Button.builder(Component.literal("×"),b->onClose()).bounds(left+panelW-27,top+9,18,20).build());
            addRenderableWidget(Button.builder(Component.literal("A+"),b->scale(1)).bounds(left+panelW-79,top+9,24,20).build());
            addRenderableWidget(Button.builder(Component.literal("A−"),b->scale(-1)).bounds(left+panelW-53,top+9,24,20).build());
            int cardW=(panelW-44-(columns-1)*12)/columns, cardH=58;
            for(int i=0;i<groups.size();i++){
                final String name=groups.get(i);int col=i%columns,row=i/columns;
                routeButtons.add(addRenderableWidget(new RouteButton(0,0,cardW,cardH,b->openTree(name))));
            }
            refreshRoutes();
            addRenderableWidget(Button.builder(Component.literal("Ver mapa original"),b->{originalOnce=true;Minecraft.getInstance().setScreen(original);}).bounds(left+16,top+panelH-29,125,20).build());
        }
        private int routeMaxScroll(){int rows=(groups.size()+columns-1)/columns;return Math.max(0,rows*68-(panelH-112));}
        private void refreshRoutes(){int cardW=(panelW-44-(columns-1)*12)/columns,cardH=58,at=0;for(int i=0;i<groups.size();i++){int col=i%columns,row=i/columns;Button b=routeButtons.get(at++);int y=top+72+row*68-routeScroll;b.setX(left+16+col*(cardW+12));b.setY(y);b.setWidth(cardW);b.setHeight(cardH);b.visible=y>=top+72&&y+cardH<=top+panelH-40;b.active=b.visible;}}
        @Override public boolean mouseScrolled(double x,double y,double amount){routeScroll=Math.max(0,Math.min(routeMaxScroll(),routeScroll+(amount<0?58:-58)));refreshRoutes();return true;}
        private void scale(int delta){Minecraft mc=Minecraft.getInstance();int current=(int)mc.getWindow().getGuiScale();int max=mc.getWindow().calculateScale(0,false);mc.options.guiScale().set(Math.max(1,Math.min(max,current+delta)));mc.options.save();mc.resizeDisplay();}
        @Override public void tick(){if(introTicks<16)introTicks++;}
        @Override public void render(GuiGraphics g,int mouseX,int mouseY,float partialTick){
            g.fill(0,0,width,height,0xB3091017);g.fill(left,top,left+panelW,top+panelH,0xFF17242C);g.fill(left,top,left+panelW,top+3,0xFFCCAB70);
            g.drawString(font,"VIRGOS-MC",left+16,top+14,0xEAD8B4,false);g.drawString(font,"Códice de aventuras",left+16,top+31,0xF4F0E7,false);
            g.drawString(font,"Elegí una ruta. Después vas a ver sus pasos, requisitos y recompensas.",left+16,top+48,0xB9C7C5,false);
            int cardW=(panelW-44-(columns-1)*12)/columns,cardH=58;
            for(int i=0;i<groups.size();i++){
                String name=groups.get(i);int col=i%columns,row=i/columns,x=left+16+col*(cardW+12),y=top+72+row*(cardH+10);int[] counts=progress.get(name);int color=counts[1]==counts[0]?0xFF8EC5A4:0xFFEAC576;
                y-=routeScroll;if(y<top+72||y+cardH>top+panelH-40)continue;
                g.fill(x+1,y+1,x+3,y+cardH-1, color);g.drawString(font,name,x+12,y+10,0xF0EEE5,false);
                String status=counts[1]+" / "+counts[0]+" misiones reclamadas";g.drawString(font,status,x+12,y+31,0xA7B8C0,false);
                g.drawString(font,counts[1]==counts[0]?"COMPLETADA":"EN PROGRESO",x+cardW-font.width(counts[1]==counts[0]?"COMPLETADA":"EN PROGRESO")-10,y+10,color,false);
            }
            if(introTicks<16)g.fill(0,0,width,height,Math.max(0,16-introTicks)*0x03000000);
            super.render(g,mouseX,mouseY,partialTick);
            if(routeMaxScroll()>0)g.drawString(font,"Rueda: más rutas",left+panelW-105,top+panelH-24,0xFF9DB7AF);
        }
        @Override public boolean isPauseScreen(){return false;}
    }

    /** A dependency-preserving visual tree. It groups existing quest IDs into readable lanes without changing server unlock rules. */
    private static final class TreeScreen extends Screen {
        private final Screen original; private final String group; private final List<Entry> entries=new ArrayList<>();
        private final List<List<Entry>> branches=new ArrayList<>(); private final List<String> branchNames=new ArrayList<>();
        private final List<Button> nodes=new ArrayList<>(); private int left,top,panelW,panelH,scroll,introTicks;
        @SuppressWarnings("unchecked") TreeScreen(Screen original)throws Exception{
            super(Component.literal("Códice de Virgos-MC"));this.original=original;
            Object content=field(original,"content");group=(String)call(content,"group");
            Class<?> client=Class.forName(PREFIX+"client.handlers.ClientQuests");Map<String,?> statuses=(Map<String,?>)call(content,"quests");
            for(var row:statuses.entrySet()){
                Optional<?> found=(Optional<?>)client.getMethod("get",String.class).invoke(null,row.getKey());if(found.isEmpty())continue;
                Object display=call(call(found.get(),"value"),"display");Map<String,?> locations=(Map<String,?>)call(display,"groups");if(!locations.containsKey(group))continue;
                Object position=call(locations.get(group),"position");ItemStack icon=new ItemStack(Items.BOOK);try{icon=(ItemStack)call(call(call(display,"icon"),"item"),"getDefaultInstance");}catch(ReflectiveOperationException ignored){}
                entries.add(new Entry(row.getKey(),((Component)call(display,"title")).getString(),((Component)call(display,"subtitle")).getString(),row.getValue().toString(),icon,((Number)call(position,"x")).intValue(),((Number)call(position,"y")).intValue()));
            }
            buildBranches();
        }
        private void buildBranches(){
            Map<String,List<Entry>> by=new LinkedHashMap<>();
            if(group.contains("Create")){by.put("Potencia y movimiento",new ArrayList<>());by.put("Procesamiento",new ArrayList<>());by.put("Automatización",new ArrayList<>());}
            else if(group.contains("Magia")){by.put("Iron’s Spellbooks",new ArrayList<>());by.put("Ars Nouveau",new ArrayList<>());by.put("Maestría",new ArrayList<>());}
            for(Entry e:entries){String key;
                if(group.contains("Create")){String id=e.id().toLowerCase(Locale.ROOT);boolean automation=id.contains("precision")||id.contains("ensamble")||id.contains("tren")||id.contains("copias")||id.contains("secuencia")||id.contains("filtro")||id.contains("medidor")||id.contains("gafas")||id.contains("llave")||id.equals("ingeniero");boolean processing=id.contains("prensa")||id.contains("mezcla")||id.contains("laton")||id.contains("aleacion")||id.contains("liquidos")||id.contains("lavado");key=automation?"Automatización":processing?"Procesamiento":"Potencia y movimiento";}
                else if(group.contains("Magia")){String id=e.id().toLowerCase(Locale.ROOT);key=id.contains("iron")||id.contains("hechicer")?"Iron’s Spellbooks":id.contains("ars")||id.contains("arcanista")?"Ars Nouveau":"Maestría";}
                else {int cut=e.id().indexOf('_');key=cut>0?e.id().substring(0,cut):"Ruta principal";}
                by.computeIfAbsent(key,k->new ArrayList<>()).add(e);
            }
            if(!group.contains("Create")&&!group.contains("Magia")&&by.size()>4){
                List<String> keys=new ArrayList<>(by.keySet());Collections.sort(keys);
                Map<String,List<Entry>> trimmed=new LinkedHashMap<>();for(int i=0;i<3;i++)trimmed.put(keys.get(i),new ArrayList<>(by.get(keys.get(i))));
                List<Entry> other=new ArrayList<>();for(int i=3;i<keys.size();i++)other.addAll(by.get(keys.get(i)));trimmed.put("Otros",other);by=trimmed;
            }
            for(var row:by.entrySet()){row.getValue().sort(Comparator.comparingInt(Entry::y).thenComparingInt(Entry::x));if(!row.getValue().isEmpty()){branchNames.add(row.getKey());branches.add(row.getValue());}}
        }
        @Override protected void init(){
            panelW=Math.min(940,width-24);panelH=Math.min(580,height-24);left=(width-panelW)/2;top=(height-panelH)/2;nodes.clear();
            addRenderableWidget(Button.builder(Component.literal("×"),b->onClose()).bounds(left+panelW-27,top+9,18,20).build());
            addRenderableWidget(Button.builder(Component.literal("A+"),b->scale(1)).bounds(left+panelW-79,top+9,24,20).build());
            addRenderableWidget(Button.builder(Component.literal("A−"),b->scale(-1)).bounds(left+panelW-53,top+9,24,20).build());
            addRenderableWidget(Button.builder(Component.literal("Mapa"),b->{try{Minecraft.getInstance().setScreen(new HubScreen(original));}catch(Exception error){LogUtils.getLogger().error("Virgos codex: could not open route map",error);}}).bounds(left+16,top+panelH-29,60,20).build());
            addRenderableWidget(Button.builder(Component.literal("Mapa original"),b->{originalOnce=true;Minecraft.getInstance().setScreen(original);}).bounds(left+82,top+panelH-29,100,20).build());
            for(List<Entry> branch:branches)for(Entry e:branch){final Entry entry=e;nodes.add(addRenderableWidget(new QuestRowButton(0,0,10,b->{remember();send("quests.OpenQuestPacket",new Class<?>[]{String.class,String.class,boolean.class},group,entry.id(),false);})));}
            refreshLayout();
        }
        private void scale(int delta){Minecraft mc=Minecraft.getInstance();int current=(int)mc.getWindow().getGuiScale();int max=mc.getWindow().calculateScale(0,false);mc.options.guiScale().set(Math.max(1,Math.min(max,current+delta)));mc.options.save();mc.resizeDisplay();}
        @Override public void tick(){if(introTicks<16)introTicks++;}
        private void remember(){savedGroup=group;}
        private int treeMaxScroll(){int max=0;for(List<Entry> b:branches)max=Math.max(max,b.size());return Math.max(0,max*45-((panelH-112)-29));}
        private boolean nodeVisible(int y){int headerY=top+62;return y>=headerY+30&&y+40<=headerY+(panelH-112)-4;}
        private void refreshLayout(){int cols=Math.max(1,branches.size()),gap=10,cardW=(panelW-32-gap*(cols-1))/cols,headerY=top+62,nodeH=45;int at=0;for(int col=0;col<branches.size();col++){List<Entry> branch=branches.get(col);for(int i=0;i<branch.size();i++){Button b=nodes.get(at++);int y=headerY+30+i*nodeH-scroll,x=left+16+col*(cardW+gap);boolean visible=nodeVisible(y);b.setX(x+8);b.setY(y);b.setWidth(Math.max(10,cardW-16));b.setHeight(40);b.visible=visible;b.active=visible;}}}
        @Override public boolean mouseScrolled(double x,double y,double amount){scroll=Math.max(0,Math.min(treeMaxScroll(),scroll+(amount<0?45:-45)));refreshLayout();return true;}
        @Override public void render(GuiGraphics g,int mouseX,int mouseY,float partialTick){
            g.fill(0,0,width,height,0xB3091017);g.fill(left,top,left+panelW,top+panelH,0xFF17242C);g.fill(left,top,left+panelW,top+3,0xFFCCAB70);g.drawString(font,"VIRGOS-MC",left+16,top+14,0xEAD8B4,false);g.drawString(font,group+"  ·  Árbol de progreso",left+16,top+31,0xF4F0E7,false);g.drawString(font,"Las ramas usan tus misiones actuales: abrir una tarjeta conserva tu progreso y sus recompensas.",left+16,top+48,0xB9C7C5,false);
            int cols=Math.max(1,branches.size()),gap=10,cardW=(panelW-32-gap*(cols-1))/cols,headerY=top+62,nodeH=45,at=0;int pulse=(int)(45+25*Math.sin((introTicks+partialTick)*0.35));for(int col=0;col<branches.size();col++){int x=left+16+col*(cardW+gap);g.fill(x,headerY,x+cardW,top+panelH-38,0xFF111B22);List<Entry> branch=branches.get(col);int done=(int)branch.stream().filter(e->e.status().equals("COMPLETED_CLAIMED")).count();g.drawString(font,font.plainSubstrByWidth(branchNames.get(col),Math.max(20,cardW-20)),x+10,headerY+9,0xEAD8B4,false);g.drawString(font,done+"/"+branch.size()+" completadas",x+10,headerY+21,0xFF9DB7AF,false);for(int i=0;i<branch.size();i++){Entry e=branch.get(i);int y=headerY+30+i*nodeH-scroll;if(!nodeVisible(y)){at++;continue;}int color=switch(e.status()){case "COMPLETED_CLAIMED"->0xFF8EC5A4;case "COMPLETED"->0xFFEAC576;case "LOCKED"->0xFF97A3AF;default->0xFFF0EEE5;};boolean hover=mouseX>=x+8&&mouseX<x+cardW-8&&mouseY>=y+3&&mouseY<y+41;g.fill(x+8,y+3,x+cardW-8,y+41,hover?0xFF2B4248:0xFF1C2B32);g.fill(x+8,y+3,x+10,y+38,color);g.renderItem(e.icon(),x+18,y+13);g.drawString(font,font.plainSubstrByWidth(e.title(),Math.max(20,cardW-58)),x+45,y+9,color,false);String status=switch(e.status()){case "COMPLETED_CLAIMED"->"LISTA";case "COMPLETED"->"RECLAMAR";case "LOCKED"->"BLOQUEADA";case "DEPENDENCIES_VISIBLE"->"VER REQUISITO";default->"DISPONIBLE";};g.drawString(font,status,x+45,y+25,color,false);if(i<branch.size()-1)g.fill(x+cardW/2-1,y+39,x+cardW/2+1,y+nodeH-1,pulse<50?0xFF506B58:0xFF3D5544);at++;}}
            super.render(g,mouseX,mouseY,partialTick);if(scroll>0)g.drawString(font,"Rueda: desplazate por el árbol",left+panelW-190,top+panelH-24,0xFF9DB7AF,false);
        }
        @Override public boolean isPauseScreen(){return false;}
    }

    private static final class LibraryScreen extends Screen {
        private final Screen original;
        private final String group;
        private final List<String> groups;
        private final List<Entry> entries=new ArrayList<>();
        private List<Entry> visible=List.of();
        private EditBox search;
        private int left,top,panelW,panelH,sidebar,listX,listW,rows,page,filter,chapterOffset,chapterRows;
        private final List<Button> rowButtons=new ArrayList<>();
        private final List<Button> chapterButtons=new ArrayList<>(),filterButtons=new ArrayList<>();
        @SuppressWarnings("unchecked") LibraryScreen(Screen original)throws Exception {
            super(Component.literal("Códice de Virgos-MC"));this.original=original;
            Object content=field(original,"content");group=(String)call(content,"group");
            Class<?> client=Class.forName(PREFIX+"client.handlers.ClientQuests");
            groups=List.copyOf((List<String>)client.getMethod("groups").invoke(null));
            Map<String,?> statuses=(Map<String,?>)call(content,"quests");
            for(var row:statuses.entrySet()){
                Optional<?> found=(Optional<?>)client.getMethod("get",String.class).invoke(null,row.getKey());
                if(found.isEmpty())continue;
                Object value=call(found.get(),"value"),display=call(value,"display");
                Map<String,?> locations=(Map<String,?>)call(display,"groups");
                if(!locations.containsKey(group))continue;
                Object position=call(locations.get(group),"position");
                ItemStack icon=new ItemStack(Items.BOOK);
                try{icon=(ItemStack)call(call(call(display,"icon"),"item"),"getDefaultInstance");}catch(ReflectiveOperationException ignored){}
                entries.add(new Entry(row.getKey(),((Component)call(display,"title")).getString(),((Component)call(display,"subtitle")).getString(),row.getValue().toString(),icon,((Number)call(position,"x")).intValue(),((Number)call(position,"y")).intValue()));
            }
            entries.sort(Comparator.comparingInt(Entry::y).thenComparingInt(Entry::x));
            if(!savedGroup.equals(group)){savedGroup=group;savedPage=0;savedQuery="";}
            page=savedPage;filter=savedFilter;
        }
        @Override protected void init(){
            panelW=Math.min(920,width-24);panelH=Math.min(570,height-24);left=(width-panelW)/2;top=(height-panelH)/2;
            sidebar=Math.min(162,Math.max(120,panelW/4));listX=left+sidebar+14;listW=panelW-sidebar-28;
            rows=Math.max(1,(panelH-142)/44);rowButtons.clear();chapterButtons.clear();filterButtons.clear();
            addRenderableWidget(Button.builder(Component.literal("×"),b->onClose()).bounds(left+panelW-27,top+9,18,20).build());
            addRenderableWidget(Button.builder(Component.literal("A+"),b->scale(1)).bounds(left+panelW-79,top+9,24,20).build());
            addRenderableWidget(Button.builder(Component.literal("A−"),b->scale(-1)).bounds(left+panelW-53,top+9,24,20).build());
            chapterRows=Math.max(1,Math.min(groups.size(),(panelH-117)/20));
            chapterOffset=Math.max(0,Math.min(chapterOffset,groups.size()-chapterRows));
            for(int i=0;i<chapterRows;i++){
                final int index=i;chapterButtons.add(addRenderableWidget(Button.builder(Component.empty(),b->{remember();group(groups.get(chapterOffset+index));}).bounds(left+10,top+52+i*20,sidebar-14,18).build()));
            }
            search=addRenderableWidget(new EditBox(font,listX,top+51,listW,20,Component.literal("Buscar misión en esta sección")));
            search.setHint(Component.literal("Buscar en esta sección…"));search.setMaxLength(80);search.setValue(savedQuery);
            search.setResponder(s->{page=0;refresh();});
            String[] filters={"Todas","Pendientes","Para reclamar"};int fw=Math.min(102,(listW-8)/3);
            for(int i=0;i<filters.length;i++){final int choice=i;filterButtons.add(addRenderableWidget(Button.builder(Component.literal(filters[i]),b->{filter=choice;page=0;refresh();}).bounds(listX+i*(fw+4),top+76,fw,20).build()));}
            for(int i=0;i<rows;i++){final int index=i;rowButtons.add(addRenderableWidget(new QuestRowButton(listX,top+105+i*44,listW,b->{int at=page*rows+index;if(at<visible.size()){remember();send("quests.OpenQuestPacket",new Class<?>[]{String.class,String.class,boolean.class},group,visible.get(at).id(),false);}})));}
            addRenderableWidget(Button.builder(Component.literal("Anterior"),b->{page=Math.max(0,page-1);refresh();}).bounds(listX,top+panelH-29,65,20).build());
            addRenderableWidget(Button.builder(Component.literal("Siguiente"),b->{page=Math.min(Math.max(0,(visible.size()-1)/rows),page+1);refresh();}).bounds(listX+69,top+panelH-29,65,20).build());
            addRenderableWidget(Button.builder(Component.literal("Actualizar"),b->{remember();group(group);}).bounds(listX+listW-79,top+panelH-29,79,20).build());
            addRenderableWidget(Button.builder(Component.literal("Mapa"),b->{remember();try{Minecraft.getInstance().setScreen(new HubScreen(original));}catch(Exception error){LogUtils.getLogger().error("Virgos codex: could not open route map",error);}}).bounds(listX+listW-140,top+panelH-29,54,20).build());
            addRenderableWidget(Button.builder(Component.literal("Mi perfil"),b->{remember();if(minecraft.player!=null)minecraft.player.connection.sendCommand("perfil");}).bounds(left+10,top+panelH-54,sidebar-14,20).build());
            addRenderableWidget(Button.builder(Component.literal("Ver mapa original"),b->{remember();originalOnce=true;Minecraft.getInstance().setScreen(original);}).bounds(left+10,top+panelH-29,sidebar-14,20).build());
            refresh();
        }
        private void scale(int delta){
            Minecraft mc=Minecraft.getInstance();int current=(int)mc.getWindow().getGuiScale();int max=mc.getWindow().calculateScale(0,false);
            mc.options.guiScale().set(Math.max(1,Math.min(max,current+delta)));mc.options.save();remember();mc.resizeDisplay();
        }
        private void remember(){savedGroup=group;savedPage=page;savedFilter=filter;savedQuery=search==null?"":search.getValue();}
        private void refresh(){
            String term=search==null?"":search.getValue().toLowerCase(Locale.ROOT);
            visible=entries.stream().filter(e->(e.title()+" "+e.subtitle()).toLowerCase(Locale.ROOT).contains(term)).filter(e->filter==0||(filter==1&&!e.status().equals("COMPLETED_CLAIMED"))||(filter==2&&e.status().equals("COMPLETED"))).toList();
            page=Math.min(page,Math.max(0,(visible.size()-1)/Math.max(1,rows)));
            for(int i=0;i<rowButtons.size();i++){boolean show=page*rows+i<visible.size();Button button=rowButtons.get(i);button.visible=show;button.active=show;if(show)button.setMessage(Component.literal(visible.get(page*rows+i).title()));}
            for(int i=0;i<chapterButtons.size();i++){String name=groups.get(chapterOffset+i);chapterButtons.get(i).setMessage(Component.literal(name));chapterButtons.get(i).active=!name.equals(group);}
            for(int i=0;i<filterButtons.size();i++)filterButtons.get(i).active=i!=filter;
            remember();
        }
        @Override public boolean mouseScrolled(double x,double y,double amount){
            if(x>=left&&x<listX){chapterOffset=Math.max(0,Math.min(groups.size()-chapterRows,chapterOffset+(amount<0?1:-1)));refresh();return true;}
            if(x>=listX&&x<=listX+listW){page=Math.max(0,Math.min(Math.max(0,(visible.size()-1)/rows),page+(amount<0?1:-1)));refresh();return true;}return super.mouseScrolled(x,y,amount);
        }
        @Override public void render(GuiGraphics g,int mouseX,int mouseY,float partialTick){
            g.fill(0,0,width,height,0xB3091017);g.fill(left,top,left+panelW,top+panelH,0xFF17242C);g.fill(left,top,left+sidebar,top+panelH,0xFF111B22);g.fill(left,top,left+panelW,top+3,0xFFCCAB70);
            g.drawString(font,"VIRGOS-MC",left+12,top+13,0xEAD8B4,false);g.drawString(font,"Códice de aventuras",listX,top+12,0xF4F0E7,false);
            g.drawString(font,group+"  ·  Progreso personal",listX,top+29,0x9DB7AF,false);
            g.drawString(font,"¿Está bloqueada? Abrila: ahí figura el requisito exacto.",listX,top+40,0xB9C7C5,false);
            super.render(g,mouseX,mouseY,partialTick);
            if(chapterRows<groups.size())g.drawString(font,"Rueda: más capítulos",left+10,top+panelH-66,0x9DB7AF,false);
            for(int i=0;i<rows&&page*rows+i<visible.size();i++){
                Entry entry=visible.get(page*rows+i);int y=top+105+i*44;
                boolean hover=(mouseX>=listX&&mouseX<listX+listW&&mouseY>=y&&mouseY<y+40)||rowButtons.get(i).isFocused();
                g.fill(listX+1,y+1,listX+listW-1,y+39,hover?0xFF354B51:0xFF22343D);
                int color=switch(entry.status()){case "COMPLETED"->0xEAC576;case "COMPLETED_CLAIMED"->0x8EC5A4;case "LOCKED"->0x97A3AF;default->0xF0EEE5;};
                String state=switch(entry.status()){case "COMPLETED"->"RECLAMAR";case "COMPLETED_CLAIMED"->"COMPLETADA";case "LOCKED","DEPENDENCIES_VISIBLE"->"VER REQUISITO";default->"DISPONIBLE";};
                g.fill(listX+1,y+1,listX+3,y+39,0xFF000000|color);g.renderItem(entry.icon(),listX+10,y+11);
                g.drawString(font,font.plainSubstrByWidth(entry.title(),Math.max(30,listW-124)),listX+35,y+8,color,false);
                g.drawString(font,font.plainSubstrByWidth(entry.subtitle(),listW-43),listX+35,y+24,0xA7B8C0,false);
                g.drawString(font,state,listX+listW-font.width(state)-9,y+9,color,false);
            }
            if(visible.isEmpty())g.drawString(font,"No hay misiones para este filtro.",listX+8,top+115,0xBAC5C6,false);
            String count=(page+1)+" / "+Math.max(1,(visible.size()+rows-1)/rows)+"  ·  "+visible.size()+" misiones";
            if(listW>360)g.drawCenteredString(font,count,listX+listW/2,top+panelH-23,0xBAC5C6);
        }
        @Override public boolean isPauseScreen(){return false;}
        @Override public void onClose(){remember();super.onClose();}
    }
}
