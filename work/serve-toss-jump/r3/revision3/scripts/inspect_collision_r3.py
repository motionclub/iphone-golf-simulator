import bpy,sys,collections
from mathutils.bvhtree import BVHTree
a=sys.argv[sys.argv.index('--')+1:];tag=a[0]
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');act=bpy.data.actions['Serve'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
bpy.data.objects['Racket_Classic'].scale=(1.3,)*3
for f in [0,7,10,12,73,74]:
 bpy.context.scene.frame_set(f);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
 verts=[];tris=[];owners=[];groups=[]
 for nm in [('Body_M' if tag=='male' else 'Body_F'),('Face_M' if tag=='male' else 'Face_F'),'Kit_Top','Kit_Bottom','Kit_Sock_L','Kit_Sock_R','Kit_Shoe_L','Kit_Shoe_R']:
  o=bpy.data.objects.get(nm)
  if not o:continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();base=len(verts)
  verts += [ev.matrix_world@v.co for v in me.vertices];me.calc_loop_triangles()
  for t in me.loop_triangles:
   tris.append(tuple(base+i for i in t.vertices));owners.append(nm)
   weights=collections.Counter()
   for i in t.vertices:
    for g in me.vertices[i].groups:weights[o.vertex_groups[g.group].name]+=g.weight
   groups.append(weights.most_common(1)[0][0] if weights else '-')
  ev.to_mesh_clear()
 bvh=BVHTree.FromPolygons(verts,tris);counts=collections.Counter()
 for nm in ['Racket_Classic','StringBed']:
  ev=bpy.data.objects[nm].evaluated_get(dg);me=ev.to_mesh()
  for v in me.vertices:
   p=ev.matrix_world@v.co;loc,nor,idx,dist=bvh.find_nearest(p)
   if loc and (loc-p).dot(nor)>.003:counts[(nm,owners[idx],groups[idx])]+=1
  ev.to_mesh_clear()
 print('COLLISION',tag,f,dict(counts))
