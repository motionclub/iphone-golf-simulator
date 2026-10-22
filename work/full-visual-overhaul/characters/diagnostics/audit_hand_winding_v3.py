import bpy,pathlib,sys,json
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_FistSurfaceV3.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));groups={g.index:g.name for g in body.vertex_groups};report={}
for side in ('Left','Right'):
 H=rig.data.bones[side+'Hand'].matrix_local.inverted()@rig.matrix_world.inverted()@body.matrix_world;p=[H@v.co for v in body.data.vertices];totals={d:{'outward':0,'inward':0,'degenerate':0} for d in ('Thumb','Index','Middle','Ring','Little')}
 for poly in body.data.polygons:
  weights={d:sum(g.weight for i in poly.vertices for g in body.data.vertices[i].groups if groups[g.group].startswith(side+d))/len(poly.vertices) for d in totals};d=max(weights,key=weights.get)
  if weights[d]<.85:continue
  names=[side+d+j for j in ('Proximal','Intermediate','Distal')];pts=[rig.data.bones[side+'Hand'].matrix_local.inverted()@rig.data.bones[n].head_local for n in names]+[rig.data.bones[side+'Hand'].matrix_local.inverted()@rig.data.bones[names[-1]].tail_local]
  centre=sum((p[i] for i in poly.vertices),Vector())/len(poly.vertices);near=min((a+(b-a)*max(0,min(1,(centre-a).dot(b-a)/(b-a).length_squared)) for a,b in zip(pts,pts[1:])),key=lambda q:(q-centre).length_squared)
  n=(p[poly.vertices[1]]-p[poly.vertices[0]]).cross(p[poly.vertices[2]]-p[poly.vertices[0]])
  dot=n.dot(centre-near);totals[d]['outward' if dot>1e-12 else 'inward' if dot<-1e-12 else 'degenerate']+=1
 report[side]={'bodyWorldDeterminant':body.matrix_world.determinant(),'bodyToHandDeterminant':H.determinant(),'fingers':totals}
(R/f'proof/full-visual-overhaul/characters/source-hand-winding-v3-{sex}.json').write_text(json.dumps(report,indent=2));print('HAND_WINDING_V3',sex,report,flush=True)
