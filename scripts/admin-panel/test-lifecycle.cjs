'use strict';
// Explicit maintenance test: refuses to stop Minecraft while players are present.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),base='http://127.0.0.1:8765';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const html=await(await fetch(base)).text(),token=html.match(/name="panel-token" content="([a-f0-9]+)"/)[1];
  async function api(route,body){const r=await fetch(base+'/api/'+route,{method:body?'POST':'GET',headers:{'X-Panel-Token':token,...(body?{'Content-Type':'application/json',Origin:base}:{})},body:body?JSON.stringify(body):undefined});const data=await r.json();if(!r.ok)throw Error(data.error);return data;}
  let initial=await api('status');const resume=process.argv.includes('--resume');
  if(resume) {
    const run=JSON.parse(fs.readFileSync(path.join(root,'.runtime/active-run.json'),'utf8'));
    const pending=JSON.parse(fs.readFileSync(path.join(root,'.runtime/panel-operation.json'),'utf8'));
    assert.equal(pending.action,'stop');assert.ok(Date.now()-Date.parse(pending.requestedAt)<900000);assert.ok(['backup','stopping','offline'].includes(initial.state));initial={...initial,pid:run.pid};
  } else {assert.equal(initial.state,'online');assert.equal(initial.online,0,'Maintenance test refuses to stop a populated server');}
  const changes=[];let last='';
  async function until(wanted,timeout){const end=Date.now()+timeout;while(Date.now()<end){const s=await api('status');if(s.state!==last){console.log(s.state);changes.push({at:new Date().toISOString(),state:s.state});last=s.state;}if(s.state==='error')throw Error(s.detail);if(s.state===wanted)return s;await sleep(2000);}throw Error('Timed out waiting for '+wanted);}
  if(!resume)await api('action',{action:'stop',confirm:'stop'});
  const stopped=await until('offline',360000);
  assert.ok(Date.parse(stopped.backup?.completed)>Date.now()-360000,'A fresh verified backup is required');assert.equal(stopped.backup.worlds,6);
  await api('action',{action:'start'});
  const started=await until('online',360000);assert.notEqual(started.pid,initial.pid);assert.equal(started.canCommand,true);
  await api('action',{action:'command',command:'list',confirm:'command'});
  const result={passed:true,initialPid:initial.pid,finalPid:started.pid,backup:stopped.backup,changes,completed:new Date().toISOString()};fs.writeFileSync(path.join(root,'.lab/admin-panel/lifecycle-result.json'),JSON.stringify(result,null,2));console.log('Real shutdown, verified backup, start and console passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
