// VIRGOS-INTEGRAL-1
// Managed local run: no Windows service or installed Playit agent.
const {spawn,execFileSync}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const net=require('node:net');
const root=path.resolve(__dirname,'..');
const stateFile=path.join(root,'.runtime/active-run.json');
const read=file=>JSON.parse(fs.readFileSync(path.join(root,file),'utf8').replace(/^\uFEFF/,''));
const {classifyExit,readCheckpoint,createAudit}=require('./virgos-lifecycle.cjs');
const audit=createAudit(root);
async function main(restartAttempt=0){
  const base=read('versions.lock.json');
  execFileSync('powershell.exe',['-NoProfile','-ExecutionPolicy','Bypass','-File',path.join(root,'scripts/validar-entrega.ps1'),'-ServerPath',root,'-Quiet'],{cwd:root,windowsHide:true,stdio:'pipe'});
  if(fs.existsSync(stateFile)){
    const old=read('.runtime/active-run.json');
    const owner=old.backupInProgress?old.runner:(!old.finished?old.pid:null);
    if(owner){try{process.kill(owner,0);throw Error('El servidor está en ejecución o verificando un respaldo.');}catch(e){if(e.code!=='ESRCH')throw e;}}
  }
  const props=fs.readFileSync(path.join(root,'server.properties'),'utf8');
  if(!/^server-port=25565$/m.test(props)||!/^level-name=virgos_world$/m.test(props)||!/^online-mode=false$/m.test(props))throw Error('Configuración pública inesperada');
  if(!/^eula=true$/m.test(fs.readFileSync(path.join(root,'eula.txt'),'utf8')))throw Error('EULA no aceptado');
  await new Promise((resolve,reject)=>{
    const probe=net.connect({host:'127.0.0.1',port:25565});
    probe.setTimeout(700);
    probe.on('connect',()=>{probe.destroy();reject(Error('Puerto 25565 ocupado'));});
    probe.on('error',e=>{if(e.code==='ECONNREFUSED')resolve();else reject(e);});
    probe.on('timeout',()=>{probe.destroy();reject(Error('No se pudo comprobar el puerto'));});
  });
  const commands=path.join(root,'.runtime/public-commands.txt');fs.writeFileSync(commands,'');
  const output=fs.openSync(path.join(root,'.runtime/public-console.log'),'w');
  const java=path.join(root,'.runtime',base.java.folder,'bin/java.exe');
  const child=spawn(java,['-Xms1G','-Xmx8G','-XX:+UseParallelGC','-Xlog:gc:file=.runtime/gc-server.log:time,level,tags:filecount=3,filesize=2M','-Dfile.encoding=UTF-8','-jar','ketting-server.jar','-minecraftVersion',base.minecraft,'-forgeVersion',base.forge,'-kettingVersion',base.ketting,'-daul','-dau','-noui','nogui'],{cwd:root,stdio:['pipe',output,output],windowsHide:true});
  const started=new Date().toISOString();
  fs.writeFileSync(stateFile,JSON.stringify({mode:'managed',checkpointSupport:true,pid:child.pid,runner:process.pid,started},null,2));
  console.log('Servidor público iniciado, PID',child.pid);
  audit('start',{runner:process.pid,javaPid:child.pid,started,javaVersion:base.java.version,collector:'ParallelGC'});
  let offset=0, intentionalStop=false;
  const timer=setInterval(()=>{const data=fs.readFileSync(commands,'utf8');if(data.length<offset)offset=0;if(data.length>offset){const chunk=data.slice(offset);if(/(?:^|\r?\n)\s*stop\s*(?:\r?\n|$)/i.test(chunk)){if(!intentionalStop)audit('stop-observed',{runner:process.pid,javaPid:child.pid,source:'public-commands.txt',started});intentionalStop=true;}child.stdin.write(chunk);offset=data.length;}},200);
  child.on('error',e=>{console.error(e);clearInterval(timer);process.exitCode=1;});
  child.on('exit',(code,signal)=>{
    clearInterval(timer);fs.closeSync(output);
    const classification=classifyExit(code,intentionalStop,readCheckpoint(root),started);
    const unexpected=classification.unexpected;
    audit('exit',{runner:process.pid,javaPid:child.pid,started,code,signal,...classification});
    const stopped={mode:'managed',pid:child.pid,runner:process.pid,finished:new Date().toISOString(),exitCode:code,signal:signal||null,unexpected,backupInProgress:!unexpected&&code===0};
    fs.writeFileSync(stateFile,JSON.stringify(stopped,null,2));
    console.log('Servidor público finalizado:',code,'signal',signal||'none','unexpected',unexpected);
    const maintenance=read('config/virgos/maintenance.json');
    const maxRestarts=Number.isInteger(maintenance.maxUnexpectedRestarts)?maintenance.maxUnexpectedRestarts:3;
    const delay=Math.max(5,Number(maintenance.restartDelaySeconds)||15)*1000;
    if(unexpected && maintenance.autoRestartOnUnexpectedExit!==false && restartAttempt<maxRestarts){
      fs.writeFileSync(stateFile,JSON.stringify({...stopped,restarting:true,restartAttempt:restartAttempt+1,backupInProgress:false},null,2));
      console.error(`El servidor terminó inesperadamente; reinicio automático ${restartAttempt+1}/${maxRestarts} en ${Math.round(delay/1000)}s.`);
      setTimeout(()=>main(restartAttempt+1).catch(error=>{console.error('El reinicio automático falló:',error.message);process.exitCode=1;}),delay);
      return;
    }
    process.exitCode=(code!==0||unexpected)?(code||1):0;
    if(unexpected||code!==0)return;
    try {
      const completed=JSON.parse(execFileSync('powershell.exe',['-NoProfile','-ExecutionPolicy','Bypass','-File',path.join(root,'scripts/finalizar-ejecucion.ps1'),'-RunStarted',started,'-ExitCode','0'],{cwd:root,windowsHide:true,encoding:'utf8',stdio:'pipe',maxBuffer:1024*1024}).trim());
      console.log('Respaldo completo verificado:',completed.backup);
      fs.writeFileSync(stateFile,JSON.stringify({...stopped,backupInProgress:false},null,2));
      if(completed.restart){console.log('Reiniciando después del checkpoint sin jugadores.');main().catch(error=>{console.error(error.message);process.exitCode=1;});}
    }catch(error){fs.writeFileSync(stateFile,JSON.stringify({...stopped,backupInProgress:false,backupError:true},null,2));console.error('El respaldo automático requiere atención:',error.stderr?.toString()||error.message);process.exitCode=1;}
  });
}
try {
  const release=require('./server-lock.cjs').acquire(root);
  process.on('exit',release);
  main().catch(error=>{console.error(error.message);process.exitCode=1;});
} catch(error) {console.error(error.message);process.exitCode=1;}
