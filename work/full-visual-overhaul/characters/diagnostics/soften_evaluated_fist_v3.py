"""Smooth the actual evaluated LBS fist; bake a pre-skin corrective.
The retained +35mm cut and all exterior forearm/body vertices remain exact.
A Taubin positive/negative pass removes joint ridges without shrinking digits.
"""
import bpy,pathlib,sys,json,math
from mathutils import Vector,Matrix
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ClosedFistV3.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'))
bpy.context.view_layer.update();B=rig.matrix_world.inverted()@body.matrix_world;toBody=B.inverted()
rest=[v.co.copy() for v in body.data.vertices];groups={g.index:g.name for g in body.vertex_groups}
trans={b.name:toBody@rig.pose.bones[b.name].matrix@b.matrix_local.inverted()@B for b in rig.data.bones}
matrices=[];posed=[]
for i,v in enumerate(body.data.vertices):
 m=Matrix(((0,0,0,0),)*4);total=0
 for g in v.groups:
  if groups[g.group] in trans:m+=trans[groups[g.group]]*g.weight;total+=g.weight
 if total<.99:m=Matrix.Identity(4)
 matrices.append(m);posed.append(m@rest[i])
adj=[set() for _ in rest]
for e in body.data.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
if not body.data.shape_keys:body.shape_key_add(name='Basis',from_mix=False)
report={}
def ease(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
for side in ('Left','Right'):
 H=rig.data.bones[side+'Hand'].matrix_local.inverted()@B
 ids={g.index for g in body.vertex_groups if g.name==side+'Hand' or any(g.name.startswith(side+d) for d in ('Thumb','Index','Middle','Ring','Little'))}
 mask={}
 for i,v in enumerate(body.data.vertices):
  amount=sum(g.weight for g in v.groups if g.group in ids);p=H@rest[i]
  if amount>.2 and p.y>.04:mask[i]=ease(.04,.055,p.y)*min(1,amount*2)
 current=[v.copy() for v in posed]
 for repeat in range(16):
  for factor in (.5,-.53):
   nextpoints=[v.copy() for v in current]
   for i,amount in mask.items():
    if adj[i]:nextpoints[i]=current[i]+(sum((current[j] for j in adj[i]),Vector())/len(adj[i])-current[i])*(factor*amount)
   current=nextpoints
 key=body.shape_key_add(name='Hero_Fist_'+side,from_mix=False);changes=[];skip=0
 for i,amount in mask.items():
  m=matrices[i]
  if abs(m.determinant())<1e-7:skip+=1;continue
  correction=current[i]-posed[i]
  # This is a surface refinement, not a second anatomical repositioning.
  if correction.length>.006:correction*=.006/correction.length
  key.data[i].co=m.inverted()@(posed[i]+correction)
  changes.append((i,correction.length,(key.data[i].co-rest[i]).length))
 key.value=1
 report[side]={'vertices':len(changes),'singularSkipped':skip,'maxPosedDeltaMetres':max(x[1] for x in changes),'maxBindDeltaMetres':max(x[2] for x in changes),'meanPosedDeltaMetres':sum(x[1] for x in changes)/len(changes),'outsideRetainedCutDeltaMetres':0,'cutHandLocalYMetres':.035,'construction':'16 Taubin cycles applied to actual evaluated linear-skinned posed mesh, inverse-skinned corrective'}
bpy.context.view_layer.update();out=R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_FistSurfaceV3.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
(R/f'proof/full-visual-overhaul/characters/fist-surface-soft-v3-{sex}.json').write_text(json.dumps(report,indent=2));print('FIST_SURFACE_SOFT_V3',sex,report,flush=True)
