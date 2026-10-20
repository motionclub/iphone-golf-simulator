"""Calibrate the 3/4-back sheet panels by silhouette alignment of the UNMODIFIED body parts (legs z<0.68, shoulders/neck z>1.30; arms excluded by only using the central body runs).
python3 calib34.py <panel q3BL|q3BR> : sweeps yaw offsets and column shifts; prints IoU table; picks the best."""
import sys, os, subprocess, json
import numpy as np
from PIL import Image
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin'; R=W+'/../..'
L=np.asarray(Image.open(R+'/ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('L')).astype(float)
BOX={'q3BL':(690,890,440,700,(676,690,884,898)),'q3BR':(980,1180,440,700,(1000,1008,1146,1154))}
MPP=0.00582; SOLE=673.5
pan=sys.argv[1]; c0,c1,r0,r1,(b0,b1,b2,b3)=BOX[pan]
pm=np.zeros((r1-r0,c1-c0),bool)
for r in range(r0,r1):
    bg=np.median(np.concatenate([L[r,b0:b1],L[r,b2:b3]])); pm[r-r0]=L[r,c0:c1]>bg+9
def zrows(zlo,zhi): return [int(round(SOLE-z/MPP))-r0 for z in np.arange(zlo,zhi,0.004)]
rows=[r for r in zrows(0.05,0.68)+zrows(1.30,1.62) if 0<=r<r1-r0]
cen=(c1-c0)//2
def body_run(m,r):
    row=m[r]; idx=np.where(row)[0]
    if len(idx)==0: return None
    br=np.where(np.diff(idx)>1)[0]; st=[idx[0]]+[idx[b+1] for b in br]; en=[idx[b] for b in br]+[idx[-1]]
    runs=[(s,e) for s,e in zip(st,en) if e>=cen-45 and s<=cen+45]
    if not runs: return None
    return min(s for s,e in runs), max(e for s,e in runs)
pe={r:body_run(pm,r) for r in rows}
env0=dict(os.environ, PYTHONPATH=R+'/work/male-micro1i/pylib')
def render(yoff,coff):
    env=dict(env0, YAWOFF=str(yoff), COLOFF=str(coff))
    subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup','--python','rig.py','--',W+'/baseline/HeroBase_Male_Silhouette.blend',W+'/r/cal','reg_%s_%d_%d_%d_%d_4'%(pan,c0,c1,r0,r1),'sil'],cwd=W,env=env,capture_output=True)
    a=np.asarray(Image.open(W+'/r/cal/reg_%s_%d_%d_%d_%d_4.png'%(pan,c0,c1,r0,r1)))[...,3]>127
    return a
def score(a):
    errs=[]
    for r in rows:
        p=pe[r]
        if p is None: continue
        ra=a[r*4:r*4+4].any(0); idx=np.where(ra)[0]
        if len(idx)==0: continue
        br=np.where(np.diff(idx)>1)[0]; st=[idx[0]]+[idx[b+1] for b in br]; en=[idx[b] for b in br]+[idx[-1]]
        runs=[(s/4,e/4) for s,e in zip(st,en) if e/4>=cen-45 and s/4<=cen+45]
        if not runs: continue
        l=min(s for s,e in runs); rr=max(e for s,e in runs); errs.append((l-p[0],rr-p[1]))
    e=np.array(errs); return float(np.sqrt((e**2).mean())), e.mean(0)
best=None
import itertools
from concurrent.futures import ThreadPoolExecutor
grid=[(y,c,m) for y in (0,3,6,9,12,15) for c in (-4,0,4) for m in (0.98,1.0,1.02)]
def render2(yoff,coff,mpf,tag):
    env=dict(env0, YAWOFF=str(yoff), COLOFF=str(coff), MPPF=str(mpf))
    out=W+'/r/cal_'+tag
    subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup','--python','rig.py','--',W+'/baseline/HeroBase_Male_Silhouette.blend',out,'reg_%s_%d_%d_%d_%d_4'%(pan,c0,c1,r0,r1),'sil'],cwd=W,env=env,capture_output=True)
    a=np.asarray(Image.open(out+'/reg_%s_%d_%d_%d_%d_4.png'%(pan,c0,c1,r0,r1)))[...,3]>127
    return a
def job(g):
    y,c,m=g; a=render2(y,c,m,f'{y}_{c}_{m}'); rms,mean=score(a); return g,rms,mean
with ThreadPoolExecutor(6) as ex: res=list(ex.map(job,grid))
res.sort(key=lambda t:t[1])
for g,rms,mean in res[:8]: print(f'{pan} yaw+{g[0]:+d} col{g[1]:+d} mpp x{g[2]}: rms {rms:5.2f} px mean (L,R) {mean[0]:+5.2f},{mean[1]:+5.2f}')
