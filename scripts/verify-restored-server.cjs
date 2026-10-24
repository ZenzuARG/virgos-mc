/* Boot a recovered lab backup on a separate localhost port, audit and stop.
 * This never starts or modifies the public server.
 */
const fs=require('node:fs');
const path=require('node:path');
const net=require('node:net');
const {spawn}=require('node:child_process');
const root=path.resolve(__dirname,'..');
const allowed=fs.realpathSync(path.join(root,'.lab','restore-check'))+path.sep;
if(!process.argv[2])throw Error('Provide the recovered folder.');
const cwd=fs.realpathSync(path.resolve(process.argv[2]));
if(!cwd.toLowerCase().startsWith(allowed.toLowerCase()))throw Error('Only isolated restore-check folders are allowed.');
const recovery=JSON.parse(fs.readFileSync(path.join(cwd,'restore-verification.json'),'utf8').replace(/^\uFEFF/,''));
const mods=fs.readdirSync(path.join(cwd,'mods')).filter(f=>f.endsWith('.jar'));
if(mods.some(f=>f.toLowerCase().includes('playit')))throw Error('Recovery verification must have no public tunnel.');
const stateFile=path.join(cwd,'runtime-verification-process.json');
if(fs.existsSync(stateFile)){
  const old=JSON.parse(fs.readFileSync(stateFile,'utf8'));
  if(old.pid&&!old.finished){
    try{process.kill(old.pid,0);throw Error('This recovery test is still running.');}
    catch(error){if(error.code!=='ESRCH')throw error;}
  }
}
const propertiesFile=path.join(cwd,'server.properties');
let properties=fs.readFileSync(propertiesFile,'utf8');
if(!/^server-ip=127\.0\.0\.1$/m.test(properties))throw Error('Expected a localhost-only recovered lab.');
properties=properties.replace(/^server-port=\d+$/m,'server-port=25576');
fs.writeFileSync(propertiesFile,properties);
// Libraries are reproducible launcher dependencies, excluded from the backup.
// Copy the existing verified runtime cache instead of redownloading it.
const libraries=path.join(cwd,'libraries');
if(!fs.existsSync(libraries))fs.cpSync(path.join(root,'.lab','server','libraries'),libraries,{recursive:true,errorOnExist:true,force:false});
const base=JSON.parse(fs.readFileSync(path.join(root,'versions.lock.json'),'utf8'));
const serverLog=path.join(cwd,'runtime-verification.log');
const reportFile=path.join(root,'.lab','reports','restore-runtime-verification.json');
const auditPath=path.join(cwd,'virgos-reports','bastion-audit.json');

async function main(){
  await new Promise((resolve,reject)=>{
    const probe=net.createServer();probe.once('error',reject);
    probe.listen(25576,'127.0.0.1',()=>probe.close(resolve));
  });
  const started=Date.now();
  const output=fs.openSync(serverLog,'w');
  const args=['-Xms1G','-Xmx5G','-Dfile.encoding=UTF-8','-jar','ketting-server.jar',
    '-minecraftVersion',base.minecraft,'-forgeVersion',base.forge,'-kettingVersion',base.ketting,'-daul','-dau','-noui','nogui'];
  const child=spawn(path.join(root,'.runtime',base.java.folder,'bin','java.exe'),args,{cwd,stdio:['pipe',output,output],windowsHide:true});
  fs.writeFileSync(stateFile,JSON.stringify({pid:child.pid,started:new Date(started).toISOString()}));
  console.log('Recovered server booting locally on 25576, PID',child.pid);
  let requested=false,stopping=false,timeout=false,audit=null,bootReady=false;
  const stop=()=>{if(!stopping){stopping=true;child.stdin.write('save-all flush\nstop\n');}};
  const poll=setInterval(()=>{
    try{
      const log=fs.readFileSync(serverLog,'utf8');
      bootReady=log.includes('Done (') && log.includes('Virgos: AuthMe bridge ready');
      if(bootReady&&!requested){requested=true;child.stdin.write('virgos status\nvirgos audit\n');console.log('Recovered world is ready; checking the saved spawn.');}
      if(requested&&fs.existsSync(auditPath)&&fs.statSync(auditPath).mtimeMs>=started){
        audit=JSON.parse(fs.readFileSync(auditPath,'utf8'));stop();
      }
      if(Date.now()-started>300000&&!stopping){timeout=true;console.log('Recovery verification timed out; requesting a clean stop.');stop();}
    }catch(error){console.error(error.message);timeout=true;stop();}
  },1000);
  child.on('error',error=>{clearInterval(poll);fs.closeSync(output);console.error(error);process.exitCode=1;});
  child.on('exit',code=>{
    clearInterval(poll);fs.closeSync(output);
    const finished=new Date().toISOString();
    fs.writeFileSync(stateFile,JSON.stringify({pid:child.pid,finished,exitCode:code}));
    const passed=code===0 && bootReady && !timeout && audit && audit.checked>100000
      && ['missing','unsupported','blockedWalkChecks','routeProblems'].every(key=>Array.isArray(audit[key])&&audit[key].length===0);
    const report={passed:!!passed,recoveredFolder:cwd,recovery,port:25576,publicTunnel:false,mods:mods.length,
      started:new Date(started).toISOString(),finished,exitCode:code,audit,
      dimensions:fs.readdirSync(cwd).filter(name=>name.startsWith('virgos_world')&&fs.statSync(path.join(cwd,name)).isDirectory())};
    fs.writeFileSync(reportFile,JSON.stringify(report,null,2));
    console.log(passed?'PASS: recovered server booted, audited its spawn and stopped cleanly.':'FAIL: inspect '+reportFile);
    process.exitCode=passed?0:1;
  });
}
main().catch(error=>{console.error(error);process.exitCode=1;});
