import bpy,json
from pathlib import Path
w=Path('work/character-female33');bpy.ops.wm.open_mainfile(filepath=str(w/'Female_Baseline.blend'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');d={name:list(rig.matrix_world@rig.data.bones[name].head_local) for name in ['Hips','Spine','Chest','Neck','Head','LeftShoulder','LeftUpperArm','LeftLowerArm','RightUpperArm','RightLowerArm']};print(json.dumps(d,indent=2),flush=True);(w/'rig-landmarks.json').write_text(json.dumps(d,indent=2))
