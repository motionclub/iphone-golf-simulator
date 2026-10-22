"""Zone / topology / quality audit of a candidate coordinate array vs the start mesh.  usage: py.sh audit.py <coords.npy> <out.json> [start.npz]"""
import sys, json, numpy as np
from pathlib import Path
W=Path(__file__).resolve().parent
sys.path.insert(0,str(W))
from zonelib import *
import quality, handobj
cand=np.load(sys.argv[1]).astype(np.float32); out=sys.argv[2]
V0,T0,polys=load('data/mesh_start.npz') if len(sys.argv)<4 else load(sys.argv[3])
V0f=V0.astype(np.float32)
zR=np.load(W/'data/zone_R.npy'); zL=np.load(W/'data/zone_L.npy'); zone=zR|zL; shell=np.load(W/'data/shell_cur.npy')
assert cand.shape==V0f.shape,(cand.shape,V0f.shape)
moved=(cand!=V0f).any(1)
d=np.linalg.norm(cand.astype(np.float64)-V0f.astype(np.float64),axis=1)
res={}
res['verts']=int(len(V0f)); res['moved_total']=int(moved.sum()); res['moved_outside_zone']=int((moved&~zone).sum())
res['moved_in_R']=int((moved&zR).sum()); res['moved_in_L']=int((moved&zL).sum())
res['moved_hand_shell']=int((moved&shell).sum()); res['moved_forearm_nonshell']=int((moved&~shell).sum())
res['max_disp_mm_all']=float(1000*d.max()); res['max_disp_mm_nonshell']=float(1000*d[moved&~shell].max()) if (moved&~shell).any() else 0.0
res['p95_disp_mm_nonshell']=float(1000*np.percentile(d[moved&~shell],95)) if (moved&~shell).any() else 0.0
V=V0f.copy().astype(np.float64); 
# regions that must stay bit-identical
x=V0[:,0]; z=V0[:,2]
regions={'head_neck(z>=1.40)':z>=1.40,'torso+pelvis(|x|<0.215,z>=0.78)':(np.abs(x)<0.215)&(z>=0.78)&(z<1.40),'legs_feet(z<0.78,|x|<0.40)':(z<0.78)&(np.abs(x)<0.40),'whole_body_outside_arm_zone':~zone}
for k,m in regions.items(): res['bit_identical_'+k]=bool((~moved[m]).all()); res['moved_in_'+k]=int((moved&m).sum())
# upper arm / deltoid (t < -0.02) untouched? (edits are meant to start at the elbow)
tR=quality.arm_t(V0,+1); tL=quality.arm_t(V0,-1)
upper=((zR&(tR<-0.03))|(zL&(tL<-0.03)))
res['upper_arm_and_deltoid_moved']=int((moved&upper).sum())
# topology: same polygon list is guaranteed by coordinate-only edit; verify shapes
res['topology']='coordinate-only edit: vertex count and polygon list unchanged (verified again after the blend is written)'
# mirror symmetry of the arms (R vs mirrored L)
def mirr(V):
    A=V[zR]; B=V[zL]*np.array([-1,1,1]); 
    dd=np.sqrt(((A[:,None,:]-B[None,:,:])**2).sum(2)).min(1); return float(1000*dd.mean()),float(1000*np.percentile(dd,95)),float(1000*dd.max())
res['mirror_mean_p95_max_mm_start']=mirr(V0); res['mirror_mean_p95_max_mm_cand']=mirr(cand.astype(np.float64))
# quality
m0=quality.metrics(V0,T0,polys,zR,zL,shell); m1=quality.metrics(cand.astype(np.float64),T0,polys,zR,zL,shell)
res['quality_start']=m0; res['quality_cand']=m1
# hand ROI silhouette XOR
arm=(np.abs(V0[:,0])>0.2)&(V0[:,2]>0.78)&(V0[:,2]<1.40); sel=arm[T0].all(1)
t0,r0=handobj.xor_report(V0,T0,sel); t1,r1=handobj.xor_report(cand.astype(np.float64),T0,sel)
res['hand_roi_xor_start']=t0; res['hand_roi_xor_cand']=t1
res['hand_roi_xor_per_roi']={f'{k[0]}_{k[1]}':(r0[k][0],r1[k][0]) for k in r0}
# winding / flipped faces among zone polygons
Fn0=quality.face_normals(V0,polys); Fn1=quality.face_normals(cand.astype(np.float64),polys)
pz=np.array([zone[list(p)].all() for p in polys]); dot=(Fn0*Fn1).sum(1)
res['zone_polys']=int(pz.sum()); res['flipped_polys(dot<0 vs start)']=int(((dot<0)&pz).sum()); res['polys_normal_turn_gt60deg']=int(((dot<0.5)&pz).sum())
# degenerate faces
def area(V,p):
    q=V[list(p)]; n=np.cross(q[1]-q[0],q[2]-q[0]); 
    if len(p)==4: n=n+np.cross(q[2]-q[0],q[3]-q[0])
    return 0.5*np.linalg.norm(n)
a1=np.array([area(cand.astype(np.float64),p) for i,p in enumerate(polys) if pz[i]]); res['zone_min_poly_area_mm2']=float(a1.min()*1e6); res['zone_degenerate_polys(<0.05mm2)']=int((a1<5e-8).sum())
json.dump(res,open(out,'w'),indent=1); print(json.dumps({k:v for k,v in res.items() if k not in('quality_start','quality_cand','hand_roi_xor_per_roi')},indent=1))
print('quality start',json.dumps(m0)); print('quality cand',json.dumps(m1))
