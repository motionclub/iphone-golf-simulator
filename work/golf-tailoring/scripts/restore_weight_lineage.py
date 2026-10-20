import bpy,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(W.parent/'golf-look/export'/f'Golf_{sex}_Draft.blend'))
 originals={}
 for o in bpy.data.objects:
  if o.type=='MESH' and o.name.startswith('Golf_'):
   originals[o.name]=[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in o.data.vertices]
 bpy.ops.wm.open_mainfile(filepath=str(W/'export'/f'Golf_{sex}_Draft.blend'))
 for name,rows in originals.items():
  o=bpy.data.objects.get(name)
  if not o or len(o.data.vertices)!=len(rows):continue
  for g in list(o.vertex_groups):o.vertex_groups.remove(g)
  groups={n:o.vertex_groups.new(name=n) for n in {n for row in rows for n in row}}
  for i,row in enumerate(rows):
   for n,w in row.items():groups[n].add([i],w,'REPLACE')
 # Tuck the polo's former open side vents completely below the waistband.
 o=bpy.data.objects['Golf_Polo'];ks=o.data.shape_keys.key_blocks
 for i,v in enumerate(o.data.vertices):
  t=max(0,min(1,(1.045-v.co.z)/.045));dz=.024*t*t*(3-2*t)
  for key in ks:key.data[i].co.z-=dz
  v.co=ks[0].data[i].co
 bpy.ops.wm.save_as_mainfile(filepath=str(W/'export'/f'Golf_{sex}_Draft.blend'));print('RESTORED_LINEAGE',sex)
