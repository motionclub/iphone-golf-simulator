import bpy,json,math
from pathlib import Path
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
report=[]
for sex in ['Male','Female']:
 for clip in ['Forehand','Backhand','Serve']:
  bpy.ops.wm.read_factory_settings(use_empty=True)
  bpy.ops.import_scene.fbx(filepath=str(r/f'Unity/Assets/Characters/MatchHeroes/{sex}/{sex}_{clip}.fbx'))
  arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');act=arm.animation_data.action
  fps=bpy.context.scene.render.fps;start=float(act.frame_range[0]);end=float(act.frame_range[1])
  out={'sex':sex,'clip':clip,'fps':fps,'range':[start,end],'samples':[]}
  times=[.2333,.25,.2667,.28,.3,.3052,.32,.3438,.4941,.5976,.6667,.6833] if clip=='Forehand' else [.2667,.3052,.3333,.45,.503,.6333,.6417,.6833] if clip=='Backhand' else [1.60,1.633,1.6667,1.70,1.7333,1.7667,1.80]
  for t in times:
   frame=start+t*fps;bpy.context.scene.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update()
   sample={'time':t}
   for name in ['Hips','LeftHand','RightHand','LeftUpperArm','LeftLowerArm','RightUpperArm','RightLowerArm']:
    bone=arm.pose.bones.get(name)
    if bone:sample[name]=list(arm.matrix_world@bone.head)
   out['samples'].append(sample)
  report.append(out)
(r/'work/full-visual-overhaul/tennis/stroke-source-probe.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
