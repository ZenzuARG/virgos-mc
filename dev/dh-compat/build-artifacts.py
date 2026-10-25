"""Build a pinned laboratory dependency patch; never changes installed files."""
import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
import os
from pathlib import Path

ORIGINAL = 'a537a71171d935540b56b7598d0de2c106f6f5026336c713d89a1d9ea0ea14e3'
DH_NAME = 'DistantHorizons-3.3.3-1.20.1-fabric-forge.jar'
ADDON_NAME = 'virgos_dh_compat-0.1.0.jar'
HELPER = 'com/seibel/distanthorizons/core/lab/SemanticPointComparison.class'
TARGET = 'com/seibel/distanthorizons/core/dataObjects/fullData/sources/FullDataSourceV2.class'
FORBIDDEN = [Path('D:/proyectos/mc-server'), Path('C:/Users/zulia/AppData/Local/Virgos-MC/juego')]

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def jdk_tools(java_home, windows=None):
    suffix = '.exe' if (os.name == 'nt' if windows is None else windows) else ''
    return tuple(Path(java_home) / 'bin' / (name + suffix) for name in ['java', 'javac'])

def validate(original, addon, asm, output):
    original, addon, asm = [Path(p).resolve(strict=True) for p in (original, addon, asm)]
    output = Path(output).absolute()
    for path in [output, *output.parents]:
        if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()): raise ValueError('Linked output forbidden')
    output = output.resolve()
    if sha(original) != ORIGINAL: raise ValueError('Unrecognized DH input; installed artifact is never patched in place')
    if addon.name != ADDON_NAME: raise ValueError('Unexpected addon artifact name')
    for protected in [*FORBIDDEN, original, addon, asm]:
        protected = protected.resolve()
        if output == protected or output in protected.parents or protected in output.parents:
            raise ValueError('Artifact output overlaps protected input/runtime')
    for path in [output, *output.parents]:
        if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()): raise ValueError('Linked output forbidden')
    return original, addon, asm, output

def build(original, addon, asm, output, java_home, qa=None):
    original, addon, asm, output = validate(original, addon, asm, output)
    root = Path(__file__).resolve().parent
    java_home = Path(java_home).resolve(strict=True)
    java, javac = jdk_tools(java_home)
    if not java.is_file() or not javac.is_file(): raise ValueError('Java 17 JDK required')
    if qa and (not Path(qa).is_file() or not Path(qa).name.startswith('virgos_local_qa-')): raise ValueError('Unexpected observer artifact')
    output.mkdir(parents=True,exist_ok=True); cache = output/'.build'; cache.mkdir(exist_ok=True)
    sources = sorted((root/'patcher').rglob('*.java'))
    subprocess.run([str(javac),'--release','17','-encoding','UTF-8','-d',str(cache),'-cp',os.pathsep.join([str(asm),str(original)]),*[str(p) for p in sources]],check=True)
    intermediate = cache/'patched-unbundled.jar'
    subprocess.run([str(java),'-cp',os.pathsep.join([str(asm),str(cache)]),'PatchDh',str(output),str(original),str(intermediate)],check=True)
    target = output/DH_NAME
    # Fixed timestamps/order and a fixed compiler toolchain make identical inputs reproducible.
    with zipfile.ZipFile(intermediate) as source, zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as result:
        for name in sorted([*source.namelist(), HELPER]):
            entry = zipfile.ZipInfo(name,(2026,1,1,0,0,0)); entry.compress_type=zipfile.ZIP_DEFLATED
            entry.create_system=3;entry.external_attr=0o100644 << 16
            data=(cache/HELPER).read_bytes() if name==HELPER else source.read(name)
            result.writestr(entry,data)
    with zipfile.ZipFile(original) as before, zipfile.ZipFile(target) as after:
        changed=[n for n in before.namelist() if before.read(n)!=after.read(n)]
        if changed != [TARGET] or set(after.namelist())-set(before.namelist())!={HELPER}: raise ValueError('Unexpected patch footprint')
    shutil.copyfile(addon,output/ADDON_NAME)
    names=[DH_NAME,ADDON_NAME]
    if qa: shutil.copyfile(qa,output/Path(qa).name);names.append(Path(qa).name)
    manifest={'schema':1,'originalDhSha256':ORIGINAL,'fixVersion':'semantic-merge-v2','artifacts':[{'filename':n,'sha256':sha(output/n)} for n in names]}
    (output/'compat-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['original','addon','asm','output','java-home']:parser.add_argument('--'+name,required=True)
    parser.add_argument('--qa')
    a=parser.parse_args()
    try: print(json.dumps(build(a.original,a.addon,a.asm,a.output,a.java_home,a.qa)))
    except (ValueError,OSError,subprocess.CalledProcessError) as error:parser.exit(1,'Build refused: '+str(error)+'\n')
