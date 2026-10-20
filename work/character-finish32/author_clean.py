import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-finish32'
bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Finish.blend'));o=bpy.data.objects['Kit_Top'];m=o.data;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
adj=[set() for _ in m.vertices]
for e in m.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();groups=[]
for i in range(len(adj)):
 if i in seen:continue
 q=[i];seen.add(i);ids=[]
 while q:
  j=q.pop();ids.append(j)
  for k in adj[j]:
   if k not in seen:seen.add(k);q.append(k)
 groups.append(ids)
groups.sort(key=len,reverse=True);main=set(groups[0]);collar=set(groups[1]);P=[v.co.copy() for v in m.vertices];tri=[list(f.vertices) for f in m.polygons if all(i in main for i in f.vertices)];bvh=BVHTree.FromPolygons(P,tri,all_triangles=True)
weights=[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in m.vertices]
def bind(q):
 hit,n,fi,dist=bvh.find_nearest(q);ids=tri[fi];bc=barycentric_transform(hit,*[P[j] for j in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));out={}
 for i,v in zip(ids,bc):
  for name,weight in weights[i].items():out[name]=out.get(name,0)+weight*max(0,v)
 out=sorted(out.items(),key=lambda x:-x[1])[:4];s=sum(v for _,v in out);return [(n,v/s) for n,v in out]
def front(x,z,lift=.0018):
 hit,n,_,_=bvh.ray_cast(Vector((x,-.6,z)),Vector((0,1,0)))
 if hit is None:raise RuntimeError('Placket support missing')
 return hit+Vector((0,-lift,0))
kill=[v.index for v in m.vertices if v.index not in main and v.index not in collar];bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in kill],context='VERTS');bm.to_mesh(m);bm.free()
# The source shirt already includes its sleeve turn and lining. Delete floating overlays.
parts=[]
def part(name,V,F,role,Ws=None):
 me=bpy.data.meshes.new(name);me.from_pydata(V,[],F);me.update();obj=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(obj);me.materials.append(bpy.data.materials[role])
 for group in o.vertex_groups:obj.vertex_groups.new(name=group.name)
 for i,v in enumerate(me.vertices):
  for n,vv in (Ws[i] if Ws is not None else bind(v.co)):obj.vertex_groups[n].add([i],vv,'REPLACE')
 uv=me.uv_layers.new(name='UVMap')
 for poly in me.polygons:
  poly.use_smooth=True
  for li in poly.loop_indices:
   p=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(p.x*3+.5,p.z*3)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();parts.append(obj)
V=[];F=[];nx=6;nz=12
for layer in range(2):
 for row in range(nz):
  z=1.302+.067*row/(nz-1)
  for col in range(nx):
   x=.027*(col/(nx-1)-.5);q=front(x,z,.0013 if layer else .0024);V.append(q)
for layer in range(2):
 off=layer*nx*nz
 for row in range(nz-1):
  for col in range(nx-1):
   a=off+row*nx+col;f=(a,a+1,a+1+nx,a+nx);F.append(f if layer else f[::-1])
for col in range(nx-1):
 a=col;b=(nz-1)*nx+col;off=nx*nz;F.extend([(a,a+off,a+off+1,a+1),(b,b+1,b+1+off,b+off)])
for row in range(nz-1):
 a=row*nx;b=a+nx-1;off=nx*nz;F.extend([(a,a+nx,a+nx+off,a+off),(b,b+off,b+nx+off,b+nx)])
part('PoloPlacket',V,F,'Kit_Shirt')
for idx,z in enumerate([1.350,1.321]):
 c=front(0,z,.0040);ws=bind(c);V=[];F=[];seg=16;rings=8
 for a in range(rings+1):
  theta=math.pi*a/rings
  for b in range(seg):
   phi=2*math.pi*b/seg;V.append(c+Vector((.0038*math.sin(theta)*math.cos(phi),-.0015*math.cos(theta),.0038*math.sin(theta)*math.sin(phi))))
 for a in range(rings):
  for b in range(seg):F.append((a*seg+b,a*seg+(b+1)%seg,(a+1)*seg+(b+1)%seg,(a+1)*seg+b))
 part('PoloButton'+str(idx),V,F,'Kit_Sock',[ws for _ in V])
bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
for ob in parts:ob.select_set(True)
bpy.context.view_layer.objects.active=o;bpy.ops.object.join();m=o.data
if m.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
for poly in m.polygons:poly.use_smooth=True
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_Clean.blend'))
bpy.ops.export_scene.fbx(filepath=str(r/'Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
(w/'clean-source.json').write_text(json.dumps({'vertices':len(m.vertices),'triangles':sum(len(f.vertices)-2 for f in m.polygons),'removedDetachedOverlayVertices':len(kill),'bodyChanged':False,'colorsBaked':False},indent=2))
