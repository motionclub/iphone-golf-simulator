"""blender -b baseline/HeroBase_Female.blend --python fit_legs.py -- out.blend [depth_bias_mm]
Remaps lower-leg depth (y) per z slice to the plate profile targets (data/leg_targets.json). Positions only; z<0.58."""
import bpy, numpy as np, json, sys
from pathlib import Path
W=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-parallel-limbs')
args=sys.argv[sys.argv.index('--')+1:]; OUT=args[0]; BIAS=float(args[1])/1000 if len(args)>1 else 0.005
T=json.load(open(W/'data/leg_targets.json'))
z=np.array(T['z']); pf=np.array(T['plate_front_y']); pb=np.array(T['plate_back_y']); mf=np.array(T['model_front_y']); mb=np.array(T['model_back_y'])
# plate union of two (yawed) legs is slightly deeper than a single leg: pull each edge in by BIAS
pf=pf+BIAS; pb=pb-BIAS
def sm(x0,x1,v): t=np.clip((v-x0)/(x1-x0),0,1); return t*t*(3-2*t)
w=1-sm(0.42,0.58,z)                                   # full plate target below 0.42, model target above 0.58
tf=mf+(pf-mf)*w; tb=mb+(pb-mb)*w
# keep z<0.14 flat (extrapolate); the old foot below 0.157 is replaced anyway
ZMAX=0.58
me=bpy.data.objects['Body_F'].data
n=len(me.vertices); co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); V=co.reshape(-1,3).copy(); V0=V.copy()
sel=np.where((V[:,2]<ZMAX)&(V[:,2]>=0.14))[0]          # feet (<0.14) are replaced wholesale; ankle ring + calf only
zz=np.clip(V[sel,2],z.min(),z.max())
yf=np.interp(zz,z,mf); yb=np.interp(zz,z,mb); TF=np.interp(zz,z,tf); TB=np.interp(zz,z,tb)
V[sel,1]=TF+(V[sel,1]-yf)*(TB-TF)/(yb-yf)
co2=V.reshape(-1).astype(np.float32); me.vertices.foreach_set('co',co2); me.update()
moved=np.where(np.any(V!=V0,axis=1))[0]
print('moved',len(moved),'z range',V0[moved,2].min(),V0[moved,2].max(),'max |dy| mm',np.abs(V[moved,1]-V0[moved,1]).max()*1000)
json.dump({'moved':int(len(moved)),'max_dy_mm':float(np.abs(V[moved,1]-V0[moved,1]).max()*1000),'z_max_moved':float(V0[moved,2].max())},open(W/'data/legfit_report.json','w'))
# ankle ring parameters for the foot SDF (after the remap)
ring={}
for sd in (1,-1):
    m=(np.sign(V[:,0])==sd)&(np.abs(V[:,0])>0.05)&(V[:,2]>0.1565)&(V[:,2]<0.1580)
    P=V[m]; ring[str(sd)]={'n':int(m.sum()),'cx':float((P[:,0].min()+P[:,0].max())/2),'a':float((P[:,0].max()-P[:,0].min())/2),
                          'cy':float((P[:,1].min()+P[:,1].max())/2),'b':float((P[:,1].max()-P[:,1].min())/2)}
print('ring',ring)
json.dump(ring,open(W/'data/ring_params.json','w'),indent=1)
bpy.ops.wm.save_as_mainfile(filepath=str(W/OUT))
