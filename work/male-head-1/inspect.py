import bpy, numpy as np, json, hashlib, shutil
from pathlib import Path
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'); W=R/'work/male-head-1'; D=R/'ArtDir/hero/base_lock'
b=D/'blender/HeroBase_Male_Silhouette.blend'; bpy.ops.wm.open_mainfile(filepath=str(b))
o=bpy.data.objects['Body_M']; m=o.data; m.calc_loop_triangles()
assert not (W/'baseline/mesh.npz').exists()
shutil.copy2(b,W/'baseline/HeroBase_Male_Silhouette.blend')
np.savez(W/'baseline/mesh.npz',co=np.array([tuple(v.co) for v in m.vertices]),edges=np.array([tuple(e.vertices) for e in m.edges]),tri=np.array([tuple(f.vertices) for f in m.loop_triangles]))
matrix=lambda o:list(sum((list(r) for r in o.matrix_world),[]))
data={'source_sha256':hashlib.sha256(b.read_bytes()).hexdigest(),'body_matrix':matrix(o),'nonbody_matrix':{o.name:matrix(o) for o in bpy.data.objects if o.type!='MESH'},'connectivity_sha256':hashlib.sha256(json.dumps([list(f.vertices) for f in m.polygons],separators=(',',':')).encode()).hexdigest(),'cameras':{o.name:{'scale':o.data.ortho_scale,'props':dict(o.items())} for o in bpy.data.objects if o.type=='CAMERA'},'faces':[list(f.vertices) for f in m.polygons]}
(W/'baseline/invariants.json').write_text(json.dumps(data,indent=2)); print(data['source_sha256'])
