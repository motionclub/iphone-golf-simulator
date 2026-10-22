"""Read-only exact mesh/rest-rig check of frozen inputs versus draft/proof copies."""
import bpy,json,hashlib
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def digest(x):return hashlib.sha256(repr(x).encode()).hexdigest()
def specimen(sex,path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    meshes={}
    for name in ['Body_M','Face_M'] if sex=='Male' else ['Body_F','Face_F','Hair_F']:
        o=bpy.data.objects[name]
        meshes[name]=digest(([(tuple(v.co),[(o.vertex_groups[g.group].name,g.weight) for g in v.groups]) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons]))
    rig=bpy.data.objects['Rig_'+sex]
    rest=digest([(b.name,b.parent.name if b.parent else None,tuple(map(tuple,b.matrix_local)),tuple(b.head_local),tuple(b.tail_local)) for b in rig.data.bones])
    return dict(meshes=meshes,rest_rig=rest,bone_count=len(rig.data.bones))
rows=[]
for sex in ['Male','Female']:
    src=specimen(sex,W/f'inputs/HeroBase_{sex}_Dressed.blend')
    for kind in ['Draft','SwingProof']:
        path=W/f'export/Golf_{sex}_{kind}.blend';dst=specimen(sex,path)
        same=src==dst
        assert same,(sex,kind,'frozen identity changed')
        rows.append(dict(sex=sex,kind=kind,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),identity=dst,unchanged=True))
(W/'data/identity_swing_checkpoint.json').write_text(json.dumps(rows,indent=2)+'\n')
print('IDENTITY PASS: both body/face meshes, female hair, weights, bone names/parents/rest matrices exact in both draft/proof copies',flush=True)
