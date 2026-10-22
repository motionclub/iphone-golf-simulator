"""before/after zoom of upper arm and forearm.  python3 armzoom.py <before_tag> <after_tag> <out.png>"""
import subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-arms-hands-form2'
sys.path.insert(0,W)
from sheetlib import font, sheet
a,b,outp=sys.argv[1:4]
AX=np.array([0.678,-0.178,-0.713]); AX/=np.linalg.norm(AX); C0=np.array([0.437,-0.061,1.064])
def spec(name,t,d,up=(0,0,1),scale=0.33,side=+1):
    c=C0+AX*t; c=c.copy()
    if side<0: c[0]=-c[0]
    d=np.array(d,float); d/=np.linalg.norm(d)
    if side<0: d[0]=-d[0]
    return f'{name}:{",".join("%.5f"%x for x in c)}:{",".join("%.5f"%x for x in d)}:{scale}:55:-40:{",".join("%.5f"%x for x in up)}'
specs=[spec('upper_front',-0.17,(0,-1,0)),spec('upper_back',-0.17,(0,1,0)),spec('upper_outer',-0.17,(1,0,0.15)),
       spec('fore_front',-0.02,(0,-1,0)),spec('fore_back',-0.02,(0,1,0)),spec('fore_outer',-0.02,(1,0,0.15)),
       spec('delt_front',-0.28,(0,-1,0)),spec('delt_back',-0.28,(0,1,0)),spec('delt_top',-0.28,(0.2,0,1),up=(0,1,0))]
rows=[]
for tag in (a,b):
    cand='base' if tag=='base' else f'{W}/data/cand_{tag}.npz'
    od=f'{W}/proof/it/{tag}_armzoom'
    env=dict(os.environ); env['CLIP']='0.14'; env['FAR']='0.14'; env['RES']='700'; env['AO']='1'
    cmd=['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup',f'{W}/baseline/HeroBase_Male_Silhouette.blend','--python',f'{W}/closeup3.py','--',cand,od]+specs
    r=subprocess.run(cmd,capture_output=True,text=True,env=env)
    if 'CLOSEUP_DONE' not in r.stdout: print(r.stdout[-600:],r.stderr[-600:])
    names=[s.split(':')[0] for s in specs]
    p=sheet(od,names,f'{W}/proof/it/{tag}_armzoom.png',cols=3,size=520,title=('BEFORE' if tag=='base' else 'AFTER '+tag)); rows.append(Image.open(p).convert('RGB'))
S=Image.new('RGB',(rows[0].width,sum(r.height for r in rows))); y=0
for r in rows: S.paste(r,(0,y)); y+=r.height
S.save(outp); print(outp,S.size)
