import json,os,subprocess,sys
from pathlib import Path
home=Path.home(); apply=len(sys.argv)>1
rows=json.load(open('preflight.json'))
ps=subprocess.check_output(['ps','-axo','command'],text=True)
lsof=subprocess.run(['lsof','-nP','-Fn'],capture_output=True,text=True).stdout
skip=[home/'Setup Guide In-Editor Tutorial']
out=[]
for r in rows:
    p=Path(r['path'])
    if r['kind']!='unity' or r['age_h']<168 or not str(p).startswith(str(home)+'/'): continue
    if 'Documents/Codex' in str(p) or p in skip: continue
    if str(p) in ps or str(p) in lsof: print('IN USE skip',p); continue
    out.append(p)
for p in out: print(('DEL ' if apply else 'would ')+str(p))
if apply:
    import shutil
    with open('clones_journal.txt','a') as j:
        for p in out:
            shutil.rmtree(p,ignore_errors=True); j.write(str(p)+'\n'); print('deleted',p,flush=True)
