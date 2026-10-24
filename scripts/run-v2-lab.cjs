const fs=require('node:fs');
const path=require('node:path');
const {spawn}=require('node:child_process');
const root=path.resolve(__dirname,'..'),cwd=path.join(root,'.lab/v2/server');
const base=JSON.parse(fs.readFileSync(path.join(root,'versions.lock.json'),'utf8').replace(/^\uFEFF/,''));
const props=fs.readFileSync(path.join(cwd,'server.properties'),'utf8');
if(!/^server-ip=127\.0\.0\.1$/m.test(props)||!/^server-port=25575$/m.test(props))throw Error('Laboratory must be local only');
if(fs.readdirSync(path.join(cwd,'mods')).some(f=>f.includes('playit')))throw Error('No tunnel in lab');
const stateFile=path.join(cwd,'process.json');
if(fs.existsSync(stateFile)){const old=JSON.parse(fs.readFileSync(stateFile,'utf8'));if(!old.finished){try{process.kill(old.pid,0);throw Error('Lab still running');}catch(e){if(e.code!=='ESRCH')throw e;}}}
const queue=path.join(cwd,'console-commands.txt');fs.writeFileSync(queue,'');
const log=fs.openSync(path.join(cwd,'console.log'),'w');
const child=spawn(path.join(root,'.runtime',base.java.folder,'bin/java.exe'),['-Xms1G','-Xmx8G','-Dfile.encoding=UTF-8','-jar','ketting-server.jar','-minecraftVersion',base.minecraft,'-forgeVersion',base.forge,'-kettingVersion',base.ketting,'-daul','-dau','-noui','nogui'],{cwd,stdio:['pipe',log,log],windowsHide:true});
fs.writeFileSync(stateFile,JSON.stringify({pid:child.pid,runner:process.pid,started:new Date().toISOString(),cwd},null,2));
let offset=0;const timer=setInterval(()=>{const text=fs.readFileSync(queue,'utf8');if(text.length<offset)offset=0;if(text.length>offset){child.stdin.write(text.slice(offset));offset=text.length;}},250);
child.on('exit',code=>{clearInterval(timer);fs.closeSync(log);fs.writeFileSync(stateFile,JSON.stringify({pid:child.pid,finished:new Date().toISOString(),exitCode:code,cwd},null,2));process.exitCode=code||0;});
child.on('error',error=>{clearInterval(timer);console.error(error.message);process.exitCode=1;});
console.log('Local v2 laboratory PID',child.pid);
