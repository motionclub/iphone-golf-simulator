import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

def parts(m):
 a=[[] for _ in m.vertices]
 for e in m.edges:
  i,j=e.vertices;a[i].append(j);a[j].append(i)
 seen=set();out=[]
 for i in range(len(a)):
  if i in seen:continue
  q=[i];seen.add(i);c=[]
  while q:
   v=q.pop();c.append(v)
   for j in a[v]:
    if j not in seen:seen.add(j);q.append(j)
  out.append(c)
 return sorted(out,key=len,reverse=True)

def construct_pockets(o):
 m=o.data;m.update();P=np.array([v.co[:] for v in m.vertices]);N=np.array([v.normal[:] for v in m.vertices]);cs=parts(m);weights=[[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in m.vertices];kd=KDTree(len(P))
 for i,p in enumerate(P):kd.insert(Vector(p),i)
 kd.balance();curves=[];welts=[]
 m.calc_loop_triangles();main=set(cs[0]);sourceTri=[tuple(t.vertices) for t in m.loop_triangles if all(v in main for v in t.vertices)]
 surface=BVHTree.FromPolygons([Vector(p) for p in P],sourceTri,all_triangles=True)
 def copied_weights(point):
  _,idx,dist=kd.find(point)
  if dist<1e-6:return weights[idx]
  nearest,_,face,_=surface.find_nearest(point)
  if nearest is None:return weights[idx]
  ids=sourceTri[face];a,b,c=P[list(ids)];q=np.array(nearest)-a;e=b-a;f=c-a
  ee=e@e;ef=e@f;ff=f@f;qe=q@e;qf=q@f;den=max(ee*ff-ef*ef,1e-15)
  v=(ff*qe-ef*qf)/den;w=(ee*qf-ef*qe)/den;bc=np.maximum([1-v-w,v,w],0);bc/=bc.sum();total={}
  for vi,alpha in zip(ids,bc):
   for name,weight in weights[vi]:total[name]=total.get(name,0)+float(alpha)*weight
  values=sorted(total.items(),key=lambda v:v[1],reverse=True)[:4];norm=sum(v[1] for v in values)
  return [(name,weight/norm) for name,weight in values if weight>1e-8]
 for ids in cs:
  q=P[ids]
  if len(ids)!=60 or q[:,2].min()<.82 or q[:,2].max()>.93:continue
  _,_,v=np.linalg.svd(q-q.mean(0),full_matrices=False);t=(q-q.mean(0))@v[0];order=np.argsort(t)
  # Existing 60 vertices are three cross-section rings at 20 positions.
  ct=np.array([q[order[j:j+3]].mean(0) for j in range(0,60,3)])
  curves.append(ct);welts.extend(ids)
 assert len(curves)==2
 bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in welts],context='VERTS');bm.to_mesh(m);bm.free()
 def make(name,vs,faces,material=None):
  me=bpy.data.meshes.new(name);me.from_pydata(vs,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
  obj=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(obj);obj.matrix_world=o.matrix_world.copy()
  if material:me.materials.append(bpy.data.materials[material])
  return obj
 def weights_to(obj):
  for vertex in obj.data.vertices:
   assigned=copied_weights(vertex.co)
   for g in list(vertex.groups):obj.vertex_groups[g.group].remove([vertex.index])
   for name,w in assigned:
    vg=obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name);vg.add([vertex.index],w,'REPLACE')
 made=[];start=len(o.data.polygons)
 for ct in curves:
  bases=[]
  for i,C in enumerate(ct):
   _,idx,_=kd.find(Vector(C));n=N[idx].copy();n/=np.linalg.norm(n);d=ct[min(i+1,len(ct)-1)]-ct[max(0,i-1)];u=np.cross(d,n);u/=np.linalg.norm(u);bases.append((C,n,u))
  # A closed boolean cutter gives an actual continuous slot, including fractional boundary triangles.
  vs=[]
  for C,n,u in bases:
   for pos in [C-u*.006-n*.018,C+u*.006-n*.018,C-u*.006+n*.012,C+u*.006+n*.012]:vs.append(tuple(pos))
  faces=[]
  for i in range(len(ct)-1):
   a=i*4;b=a+4;faces.extend([(a,a+1,b+1,b),(a+2,b+2,b+3,a+3),(a,b,b+2,a+2),(a+1,a+3,b+3,b+1)])
  faces.extend([(0,2,3,1),(len(vs)-4,len(vs)-3,len(vs)-1,len(vs)-2)])
  cutter=make('Pocket_boolean',vs,faces);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
  mod=o.modifiers.new('Clean pocket opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
  vs=[];faces=[]
  for C,n,u in bases:
   for pos in [C-u*.010-n*.0015,C+u*.010-n*.0015,C-u*.006,C+u*.006]:vs.append(tuple(pos))
  for i in range(len(ct)-1):
   a=i*4;b=a+4;faces.extend([(a,a+1,b+1,b),(a,a+2,b+2,b),(a+1,b+1,b+3,a+3)])
  faces.extend([(0,2,3,1),(len(vs)-4,len(vs)-3,len(vs)-1,len(vs)-2)])
  bag=make('Pocket_interior',vs,faces,'Kit_ShortsBand')
  bm=bmesh.new();bm.from_mesh(bag.data);bm.faces.ensure_lookup_table()
  if bm.faces[0].normal.dot(Vector(bases[0][1]))<0:
   for face in bm.faces:face.normal_flip()
  bm.to_mesh(bag.data);bm.free();weights_to(bag);made.append(bag)
  for side in [-1,1]:
   vs=[];faces=[]
   for C,n,u in bases:
    for pos in [C+u*side*.006-n*.0005,C+u*side*.009-n*.0005,C+u*side*.006+n*.001,C+u*side*.009+n*.001]:vs.append(tuple(pos))
   for i in range(len(ct)-1):
    a=i*4;b=a+4;faces.extend([(a,a+1,b+1,b),(a+2,b+2,b+3,a+3),(a,b,b+2,a+2),(a+1,a+3,b+3,b+1)])
   faces.extend([(0,2,3,1),(len(vs)-4,len(vs)-3,len(vs)-1,len(vs)-2)])
   lip=make('Pocket_turned_lip',vs,faces,'Kit_Shorts');weights_to(lip);made.append(lip)
 for i,material in enumerate(o.data.materials):
  if material is None:o.data.materials[i]=bpy.data.materials['Kit_Shorts']
 weights_to(o)
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
 for obj in made:obj.select_set(True)
 bpy.context.view_layer.objects.active=o;bpy.ops.object.join()
 return len(o.data.polygons)-start
