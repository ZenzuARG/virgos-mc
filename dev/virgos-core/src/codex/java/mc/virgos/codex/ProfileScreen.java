package mc.virgos.codex;

import com.google.gson.*;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import java.text.NumberFormat;
import java.util.*;

/** A read-only character sheet populated exclusively by the server. */
public final class ProfileScreen extends Screen {
    private final JsonObject data;
    private int left,top,panelW,panelH,tab,page;
    private EditBox name;
    private String error;
    private final NumberFormat numbers=NumberFormat.getIntegerInstance(Locale.forLanguageTag("es-AR"));
    public ProfileScreen(String json){super(Component.literal("Perfil de jugador"));data=JsonParser.parseString(json).getAsJsonObject();}
    public static void accept(String json){
        JsonObject data=JsonParser.parseString(json).getAsJsonObject();Minecraft client=Minecraft.getInstance();
        if(data.has("error")){if(client.screen instanceof ProfileScreen profile)profile.error=data.get("error").getAsString();return;}
        client.setScreen(new ProfileScreen(json));
    }
    private void query(String player){
        if(!player.matches("[A-Za-z0-9_]{1,16}")){error="Usá letras, números y guion bajo; sin espacios.";return;}
        error=null;
        if(minecraft!=null&&minecraft.player!=null)minecraft.player.connection.sendCommand("perfil "+player);
    }
    @Override protected void init(){
        panelW=Math.min(700,width-24);panelH=Math.min(470,height-24);left=(width-panelW)/2;top=(height-panelH)/2;
        name=addRenderableWidget(new EditBox(font,left+16,top+49,Math.min(170,panelW-125),20,Component.literal("Nombre del jugador")));name.setMaxLength(16);name.setValue(data.get("name").getAsString());
        addRenderableWidget(Button.builder(Component.literal("Consultar"),b->query(name.getValue())).bounds(name.getX()+name.getWidth()+5,top+49,74,20).build());
        addRenderableWidget(Button.builder(Component.literal("×"),b->onClose()).bounds(left+panelW-30,top+10,20,20).build());
        addRenderableWidget(Button.builder(Component.literal("Resumen"),b->{tab=0;page=0;}).bounds(left+16,top+77,89,20).build());
        addRenderableWidget(Button.builder(Component.literal("Misiones"),b->{tab=1;page=0;}).bounds(left+109,top+77,89,20).build());
        addRenderableWidget(Button.builder(Component.literal("Jugadores"),b->{tab=2;page=0;}).bounds(left+202,top+77,89,20).build());
        addRenderableWidget(Button.builder(Component.literal("Mi perfil"),b->{if(minecraft.player!=null)query(minecraft.player.getGameProfile().getName());}).bounds(left+16,top+panelH-30,84,20).build());
        addRenderableWidget(Button.builder(Component.literal("Códice [J]"),b->VirgosCodex.openCodex()).bounds(left+panelW-105,top+panelH-30,89,20).build());
        addRenderableWidget(Button.builder(Component.literal("←"),b->page=Math.max(0,page-1)).bounds(left+panelW/2-24,top+panelH-30,22,20).build());
        addRenderableWidget(Button.builder(Component.literal("→"),b->page++).bounds(left+panelW/2+2,top+panelH-30,22,20).build());
    }
    private long value(String key){return data.get(key).getAsLong();}
    private String number(String key){return numbers.format(value(key));}
    private String time(){long seconds=value("seconds");return seconds/3600+" h "+seconds%3600/60+" min";}
    private void card(GuiGraphics g,int x,int y,int w,String label,String value){
        g.fill(x,y,x+w,y+43,0xFF253A43);g.drawString(font,label,x+9,y+7,0xA9C0C5,false);g.drawString(font,font.plainSubstrByWidth(value,w-18),x+9,y+24,0xF0DEB8,false);
    }
    @Override public void render(GuiGraphics g,int mouseX,int mouseY,float partialTick){
        g.fill(0,0,width,height,0xC0091017);g.fill(left,top,left+panelW,top+panelH,0xFF17242C);g.fill(left,top,left+panelW,top+3,0xFFCCAB70);
        g.drawString(font,data.get("name").getAsString()+"  ·  Rango "+data.get("rank").getAsString(),left+16,top+14,0xEAD8B4,false);
        String subtitle=error!=null?error:(data.get("online").getAsBoolean()?"En línea · Estadísticas de este mundo":"Desconectado · Último registro guardado");
        g.drawString(font,font.plainSubstrByWidth(subtitle,panelW-32),left+16,top+31,error==null?0x9DB7AF:0xF3AAA2,false);
        int x=left+16,y=top+107,w=panelW-32,available=panelH-150;
        if(tab==0){
            String[][] cards={{"Tiempo conectado",time()},{"Nivel de experiencia",number("level")},{"Misiones completadas",value("quests")<0?"No disponible":number("quests")+" / "+number("questTotal")},{"Criaturas derrotadas",number("mobs")},{"Muertes",number("deaths")},{"A pie y nadando",String.format(Locale.forLanguageTag("es-AR"),"%.1f km",value("distanceCm")/100000d)},{"Bloques minados",number("mined")},{"Objetos fabricados",number("crafted")},{"Saltos",number("jumps")},{"Peces capturados",number("fish")}};
            int count=Math.max(1,(available-17)/49)*2,maxPage=Math.max(0,(cards.length-1)/count);page=Math.min(page,maxPage);
            for(int i=0;i<count&&page*count+i<cards.length;i++){String[] row=cards[page*count+i];card(g,x+(i%2)*(w/2+3),y+(i/2)*49,w/2-3,row[0],row[1]);}
            g.drawString(font,"Incluye AFK. Las horas no dan rangos. · "+(page+1)+"/"+(maxPage+1),x,top+panelH-43,0x9DB7AF,false);
        }else{
            JsonArray list=data.getAsJsonArray(tab==1?"chapters":"players");int count=Math.max(1,available/26);page=Math.min(page,Math.max(0,(list.size()-1)/count));
            for(int i=0;i<count&&page*count+i<list.size();i++){
                int rowY=y+i*26;g.fill(x,rowY,x+w,rowY+22,0xFF253A43);
                if(tab==1){JsonObject row=list.get(page*count+i).getAsJsonObject();String label=row.get("name").getAsString();String score=row.get("done").getAsString()+" / "+row.get("total").getAsString();g.drawString(font,label,x+8,rowY+6,0xEAD8B4,false);g.drawString(font,score,x+w-font.width(score)-8,rowY+6,0xAED3BE,false);int bar=(int)((w-16)*row.get("done").getAsDouble()/Math.max(1,row.get("total").getAsInt()));g.fill(x+8,rowY+19,x+8+bar,rowY+21,0xFF8EC5A4);}
                else g.drawString(font,list.get(page*count+i).getAsString()+"  →  Ver perfil",x+8,rowY+6,0xEAD8B4,false);
            }
            String footer=(tab==1?number("rewards")+" por reclamar. Incluye guías.":"Clic en un nombre para ver su perfil.")+" · "+(page+1)+"/"+Math.max(1,(list.size()+count-1)/count);
            g.drawString(font,footer,x,top+panelH-43,0x9DB7AF,false);
        }
        super.render(g,mouseX,mouseY,partialTick);
    }
    @Override public boolean mouseScrolled(double x,double y,double amount){page=Math.max(0,page+(amount<0?1:-1));return true;}
    @Override public boolean mouseClicked(double x,double y,int button){
        if(tab==2&&button==0&&x>=left+16&&x<=left+panelW-16&&y>=top+107&&y<top+panelH-43){int count=Math.max(1,(panelH-150)/26),index=page*count+(int)(y-top-107)/26;JsonArray names=data.getAsJsonArray("players");if(index<names.size()){query(names.get(index).getAsString());return true;}}
        return super.mouseClicked(x,y,button);
    }
    @Override public boolean isPauseScreen(){return false;}
}
