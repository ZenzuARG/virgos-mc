"""Update the owner's existing installer message, then verify both downloads."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,urllib.request,urllib.error,uuid
R=Path(__file__).resolve().parents[1];V=R/'.lab/v2'
assert json.loads((V/'final.json').read_text('utf-8'))['readyForPlayers']
assert json.loads((R/'pack/current-release.json').read_text('utf-8'))['version']=='2.0.0'
token=(R/'plugins/DiscordSRV/.token').read_text('utf-8-sig').strip()
guild='736709362206113802';channel='1561436921006137527';bot='1561500718144299008'
release_meta=json.loads((R/'pack/current-release.json').read_text('utf-8'))
message_id=release_meta.get('discordMessage','').rstrip('/').split('/')[-1] or None
content='''**Virgos-MC 2.0 — Mundo nuevo, instalador actualizado**

**1.** Descargá `Virgos-MC-2.0.0-instalar.zip` y elegí **Extraer todo**.
**2.** Cerrá Minecraft y tu launcher. Abrí **EMPEZAR.bat** y elegí **TLauncher** u **Oficial**.
**3.** Si ya jugabas, elegí la misma carpeta y **Revisar / reparar**. Si es tu primera vez, tocá **Instalar**. Esperá a que termine.
**4.** Abrí tu launcher y entrá a **Multijugador → Virgos-MC**.

**TLauncher:** abrilo y cerralo una vez antes de instalar. El asistente configura carpeta, Forge y memoria; después, **Abrir mi launcher → Entrar al juego**.
**Oficial:** elegí la instalación **Virgos-MC** y tocá **Jugar**.

🌍 **virgos-mc.playit.plus** · Java **1.20.1** · paquete **2.0.0**
🔑 Conservá tu nombre y contraseña: `/login tuClave`. Si sos nuevo: `/register tuClave tuClave`.
📖 **J**: 244 misiones en 10 capítulos, con búsqueda y filtros.
👤 `/perfil` o `/perfil Nombre`: horas, nivel, rango, misiones y estadísticas.
🏠 `/virgos guia bases`: proteger tu base. `/virgos menu`: ayuda y mercado.
🎙️ **O** configura la voz; **Bloq Mayús** para hablar después del login.

**Esta versión reinicia mundo, inventario, misiones y bases.** Hay terreno nuevo, ciudades con Create, fortalezas, barcos, nuevas aventuras y jefes. El progreso personal va a tu ritmo y las expediciones importantes requieren compañeros.

Necesitás Windows x64, unos 10 GB libres y tu launcher. El ZIP descarga los mods verificados. RAM: 6 GB para PC con 16 GB o más; 5 GB para PC con 12 GB. Se cambia en **Opciones de carpeta y memoria**. Empezá sin shaders; el primer inicio puede tardar varios minutos.

Si vence la primera conexión, volvé a Multijugador e intentá otra vez. No hace falta instalar Playit ni abrir puertos. Instrucciones adjuntas y dentro del ZIP.'''
assert len(content)<=2000,len(content)
release=json.loads((R/'dist/release.json').read_text('utf-8'));assert release['version']=='2.0.0'
installer=next(f for f in release['files'] if f['name'].endswith('-instalar.zip'))
files=[(installer['name'],(R/'dist'/installer['name']).read_bytes(),'application/zip'),('COMO-INSTALAR-VIRGOS-MC.txt',(R/'templates/LEEME.txt').read_bytes(),'text/plain; charset=utf-8')]
assert hashlib.sha256(files[0][1]).hexdigest()==installer['sha256']
assert all(token.encode() not in data for _,data,_ in files)
def api(path,data=None,content_type=None,method=None):
    headers={'Authorization':'Bot '+token,'User-Agent':'VirgosMC-Setup/1.0'}
    if content_type:headers['Content-Type']=content_type
    request=urllib.request.Request('https://discord.com/api/v10/'+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)
    except urllib.error.HTTPError as e:raise RuntimeError('Discord API HTTP '+str(e.code)) from None
dest=api('channels/'+channel);assert dest['guild_id']==guild and dest['name']=='virgos-mc'
path=f'channels/{channel}/messages/{message_id}'
try:
    existing=api(path)
    assert existing['author']['id']==bot
except RuntimeError as exc:
    if 'HTTP 404' not in str(exc): raise
    existing=None
record={'version':'2.0.0','channelId':channel,'guildId':guild,'messageId':message_id,'url':f'https://discord.com/channels/{guild}/{channel}/{message_id}','status':'prepared','files':[{'name':n,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)} for n,b,_ in files]}
out=V/'discord-delivery.json';out.write_text(json.dumps(record,indent=2),'utf-8')
if (existing is None or existing['content']!=content
        or {a['filename'] for a in existing['attachments']}!={f[0] for f in files}
        or {a['filename']:a.get('size') for a in existing['attachments']}!={n:len(data) for n,data,_ in files}):
    if existing is not None:
        (V/'discord-message-before-v2.json').write_text(json.dumps(existing,ensure_ascii=False,indent=2),'utf-8')
    boundary='VirgosV2'+uuid.uuid4().hex
    payload={'content':content,'allowed_mentions':{'parse':[]},'attachments':[{'id':i,'filename':n} for i,(n,_,_) in enumerate(files)]}
    parts=[f'--{boundary}\r\nContent-Disposition: form-data; name="payload_json"\r\nContent-Type: application/json\r\n\r\n'.encode()+json.dumps(payload,ensure_ascii=False).encode()+b'\r\n']
    for i,(name,data,mime) in enumerate(files):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="files[{i}]"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n'.encode()+data+b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode())
    if existing is None:
        message=api(f'channels/{channel}/messages',b''.join(parts),'multipart/form-data; boundary='+boundary,'POST')
    else:
        message=api(path,b''.join(parts),'multipart/form-data; boundary='+boundary,'PATCH')
else:
    message=existing
assert message['content']==content and message['author']['id']==bot
assert not message['mention_everyone'] and not message['mentions'] and not message['mention_roles']
assert len(message['attachments'])==len(files)
for name,data,_ in files:
    attachment=next(a for a in message['attachments'] if a['filename']==name)
    request=urllib.request.Request(attachment['url'],headers={'User-Agent':'VirgosMC-Setup/1.0'})
    with urllib.request.urlopen(request,timeout=30) as response:download=response.read(len(data)+1)
    assert hashlib.sha256(download).digest()==hashlib.sha256(data).digest(),name
record.update(messageId=message['id'],url=f'https://discord.com/channels/{guild}/{channel}/{message["id"]}',status='verified',verified=datetime.now(timezone.utc).isoformat(),attachmentsDownloadVerified=True)
out.write_text(json.dumps(record,indent=2),'utf-8');print(json.dumps(record))
