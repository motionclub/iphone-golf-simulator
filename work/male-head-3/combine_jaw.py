from pathlib import Path
import numpy as np,json
W=Path(__file__).resolve().parent;d=np.load(W/'baseline/mesh.npz');b=d['co'];tri=d['tri'];f=np.load(W/'fair.npy');loft=np.load(W/'loft.npy');delta=(f-b)+(loft-b)
def normals(co):
 t=co[tri];return np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
scope=np.max(b[tri,2],axis=1)>1.35
for fraction in [1,.8,.6,.4,.2]:
 c=b+delta*fraction;rev=int(np.sum(np.einsum('ij,ij->i',normals(c),normals(b))[scope]<0))
 if rev==0:break
assert rev==0 and np.array_equal(c[:,[0,2]],b[:,[0,2]]) and np.array_equal(c[b[:,2]<1.35],b[b[:,2]<1.35])
np.save(W/'jaw.npy',c)
a,e=d['edges'].T;count=np.bincount(np.r_[a,e],minlength=len(b))
def lap(co):return np.bincount(np.r_[a,e],weights=np.r_[co[e,1],co[a,1]],minlength=len(b))/count-co[:,1]
region=(b[:,2]>1.365)&(b[:,2]<1.525)&(abs(b[:,0])>.025)&(abs(b[:,0])<.069)&(b[:,1]<-.06)
q={'method':'Existing jaw/under-chin/neck Y-coordinate sculpt: local depth fairing and rounded lower-face depth guided by fixed head-detail profile calipers, with continuous falloffs and central profile retention. No remesh.','baseline_sha256':json.loads((W/'baseline/invariants.json').read_text())['source_sha256'],'accepted_blend_fraction':fraction,'changed_vertices':int(np.sum(np.any(c!=b,axis=1))),'maximum_displacement_metres':float(np.max(np.linalg.norm(c-b,axis=1))),'X_Z_coordinates_unchanged':True,'body_below_1_35m_unchanged':True,'head_triangle_normal_reversals':rev,'diagnostic_mean_absolute_depth_laplacian_mm_before':float(np.mean(abs(lap(b)[region]))*1000),'diagnostic_mean_absolute_depth_laplacian_mm_after':float(np.mean(abs(lap(c)[region]))*1000),'rejected_candidates':'Unconstrained XYZ fairing worsened both authority view errors; full-strength local jaw projection rotated existing thin face normals. Both rejected before main-file mutation.'}
(W/'jaw-edit.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
