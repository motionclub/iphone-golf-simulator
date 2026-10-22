import bpy,json,sys,pathlib
from collections import defaultdict
R=pathlib.Path(__file__).resolve().parents[4]; sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend'))
body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body_'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');output={}
for side in ('Left','Right'):
 p=rig.data.bones[side+'ThumbProximal'].head_local;m=rig.data.bones[side+'ThumbIntermediate'].head_local;d=(m-p).normalized();length=(m-p).length;groups=defaultdict(float);count=0;vertices=[]
 for v in body.data.vertices:
  pt=rig.matrix_world.inverted()@body.matrix_world@v.co;delta=pt-p;s=delta.dot(d)/length;distance=(delta-d*delta.dot(d)).length
  if not (-.15<s<1.15 and distance<.016):continue
  count+=1;weights={body.vertex_groups[g.group].name:g.weight for g in v.groups}
  for name,w in weights.items():groups[name]+=w
  vertices.append(dict(index=v.index,station=s,distance=distance,weights=weights))
 output[side]={'regionVertices':count,'weights':dict(sorted(groups.items(),key=lambda kv:-kv[1])),'vertices':vertices}
path=R/f'proof/full-visual-overhaul/characters/thumb-tube-audit-{sex}.json';path.write_text(json.dumps(output,indent=2));print('THUMB_TUBE',sex,{s:dict(regionVertices=v['regionVertices'],weights=v['weights']) for s,v in output.items()})
