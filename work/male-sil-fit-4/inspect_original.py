import bpy,numpy as np,json,hashlib
from pathlib import Path
W=Path(__file__).resolve().parent;R=W.parents[1];path=R/'work/male-silhouette/micro1-baseline/HeroBase_Male_Silhouette.blend'
bpy.ops.wm.open_mainfile(filepath=str(path));o=next(o for o in bpy.data.objects if o.type=='MESH');m=o.data;co=np.array([tuple(v.co) for v in m.vertices]);np.save(W/'original_coordinates.npy',co)
base=np.load(W/'baseline/mesh.npz');assert len(co)==len(base['co']);assert np.array_equal(np.array([tuple(e.vertices) for e in m.edges]),base['edges'])
print('ORIGINAL_VERTEX_CORRESPONDENCE_VERIFIED',o.name,len(co),hashlib.sha256(path.read_bytes()).hexdigest())
for i in [24055,24057,24064,24065,24071,24072,24079,24080,24149,24211]:print(i,co[i].tolist(),base['co'][i].tolist())
