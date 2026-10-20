"""arm clay views in a frame along the arm axis.  python3 armviews.py <tag> <side R|L> [out.png] [scale]"""
import subprocess, sys, os
import numpy as np
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-arms-hands-form2'
sys.path.insert(0,W)
from sheetlib import sheet
tag=sys.argv[1]; sd=sys.argv[2]; outp=sys.argv[3] if len(sys.argv)>3 else f'{W}/proof/it/{tag}_arm_{sd}.png'; scale=sys.argv[4] if len(sys.argv)>4 else '0.95'
side=+1 if sd=='R' else -1
AX=np.array([0.678,-0.178,-0.713]); AX/=np.linalg.norm(AX)
C0=np.array([0.437,-0.061,1.064])      # shoulder-ish reference on the right arm
ctr=np.array([0.43,-0.065,1.10])        # middle of the arm
def mirror(v): 
    v=np.array(v,float); 
    if side<0: v[0]=-v[0]
    return v
c=mirror(ctr)
vecs={'front':(0,-1,0),'back':(0,1,0),'outer':(1,0,0.1) if side>0 else (-1,0,0.1),'inner':(-1,0,-0.1) if side>0 else (1,0,-0.1),'top':(0,0,1),'q_front_out':(0.7,-0.7,0.2) if side>0 else (-0.7,-0.7,0.2)}
sp=[]
for n,v in vecs.items():
    d=np.array(v,float); d/=np.linalg.norm(d)
    up=np.array([0,0,1.0]) if n!='top' else np.array([0,1.0,0])
    sp.append(f'{n}:{",".join("%.5f"%x for x in c)}:{",".join("%.5f"%x for x in d)}:{scale}:55:-40:{",".join("%.5f"%x for x in up)}')
cand='base' if tag=='base' else f'{W}/data/cand_{tag}.npz'
od=f'{W}/proof/it/{tag}_arm{sd}'
env=dict(os.environ); env.setdefault('CLIP','0.45'); env.setdefault('FAR','0.45'); env.setdefault('RES','900')
cmd=['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup',f'{W}/baseline/HeroBase_Male_Silhouette.blend','--python',f'{W}/closeup3.py','--',cand,od]+sp
r=subprocess.run(cmd,capture_output=True,text=True,env=env)
if 'CLOSEUP_DONE' not in r.stdout: print(r.stdout[-800:],r.stderr[-800:])
print(sheet(od,list(vecs),outp,cols=3,size=520,title=f'{tag} arm {sd}'))
