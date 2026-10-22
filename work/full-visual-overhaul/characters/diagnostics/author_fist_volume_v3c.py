"""Editable pose-space volume corrective from evaluated DQS geometry.
The engine retains linear skinning; the difference is baked as a named morph.
Only local hand skin above the retained wrist boundary changes.
"""
import bpy,pathlib,sys,json
from mathutils import Vector,Matrix
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ClosedFistV3C.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));bpy.context.view_layer.update()
B=rig.matrix_world.inverted()@body.matrix_world;A=B.inverted();groups={g.index:g.name for g in body.vertex_groups};rest=[v.co.copy() for v in body.data.vertices]
trans={b.name:A@rig.pose.bones[b.name].matrix@b.matrix_local.inverted()@B for b in rig.data.bones};matrices=[];posed=[]
for i,v in enumerate(body.data.vertices):
 m=Matrix(((0,0,0,0),)*4);total=0
 for g in v.groups:
  if groups[g.group] in trans:m+=trans[groups[g.group]]*g.weight;total+=g.weight
 if total<.99:m=Matrix.Identity(4)
 matrices.append(m);posed.append(m@rest[i])
for modifier in body.modifiers:
 if modifier.type=='ARMATURE':modifier.use_deform_preserve_volume=True
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();target=[v.co.copy() for v in mesh.vertices];ev.to_mesh_clear()
for modifier in body.modifiers:
 if modifier.type=='ARMATURE':modifier.use_deform_preserve_volume=False
if not body.data.shape_keys:body.shape_key_add(name='Basis',from_mix=False)
adj=[set() for _ in rest]
for e in body.data.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
report={}
def ease(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
for side in ('Left','Right'):
 H=rig.data.bones[side+'Hand'].matrix_local.inverted()@B;ids={g.index for g in body.vertex_groups if g.name==side+'Hand' or any(g.name.startswith(side+d) for d in ('Thumb','Index','Middle','Ring','Little'))};mask={}
 for i,v in enumerate(body.data.vertices):
  amount=sum(g.weight for g in v.groups if g.group in ids);p=H@rest[i]
  if amount>.98 and p.y>.04:mask[i]=ease(.04,.055,p.y)
 current=[v.copy() for v in target]
 # Gentle volume-preserving surface fairing removes remesh edge corrugation.
 for repeat in range(6):
  for factor in (.5,-.53):
   nextpoints=[v.copy() for v in current]
   for i,amount in mask.items():
    if adj[i]:nextpoints[i]=current[i]+(sum((current[j] for j in adj[i]),Vector())/len(adj[i])-current[i])*(factor*amount)
   current=nextpoints
 key=body.shape_key_add(name='Hero_Fist_'+side,from_mix=False);changes=[];skip=0
 for i,amount in mask.items():
  m=matrices[i]
  if abs(m.determinant())<1e-7:skip+=1;continue
  correction=(current[i]-posed[i])*amount;key.data[i].co=m.inverted()@(posed[i]+correction);changes.append((correction.length,(key.data[i].co-rest[i]).length))
 key.value=1;report[side]={'vertices':len(changes),'maxPosedDeltaMetres':max(x[0] for x in changes),'maxBindDeltaMetres':max(x[1] for x in changes),'meanPosedDeltaMetres':sum(x[0] for x in changes)/len(changes),'singularSkipped':skip,'outsideRetainedCutDeltaMetres':0,'construction':'evaluated dual-quaternion volume, 6 Taubin cycles, inverse-linear-skin morph'}
bpy.context.view_layer.update();out=R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_FistSurfaceV3C.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
(R/f'proof/full-visual-overhaul/characters/fist-volume-v3c-{sex}.json').write_text(json.dumps(report,indent=2));print('FIST_VOLUME_V3B',sex,report,flush=True)
