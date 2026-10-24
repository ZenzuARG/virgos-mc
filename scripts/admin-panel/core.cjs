'use strict';
const fs = require('node:fs');
const path = require('node:path');
const net = require('node:net');
const crypto = require('node:crypto');
const zlib = require('node:zlib');
const {spawn} = require('node:child_process');
const {DatabaseSync} = require('node:sqlite');

const NAME = /^[A-Za-z0-9_]{1,16}$/;
const GROUP = /^[a-z0-9_-]{1,48}$/;
const NODE = /^(?:[a-z0-9_-]+[.:])*[a-z0-9_*-]+$/;
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
function alive(pid) { if (!Number.isInteger(pid) || pid < 1) return false; try { process.kill(pid, 0); return true; } catch { return false; } }
function json(file, fallback = {}) { try { return JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '')); } catch { return fallback; } }
function writeJson(file, value) { fs.mkdirSync(path.dirname(file), {recursive: true}); const tmp = file + '.tmp'; fs.writeFileSync(tmp, JSON.stringify(value, null, 2)); fs.renameSync(tmp, file); }
function cleanLine(value, max = 500) {
  if (typeof value !== 'string' || !value.trim() || value.length > max || /[\x00-\x1f\x7f\u2028\u2029]/.test(value)) throw Error('Escribí una sola línea válida.');
  return value.trim();
}
function redact(text) {
  return String(text).replace(/\x1b\[[0-9;]*m/g, '').replace(/§[0-9a-fk-or]/gi, '').split(/\r?\n/).map(line => {
    if (/(?:\/(?:authme:)?(?:login|log|register|reg|changepassword|changepass|password)\s|\bauthme\s+(?:changepassword|register)\s|(?:token|secret|password|authorization|api.?key)\s*[=:])/i.test(line)) return '[Línea de autenticación ocultada]';
    return line.replace(/\b[\w-]{24,28}\.[\w-]{6}\.[\w-]{25,}\b/g, '[token oculto]');
  }).join('\n');
}
function tail(file, max = 90000) { try { const fd = fs.openSync(file, 'r'); try { const size = fs.fstatSync(fd).size; const b = Buffer.alloc(Math.min(size, max)); fs.readSync(fd, b, 0, b.length, Math.max(0, size - max)); return b.toString('utf8').split(/\r?\n/).slice(size > max ? 1 : 0).slice(-300).join('\n'); } finally { fs.closeSync(fd); } } catch { return ''; } }
function varint(n) { const bytes = []; do { let b = n & 127; n >>>= 7; if(n) b |= 128; bytes.push(b); } while(n); return Buffer.from(bytes); }
function readVarint(b, start = 0) { let n = 0; for(let i = 0; i < 5; i++) { if(start + i >= b.length) return null; const v = b[start + i]; n |= (v & 127) << (i * 7); if(!(v & 128)) return {value: n, end: start+i+1}; } throw Error('Respuesta inválida'); }
function ping(port = 25565) {
  return new Promise(resolve => {
    const socket = net.connect({host: '127.0.0.1', port}); let data = Buffer.alloc(0), done = false;
    const finish = value => { if(done) return; done = true; socket.destroy(); resolve(value); };
    socket.setTimeout(1600, () => finish(null)); socket.on('error', () => finish(null)); socket.on('end', () => finish(null));
    socket.on('connect', () => { const host = Buffer.from('localhost'), p = Buffer.alloc(2); p.writeUInt16BE(port); const handshake = Buffer.concat([varint(0),varint(763),varint(host.length),host,p,varint(1)]); socket.write(Buffer.concat([varint(handshake.length),handshake,Buffer.from([1,0])])); });
    socket.on('data', chunk => { try { data = Buffer.concat([data, chunk]); if(data.length > 1048576) return finish(null); const len = readVarint(data); if(!len || data.length < len.end + len.value) return; const id = readVarint(data,len.end); if(!id || id.value !== 0) return finish(null); const str = readVarint(data,id.end); if(!str || str.value < 0 || str.end + str.value > data.length) return finish(null); finish(JSON.parse(data.subarray(str.end,str.end+str.value).toString())); } catch { finish(null); } });
  });
}
function launch(root) {
  const out = fs.openSync(path.join(root,'.runtime/runner.log'),'w'), err = fs.openSync(path.join(root,'.runtime/runner-error.log'),'w');
  try { const child = spawn(process.execPath, [path.join(root,'scripts/run-public.cjs')], {cwd:root, detached:true, windowsHide:true, stdio:['ignore',out,err]}); child.on('error', error => fs.appendFileSync(path.join(root,'.runtime/runner-error.log'),error.message)); child.unref(); return child.pid; } finally { fs.closeSync(out); fs.closeSync(err); }
}
class Controller {
  constructor(root, deps = {}) {
    this.root = root; this.deps = {alive,ping,launch,...deps}; this.busy = false; this.permBusy = false;
    this.path = name => path.join(root,name); this.read = (name, fallback) => json(this.path(name),fallback);
    fs.mkdirSync(this.path('.runtime'),{recursive:true});
  }
  async status() {
    const probe = await this.deps.ping();
    // Read AFTER the asynchronous probe: Java can exit and start its backup while
    // the socket request is pending. A partial legacy state write must fail closed.
    const fresh = this.read('.runtime/active-run.json',null);
    const run = fresh || this.lastRun || {}, launchState = this.read('.runtime/panel-launch.json');
    if(fresh) this.lastRun=fresh;
    const live = !run.finished && this.deps.alive(run.pid), runner = this.deps.alive(run.runner);
    const launching = this.deps.alive(launchState.pid) && Date.now()-Date.parse(launchState.requestedAt)<300000 && (!live || Date.parse(run.started)<Date.parse(launchState.requestedAt));
    const offlineBackup = this.read('.runtime/panel-backup.json');
    const copying = (run.backupInProgress && runner) || (!offlineBackup.finished && this.deps.alive(offlineBackup.pid));
    let state = copying ? 'backup' : probe ? (live ? 'online' : 'external') : live || launching ? 'starting' : run.mode==='managed'&&runner ? 'stopping' : 'offline';
    let detail = '';
    const pending = this.read('.runtime/panel-operation.json');
    if(pending.runStarted === run.started && live) {
      if(Date.now()-Date.parse(pending.requestedAt)<120000) state='stopping';
      else detail='La detención sigue pendiente. Revisá la consola antes de reintentar.';
    }
    if(!live && !copying && !launching && !probe && (run.backupError || (run.exitCode != null && run.exitCode !== 0))) { state='error'; detail='El último cierre o respaldo terminó con un error. Revisá la consola.'; }
    if(!live && !probe && !copying && launchState.pid && !this.deps.alive(launchState.pid) && Date.parse(launchState.requestedAt)>Date.parse(run.started||run.finished||0)) { state='error'; detail='El arranque no se completó. Revisá los mensajes del controlador.'; }
    if(live && !probe && Date.now()-Date.parse(run.started)>300000 && state==='starting') {state='unresponsive'; detail='El proceso está activo pero no responde a la consulta de Minecraft.';}
    if(run.mode==='console' && live) detail='Esta instancia se inició con iniciar.bat. Los comandos se ingresan en esa consola; el próximo arranque desde el panel habilita todos los controles.';
    if(offlineBackup.finished && !offlineBackup.ok && Date.parse(offlineBackup.finished)>Date.parse(this.read('.runtime/last-backup.json').completed||0)) detail='El respaldo manual no terminó correctamente. Revisá Consola → Respaldo manual.';
    const unreadable=!fresh&&fs.existsSync(this.path('.runtime/active-run.json'));
    if(unreadable) {state='unresponsive';detail='El controlador está actualizando su estado. Los controles se habilitarán cuando se pueda confirmar.';}
    const backup = this.read('.runtime/last-backup.json'), release = this.read('pack/current-release.json');
    const available=live && run.mode==='managed' && this.deps.alive(run.runner) && !copying && state!=='stopping' && !unreadable;
    return {state,detail,managed:run.mode==='managed',canCommand:available,canStart:['offline','error'].includes(state),started:live?run.started:null,pid:live?run.pid:null,online:probe?.players?.online??null,max:probe?.players?.max??10,sample:probe?.players?.sample??[],version:release.version||'2.0.0',minecraft:release.minecraft||'1.20.1',mods:release.clientRequired||114,address:'virgos-mc.playit.plus',backup:backup.completed?{completed:backup.completed,name:path.basename(backup.archive),files:backup.verifiedFiles,worlds:backup.worldFolders?.length}:null,backupError:!!run.backupError};
  }
  queue(command) {
    command=cleanLine(command,2000).replace(/^\//,'');
    const run=this.read('.runtime/active-run.json');
    if(run.mode!=='managed'||run.finished||!this.deps.alive(run.pid)||!this.deps.alive(run.runner)) throw Error('No hay un servidor controlable. Encendelo desde el panel.');
    fs.appendFileSync(this.path('.runtime/public-commands.txt'),command+'\n','utf8');
  }
  audit(action, details='') { fs.appendFileSync(this.path('.runtime/admin-panel-actions.jsonl'),JSON.stringify({at:new Date().toISOString(),action,details:redact(details)})+'\n'); }
  accounts() {
    if(this.deps.accounts) return this.deps.accounts();
    let db; try { db=new DatabaseSync(this.path('plugins/AuthMe/authme.db'),{readOnly:true}); return db.prepare('SELECT realname AS name, lastlogin FROM authme').all(); } catch { return []; } finally { db?.close(); }
  }
  players(status) {
    const map=new Map();
    const add=(p,extra={})=>{ if(!NAME.test(p.name||'')) return; const key=p.name.toLowerCase(); map.set(key,{...(map.get(key)||{name:p.name}),...p,...extra}); };
    for(const p of this.read('usercache.json',[])) add({name:p.name,uuid:p.uuid});
    for(const p of Object.values(this.read('virgos_world/virgos-profiles.json').players||{})) add({name:p.name,uuid:p.uuid,profile:p});
    for(const p of this.accounts()) add(p,{registered:true});
    for(const p of this.read('banned-players.json',[])) add({name:p.name,uuid:p.uuid},{banned:true,reason:p.reason});
    for(const p of this.read('ops.json',[])) add({name:p.name,uuid:p.uuid},{op:true});
    for(const p of status.sample) add({name:p.name,uuid:p.id},{online:true});
    return [...map.values()].filter(p=>p.registered||p.profile||p.online||p.op||p.banned).sort((a,b)=>Number(!!b.online)-Number(!!a.online)||a.name.localeCompare(b.name));
  }
  permissions() { return this.read('.runtime/admin-permissions.json',{groups:{},users:{},updated:null}); }
  async refreshPermissions() {
    if(this.permBusy) throw Error('Ya se están leyendo los permisos.');
    this.permBusy=true;
    const filename='admin-panel-'+crypto.randomBytes(8).toString('hex'), file=this.path('plugins/LuckPerms/'+filename+'.json.gz');
    try {
      this.queue('lp export '+filename);
      for(let i=0;i<50;i++) {
        await sleep(200);
        try {
          const raw=JSON.parse(zlib.gunzipSync(fs.readFileSync(file),{maxOutputLength:8*1024*1024}));
          if(!raw.groups||!raw.users) continue;
          const data={updated:new Date().toISOString(),groups:raw.groups,users:raw.users};
          writeJson(this.path('.runtime/admin-permissions.json'),data); return data;
        } catch(error) { if(!['ENOENT','Z_BUF_ERROR','Z_DATA_ERROR'].includes(error.code)&&!(error instanceof SyntaxError)) throw error; }
      }
      throw Error('LuckPerms no respondió a tiempo. Podés reintentar la lectura.');
    } finally { this.permBusy=false; try {fs.unlinkSync(file);} catch {} }
  }
  async action(body) {
    if(this.busy) throw Error('Hay otra acción en curso. Esperá unos segundos.');
    this.busy=true;
    try {
      const status=await this.status(), action=body.action;
      if(action==='start') {
        if(!status.canStart) throw Error('El servidor ya está activo o realizando una operación.');
        const pid=this.deps.launch(this.root); if(!pid) throw Error('No se pudo iniciar el controlador.');
        writeJson(this.path('.runtime/panel-launch.json'),{pid,requestedAt:new Date().toISOString()});
        this.audit('start'); return {message:'Arranque solicitado. El indicador se actualizará cuando Minecraft responda.'};
      }
      if(['stop','restart','backup'].includes(action)) {
        if(body.confirm!==action) throw Error('Confirmá esta operación en el panel.');
        if(action==='backup'&&status.canStart) {
          const script=this.path('scripts/admin-panel/backup.ps1');
          const out=fs.openSync(this.path('.runtime/panel-backup.log'),'w');
          let child; try { child=spawn('powershell.exe',['-NoProfile','-ExecutionPolicy','Bypass','-File',script],{cwd:this.root,detached:true,windowsHide:true,stdio:['ignore',out,out]}); child.on('error',e=>fs.appendFileSync(this.path('.runtime/panel-backup.log'),e.message)); child.unref(); } finally {fs.closeSync(out);}
          writeJson(this.path('.runtime/panel-backup.json'),{pid:child.pid,started:new Date().toISOString()}); this.audit(action); return {message:'Creando y verificando una copia completa. El servidor permanecerá apagado.'};
        }
        if(!status.canCommand) throw Error('El servidor no está listo para esta operación.');
        if(action!=='stop') writeJson(this.path('.runtime/checkpoint-request.json'),{schema:1,reason:'full-backup',label:action==='backup'?'manual':'auto',requestedAt:new Date().toISOString()});
        this.queue('stop'); writeJson(this.path('.runtime/panel-operation.json'),{action,runStarted:this.read('.runtime/active-run.json').started,requestedAt:new Date().toISOString()});
        this.audit(action); return {message:action==='stop'?'Guardando y apagando. Después se verificará el respaldo.':'Guardando, respaldando y reiniciando. Puede demorar varios minutos.'};
      }
      if(!status.canCommand) throw Error('Esperá a que el servidor esté listo y administrado desde el panel.');
      if(action==='permissions-refresh') {await this.refreshPermissions();return {message:'Permisos leídos desde LuckPerms.'};}
      let command;
      if(action==='save') command='save-all flush';
      else if(action==='command') {
        command=cleanLine(body.command,2000).replace(/^\//,'');
        if(/^(?:(?:minecraft|bukkit):)?(?:stop|restart|reload)\b/i.test(command)||/^virgos\s+checkpoint\b/i.test(command)) throw Error('Usá los botones de apagado, reinicio o respaldo para esa operación.');
        if(/^(?:authme:)?(?:login|log|register|reg|changepassword|changepass|password)\b|^authme\s+(?:changepassword|register)\b/i.test(command)) throw Error('Las claves de cuentas se gestionan fuera de la consola del panel.');
        if(body.confirm!=='command') throw Error('Confirmá el comando antes de enviarlo.');
      } else if(action==='player') {
        if(!NAME.test(body.name||'')) throw Error('Nombre de jugador inválido.');
        const player=this.players(status).find(p=>p.name===body.name);
        if(!player) throw Error('Elegí un jugador conocido por el servidor.');
        if(body.confirm!==body.operation) throw Error('Confirmá la acción sobre el jugador.');
        const name=player.name, op=body.operation;
        if(['op','deop','ban','pardon'].includes(op)) {
          if(op==='op'&&!player.registered) throw Error('La cuenta debe estar registrada en AuthMe antes de recibir OP.');
          command=op+' '+name+(op==='ban'?' '+cleanLine(body.reason||'Acceso suspendido por administración.',160):'');
        } else if(op==='kick') {if(!player.online) throw Error('Ese jugador no está conectado.');command='kick '+name+' '+cleanLine(body.reason||'Desconectado por administración.',160);}
        else if(op==='spawn') {if(!player.online) throw Error('Ese jugador no está conectado.');command='execute in minecraft:overworld run tp '+name+' 672.5 80 752.5';}
        else throw Error('Acción de jugador no admitida.');
      } else if(action==='permission') {
        if(body.confirm!=='permission') throw Error('Confirmá el cambio de permisos.');
        const kind=body.kind, target=body.target;
        if(!['user','group'].includes(kind)||(kind==='user'?!NAME.test(target||''):!GROUP.test(target||''))) throw Error('Destino de permisos inválido.');
        if(kind==='user'&&!this.players(status).some(p=>p.name===target&&p.registered)) throw Error('Elegí una cuenta registrada en AuthMe.');
        if(kind==='group'&&!this.permissions().groups[target]&&body.operation!=='create') throw Error('Actualizá los permisos y elegí un grupo existente.');
        if(body.operation==='create'&&kind==='group') command='lp creategroup '+target;
        else if(['add','remove'].includes(body.operation)) {
          if(kind!=='user'||!GROUP.test(body.group||'')||!this.permissions().groups[body.group]) throw Error('Elegí un grupo existente.');
          command=`lp user ${target} parent ${body.operation} ${body.group}`;
        } else if(['true','false','unset'].includes(body.value)&&NODE.test(body.node||'')&&body.node.length<160) {
          command=`lp ${kind} ${target} permission ${body.value==='unset'?'unset':'set'} ${body.node}${body.value==='unset'?'':' '+body.value}`;
        } else throw Error('Permiso inválido. Usá un nodo como minecraft.command.kick.');
      } else throw Error('Acción desconocida.');
      this.queue(command); this.audit(action,command);
      return {message:action==='permission'?'Cambio enviado a LuckPerms. Se volverán a leer las reglas para comprobarlo.':'Comando enviado. La respuesta real aparece en la consola.'};
    } finally {this.busy=false;}
  }
  logs() {return {console:redact(tail(this.path('logs/latest.log'))),runner:redact(tail(this.path('.runtime/runner.log'),10000)+'\n'+tail(this.path('.runtime/runner-error.log'),10000)),backup:redact(tail(this.path('.runtime/panel-backup.log'),6000)),actions:tail(this.path('.runtime/admin-panel-actions.jsonl'),12000)};}
}
module.exports={Controller,alive,json,writeJson,redact,cleanLine,ping,readVarint,varint,NAME};
