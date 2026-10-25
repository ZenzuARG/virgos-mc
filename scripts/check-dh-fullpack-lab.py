"""Exercise only the authorized local laboratory through normal QA actions."""
import argparse, hashlib, json, shutil, sqlite3, time
from pathlib import Path
from dh_fullpack_lab import policy

# 1024 blocks from spawn: outside both vanilla distance and the old 32-chunk gate.
FIXTURE_SECTION_X = 16
FIXTURE_X = FIXTURE_SECTION_X * 64
VIEW_X = FIXTURE_X - 256
# Chunk import competes with initial generation; this is a bounded convergence
# check, not a claim of instantaneous updates under that load.
SERVER_UPDATE_DEADLINE = 150

class Proof:
 def __init__(self, lab, role):
  self.lab=Path(lab).resolve();self.role=role;self.name='VirgosQA2' if role=='client2' else 'VirgosQA1'
  if self.lab!=policy.AUTHORIZED_LAB.resolve() or role not in {'client','client2'}:raise ValueError('Unauthorized laboratory role')
  self.output=self.lab/'proof'/role
  for path in [self.output,*self.output.parents]:
   if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()):raise ValueError('Linked proof output')
  self.output.mkdir(parents=True,exist_ok=True);self.checks={}
 def read(self,p):
  try:return json.loads(policy.regular(p).read_text('utf-8-sig'))
  except (OSError,ValueError):return {}
 def live(self):
  for role in ['server',self.role]:
   state=self.read(self.lab/role/'process.json')
   if state.get('finished'):raise RuntimeError(role+' stopped during proof: '+str(state))
 def wait(self,test,seconds,label):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   self.live()
   try:
    result=test()
    if result:return result
   except (OSError,sqlite3.Error,json.JSONDecodeError):pass
   time.sleep(.25)
  raise RuntimeError('Deadline: '+label)
 def save(self,label,value):
  path=self.output/(label+'.json')
  for p in [path,*path.parents]:
   if p.is_symlink() or (hasattr(p,'is_junction') and p.is_junction()):raise ValueError('Linked output')
  path.write_text(json.dumps(value,indent=2),encoding='utf-8')
 def action(self,action,**extra):
  q=policy.regular(self.lab/self.role/'virgos-qa/commands.jsonl')
  with q.open('a',encoding='utf-8') as stream:stream.write(json.dumps({'action':action,**extra})+'\n')
 def command(self,command):
  q=policy.regular(self.lab/'server/commands.txt')
  with q.open('a',encoding='utf-8') as stream:stream.write(command+'\n')
 def status(self):return self.read(self.lab/self.role/'virgos-qa/status.json')
 def audit(self,label):
  p=self.lab/self.role/'virgos-qa/dh-audit.json';stamp=time.time();self.action('audit_dh')
  value=self.wait(lambda:self.read(p) if p.exists() and p.stat().st_mtime>=stamp and not self.read(p).get('pending') else None,25,label)
  self.save(label,value);return value
 def row(self,role):
  paths=[self.lab/'server/virgos_world/data/DistantHorizons.sqlite'] if role=='server' else list((self.lab/role/'Distant_Horizons_server_data').rglob('DistantHorizons.sqlite'))
  for path in paths:
   if not path.exists() or (role!='server' and 'overworld' not in str(path.parent)):continue
   policy.regular(path)
   with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=3) as db:
    db.execute('PRAGMA query_only=ON');db.row_factory=sqlite3.Row
    try:row=db.execute('SELECT * FROM FullData WHERE DetailLevel=0 AND PosX=? AND PosZ=0',(FIXTURE_SECTION_X,)).fetchone()
    except sqlite3.OperationalError:continue
    if row:
     return {k:({'sha256':hashlib.sha256(row[k]).hexdigest(),'bytes':len(row[k])} if isinstance(row[k],bytes) else row[k]) for k in row.keys()}
  return None
 def same(self,a,b):return a is not None and b is not None and all(a[k]==b[k] for k in ['Data','Mapping'])
 def changed(self,previous):
  current=self.row('server')
  # Palettes retain previously seen blocks; reusing one can change Data alone.
  return current if current is not None and not self.same(current,previous) else None
 def converged(self,label):
  def check():
   a,b=self.row('server'),self.row(self.role)
   return {'server':a,'client':b} if self.same(a,b) else None
  result=self.wait(check,150,label);self.save(label,result);self.checks[label]=True;return result
 def auth(self,initial):
  # These are disposable, offline, whitelisted QA accounts in a fresh AuthMe DB.
  if initial:self.action('command',value='register LabOnly2026Test LabOnly2026Test')
  self.action('command',value='login LabOnly2026Test')
  end=time.monotonic()+75
  while time.monotonic()<end:
   audit=self.audit('auth-negotiation')
   if audit.get('serverReady'):return audit
   time.sleep(2)
  raise RuntimeError('Native DH did not become ready after normal AuthMe login; no repair was sent')
 def position(self):
  # Legitimate proximity avoids a cold cache's nearest-first backlog, never visiting the fixture.
  self.command(f'tp {self.name} {VIEW_X} 201 0')
  self.wait(lambda:abs(self.status().get('x',0)-VIEW_X)<2,30,'remote viewing position')
  audit=self.audit('remote-viewing-position')
  if audit.get('remoteVanillaChunkPresent') is not False:raise RuntimeError('Remote fixture entered vanilla cache')
 def chunky_active(self,label):
  log=policy.regular(self.lab/'server/console.log');offset=log.stat().st_size
  self.command('forge:chunky progress')
  def check():
   with log.open('rb') as stream:
    stream.seek(offset);lines=stream.read().decode('utf-8',errors='replace').splitlines()
   if any('[Chunky] No tasks running.' in line for line in lines):raise RuntimeError('Chunky ended before '+label)
   progress=[line for line in lines if '[Chunky] Task running for minecraft:overworld.' in line]
   return {'observedAt':time.time(),'progress':progress[-1]} if progress else None
  self.save(label,self.wait(check,20,label));self.checks[label]=True
 def visual(self):
  self.action('look',yaw=-90,pitch=8)
  self.wait(lambda:abs(self.status().get('yaw',0)+90)<2,10,'remote viewing direction')
  folder=self.lab/self.role/'screenshots';previous=set(folder.glob('virgos-qa-*.png'))
  self.action('screenshot')
  def captured():
   for path in folder.glob('virgos-qa-*.png'):
    if path not in previous and path.read_bytes().endswith(b'\x00\x00\x00\x00IEND\xaeB`\x82'):return policy.regular(path)
  source=self.wait(captured,30,'remote visual screenshot')
  shutil.copy2(source,self.output/'remote-fixture.png')
  audit=self.audit('remote-visual-audit')
  if audit.get('remoteVanillaChunkPresent') is not False or audit.get('rendererDisabledByException') is not False:raise RuntimeError('Visual evidence lacks an active remote renderer')
  self.checks['remote-visual-captured']=True
 def probe(self,label,**extra):
  p=self.lab/self.role/'virgos-qa/merge-probe.json';stamp=time.time();self.action('probe_dh_merge',**extra)
  d=self.wait(lambda:self.read(p) if p.exists() and p.stat().st_mtime>=stamp else None,45,label);self.save(label,d);return d
 def run(self):
  self.wait(lambda:self.status().get('screen')=='net.minecraft.client.gui.screens.TitleScreen',240,'title')
  if self.row(self.role) is not None:raise RuntimeError('Expected an independent fresh LOD cache')
  self.command(f'forceload add {FIXTURE_X} 0 {FIXTURE_X+63} 63')
  self.command(f'fill {FIXTURE_X} 200 0 {FIXTURE_X+63} 201 63 minecraft:stone')
  self.command(f'forceload add {VIEW_X-8} -8 {VIEW_X+7} 7')
  self.command(f'fill {VIEW_X-8} 200 -8 {VIEW_X+7} 200 7 minecraft:glass')
  self.command('save-all')
  self.wait(lambda:self.row('server'),90,'remote server fixture')
  self.checks['fixture-beyond-legacy-boundary']=True
  self.checks['fresh-cache-before-join']=True;self.action('connect')
  self.wait(lambda:self.status().get('screen')=='game' and self.status().get('name')==self.name,100,'first playable world')
  # Deliberately wait like a human before authenticating; do not race the gate.
  time.sleep(10);pre=self.audit('before-auth')
  if self.row(self.role) is not None:raise RuntimeError('Remote fixture arrived before authentication')
  self.checks['no-remote-lod-before-auth']=True
  # Start after client boot, so a slow menu cannot consume the test workload.
  for command in ['world minecraft:overworld','shape circle','center 16384 0','radius 1024','start']:
   self.command('forge:chunky '+command)
  self.chunky_active('chunky-active-before-auth')
  ready=self.auth(True)
  if ready.get('remoteVanillaChunkPresent') is not False:raise RuntimeError('Fixture is not proven outside vanilla chunk cache')
  self.checks['native-ready-without-repair']=True;self.checks['outside-vanilla-cache']=True
  if ready.get('negotiated',{}).get('getGeneratorPlan')!='CHUNKS_ONLY':raise RuntimeError('Chunky disabled cached serving')
  self.position()
  self.converged('fresh-shared-download');self.save('authenticated-status',self.status())
  self.chunky_active('chunky-active-after-fresh-download')
  d=self.probe('palette-regression',fixture=True)
  if not d.get('reportedChanged') or d.get('fullAfter')!=d.get('fullIncoming') or d.get('fullBefore')==d.get('fullIncoming'):raise RuntimeError('Palette regression')
  d=self.probe('identical-noop',fixture=True,same=True)
  if d.get('reportedChanged') or not d.get('fullBefore')==d.get('fullIncoming')==d.get('fullAfter'):raise RuntimeError('No-op regression')
  self.checks['palette-regression-and-noop']=True
  old=self.row('server');self.command(f'fill {FIXTURE_X} 200 0 {FIXTURE_X+63} 200 63 create:andesite_casing');self.command('save-all')
  self.wait(lambda:self.changed(old),SERVER_UPDATE_DEADLINE,'server material update')
  self.converged('live-modded-material')
  self.chunky_active('chunky-active-after-material-update')
  old=self.row('server');self.command(f'fill {FIXTURE_X} 201 0 {FIXTURE_X+63} 207 63 minecraft:diamond_block');self.command('save-all')
  self.wait(lambda:self.changed(old),SERVER_UPDATE_DEADLINE,'server geometry update')
  self.converged('live-geometry')
  self.chunky_active('chunky-active-after-geometry-update')
  old=self.row(self.role);self.action('disconnect');self.wait(lambda:self.status().get('screen')=='net.minecraft.client.gui.screens.TitleScreen',40,'disconnect')
  time.sleep(2);self.command(f'fill {FIXTURE_X} 201 0 {FIXTURE_X+63} 207 63 minecraft:emerald_block');self.command('save-all')
  self.wait(lambda:self.changed(old),SERVER_UPDATE_DEADLINE,'offline material update')
  self.chunky_active('chunky-active-before-reconnect')
  self.action('connect');self.wait(lambda:self.status().get('screen')=='game',100,'reconnect world');self.auth(False);self.position()
  self.converged('cached-reconnect-refresh')
  self.chunky_active('chunky-active-after-reconnect')
  self.visual()
  final=self.row(self.role);self.save('before-client-close',final);self.action('quit')
  end=time.monotonic()+45
  while time.monotonic()<end:
   if self.read(self.lab/self.role/'process.json').get('finished'):break
   time.sleep(.25)
  else:raise RuntimeError('Client did not close')
  if not self.same(final,self.row(self.role)):raise RuntimeError('Cache changed during close')
  self.checks['client-cache-persisted']=True;self.save('after-client-close',self.row(self.role));return self.checks

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--lab',required=True);p.add_argument('--role',choices=['client','client2'],default='client2');a=p.parse_args();proof=Proof(a.lab,a.role)
 try:
  checks=proof.run();proof.save('result',{'status':'PASS','checks':checks});print(json.dumps({'status':'PASS','checks':checks}))
 except Exception as error:
  proof.save('result',{'status':'PARTIAL','checks':proof.checks,'error':str(error),'statusSnapshot':proof.status()});print(json.dumps({'status':'PARTIAL','error':str(error)}));raise SystemExit(1)
 finally:
  proof.command('forge:chunky pause minecraft:overworld')
