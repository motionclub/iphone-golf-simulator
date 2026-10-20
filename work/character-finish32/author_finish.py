import bpy,bmesh,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-finish32'
bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Envelope.blend'));o=bpy.data.objects['Kit_Top'];m=o.data;rig=next(x for x in bpy.data.objects if x.type=='ARMATURE')
bm=bmesh.new();bm.from_mesh(m);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.to_mesh(m);bm.free();m.update()
# Connected construction islands remain independent; the body is untouched.
adj=[set() for _ in m.vertices]
for e in m.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();groups=[]
for i in range(len(adj)):
 if i in seen:continue
 q=[i];seen.add(i);ids=[]
 while q:
  j=q.pop();ids.append(j)
  for k in adj[j]:
   if k not in seen:seen.add(k);q.append(k)
 groups.append(ids)
groups.sort(key=len,reverse=True);main=set(groups[0]);collar=groups[1]
old=np.array([tuple(v.co) for v in m.vertices]);p=old.copy();edge=np.array([(a,b) for a in main for b in adj[a] if b in main]);a,b=edge.T;count=np.bincount(a,minlength=len(p));mov=np.zeros(len(p));
# Broad cloth drape: relax the torso surface, retain neckline, cuffs and hem.
for i in main:
 x,y,z=p[i];mov[i]=min(1,max(0,(z-.978)/.05))*min(1,max(0,(1.37-z)/.07))*min(1,max(0,(.265-abs(x))/.055))
for _ in range(36):
 acc=np.zeros_like(p);np.add.at(acc,a,p[b]);avg=acc/np.maximum(1,count[:,None]);p+=(avg-p)*mov[:,None]*.38
# One rest-body constraint after smoothing prevents new intersections.
data=json.loads((w/'baseline/poses/male_intro.json').read_text());body=data['parts'][0];bp=np.array(body['vertices']).reshape(-1,3);bp[:,0]*=-1;bn=np.array(body['normals']).reshape(-1,3);bn[:,0]*=-1;bt=np.array(body['triangles']).reshape(-1,3)[:,::-1];bb=BVHTree.FromPolygons([Vector(v) for v in bp],bt.tolist(),all_triangles=True)
for i in main:
 if mov[i]<=0:continue
 hit,n,fi,dist=bb.find_nearest(Vector(p[i]));ids=bt[fi];bc=barycentric_transform(hit,*[Vector(bp[j]) for j in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));n=Vector(sum(bn[j]*v for j,v in zip(ids,bc))).normalized();signed=(Vector(p[i])-hit).dot(n)
 if signed<.010:p[i]=hit+n*.010
# Ease the button opening into a shallow V instead of a square neck slot.
for i in main:
 x,y,z=p[i]
 if y<-.072 and z>1.334 and abs(x)<.053:p[i,2]-=.026*(1-abs(x)/.053)**2*min(1,(z-1.334)/.04)
# Lower the old neckline turn beneath the new folded stand.
for i in main:
 x,y,z=p[i];radius=((x/.082)**2+((y+.020)/.082)**2)**.5
 if radius<1.23 and z>1.38:p[i,2]-=.010*min(1,(z-1.38)/.025)*min(1,(1.23-radius)/.15)
# Float existing seams and placket on the relaxed shell.
mainfaces=[list(f.vertices) for f in m.polygons if all(i in main for i in f.vertices)]
bvh=BVHTree.FromPolygons([Vector(v) for v in p],mainfaces,all_triangles=True)
for ids in groups[2:]:
 center=old[ids].mean(0);isplacket=(np.max(abs(old[ids,0]))<.021 and center[2]>1.30)
 for i in ids:
  q=Vector(old[i]);
  if isplacket:q.z-=.026*min(1,max(0,(q.z-1.31)/.083))
  hit,n,fi,dist=bvh.find_nearest(q)
  if dist<.018:p[i]=hit+n*max(.0015,(q-hit).dot(n))
for i,v in enumerate(m.vertices):v.co=p[i]
# Save a surface correspondence for the new collar and its fixed skin weights.
weights=[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in m.vertices]
def bind(q):
 hit,n,fi,dist=bvh.find_nearest(q);ids=mainfaces[fi];bc=barycentric_transform(hit,*[Vector(p[j]) for j in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));out={}
 for i,v in zip(ids,bc):
  for name,weight in weights[i].items():out[name]=out.get(name,0)+weight*max(0,v)
 out=sorted(out.items(),key=lambda x:-x[1])[:4];s=sum(v for _,v in out);return [(n,v/s) for n,v in out]
# Rebind the surviving detached hems to their own supporting cloth surface.
for ids in groups[2:]:
 for i in ids:
  ws=bind(m.vertices[i].co)
  for g in list(m.vertices[i].groups):o.vertex_groups[g.group].remove([i])
  for name,value in ws:o.vertex_groups[name].add([i],value,'REPLACE')
# Neutral buttons are independent of the user's shirt tint.
buttonMaterial=bpy.data.materials.get('Kit_Sock') or bpy.data.materials.new('Kit_Sock');buttonMaterial.diffuse_color=(.85,.83,.77,1);m.materials.append(buttonMaterial)
buttons=set(i for ids in groups[2:] if len(ids)==50 for i in ids)
for poly in m.polygons:
 if all(i in buttons for i in poly.vertices):poly.material_index=2
# Retire tiny overlapping ribbon overlays; retain actual cuff and hem construction.
kill=set(collar)
for ids in groups[2:]:
 if len(ids) in (51,54,78,165):kill.update(ids)
# Replace only the original collar island with a genuinely folded polo collar.
bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in kill],context='VERTS');bm.to_mesh(m);bm.free();m.update()
V=[];UV=[];F=[];W=[];N=80;cross=11
for k in range(N):
 angle=.24+(2*math.pi-.48)*k/(N-1);front=max(0,math.cos(angle));side=1 if math.sin(angle)>=0 else -1;af=min(angle,2*math.pi-angle)
 inner=Vector((.082*math.sin(angle),-.020-.082*math.cos(angle),1.425-.021*math.cos(angle)-.021*math.exp(-(af/.48)**2)))
 outer=Vector((.117*math.sin(angle+side*.46*math.exp(-(af/.9)**2)),-.020-.113*math.cos(angle),1.413-.068*front**2))
 # The leaf lies over the chest/back, with its front point clearly outside the placket.
 origin=Vector((outer.x,-.45 if front>0 else .35,outer.z));direction=Vector((0,1 if front>0 else -1,0));hit,n,_,_=bvh.ray_cast(origin,direction)
 if hit is not None:outer.y=hit.y+(-.006 if front>0 else .006)
 rad=Vector((math.sin(angle),-math.cos(angle),0))
 profile=[inner-rad*.002-Vector((0,0,.008)),inner-rad*.003+Vector((0,0,.006)),inner+rad*.002+Vector((0,0,.010))]
 for t in [.12,.32,.58,.80,1.0]:
  q=inner.lerp(outer,t)+Vector((0,0,.009*math.sin(math.pi*t)))
  loc,n,_,dist=bvh.find_nearest(q)
  if t>.2 and dist<.035 and (q-loc).dot(n)<.005:q=loc+n*.005
  profile.append(q)
 profile.extend([outer-Vector((0,-.002 if front>0 else .002,0)),inner.lerp(outer,.60),inner-rad*.002])
 for j,q in enumerate(profile):V.append(q);UV.append((k/(N-1),j/(cross-1)));W.append(bind(q))
for k in range(N-1):
 for j in range(cross):
  a=k*cross+j;b=(k+1)*cross+j;c=(k+1)*cross+(j+1)%cross;d=k*cross+(j+1)%cross;F.append((a,b,c,d))
F.append(tuple(reversed(range(cross))));F.append(tuple((N-1)*cross+j for j in range(cross)))
cm=bpy.data.meshes.new('PoloFold');cm.from_pydata(V,[],F);cm.update();co=bpy.data.objects.new('PoloFold',cm);bpy.context.collection.objects.link(co);cm.materials.append(bpy.data.materials['Kit_Shirt'])
for name in body['bones']:co.vertex_groups.new(name=name)
for i,ws in enumerate(W):
 for n,v in ws:co.vertex_groups[n].add([i],v,'REPLACE')
u=cm.uv_layers.new(name='UVMap')
for poly in cm.polygons:
 for li in poly.loop_indices:u.data[li].uv=UV[cm.loops[li].vertex_index]
bm=bmesh.new();bm.from_mesh(cm);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cm);bm.free()
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);co.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.join();m=o.data
if m.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
for poly in m.polygons:poly.use_smooth=True
# Moderate normal relaxation preserves the fold and sleeve edge while smoothing cloth creases.
bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free();m.update()
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_Finish.blend'))
bpy.ops.export_scene.fbx(filepath=str(r/'Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
(w/'finish-source.json').write_text(json.dumps({'vertices':len(m.vertices),'triangles':sum(len(f.vertices)-2 for f in m.polygons),'newCollarVertices':len(V),'torsoMaxChange':float(np.max(np.linalg.norm(p-old,axis=1)))},indent=2))
