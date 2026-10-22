"""Read-only frozen source shell topology; prevents double-solidifying clothes."""
import bpy,bmesh,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
out=[]
for sex in ['Male','Female']:
    bpy.ops.wm.open_mainfile(filepath=str(W/f'inputs/HeroBase_{sex}_Dressed.blend'))
    for name in ['Kit_Top','Kit_Bottom','Kit_Shoe_L']:
        o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data)
        counts={k:sum(len(e.link_faces)==k for e in bm.edges) for k in [0,1,2]}
        out.append(dict(sex=sex,object=name,vertices=len(bm.verts),edges=len(bm.edges),faces=len(bm.faces),edge_face_counts=counts,nonmanifold_edges=sum(len(e.link_faces)!=2 for e in bm.edges),Euler=len(bm.verts)-len(bm.edges)+len(bm.faces)))
        bm.free()
(W/'data/source_shell_topology.json').write_text(json.dumps(out,indent=2)+'\n')
for row in out:print(row,flush=True)
