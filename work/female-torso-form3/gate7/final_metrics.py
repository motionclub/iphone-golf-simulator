"""Collect all torso gate metrics (before=start, after=final candidate coords) into checks.json"""
import numpy as np, json, sys, io, contextlib
sys.path.insert(0,'.')
from sil import *
import metrics_fb as MF, metrics_side as MS, mesh_quality as MQ
from PIL import Image
d=np.load('data/start.npz'); co0=d['co'].astype(np.float64); tri=d['tri']
co1=np.load('data/torso_final.npy').astype(np.float32).astype(np.float64)
def torso_run_xor(co):
    res={}
    for view in ('front','back'):
        M=raster(project(co,view),tri); P=MF.masks[view]; cx=440 if view=='front' else 847
        sd=0;un=0
        for z in np.arange(0.82,1.165,0.002):
            y=int(round(679-z/S))
            pr=[r for r in MF.runs(P[y]) if r[0]<=cx<=r[1]]; mr=[r for r in MF.runs(M[y]) if r[0]<=cx<=r[1]]
            if not pr or not mr: continue
            a=np.zeros(1280,bool); b=np.zeros(1280,bool); a[pr[0][0]:pr[0][1]+1]=True; b[mr[0][0]:mr[0][1]+1]=True
            sd+=(a^b).sum(); un+=(a|b).sum()
        res[view]=float(sd/un)
    return res
def side_xor(co):
    ed=d['edges']; num=0;den=0
    for z in np.arange(0.82,1.30+1e-9,0.004):
        pf,pb=MS.plate_contour(z)
        za=co[ed[:,0],2]; zb=co[ed[:,1],2]; ya=co[ed[:,0],1]; yb=co[ed[:,1],1]; m=(za-z)*(zb-z)<0
        t=(z-za[m])/(zb[m]-za[m]); y=ya[m]+t*(yb[m]-ya[m]); mf,mb=y.min(),y.max()
        num+=abs(mf-pf)+abs(mb-pb); den+=max(mb,pb)-min(mf,pf)
    return float(num/den)
def side_rows(co,T):
    rows=[]
    for z in np.arange(0.84,1.30,0.02):
        pf,pb=MS.plate_contour(z); mf,mb=MS.model_contour(co,T,z); rows.append((float(z),float(pf),float(pb),float(mf),float(mb)))
    r=np.array(rows); return r
T=np.load('data/zone.npz')['torso']
out={'gate':'FEMALE_TORSO','zone':{'z_crotch_m':0.795,'z_neck_base_m':1.37,'moved_region_z_m':[0.795,1.34],'zone_vertices':int(T.sum()),'arm_split':'below armpit z<1.165: connected components; above: |x|>X_B(z) (0.124 up to z=1.28, ramps to 0.17 at z=1.34)'}}
with contextlib.redirect_stdout(io.StringIO()):
    fb0=MF.evaluate(co0,'before'); fb1=MF.evaluate(co1,'after')
out['front_back_silhouette_project_frame']={'before':fb0,'after':fb1,'note':'x coordinates are not changed (<=2 mm tangential denoise) so front/back whole-body error is dominated by head/arms/legs zones owned by other chats'}
out['torso_visible_edge_run_xor_rows_z0.82_1.165']={'before':torso_run_xor(co0),'after':torso_run_xor(co1),'gate':'<=0.05'}
out['side_profile_torso_band_xor_z0.82_1.30']={'before':side_xor(co0),'after':side_xor(co1),'gate':'<=0.05','anchor':'knee-centre of multi-angle left+right profile panels; scale 1.7039m/288.5px'}
r0=side_rows(co0,T); r1=side_rows(co1,T)
out['side_contour_error_mm']={'before':{'front_mean':float(np.abs(r0[:,3]-r0[:,1]).mean()*1000),'front_max':float(np.abs(r0[:,3]-r0[:,1]).max()*1000),'back_mean':float(np.abs(r0[:,4]-r0[:,2]).mean()*1000),'back_max':float(np.abs(r0[:,4]-r0[:,2]).max()*1000)},
                              'after':{'front_mean':float(np.abs(r1[:,3]-r1[:,1]).mean()*1000),'front_max':float(np.abs(r1[:,3]-r1[:,1]).max()*1000),'back_mean':float(np.abs(r1[:,4]-r1[:,2]).mean()*1000),'back_max':float(np.abs(r1[:,4]-r1[:,2]).max()*1000)}}
out['side_contour_table_after']=[{'z':a,'plate_front':b,'plate_back':c,'model_front':e,'model_back':f} for a,b,c,e,f in r1.tolist()]
np.save('data/torso_final_f32.npy',co1)
with contextlib.redirect_stdout(io.StringIO()):
    mq=MQ.run('data/torso_final_f32.npy','after')
out['mesh_quality']=mq
json.dump(out,open('checks.json','w'),indent=1)
b=out['torso_visible_edge_run_xor_rows_z0.82_1.165']; s=out['side_profile_torso_band_xor_z0.82_1.30']
print("torso-run XOR front/back  before",{k:round(v,4) for k,v in b['before'].items()},"after",{k:round(v,4) for k,v in b['after'].items()})
print("side torso-band XOR before %.4f after %.4f"%(s['before'],s['after']))
print("side contour mm",out['side_contour_error_mm'])
print("flipped tris",mq['flipped_tris'],"tri count",mq['total_tris'])
print("front/back full-body XOR before",{v:round(fb0[v]['full'],4) for v in fb0},"after",{v:round(fb1[v]['full'],4) for v in fb1})
