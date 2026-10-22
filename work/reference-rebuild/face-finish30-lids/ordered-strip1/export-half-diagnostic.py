import bpy,numpy as np
from pathlib import Path
O=Path.cwd()/'work/reference-rebuild/face-finish30-lids/ordered-strip1';bpy.ops.wm.open_mainfile(filepath=str(O/'Male_Face30OrderedLids.blend'));b=bpy.data.objects['Body'];f=bpy.data.objects['ReferenceFeatures'];d={}
for tag,ob in [('body',b),('features',f)]:
 ob.data.calc_loop_triangles();d[tag+'Triangles']=np.array([q.vertices[:]for q in ob.data.loop_triangles]);d[tag+'Materials']=np.array([q.material_index for q in ob.data.loop_triangles]);d[tag+'Half']=np.array([v.co[:]for v in ob.data.shape_keys.key_blocks['Hero_Blink_Half'].data]);d[tag+'Basis']=np.array([v.co[:]for v in ob.data.shape_keys.key_blocks['Basis'].data]);d[tag+'Full']=np.array([v.co[:]for v in ob.data.shape_keys.key_blocks['Hero_Blink'].data])
np.savez_compressed(O/'half-diagnostic.npz',**d)
