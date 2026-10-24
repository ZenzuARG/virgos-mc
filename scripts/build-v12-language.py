"""Small Spanish UI overlay for the public market; official mod files remain intact."""
from pathlib import Path
import json,zipfile,re
R=Path(__file__).resolve().parents[1]
words={
 'Oak Shelf':'Puesto de roble','Trader Storage':'Almacén del puesto','No Available Trades':'No hay ofertas disponibles',
 'Sale':'Venta','Purchase':'Compra','Barter':'Trueque','Nothing':'Nada','Main':'Principal',
 'Edit Trades':'Editar ofertas','Open Trader Storage':'Abrir almacén del puesto','Return to Trades':'Volver a las ofertas',
 'Trader Settings':'Ajustes del puesto','Trader Logs':'Historial del puesto','Trader Info':'Información del puesto',
 'Trader Stats':'Estadísticas del puesto','Trader Rules':'Reglas del puesto','Edit Trade-Specific Rules':'Reglas de esta oferta',
 'Money Storage':'Almacén de dinero','Collect Money':'Retirar dinero','Store Money':'Depositar dinero',
 'Pickup Entire Trader':'Retirar el puesto completo','Trader Name':'Nombre del puesto','Ally Permissions':'Permisos de aliados',
 'Allies':'Aliados','Misc Settings':'Otros ajustes','Settings Clipboard':'Copiar configuración',
 'Copy':'Copiar','Paste':'Pegar','Trade Direction':'Tipo de intercambio','Open Storage':'Abrir almacén',
 'Bounty Board':'Tablón de encargos','Bounty':'Encargo','Decree':'Orden de trabajo','Decrees':'Órdenes de trabajo',
 'Invalid Decree':'Orden no válida','Bring this to a Bounty Board!':'Llevá esto a un tablón de encargos.',
 'Fullfill your bounty by right clicking on a bounty board.':'Con el encargo en la mano, hacé clic derecho en un tablón para entregar los materiales.',
 'This bounty has expired.':'Este encargo venció.','Required':'Se necesita','Rewards':'Recompensas',
 'Requirements not met.':'Todavía faltan materiales.','Time To Complete':'Tiempo disponible','Expired':'Vencido',
 'Common':'Común','Uncommon':'Poco común','Rare':'Raro','Epic':'Épico',
 'Work for Hire':'Un trabajo para hoy','Take a bounty from a bounty board':'Tomá un encargo del tablón',
 'Honest Pay for Honest Work':'Trabajo cumplido','Complete a bounty!':'Completá un encargo',
}
files={}
with zipfile.ZipFile(R/'pack/client-overrides/resourcepacks/Virgos-MC-UI.zip') as z:
 files={n:z.read(n) for n in z.namelist()}
counts={}
for mod,jar in [('lightmanscurrency','lightmanscurrency-1.20.1-2.3.0.6.jar'),('bountiful','Bountiful-6.0.4+1.20.1-forge.jar')]:
 with zipfile.ZipFile(R/'.cache/pack/downloads'/jar) as z:english=json.loads(z.read('assets/'+mod+'/lang/en_us.json'))
 translation={k:words[v] for k,v in english.items() if v in words}
 if mod=='bountiful':
  for key in english:
   if key.startswith('bountiful.decree.') and key.endswith('.name'):
    decree=key.split('.')[2]
    translation[key]='Cocina del pueblo' if decree in ['farmer','fisherman','butcher','shepherd'] else 'Taller del pueblo' if decree in ['inventor','armorer','toolsmith'] else 'Caminos del pueblo'
 for lang in ['es_es','es_ar','es_mx','es_cl','es_ec']:
  path=f'assets/{mod}/lang/{lang}.json';old={}
  # LC ships malformed trailing commas. Filter its lower-priority translations
  # and supply repaired, complete files so Minecraft can read our overlay.
  if mod=='lightmanscurrency':
   with zipfile.ZipFile(R/'.cache/pack/downloads'/jar) as z:
    if path in z.namelist():old=json.loads(re.sub(r',\s*([}\]])',r'\1',z.read(path).decode()))
  old.update(json.loads(files.get(path,b'{}')));old.update(translation)
  files[path]=json.dumps(old,ensure_ascii=False,indent=2).encode()
 counts[mod]=len(translation)
meta=json.loads(files['pack.mcmeta'])
meta['filter']={'block':[{'namespace':'lightmanscurrency','path':r'lang/es_(es|ar|mx|cl|ec)\.json'}]}
files['pack.mcmeta']=json.dumps(meta,ensure_ascii=False,indent=2).encode()
out=R/'.lab/v12/client-overrides/resourcepacks/Virgos-MC-UI.zip';out.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for path,data in files.items():z.writestr(path,data)
print('Spanish market UI:',counts)
