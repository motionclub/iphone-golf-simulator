import numpy as np,json
from pathlib import Path
W=Path(__file__).resolve().parent;b=np.load(W/'baseline/mesh.npz')['co'];c=b.copy();p=np.load(W/'profile-targets.npz');ref=p['reference'];old=p['current'];x,y,z=b.T
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
of=np.interp(z,old[:,0],old[:,1]);ob=np.interp(z,old[:,0],old[:,2]);nf=np.interp(z,ref[:,0],ref[:,1]);nb=np.interp(z,ref[:,0],ref[:,2])
# Interpolate the measured profile correction on existing Y coordinates.
# Keep X/Z unchanged, with the unchanged body as the lower boundary.
centre=(of+ob)/2;ratio=(y-centre)/np.maximum((ob-of)/2,.002)
newcentre=(nf+nb)/2;newy=newcentre+ratio*(nb-nf)/2
weight=smooth(1.385,1.405,z)
c[:,1]+=weight*(newy-y)
np.save(W/'profile.npy',c)
assert np.array_equal(c[:,[0,2]],b[:,[0,2]]) and np.array_equal(c[z<1.385],b[z<1.385])
(W/'profile-edit.json').write_text(json.dumps({'part':'head/jaw/neck sagittal profile','baseline_sha256':json.loads((W/'baseline/invariants.json').read_text())['source_sha256'],'method':'Existing per-layer Y-coordinate sculpt from fixed, normalized outer head-detail contours and the current central surface rays; 20 mm neck-to-body falloff. No remesh, replacement or primary-mask/camera changes.','X_Z_coordinates_unchanged':True,'body_below_1_385m_unchanged':True,'changed_vertices':int(np.sum(np.any(c!=b,axis=1))),'maximum_displacement_metres':float(np.linalg.norm(c-b,axis=1).max())},indent=2))
print('PROFILE_SCULPT',float(np.linalg.norm(c-b,axis=1).max()))
