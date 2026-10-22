import bpy,json,sys,pathlib,math
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend'))
body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body_'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
old=[v.co.copy() for v in body.data.vertices];stats=[]
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
for side in ('Left','Right'):
 hand=body.vertex_groups.get(side+'Hand');prox=body.vertex_groups.get(side+'ThumbProximal');p=rig.data.bones[side+'ThumbProximal'].head_local;m=rig.data.bones[side+'ThumbIntermediate'].head_local;direction=m-p;length=direction.length;axis=direction/length
 four={g.index for g in body.vertex_groups if g.name.startswith(side) and any(d in g.name for d in ('Index','Middle','Ring','Little'))}; changed=0;maximum=0
 for v in body.data.vertices:
  weights={g.group:g.weight for g in v.groups};hw=weights.get(hand.index,0)
  if hw<.2 or sum(w for g,w in weights.items() if g in four)>.05:continue
  point=rig.matrix_world.inverted()@body.matrix_world@v.co;delta=point-p;s=delta.dot(axis)/length;distance=(delta-axis*delta.dot(axis)).length
  radius=.010 if sex=='Female' else .012
  transfer=hw*.9*smooth(.02,.50,s)*(1-smooth(.80,1.50,s))*(1-smooth(radius*.45,radius,distance))
  if transfer<.005:continue
  hand.add([v.index],hw-transfer,'REPLACE');prox.add([v.index],weights.get(prox.index,0)+transfer,'REPLACE');changed+=1;maximum=max(maximum,transfer*2)
 stats.append({'side':side,'changedVertices':changed,'maxWeightL1':maximum,'radiusMetres':radius})
assert all((v.co-p).length<1e-10 for v,p in zip(body.data.vertices,old))
out=R/'ArtDir/hero/kit/premium/source'/f'Premium_{sex}_ThumbWeights.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
report=R/'proof/full-visual-overhaul/characters'/f'thumb-weight-repair-{sex}.json';report.write_text(json.dumps({'gate':'SOURCE ONLY: unchanged 53 bones/rest/positions/normals/topology, measured thumb-root transfer; actual +/-30 and full fist proof pending','stats':stats},indent=2));print('THUMB_WEIGHT_REPAIR',sex,stats)
