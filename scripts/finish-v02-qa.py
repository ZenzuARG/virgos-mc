"""Record public voice evidence and retire only our temporary public QA identity."""
from pathlib import Path
import json, time
root=Path(__file__).resolve().parents[1]
folder=root/'client/standard/virgos-qa'
server=(root/'logs/latest.log').read_text('utf-8',errors='replace')
client=(root/'client/standard/logs/latest.log').read_text('utf-8',errors='replace')
account=json.loads((root/'.cache/qa-account-2.json').read_text('utf-8'))
assert account['name']=='VirgosQA2'
assert 'VirgosQA2 logged in' in server
assert 'successfully connected to voice chat' in server
assert 'Server acknowledged connection check' in client
assert 'Could not match UDP packet to a tunnel' not in server
assert 'vozConectados=1' in server
report={
    'gameEndpoint':'virgos-mc.playit.plus',
    'voiceEndpoint':'practically-accountant.tun.ply.gg:2685',
    'coreStatus':[line for line in server.splitlines() if 'vozConectados=1' in line][-1],
    'authenticatedGameLogin':True,
    'voiceAuthenticatedAndConnected':True,
    'publicUdpEcho':json.loads((root/'.lab/reports/voice-ping-public.json').read_text('utf-8')),
    'scope':'Real Forge client and public UDP handshake. No microphone capture or human listening test.',
    'playitPatch':json.loads((root/'versions.lock.json').read_text('utf-8'))['playitCompanion']['version']}
def send(action):
    with (folder/'commands.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(action)+'\n')
start=len(client)
send({'action':'command','value':'unregister '+account['password']})
deadline=time.monotonic()+20
while time.monotonic()<deadline:
    client=(root/'client/standard/logs/latest.log').read_text('utf-8',errors='replace')
    # Server log is authoritative; never include the command or secret in output.
    server=(root/'logs/latest.log').read_text('utf-8',errors='replace')
    if 'VirgosQA2 unregistered' in server or 'Unregistered player VirgosQA2' in server:
        report['testAccountUnregistered']=True;break
    time.sleep(.5)
else:
    report['testAccountUnregistered']='Check AuthMe database before completion'
send({'action':'quit'})
(root/'.lab/reports/qa-v02-public-voice.json').write_text(json.dumps(report,indent=2),'utf-8')
print(json.dumps(report))
