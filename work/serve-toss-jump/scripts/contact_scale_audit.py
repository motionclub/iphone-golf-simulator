"""Read both original/candidate FBXs' strings centres at the game's 1.3x racket scale."""
import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1]
out={}
for tag,H in [('male','Male'),('female','Female')]:
    vals={}
    for kind,folder in [('baseline','rollback'),('candidate','export/fbx')]:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=str(W/folder/f'{H}_Serve.fbx'),automatic_bone_orientation=False)
        rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
        action=rig.animation_data.action
        imported_range=list(action.frame_range)
        imported_fps=bpy.context.scene.render.fps/bpy.context.scene.render.fps_base
        bpy.context.scene.frame_set(52)
        racket=bpy.data.objects['Racket_Classic'];original_scale=list(racket.scale)
        racket.scale=(1.3,1.3,1.3);bpy.context.view_layer.update()
        dg=bpy.context.evaluated_depsgraph_get();bed=bpy.data.objects['StringBed'].evaluated_get(dg);me=bed.to_mesh()
        v=np.array([x.co for x in me.vertices]);c=(v.min(0)+v.max(0))/2
        vals[kind]={'strings_13':list(bed.matrix_world@Vector(c)), 'original_racket_scale':original_scale,'StringBed_parent':bpy.data.objects['StringBed'].parent.name,'imported_frame_range':imported_range,'imported_fps':imported_fps,'imported_length_s':(imported_range[1]-imported_range[0])/imported_fps}
        bed.to_mesh_clear()
    vals['strings_delta_13_mm']=float(np.linalg.norm(np.array(vals['candidate']['strings_13'])-vals['baseline']['strings_13'])*1000)
    out[tag]=vals
(W/'data/contact_racket_scale_audit.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
