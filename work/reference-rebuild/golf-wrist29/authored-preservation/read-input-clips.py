import bpy,json,sys
from pathlib import Path
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=R/'work/reference-rebuild/golf-wrist29/authored-preservation'
sex=sys.argv[sys.argv.index('--')+1];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(R/f'Unity/Assets/Resources/Hero/golfer_{"f" if sex=="Female" else "m"}.fbx'),use_anim=True)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');meta={'sex':sex,'rig':rig.name,'bones':len(rig.data.bones),'actions':[(a.name,list(a.frame_range)) for a in bpy.data.actions]};(W/f'{sex}-input-clips.inventory.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta))
