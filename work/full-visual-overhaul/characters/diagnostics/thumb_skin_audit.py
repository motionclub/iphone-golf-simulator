import bpy,json,sys,pathlib
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[4]; sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend'))
body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body_'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
rig.animation_data_clear()
for p in rig.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update()
result={'sex':sex,'side':{}}
for side in ('Left','Right'):
 H=rig.data.bones[side+'Hand'].matrix_local.inverted();info={}
 for name in ('ThumbProximal','ThumbIntermediate','ThumbDistal','IndexProximal','IndexIntermediate','IndexDistal'):
  full=side+name;b=rig.data.bones[full];group=body.vertex_groups.get(full);points=[]
  if group:
   for v in body.data.vertices:
    weight=sum(g.weight for g in v.groups if g.group==group.index)
    if weight>.25:points.append((H@(rig.matrix_world.inverted()@body.matrix_world@v.co),weight))
  info[name]={'boneHeadHand':list(H@b.head_local),'boneTailHand':list(H@b.tail_local),'weightedVertices':len(points),'weightedMin':[min(p[d] for p,w in points) if points else 0 for d in range(3)],'weightedMax':[max(p[d] for p,w in points) if points else 0 for d in range(3)],'centroid':list(sum((p*w for p,w in points),Vector())/sum(w for p,w in points)) if points else [],'restLocal':[list(row) for row in (b.parent.matrix_local.inverted()@b.matrix_local)]}
 result['side'][side]=info
out=R/f'proof/full-visual-overhaul/characters/thumb-skin-audit-{sex}.json';out.write_text(json.dumps(result,indent=2));print('THUMB_SKIN_AUDIT',out)
