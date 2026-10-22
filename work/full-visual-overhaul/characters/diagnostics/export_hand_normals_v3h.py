import bpy,pathlib,sys,json,math
from mathutils import Vector,Matrix,Quaternion
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_FistSurfaceV3H.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));full={p.name:(p.rotation_quaternion.copy(),p.location.copy(),p.scale.copy()) for p in rig.pose.bones};B=rig.matrix_world.inverted()@body.matrix_world;A=B.inverted();groups={g.index:g.name for g in body.vertex_groups};rest=[v.co.copy() for v in body.data.shape_keys.key_blocks['Basis'].data]
result={'version':'match-hero-hand-anatomy-v3','construction':'Four independently sculpted evaluated surfaces and inverse blended skin normal map; fixed wrist cut retained','left':[],'right':[],'stages':[]};audit={}
for stage in (.25,.5,.75,1):
 for p in rig.pose.bones:
  if any(p.name.startswith(side+d) for side in ('Left','Right') for d in ('Thumb','Index','Middle','Ring','Little')):
   q,l,s=full[p.name];p.rotation_quaternion=Quaternion().slerp(q,stage);p.location=l*stage;p.scale=Vector((1,1,1)).lerp(s,stage)
 bpy.context.view_layer.update();trans={b.name:(A@rig.pose.bones[b.name].matrix@b.matrix_local.inverted()@B).to_3x3() for b in rig.data.bones};matrices=[]
 for v in body.data.vertices:
  m=Matrix(((0,0,0),)*3);total=0
  for g in v.groups:
   if groups[g.group] in trans:m+=trans[groups[g.group]]*g.weight;total+=g.weight
  matrices.append(m if total>.99 else Matrix.Identity(3))
 for side in ('Left','Right'):
  H=rig.data.bones[side+'Hand'].matrix_local.inverted()@B;ids={g.index for g in body.vertex_groups if g.name==side+'Hand' or any(g.name.startswith(side+d) for d in ('Thumb','Index','Middle','Ring','Little'))};suffix=side if stage==1 else str(round(stage*100))+'_'+side;shape='Hero_Fist_'+suffix;field=body.data.attributes['Hero_Fist_PosedNormal_'+suffix];entries=[];maximum=0;singular=0
  for i,v in enumerate(body.data.vertices):
   amount=sum(g.weight for g in v.groups if g.group in ids);hp=H@rest[i]
   if amount<.98 or hp.y<.04 or field.data[i].vector.length<.5:continue
   m=matrices[i];n=field.data[i].vector.normalized()
   if abs(m.determinant())<1e-7:singular+=1;continue
   pre=(m.inverted()@n).normalized();maximum=max(maximum,math.degrees((m@pre).normalized().angle(n)));fade=max(0,min(1,(hp.y-.04)/.015));fade=fade*fade*(3-2*fade);entries.append({'p':list(rest[i]),'n':list(pre),'pn':list(n),'strength':fade})
  if stage==1:result[side.lower()]=entries
  else:result['stages'].append({'shape':shape,'entries':entries})
  audit[shape]={'vertices':len(entries),'maxInverseSkinAngularErrorDegrees':maximum,'singularSkipped':singular}
out=R/'work/full-visual-overhaul/characters/exports/HandsV3H';out.mkdir(parents=True,exist_ok=True);(out/f'{sex}_Normals.json').write_text(json.dumps(result,separators=(',',':')));(R/f'proof/full-visual-overhaul/characters/fist-normal-fields-v3h-{sex}.json').write_text(json.dumps(audit,indent=2));print('HAND_V3H_NORMALS',sex,audit,flush=True)
