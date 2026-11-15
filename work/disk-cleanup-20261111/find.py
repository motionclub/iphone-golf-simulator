"""Inventory regenerable caches: Unity Library caches + Xcode build roots, with age and in-use flags."""
import os, json, subprocess, time, sys
from pathlib import Path
HOME=Path.home()
roots=[HOME, Path('/private/tmp')]
skip_top={'Library','Applications','Music','Pictures','Movies','Public','.Trash'}
ps=subprocess.check_output(['ps','-axo','command'],text=True)
lsof=subprocess.run(['lsof','-nP','-Fn'],capture_output=True,text=True).stdout
now=time.time()
def newest(p, limit=4000):
    m=0;n=0
    for dp,dn,fn in os.walk(p):
        for f in fn:
            try:m=max(m,os.lstat(os.path.join(dp,f)).st_mtime)
            except OSError:pass
            n+=1
            if n>limit:return m
    return m
def alloc(p):
    try:return int(subprocess.check_output(['du','-sk','--',str(p)],stderr=subprocess.DEVNULL).split()[0])//1024
    except Exception:return -1
rows=[]
for root in roots:
    for dp,dn,fn in os.walk(root):
        d=Path(dp)
        rel=d.relative_to(root)
        if root==HOME and len(rel.parts)==0:
            dn[:]=[x for x in dn if x not in skip_top]
        dn[:]=[x for x in dn if x not in {'.git','node_modules','Assets','Packages'}]
        kind=None
        if 'Library' in dn and 'ProjectSettings' in dn and (d/'Assets').is_dir():kind='unity'
        elif (d/'Build/Intermediates.noindex').is_dir() or (d/'ModuleCache.noindex').is_dir() and (d/'Build').is_dir():kind='xcode'
        if kind:
            s=str(d)
            inuse=(s in ps) or (s in lsof)
            t=d/'Library' if kind=='unity' else d/'Build'
            age=(now-newest(t))/3600
            rows.append(dict(kind=kind,path=s,inuse=inuse,age_h=round(age,1),mb=alloc(t)))
            if kind=='xcode':dn[:]=[]
            else:dn[:]=[x for x in dn if x not in {'Library','Temp','Logs'}]
        if len(rel.parts)>9:dn[:]=[]
json.dump(rows,open(sys.argv[1],'w'),indent=1)
for r in sorted(rows,key=lambda r:-r['mb']):print(f"{r['kind']:5} {r['mb']:>7}MB {r['age_h']:>7}h {'INUSE' if r['inuse'] else '     '} {r['path']}")
