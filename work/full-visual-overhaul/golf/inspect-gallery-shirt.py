import bpy,bmesh,json
from pathlib import Path
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');out={}
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(R/f'work/golf-motion-fit/export/Golf_{sex}_Master.blend'));o=bpy.data.objects['Kit_Top'];bm=bmesh.new();bm.from_mesh(o.data)
 out[sex]={'verts':len(bm.verts),'faces':len(bm.faces),'boundary':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold for e in bm.edges),'material':list(set(f.material_index for f in bm.faces))};bm.free()
print(json.dumps(out))
