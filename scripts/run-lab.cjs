const {spawn}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const cwd=path.join(root,'.lab','server');
const base=JSON.parse(fs.readFileSync(path.join(root,'versions.lock.json'),'utf8'));
const props=fs.readFileSync(path.join(cwd,'server.properties'),'utf8');
if(!/^server-ip=127\.0\.0\.1$/m.test(props)||!/^server-port=25575$/m.test(props))throw Error('El laboratorio debe escuchar sólo en 127.0.0.1:25575');
if(fs.readdirSync(path.join(cwd,'mods')).some(f=>f.includes('playit')))throw Error('No se permite Playit en el laboratorio');
const stateFile=path.join(cwd,'process.json');
if(fs.existsSync(stateFile)){
  const previous=JSON.parse(fs.readFileSync(stateFile,'utf8'));
  try{process.kill(previous.pid,0);throw Error('El laboratorio todavía está en ejecución');}
  catch(e){if(e.code!=='ESRCH')throw e;}
}
const commands=path.join(cwd,'console-commands.txt');
fs.writeFileSync(commands,'');
const log=fs.openSync(path.join(cwd,'console.log'),'w');
const java=path.join(root,'.runtime',base.java.folder,'bin','java.exe');
const args=['-Xms1G','-Xmx6G','-Dfile.encoding=UTF-8','-jar','ketting-server.jar','-minecraftVersion',base.minecraft,'-forgeVersion',base.forge,'-kettingVersion',base.ketting,'-daul','-dau','-noui','nogui'];
const child=spawn(java,args,{cwd,stdio:['pipe',log,log],windowsHide:true});
let offset=0;
fs.writeFileSync(stateFile,JSON.stringify({pid:child.pid,runner:process.pid,started:new Date().toISOString(),cwd},null,2));
console.log('Laboratorio iniciado, PID',child.pid);
const timer=setInterval(()=>{
  const content=fs.readFileSync(commands,'utf8');
  if(content.length<offset)offset=0;
  if(content.length>offset){child.stdin.write(content.slice(offset));offset=content.length;}
},200);
child.on('error',e=>{console.error(e);clearInterval(timer);process.exitCode=1;});
child.on('exit',code=>{
  clearInterval(timer);fs.closeSync(log);
  fs.writeFileSync(stateFile,JSON.stringify({pid:child.pid,exitCode:code,finished:new Date().toISOString(),cwd},null,2));
  console.log('Laboratorio finalizado:',code);process.exitCode=code||0;
});
