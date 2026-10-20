import bpy,numpy as np,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
W=Path(__file__).resolve().parents[1]
def smooth(a,b,x):t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
for sex in ['Male']:
 path=W/'export'/f'Golf_{sex}_Draft.blend'
 bpy.ops.wm.open_mainfile(filepath=str(path));body=bpy.data.objects['Body_'+sex[0]];body.data.calc_loop_triangles();allowed={'Hips','Spine','Chest','UpperChest','LeftUpperLeg','RightUpperLeg'}; torso={v.index for v in body.data.vertices if sum(g.weight for g in v.groups if body.vertex_groups[g.group].name in allowed)>.85}; tri=[tuple(t.vertices) for t in body.data.loop_triangles if all(i in torso for i in t.vertices)];p=[v.co.copy() for v in body.data.vertices];tree=BVHTree.FromPolygons(p,tri,all_triangles=True)
 names={g.index:g.name for g in body.vertex_groups}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  accessory=o.name.startswith(('Golf_Belt','Golf_Buckle'))
  bottom=o.name in ['Golf_Trousers','Golf_PleatedSkort','Golf_InnerShorts']
  top=o.name=='Golf_Polo'
  if not (accessory or bottom or top):continue
  ks=o.data.shape_keys.key_blocks if o.data.shape_keys else None
  groups={g.name:g for g in o.vertex_groups}
  for name in set(names.values()):
   if name not in groups:groups[name]=o.vertex_groups.new(name=name)
  for i,v in enumerate(o.data.vertices):
   z=v.co.z;w=1 if accessory else smooth(.875,.945,z) if bottom else 1-smooth(.991,1.055,z)
   if w<=0:continue
   loc,normal,idx,dist=tree.find_nearest(v.co);ids=tri[idx];a,b,c=[p[j] for j in ids]
   bary=barycentric_transform(loc,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
   ws={}
   for g in v.groups:
    n=o.vertex_groups[g.group].name
    if n in names.values():ws[n]=g.weight*(1-w)
   for j,bw in zip(ids,bary):
    for g in body.data.vertices[j].groups:
     if names[g.group] in allowed:ws[names[g.group]]=ws.get(names[g.group],0)+max(0,bw)*g.weight*w
   ws=sorted(ws.items(),key=lambda t:-t[1])[:4];total=sum(v for _,v in ws)
   for g in o.vertex_groups:g.remove([i])
   for name,value in ws:groups[name].add([i],value/total,'REPLACE')
   if ks:
    for k in list(ks)[1:]:k.data[i].co=ks[0].data[i].co+(k.data[i].co-ks[0].data[i].co)*(1-w)
  o.data.update()
 bpy.ops.wm.save_as_mainfile(filepath=str(path));print('WAIST_REFINED',sex,flush=True)
