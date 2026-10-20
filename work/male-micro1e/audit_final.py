"""Audit final blend vs baseline. usage: blender -b --python audit_final.py -- final.blend out.json"""
import bpy, sys, json, numpy as np, hashlib
from pathlib import Path
from collections import defaultdict
argv=sys.argv[sys.argv.index('--')+1:]
final=Path(argv[0]); out=Path(argv[1]); W=Path(__file__).resolve().parent
base=np.load(W/'baseline/mesh.npz')['co'].astype(np.float32)
bpy.ops.wm.open_mainfile(filepath=str(final))
me=bpy.data.objects['Body_M'].data
co=np.array([v.co[:] for v in me.vertices],np.float32)
N0=len(base)
res={'final_blend_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'verts':len(co),'polys':len(me.polygons),
     'tris':int(sum(len(p.vertices)-2 for p in me.polygons)),'quads':int(sum(1 for p in me.polygons if len(p.vertices)==4)),'trianglesFaces':int(sum(1 for p in me.polygons if len(p.vertices)==3))}
# --- unchanged vertices
same=np.all(co[:N0]==base,axis=1)
chg=np.where(~same)[0]
res['changed_vertices_of_original_indices']=int(len(chg))
# classify changed original indices: head (z>1.43 & |x|<0.13) ; hands (|x|>0.30 & z<1.10) ; other
z=base[:,2]; x=base[:,0]
head=(z>1.40)&(np.abs(x)<0.13)
hand=(np.abs(x)>0.30)&(z<1.10)
other=~(head|hand)
res['changed_in_head_zone']=int((~same&head).sum()); res['changed_in_hand_zone']=int((~same&hand).sum()); res['changed_elsewhere']=int((~same&other).sum())
# max displacement of the head-zone verts
d=np.linalg.norm(co[:N0]-base,axis=1)
res['head_zone_max_disp_mm']=float(d[head].max()*1000)
res['head_changed_below_z_1_35']=int((~same&(z<1.35)&head).sum())
# regression regions (must be exactly unchanged)
reg={'SHOULDERS':(z>1.17)&(z<1.43)&(np.abs(x)<0.40)&(np.abs(x)>0.0),'WAIST':(z>0.90)&(z<1.10)&(np.abs(x)<0.25),
     'ARMS_SIDE(upper+fore, above wrist)':(np.abs(x)>0.28)&(z>1.0)&(z<1.30),'FEET_SIDE':(z<0.25)}
res['regression_regions']={k:{'verts':int(m.sum()),'changed':int((~same&m).sum()),'max_disp_mm':float(d[m].max()*1000)} for k,m in reg.items()}
# bounds
res['height_m']=float(co[:,2].max()-co[:,2].min()); res['bounds_min']=co.min(0).tolist(); res['bounds_max']=co.max(0).tolist()
res['feet_verts_below_4mm']=int((co[:,2]<0.004).sum()); res['lowest_z_m']=float(co[:,2].min())
# manifold audit
ec=defaultdict(int)
for p in me.polygons:
    v=list(p.vertices)
    for k in range(len(v)):
        a,b=v[k],v[(k+1)%len(v)]; ec[(min(a,b),max(a,b))]+=1
res['boundary_edges']=sum(1 for c in ec.values() if c==1); res['nonmanifold_edges']=sum(1 for c in ec.values() if c>2)
bm=np.array([list(p.vertices) for p in me.polygons if len(p.vertices)==4]) if False else None
# signed volume (outward normals => positive)
vol=0.0
for p in me.polygons:
    v=list(p.vertices)
    for k in range(1,len(v)-1):
        a,b,c=co[v[0]],co[v[k]],co[v[k+1]]
        vol+=float(np.dot(a,np.cross(b,c)))/6.0
res['signed_volume_m3']=vol
# nan check
res['nan_or_inf']=bool(~np.isfinite(co).all())
# degenerate faces (area<1e-9)
deg=0; minang=[]
for p in me.polygons:
    if p.area<1e-9: deg+=1
res['zero_area_faces']=deg
# loose verts
used=np.zeros(len(co),bool)
for p in me.polygons: used[list(p.vertices)]=True
res['loose_vertices']=int((~used).sum())
res['materials']=[m.name for m in me.materials]
out.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
