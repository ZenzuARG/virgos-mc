"""Read a local NBT audit file without adding a runtime dependency."""
import argparse
import gzip
import io
import json
import struct
from pathlib import Path


def read_nbt(path):
    data=path.read_bytes()
    if data[:2]==b'\x1f\x8b': data=gzip.decompress(data)
    stream=io.BytesIO(data)
    def number(fmt):
        size=struct.calcsize(fmt)
        return struct.unpack(fmt,stream.read(size))[0]
    def string():
        return stream.read(number('>H')).decode('utf-8',errors='replace')
    def payload(kind):
        if kind in [1,2,3,4,5,6]: return number({1:'>b',2:'>h',3:'>i',4:'>q',5:'>f',6:'>d'}[kind])
        if kind==8: return string()
        if kind==9:
            child=number('>B'); count=number('>i')
            if not 0<=count<=10000000: raise ValueError('Invalid list size')
            return [payload(child) for _ in range(count)]
        if kind==10:
            result={}
            while (child:=number('>B')):
                name=string(); result[name]=payload(child)
            return result
        if kind in [7,11,12]:
            count=number('>i')
            if not 0<=count<=10000000: raise ValueError('Invalid array size')
            return [number({7:'>b',11:'>i',12:'>q'}[kind]) for _ in range(count)]
        raise ValueError('Unsupported NBT tag '+str(kind))
    kind=number('>B'); name=string()
    result=payload(kind)
    if stream.read(1): raise ValueError('Trailing NBT content')
    return {name:result}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('path',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=json.dumps(read_nbt(args.path),ensure_ascii=True,indent=2)
    if args.output: args.output.write_text(result,'utf-8')
    else: print(result)
