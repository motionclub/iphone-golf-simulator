"""zoomed views of a candidate: python3 rv2.py <tag> <side R|L> <views: radial,palmar,...> [scale] [center a,n,w]  (WIRE=1 for wire)"""
import subprocess, sys, os, time
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-hands-form3'
sys.path.insert(0,W)
from views import specs, local_dir
from sheetlib import sheet
tag=sys.argv[1]; sd=sys.argv[2]; names=sys.argv[3].split(','); scale=float(sys.argv[4]) if len(sys.argv)>4 else 0.12
center=tuple(float(x) for x in sys.argv[5].split(',')) if len(sys.argv)>5 else (0.04,0.01,0.03)
side=+1 if sd=='R' else -1
V={'dorsal':((0,-1,0),(0,0,-1)),'palmar':((0,1,0),(0,0,-1)),'radial':((1,0,0),(0,0,-1)),'ulnar':((-1,0,0),(0,0,-1)),
   'q_dorsal_radial':((0.8,-0.6,0),(0,0,-1)),'q_palmar_radial':((0.8,0.6,0),(0,0,-1)),'q_palmar_ulnar':((-0.7,0.7,0),(0,0,-1)),'dist':((0,0,1),(0,-1,0)),
   'prox':((0,0,-1),(0,-1,0)),'top_radial':((0.5,0.0,-0.85),(0,0,-1)),'q_front':((0.6,0.3,0.74),(0,1,0)),'palmar_tilt':((0.3,0.9,-0.3),(0,0,-1)),'radial_up':((1,0,0),(0,-1,0))}
sp=specs(side,scale,center=center,views={n:V[n] for n in names})
cand='base' if tag=='base' else f'{W}/data/cand_{tag}.npz'
out=f'{W}/proof/it/{tag}_zoom{"_wire" if os.environ.get("WIRE") else ""}/{sd}'
env=dict(os.environ); env.setdefault('CLIP','0.10'); env.setdefault('FAR','0.12'); env.setdefault('RES','900')
cmd=['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup',f'{W}/baseline/HeroBase_Male_Silhouette.blend','--python',f'{W}/closeup3.py','--',cand,out]+sp
r=subprocess.run(cmd,capture_output=True,text=True,env=env)
if 'CLOSEUP_DONE' not in r.stdout: print(r.stdout[-1500:], r.stderr[-1500:])
cols=min(len(names),3)
p=sheet(out,names,f'{W}/proof/it/{tag}_zoom{"_wire" if os.environ.get("WIRE") else ""}_{sd}.png',cols=cols,size=640,title=f'{tag} {sd} zoom c={center} s={scale}')
print(p)
