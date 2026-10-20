import subprocess, os, sys
from pathlib import Path
W=Path(__file__).resolve().parent
B='/Applications/Blender.app/Contents/MacOS/Blender'
S1=W/'baseline_S1/HeroBase_Male_Silhouette_S1.blend'; NEW=W/'export/HeroBase_Male_Silhouette_arms.blend'
TR="0.60,-0.105,0.89"; TL="-0.60,-0.105,0.89"
def views(side):
    T=TR if side>0 else TL; s=side
    d=lambda x,y,z: f"{s*x},{y},{z}"
    return [f"{side_name(side)}_back:{T}:{d(0.768,0,0.642)}:0.28:55:-40",
            f"{side_name(side)}_front:{T}:{d(-0.07,-1,0.09)}:0.28:55:-40",
            f"{side_name(side)}_palm:{T}:{d(-0.55,0.7,-0.45)}:0.28:55:-40",
            f"{side_name(side)}_back3q:{T}:{d(0.5,-0.75,0.4)}:0.28:55:-40",
            f"{side_name(side)}_side:{T}:{d(0.07,1,-0.09)}:0.28:55:-40",
            f"{side_name(side)}_wrist:{('0.50,-0.10,0.97' if side>0 else '-0.50,-0.10,0.97')}:{d(-0.3,-0.85,0.2)}:0.28:55:-40"]
def side_name(s): return 'R' if s>0 else 'L'
def run(blend,out,wire=False,extra=None):
    env=dict(os.environ); env['CLIP']='0.2'
    if wire: env['WIRE']='1'; env['WIRE_T']='0.00014'
    vs=views(+1)+views(-1)+(extra or [])
    out.mkdir(parents=True,exist_ok=True)
    subprocess.run([B,'-b',str(blend),'--python',str(W/'closeup.py'),'--',str(out)]+vs,env=env,capture_output=True)
if __name__=='__main__':
    run(S1,W/'proof/final/before'); run(NEW,W/'proof/final/after')
    # thumb root wire
    extra=["thumbroot_pal:0.5852,-0.1434,0.8939:-0.768,-0.1,-0.642:0.10:55:-40","thumbroot_front:0.5852,-0.1434,0.8939:-0.07,-1,0.09:0.10:55:-40"]
    for nm,bl in (('before',S1),('after',NEW)):
        env=dict(os.environ); env['CLIP']='0.12'; env['WIRE']='1'; env['WIRE_T']='0.00012'
        d=W/f'proof/final/wire_{nm}'; d.mkdir(parents=True,exist_ok=True)
        subprocess.run([B,'-b',str(bl),'--python',str(W/'closeup.py'),'--',str(d)]+extra,env=env,capture_output=True)
    print('done')
