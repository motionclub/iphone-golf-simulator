"""Author fist normal fields from actual evaluated closed triangles.
Geometry normals are computed independently after pose-space corrections.
Their inverse blended skin map yields the blendshape's pre-skin target normals.
Only local hand fields above the retained wrist cut are touched.
"""
import bpy,pathlib,sys,json,math
from mathutils import Vector,Matrix
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_FistSurfaceV3.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));bpy.context.view_layer.update()
B=rig.matrix_world.inverted()@body.matrix_world;A=B.inverted();groups={g.index:g.name for g in body.vertex_groups}
rest=[v.co.copy() for v in body.data.shape_keys.key_blocks['Basis'].data]
trans={b.name:(A@rig.pose.bones[b.name].matrix@b.matrix_local.inverted()@B).to_3x3() for b in rig.data.bones}
eval=body.evaluated_get(bpy.context.evaluated_depsgraph_get());evaluated=eval.to_mesh()
geo=bpy.data.meshes.new('Independent posed surface normals');geo.from_pydata([v.co for v in evaluated.vertices],[],[tuple(p.vertices) for p in evaluated.polygons]);geo.update()
matrices=[]
for v in body.data.vertices:
 m=Matrix(((0,0,0),)*3);total=0
 for g in v.groups:
  if groups[g.group] in trans:m+=trans[groups[g.group]]*g.weight;total+=g.weight
 matrices.append(m if total>.99 else Matrix.Identity(3))
result={'version':'match-hero-hand-anatomy-v3','construction':'Geometry normals from final posed triangles, inverse blended skin normal map; original wrist cut retained','left':[],'right':[]};audit={}
for side in ('Left','Right'):
 H=rig.data.bones[side+'Hand'].matrix_local.inverted()@B;ids={g.index for g in body.vertex_groups if g.name==side+'Hand' or any(g.name.startswith(side+d) for d in ('Thumb','Index','Middle','Ring','Little'))}
 entries=[];maxangle=0;singular=0
 for i,v in enumerate(body.data.vertices):
  amount=sum(g.weight for g in v.groups if g.group in ids);hp=H@rest[i]
  if amount<.98 or hp.y<.04:continue
  m=matrices[i];n=geo.vertices[i].normal.normalized()
  if abs(m.determinant())<1e-7:singular+=1;continue
  pre=(m.inverted()@n).normalized();angle=(m@pre).normalized().angle(n);maxangle=max(maxangle,angle)
  # Smoothly blend into the retained original wrist normal field.
  fade=max(0,min(1,(hp.y-.04)/.015));fade=fade*fade*(3-2*fade)
  entries.append({'p':list(rest[i]),'n':list(pre),'pn':list(n),'strength':fade})
 result[side.lower()]=entries;audit[side]={'vertices':len(entries),'maxInverseSkinAngularErrorDegrees':math.degrees(maxangle),'singularSkipped':singular,'minimumHandLocalYMetres':.04}
out=R/'work/full-visual-overhaul/characters/exports/HandsV3';(out/f'{sex}_Normals.json').write_text(json.dumps(result,separators=(',',':')))
(R/f'proof/full-visual-overhaul/characters/fist-normal-fields-v3-{sex}.json').write_text(json.dumps(audit,indent=2));print('AUTHORED_HAND_NORMAL_FIELDS',sex,audit,flush=True)
