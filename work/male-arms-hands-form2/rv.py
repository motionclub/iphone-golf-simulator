"""render views of a candidate: python3 rv.py <tag> [R|L|RL] [scale] [name=views subset...]"""
import subprocess, sys, os, time
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-arms-hands-form2')
from views import specs
from sheetlib import sheet
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-arms-hands-form2'
tag=sys.argv[1]; sides=sys.argv[2] if len(sys.argv)>2 else 'R'; scale=float(sys.argv[3]) if len(sys.argv)>3 else 0.26
wire = os.environ.get('WIRE')
cand = 'base' if tag=='base' else f'{W}/data/cand_{tag}.npz'
for sd in sides:
    side = +1 if sd=='R' else -1
    sp = specs(side, scale, center=(0.0,0.0,0.065))
    out = f'{W}/proof/it/{tag}{"_wire" if wire else ""}/{sd}'
    env = dict(os.environ); env.setdefault('CLIP','0.10'); env.setdefault('FAR','0.12')
    cmd=['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup',f'{W}/baseline/HeroBase_Male_Silhouette.blend','--python',f'{W}/closeup3.py','--',cand,out]+sp
    t=time.time(); r=subprocess.run(cmd,capture_output=True,text=True,env=env)
    if 'CLOSEUP_DONE' not in r.stdout: print(r.stdout[-1500:], r.stderr[-1500:])
    names=[s.split(':')[0] for s in sp]
    p=sheet(out,names,f'{W}/proof/it/{tag}{"_wire" if wire else ""}_{sd}_sheet.png',cols=4,size=480,title=f'{tag} {sd}')
    print(p, '%.1fs'%(time.time()-t))
