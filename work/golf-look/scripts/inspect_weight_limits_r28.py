import bpy,numpy as np
from collections import Counter
for name in ['Body_M','Golf_Polo','Golf_Trousers']:
 o=bpy.data.objects[name];valid={g.index for g in o.vertex_groups if g.name in bpy.data.objects['Rig_Male'].data.bones}
 counts=Counter();lost=[]
 for v in o.data.vertices:
  weights=sorted([g.weight for g in v.groups if g.group in valid and g.weight>=.001],reverse=True);counts[len(weights)]+=1;lost.append(sum(weights[4:]))
 print(name,dict(counts),'maxDropped',max(lost),'more4',sum(x>0 for x in lost),flush=True)
