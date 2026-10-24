"""Validate the official Simple Voice Chat UDP debug echo, without credentials."""
import argparse,socket,struct,time,uuid,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('host');p.add_argument('port',type=int);a=p.parse_args()
ping=uuid.UUID('58bc9ae9-c7a8-45e4-a11c-efbb67199425').bytes
payload=uuid.uuid4().bytes+struct.pack('>q',int(time.time()*1000))
packet=b'\xff'+ping+bytes([len(payload)])+payload
with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
    sock.settimeout(5)
    for attempt in range(3):
        start=time.monotonic();sock.sendto(packet,(a.host,a.port))
        try:response,source=sock.recvfrom(4096)
        except TimeoutError:
            if attempt==2:raise
            continue
        if response!=payload:raise ValueError('Unexpected UDP response')
        result={'endpoint':f'{a.host}:{a.port}','verifiedEcho':True,'roundTripMs':round((time.monotonic()-start)*1000,2),'source':source};print(json.dumps(result));break
    out=Path(__file__).resolve().parents[1]/'.lab/reports'/('voice-ping-'+('local' if a.host=='127.0.0.1' else 'public')+'.json')
    out.write_text(json.dumps(result,indent=2),'utf-8')
