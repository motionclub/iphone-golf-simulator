"""Fit the visible lower-jaw profile, rather than only central surface rays."""
from pathlib import Path
import numpy as np,json
W=Path(__file__).resolve().parent;R=W.parents[1];d=np.load(W/'baseline/mesh.npz');b=d['co'];tri=d['tri'];c=np.load(W/'fair.npy');ref=np.load(R/'work/male-head-2/profile-targets.npz')['reference']
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
def envelope(co):
 t=co[tri];t=t[(t[:,:,2].max(1)>1.35)&(t[:,:,2].min(1)<1.545)&(np.max(abs(t[:,:,0]),1)<.13)]
 a=t[:,[0,1,2],:].reshape(-1,3);e=t[:,[1,2,0],:].reshape(-1,3)
 rows=[]
 for z in np.arange(1.35,1.545,.0005):
  ok=(np.minimum(a[:,2],e[:,2])<=z)&(np.maximum(a[:,2],e[:,2])>=z)&(abs(a[:,2]-e[:,2])>1e-10)
  u=(z-a[ok,2])/(e[ok,2]-a[ok,2]);y=a[ok,1]+u*(e[ok,1]-a[ok,1])
  if len(y):rows.append([z,y.min(),y.max()])
 return np.array(rows)
old=envelope(c);grid=old[:,0];nf=np.interp(grid,ref[:,0],ref[:,1]);delta=nf-old[:,1]
# Smooth only the displacement field; retain the chin/neck contour in the plate.
k=np.exp(-np.arange(-12,13)**2/(2*3**2));k/=k.sum();delta=np.convolve(np.pad(delta,(12,12),mode='edge'),k,mode='valid')
x,y,z=c.T;f=np.interp(z,grid,old[:,1]);rear=np.interp(z,grid,old[:,2]);cy=(f+rear)/2;ry=(rear-f)/2
front=smooth(.20,.75,(cy-y)/np.maximum(ry,.01));weight=smooth(1.368,1.392,z)*(1-smooth(1.478,1.502,z))*front
p=c.copy();p[:,1]+=np.interp(z,grid,delta)*weight
def n(co):
 t=co[tri];return np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
bn=n(b)
for fraction in [1,.85,.7,.55,.4,.25]:
 q=c+(p-c)*fraction;rev=int(np.sum(np.einsum('ij,ij->i',bn,n(q))<0))
 if not rev:break
assert rev==0
after=envelope(q);before=envelope(b)
np.save(W/'outline.npy',q);np.savez(W/'outline-profile.npz',before=before,after=after,reference=ref)
scope=np.load(W/'scope.npy')|(weight>0);np.save(W/'scope.npy',scope)
diag={}
for label,curve in [('before',before),('after',after)]:
 region=(curve[:,0]>=1.430)&(curve[:,0]<=1.480);gap=curve[region,1]-np.interp(curve[region,0],ref[:,0],ref[:,1]);diag[label+'_mean_absolute_visible_profile_gap_mm']=float(np.mean(abs(gap))*1000);diag[label+'_max_absolute_visible_profile_gap_mm']=float(np.max(abs(gap))*1000)
out={'method':'Local existing-coordinate fairing plus smooth lower-jaw anterior depth displacement from the fixed head-detail outer contour and the full visible mesh profile. No remesh or primary camera/mask changes.','baseline_sha256':json.loads((W/'baseline/invariants.json').read_text())['source_sha256'],'profile_step_fraction':fraction,'changed_vertices':int(np.sum(np.any(q!=b,axis=1))),'maximum_displacement_metres':float(np.max(np.linalg.norm(q-b,axis=1))),'triangle_normal_reversals':rev,'body_below_1_35m_unchanged':bool(np.array_equal(q[b[:,2]<=1.35],b[b[:,2]<=1.35])),'visible_profile_diagnostic':diag}
(W/'outline-edit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
