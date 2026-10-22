import bpy,pathlib,sys,json
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ClosedFistV3.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));H=rig.data.bones['LeftHand'].matrix_local.inverted()@rig.matrix_world.inverted()@body.matrix_world;group={g.index:g.name for g in body.vertex_groups};out=[]
for v in body.data.vertices:
 p=H@v.co;weights={group[g.group]:g.weight for g in v.groups}
 if not (.08<p.y<.24 and sum(w for n,w in weights.items() if n.startswith('Left') and any(d in n for d in ['Index','Middle','Ring','Little','Thumb']))>.1):continue
 hand=weights.get('LeftHand',0);other={n:w for n,w in weights.items() if w>.001 and not (n=='LeftHand' or n.startswith('Left') and any(d in n for d in ['Index','Middle','Ring','Little','Thumb']))}
 if hand>.1 or other:out.append({'id':v.index,'p':list(p),'weights':weights})
print('POISON_VERTS',len(out));print(json.dumps(out[:40],indent=2))
