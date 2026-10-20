"""python3 metrics.py : silhouette (per view + plate-consensus ratio) and side-profile metrics, baseline vs final."""
import sys, json, numpy as np
sys.path.insert(0,'../../Tools/HeroBase')
from plate_profiles import FEMALE as F
from PIL import Image, ImageDraw
H,Wd=720,1280
def poly(pts):
    im=Image.new('L',(Wd,H),0); ImageDraw.Draw(im).polygon(pts,fill=255); return np.array(im)>0
PF=poly(F['front_outline']); PB=poly(F['back_outline'])
yy,xx=np.mgrid[0:H,0:Wd]
def half(P,cx,sd): return P[:,np.clip(np.round(cx+sd*np.arange(0,140)).astype(int),0,Wd-1)]
dx=np.arange(0,140)[None,:].repeat(H,0); y=yy[:,:140]
ZONES={'arms':(y>=165)&(y<372)&(dx>=58),'hands':(y>=340)&(y<425)&(dx>=78),
       'legs':(y>=372)&(dx<110)&~((y>=372)&(y<425)&(dx>=78)),'feet':(y>=640)&(dx<110)}
plate_views={'frontL':half(PF,440,-1),'frontR':half(PF,440,1),'backL':half(PB,847,-1),'backR':half(PB,847,1)}
T=np.mean([m.astype(float) for m in plate_views.values()],0)
def err(a,b,z): 
    a=a.astype(float); b=b.astype(float); u=np.maximum(a,b)[z].sum(); return float(np.abs(a-b)[z].sum()/u) if u else float('nan')
def model_masks(prefix):
    out={}
    for v,cx in (('front',440),('back',847)):
        M=np.array(Image.open(f'{prefix}_{v}.png'))[:,:,3]>127
        out[v]=M
    return out
def zone_metrics(prefix):
    mm=model_masks(prefix); res={}
    # (a) sil.py-style per-view XOR vs the full plate polygon
    for v,P,cx in (('front',PF,440),('back',PB,847)):
        M=mm[v]; X=(P^M)
        for zn in ZONES:
            # zones in full-image coordinates
            if zn=='arms': z=(yy>=165)&(yy<372)&(np.abs(xx-cx)>=58)
            elif zn=='hands': z=(yy>=340)&(yy<425)&(np.abs(xx-cx)>=78)
            elif zn=='legs': z=(yy>=372)&(np.abs(xx-cx)<110)&~((yy>=372)&(yy<425)&(np.abs(xx-cx)>=78))
            else: z=(yy>=640)&(np.abs(xx-cx)<110)
            u=((P|M)&z).sum(); res[f'{v}_{zn}_xor_pct']=round(float(X[z].sum()/u*100),2)
    # (b) consensus: model half-mask (mean of L/R of the front render) vs mean of the four plate half-masks
    Mh=(half(mm['front'],440,-1).astype(float)+half(mm['front'],440,1).astype(float))/2
    for zn,z in ZONES.items():
        e_model=err(Mh,T,z); e_views=[err(m,T,z) for m in plate_views.values()]
        res[f'consensus_{zn}']={'model_vs_consensus':round(e_model,4),'plate_views_vs_consensus_mean':round(float(np.mean(e_views)),4),'ratio':round(e_model/float(np.mean(e_views)),3)}
    return res
def profile(prefix):
    S=0.005916/3; Tg=json.load(open('data/leg_targets.json')); zs=np.array(Tg['z']); yc=json.load(open('data/headcentre.json'))['yc']
    M=np.array(Image.open(prefix))[:,:,3]>127
    rows=[int((1.7335-z)/S) for z in zs]
    ext=lambda r:(np.where(M[r])[0].min(),np.where(M[r])[0].max()+1)
    e=np.array([ext(r) for r in rows],float); toy=lambda px: yc+(px-270)*S
    mf=toy(e[:,0]); mb=toy(e[:,1])
    df=(mf-np.array(Tg['plate_front_y']))*1000; db=(mb-np.array(Tg['plate_back_y']))*1000
    sel=(zs>=0.17)&(zs<=0.46)
    return {'z':zs[sel].round(2).tolist(),'front_dev_mm':df[sel].round(1).tolist(),'back_dev_mm':db[sel].round(1).tolist(),
            'depth_dev_mm':(db-df)[sel].round(1).tolist(),'max_abs_edge_dev_mm':float(max(np.abs(df[sel]).max(),np.abs(db[sel]).max())),
            'max_abs_depth_dev_mm':float(np.abs((db-df)[sel]).max()),'mean_abs_depth_dev_mm':float(np.abs((db-df)[sel]).mean())}
out={'baseline':zone_metrics('proof/s_base'),'final':zone_metrics('proof/s_final'),
     'profile_baseline':profile('proof/ps_base.png'),'profile_final':profile('proof/ps_final.png'),
     'plate_floor':json.load(open('data/silhouette_floor.json'))}
json.dump(out,open('data/metrics_final.json','w'),indent=1)
print('per-view XOR % (baseline -> final)')
for k in sorted(out['final']):
    if k.endswith('_xor_pct'): print(f'  {k:24s} {out["baseline"][k]:6.2f} -> {out["final"][k]:6.2f}')
print('consensus ratio (model-vs-plate-consensus / plate-view-vs-consensus)')
for zn in ZONES: print(f'  {zn:6s} baseline {out["baseline"]["consensus_"+zn]["ratio"]:5.2f}  final {out["final"]["consensus_"+zn]["ratio"]:5.2f}   (final err {out["final"]["consensus_"+zn]["model_vs_consensus"]}, plate-self {out["final"]["consensus_"+zn]["plate_views_vs_consensus_mean"]})')
for k in ('profile_baseline','profile_final'):
    p=out[k]; print(k,'max edge dev mm',round(p['max_abs_edge_dev_mm'],1),'max depth dev mm',round(p['max_abs_depth_dev_mm'],1),'mean depth dev',round(p['mean_abs_depth_dev_mm'],1))
