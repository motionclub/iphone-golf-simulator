import bpy,numpy as np
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath='work/golf-tailoring/export/Golf_Female_Draft.blend')
for name in ['Golf_PleatedSkort','Golf_InnerShorts','Golf_Polo']:
 o=bpy.data.objects[name];o.data.update();vals=[p.normal.dot(Vector((p.center.x,p.center.y+.02,0))) for p in o.data.polygons if abs(p.normal.z)<.8]
 print('NORMAL_DIRECTION',name,len(vals),'outward',sum(x>0 for x in vals),'inward',sum(x<0 for x in vals))
