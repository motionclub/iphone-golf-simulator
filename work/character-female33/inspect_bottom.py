import bpy,json,numpy as np
from pathlib import Path
w=Path('work/character-female33');bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath='Unity/Assets/Characters/MatchHeroKit/Female_Kit.fbx');o=bpy.data.objects.get('Kit_Bottom');print('OBJECTS',[a.name for a in bpy.data.objects if a.type=='MESH'],flush=True)
if o:
 m=o.data;P=np.array([v.co for v in m.vertices]);print('SKIRT',len(P),len(m.polygons),'range',P.min(0),P.max(0),'materials',[x.name for x in m.materials],flush=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(w/'Female_KitBaseline.blend'))
