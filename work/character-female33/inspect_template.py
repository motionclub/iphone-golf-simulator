import bpy,json,numpy as np
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath='work/character-finish32/Male_Polo_CuffRebuilt.blend');o=bpy.data.objects['Kit_Top'];r=next(x for x in bpy.data.objects if x.type=='ARMATURE')
for n in ['Hips','Spine','Chest','Neck','Head','LeftShoulder','LeftUpperArm','LeftLowerArm']:
 b=r.data.bones[n];print(n,list(b.head_local),list(b.tail_local))
p=np.array([v.co for v in o.data.vertices]);ids=np.flatnonzero((abs(p[:,0])<.015)&(p[:,2]>1.30));print('FRONT CENTER',[(i,p[i].tolist(),[(o.vertex_groups[g.group].name,round(g.weight,3)) for g in o.data.vertices[i].groups]) for i in ids[::max(1,len(ids)//20)]])
