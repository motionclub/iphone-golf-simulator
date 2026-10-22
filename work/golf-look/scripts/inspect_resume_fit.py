import bpy,sys,json
from pathlib import Path
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import activate_clip
sex=sys.argv[-1];b=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];r=bpy.data.objects['Rig_'+sex]
activate_clip(r,'ReadyIdle');bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
print('MODIFIERS',[(o.name,[(m.name,m.type,getattr(m,'use_deform_preserve_volume',None)) for m in o.modifiers]) for o in [b,bpy.data.objects['Golf_Polo']]])
for i in ([1503,9742,2896,12196] if sex=='Female' else [4001,10155,12163,21752]):
 v=b.data.vertices[i];print('VERTEX',i,tuple(v.co),[(b.vertex_groups[g.group].name,g.weight) for g in v.groups])
for im in bpy.data.images:
 if im.type=='IMAGE':print('IMAGE',im.name,im.filepath,bpy.path.abspath(im.filepath),im.has_data)
