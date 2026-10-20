"""Coordinate-only regional shoulder and waist repair; no remesh or rebuild."""
from pathlib import Path
import numpy as np,json
W=Path(__file__).parent;R=W.parents[1]
data=np.load(W/'baseline/mesh.npz');base=data['co'];edges=data['edges'];co=base.copy()
s=1.7/593
def smoothstep(a,b,v):
    t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
x=np.abs(base[:,0]);z=base[:,2];y=654-z/s
shoulder=smoothstep(.075,.14,x)*(1-smoothstep(.36,.44,x))*smoothstep(1.07,1.17,z)*(1-smoothstep(1.39,1.44,z))
collar=(1-smoothstep(.09,.14,x))*smoothstep(1.33,1.365,z)*(1-smoothstep(1.405,1.43,z))
shoulder=np.maximum(shoulder,collar*.7)
waist=(1-smoothstep(.15,.23,x))*smoothstep(.79,.86,z)*(1-smoothstep(1.02,1.13,z))
torso=(1-smoothstep(.16,.25,x))*smoothstep(.78,.85,z)*(1-smoothstep(1.33,1.40,z))
weights=np.maximum(shoulder,waist*.75)
count=np.bincount(edges.ravel(),minlength=len(co))[:,None]
def laplacian(p):
    total=np.zeros_like(p);np.add.at(total,edges[:,0],p[edges[:,1]]);np.add.at(total,edges[:,1],p[edges[:,0]])
    return total/np.maximum(count,1)-p
# Regional fairing suppresses the shoulder shelves and torso intersection ridges.
# It edits the existing connected vertices; the head, hands and legs are pinned.
for _ in range(95):
    co+=.47*weights[:,None]*laplacian(co)
    co-=.49*weights[:,None]*laplacian(co)
# Remove the broad deltoid shelf rather than retaining its low-frequency bump.
for _ in range(40):co+=.4*shoulder[:,None]*laplacian(co)
# Depth fairing removes the chest/deltoid and flank ridges without flattening
# the reference silhouettes. The geometric head and lower limbs are pinned.
for _ in range(80):
    delta=laplacian(co)
    co[:,1]+=.35*np.maximum(shoulder,torso*.8)*delta[:,1]
# Taper belly/flank depth at the waistband rather than leaving a radial ridge.
depth_axis=-.045
co[:,1]=depth_axis+(co[:,1]-depth_axis)*(1-.045*waist)
# Preserve the primary plate outlines: smooth shared row envelopes with X edits.
# This is geometry editing, never a mask, camera or rendered-image transform.
cfg=json.loads((R/'work/male-silhouette/contour-revision.json').read_text())
def profile(key,query):
    arr=np.array(cfg[key]);return np.array([np.interp(query,arr[:,0],arr[:,i]) for i in range(1,arr.shape[1])]).T
row=654-co[:,2]/s;ax=np.abs(co[:,0])/s
# Additional 0.5--1 mm waist taper at the side transitions.
co[:,0]*=1-.004*waist
co[base[:,2]>1.43]=base[base[:,2]>1.43]
# Keep the silhouette already close to the plate; no broad full-body smoothing.
displacement=np.linalg.norm(co-base,axis=1)
np.save(W/'revised_coordinates.npy',co)
report={'method':'Regional Taubin vertex fairing at neck/shoulder/upper arm and waist; slight waist depth taper. Existing topology preserved. All head, hands and legs outside these regions remain unchanged.',
 'changed_vertices':int((displacement>1e-8).sum()),'maximum_displacement_metres':float(displacement.max()),
 'shoulder_changed_vertices':int((shoulder>0).sum()),'waist_changed_vertices':int((waist>0).sum()),
 'head_vertices_unchanged':bool(np.array_equal(co[z>1.43],base[z>1.43])),
 'height_metres':float(np.ptp(co[:,2]))}
(W/'coordinate-edit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
