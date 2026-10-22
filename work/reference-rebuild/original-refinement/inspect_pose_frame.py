import bpy,pathlib,json,math
from mathutils import Vector
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/original-refinement';report={}
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(R/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend'));sc=bpy.context.scene;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='POSE'
 rest=rig.matrix_world@rig.data.bones['Head'].matrix_local;out={'fps':sc.render.fps/sc.render.fps_base,'restHeadWorld':list(rest.translation),'actions':[]}
 acts=[a for a in bpy.data.actions if any(n in a.name.lower() for n in ('ready','idle','introwave'))]
 rig.animation_data_create()
 for a in acts:
  rig.animation_data.action=a
  if hasattr(a,'slots') and len(a.slots):rig.animation_data.action_slot=a.slots[0]
  for t in (0,.5,1):
   sc.frame_set(int(round(a.frame_range[0]+t*sc.render.fps/sc.render.fps_base)));bpy.context.view_layer.update();posed=rig.matrix_world@rig.pose.bones['Head'].matrix;delta=posed.to_3x3()@rest.to_3x3().inverted();f=(delta@Vector((0,-1,0))).normalized();u=(delta@Vector((0,0,1))).normalized()
   out['actions'].append({'name':a.name,'time':t,'startFrame':a.frame_range[0],'forward':list(f),'up':list(u),'downPitchDegrees':math.degrees(math.asin(max(-1,min(1,-f.z)))),'yawDegrees':math.degrees(math.atan2(f.x,-f.y)),'headWorld':list(posed.translation)})
 report[sex]=out
 (O/'pose-head-frame.json').write_text(json.dumps(report,indent=2));print('POSE_HEAD_FRAME',sex,out)
