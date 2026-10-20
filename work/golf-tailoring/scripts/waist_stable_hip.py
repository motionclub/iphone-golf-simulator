import bpy
from pathlib import Path
W=Path(__file__).resolve().parents[1]
p=W/'export/Golf_Male_Draft.blend';bpy.ops.wm.open_mainfile(filepath=str(p))
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
for o in bpy.data.objects:
 if o.type!='MESH':continue
 accessory=o.name.startswith(('Golf_Belt','Golf_Buckle','Golf_PoloUnderlap'))
 facing=o.name=='Golf_PoloUnderlap';top=o.name=='Golf_Polo' or facing;bottom=o.name in ['Golf_Trousers','Golf_PocketBag']
 if not(accessory or top or bottom):continue
 hip=o.vertex_groups.get('Hips') or o.vertex_groups.new(name='Hips')
 keys=o.data.shape_keys.key_blocks if o.data.shape_keys else None
 for i,v in enumerate(o.data.vertices):
  w=1 if accessory else 1-smooth(.981,.999,v.co.z) if facing else 1-smooth(.998,1.075,v.co.z) if top else smooth(.89,.942,v.co.z)
  if w<=0:continue
  old={g.group:g.weight*(1-w) for g in v.groups};old[hip.index]=old.get(hip.index,0)+w
  for g in o.vertex_groups:g.remove([i])
  for j,val in old.items():
   if val>0:o.vertex_groups[j].add([i],val,'REPLACE')
  if keys:
   for k in list(keys)[1:]:k.data[i].co=keys[0].data[i].co+(k.data[i].co-keys[0].data[i].co)*(1-w)
 bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(p))
