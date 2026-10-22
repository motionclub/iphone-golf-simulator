import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
rows=[]
for sex in ['Male','Female']:
 for part,path in [('body',R/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend'),('golf',R/f'work/golf-motion-fit/export/Golf_{sex}_Master.blend')]:
  bpy.ops.wm.open_mainfile(filepath=str(path));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.data.pose_position='POSE'
  for b in rig.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
  bpy.context.view_layer.update();d={'sex':sex,'part':part,'path':str(path),'meshes':[],'bones':[]}
  for o in bpy.data.objects:
   if o.type=='MESH' and (o.name.startswith(('Body','Face','Kit','Hair'))):
    points=[o.matrix_world@v.co for v in o.data.vertices];d['meshes'].append({'name':o.name,'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'materials':[m.name if m else None for m in o.data.materials],'bounds':[[min(v[i] for v in points),max(v[i] for v in points)] for i in range(3)],'mods':[(m.name,m.type) for m in o.modifiers]})
  for name in ['Head','Neck','LeftUpperArm','LeftLowerArm','LeftHand','LeftUpperLeg','LeftLowerLeg','LeftFoot','RightUpperArm','Hips']:
   b=rig.pose.bones.get(name)
   if b:d['bones'].append({'name':name,'head':list(rig.matrix_world@b.head),'tail':list(rig.matrix_world@b.tail)})
  rows.append(d)
(R/'proof/full-visual-overhaul/golf/gallery-hero-inputs.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows))
