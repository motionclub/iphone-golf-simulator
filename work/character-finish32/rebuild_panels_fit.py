import bpy,bmesh,math,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-finish32'
bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Clean.blend'));old=bpy.data.objects['Kit_Top'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
# Retain the authored folded collar, placket and two buttons; replace only main cloth.
adj=[set() for _ in old.data.vertices]
for e in old.data.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();components=[]
for i in range(len(adj)):
 if i in seen:continue
 stack=[i];seen.add(i);ids=[]
 while stack:
  j=stack.pop();ids.append(j)
  for k in adj[j]:
   if k not in seen:seen.add(k);stack.append(k)
 components.append(ids)
main=set(max(components,key=len));bm=bmesh.new();bm.from_mesh(old.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in main],context='VERTS');bm.to_mesh(old.data);bm.free()
body=json.loads((w/'baseline/poses/male_intro.json').read_text())['parts'][0];BP=[Vector((-body['vertices'][i],body['vertices'][i+1],body['vertices'][i+2])) for i in range(0,len(body['vertices']),3)];BT=[body['triangles'][i:i+3][::-1] for i in range(0,len(body['triangles']),3)];tree=BVHTree.FromPolygons(BP,BT,all_triangles=True)
P=[];UV=[];F=[];W=[]
def weights(p):
 x,y,z=p;spine=min(.65,max(0,(1.20-z)/.28));shoulder=min(.45,max(0,(abs(x)-.105)/.11))*min(1,max(0,(z-1.24)/.1));side='Left' if x>0 else 'Right';return {'Chest':1-spine-shoulder,'Spine':spine,side+'Shoulder':shoulder}
def add(p,uv,weight=None):
 P.append(Vector(p));UV.append(uv);W.append(weights(p) if weight is None else weight);return len(P)-1
n=64;rows=25;z0=.947;z1=1.393;rings=[]
# Smooth elliptical cloth envelope, measured against the unchanged body.
raw=np.zeros((rows+1,n))
for k in range(rows+1):
 z=z0+(z1-z0)*k/rows;center=Vector((0,-.035,z))
 for j in range(n):
  t=2*math.pi*j/n;direction=Vector((math.cos(t),math.sin(t),0));hit,normal,fi,dist=tree.ray_cast(center,direction,.40)
  # Side rays above the underarm can hit the arm: use the torso pattern there.
  radius=dist if hit is not None else .17
  if abs(math.cos(t))>.65:radius=min(radius,.203/max(.4,abs(math.cos(t))))
  raw[k,j]=radius+.016
for it in range(24):
 nxt=raw.copy()
 for k in range(1,rows):
  for j in range(n):nxt[k,j]=raw[k,j]*.6+.1*(raw[k-1,j]+raw[k+1,j]+raw[k,(j-1)%n]+raw[k,(j+1)%n])
 raw=nxt
for k in range(rows+1):
 row=[];z=z0+(z1-z0)*k/rows
 for j in range(n):
  t=2*math.pi*j/n;rad=raw[k,j];fold=.0025*math.sin(t*5+k*.6)*max(0,1-k/12)
  zz=z+.004*math.cos(t*3)*max(0,1-k/4);row.append(add(((rad+fold)*math.cos(t),-.035+(rad+fold)*math.sin(t),zz),(j/n,k/rows*.75)))
 rings.append(row)
# Side openings are actual holes in the torso panel, with a shared sewn perimeter.
cutrow=14;cut=6
for k in range(rows):
 for j in range(n):
  mid=(j+.5)%n;side=min(mid,n-mid)<cut or abs(mid-n/2)<cut
  if k>=cutrow and side:continue
  F.append((rings[k][j],rings[k][(j+1)%n],rings[k+1][(j+1)%n],rings[k+1][j]))
# Shoulder yoke leads into the existing collar; front has a shallow opening.
prev=rings[-1]
for k in range(1,7):
 u=k/6;row=[]
 for j in range(n):
  t=2*math.pi*j/n;front=max(0,-math.sin(t));neck=Vector((.088*math.cos(t),-.011+.084*math.sin(t),1.406-.044*front**5));p=P[rings[-1][j]].lerp(neck,u);p.z+=.011*math.sin(math.pi*u)*abs(math.cos(t));row.append(add(p,(j/n,.75+.12*u)))
 for j in range(n):F.append((prev[j],prev[(j+1)%n],row[(j+1)%n],row[j]))
 prev=row
# Close each cuff with a real turned edge and a short inner lining.
for side,centerIndex in [('Left',0),('Right',32)]:
 js=[(centerIndex-cut+j)%n for j in range(cut*2+1)];lo,hi=js[0],js[-1]
 boundary=[rings[cutrow][j] for j in js]
 boundary += [rings[k][hi] for k in range(cutrow+1,rows+1)]
 boundary += [rings[rows][j] for j in js[-2::-1]]
 boundary += [rings[k][lo] for k in range(rows-1,cutrow,-1)]
 # Their loop order runs outward on both sides; derive circle coordinates from its actual geometry.
 a=rig.matrix_world@rig.data.bones[side+'UpperArm'].head_local;b=rig.matrix_world@rig.data.bones[side+'LowerArm'].head_local;axis=(b-a).normalized();front=Vector((0,-1,0));front=(front-axis*front.dot(axis)).normalized();up=axis.cross(front).normalized();center=a+axis*.175
 angle=[]
 for v in boundary:
  q=P[v]-a;angle.append(math.atan2(q.dot(up)/.086,q.dot(front)/.080))
 angle=np.unwrap(np.array(angle));direction=1 if angle[-1]>angle[0] else -1
 # Equal arc distribution avoids bunching in the original armpit crease.
 start=angle[0];angles=list(angle)
 prev=boundary
 for k in range(1,11):
  u=min(1,k/8);inner=k>8;row=[]
  for j,v in enumerate(boundary):
   ang=angles[j];radiusY=.083-(.003 if inner else 0);radiusZ=.087-(.003 if inner else 0);end=center+front*(math.cos(ang)*radiusY)+up*(math.sin(ang)*radiusZ)
   if inner:end-=axis*((k-8)*.004)
   p=P[v].lerp(end,u);bulge=math.sin(math.pi*u)*.009;p+=(front*math.cos(ang)+up*math.sin(ang))*bulge
   t=u*u*(3-2*u);bw={name:value*(1-t) for name,value in W[v].items()};bw[side+'UpperArm']=bw.get(side+'UpperArm',0)+t
   row.append(add(p,(j/len(boundary),.05+.5*k/10),bw))
  for j in range(len(boundary)):F.append((prev[j],prev[(j+1)%len(prev)],row[(j+1)%len(row)],row[j]))
  prev=row
# A small turned hem gives an actual edge instead of a loose overlay strip.
prev=rings[0]
for k in range(1,3):
 row=[]
 for j,v in enumerate(rings[0]):
  p=P[v].copy();p.x*=.985;p.y=-.035+(p.y+.035)*.985;p.z+=.004*k;row.append(add(p,(j/n,.01*k),W[v]))
 for j in range(n):F.append((prev[(j+1)%n],prev[j],row[j],row[(j+1)%n]))
 prev=row
for i,p in enumerate(P):
 hit,normal,fi,dist=tree.find_nearest(p);signed=(p-hit).dot(normal)
 if signed<.012:P[i]=hit+normal*.012
mesh=bpy.data.meshes.new('TailoredPanels');mesh.from_pydata(P,[],F);mesh.update();uv=mesh.uv_layers.new(name='UVMap')
for poly in mesh.polygons:
 for li in poly.loop_indices:uv.data[li].uv=UV[mesh.loops[li].vertex_index]
 poly.use_smooth=True
panel=bpy.data.objects.new('PoloPanels',mesh);bpy.context.collection.objects.link(panel);panel.matrix_world=old.matrix_world.copy()
for material in old.data.materials:mesh.materials.append(material)
for g in old.vertex_groups:panel.vertex_groups.new(name=g.name)
for i,ww in enumerate(W):
 items=sorted(ww.items(),key=lambda p:-p[1])[:4];total=sum(v for _,v in items)
 for name,value in items:
  if value>0:panel.vertex_groups[name].add([i],value/total,'REPLACE')
# Coherent quad construction, oriented as one surface.
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
bpy.ops.object.select_all(action='DESELECT');old.select_set(True);panel.select_set(True);bpy.context.view_layer.objects.active=old;bpy.ops.object.join()
for f in old.data.polygons:f.use_smooth=True
if old.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.object.select_all(action='DESELECT');old.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=old
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_PanelsFit.blend'))
bpy.ops.export_scene.fbx(filepath=str(w/'review-project/Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
print('PANELS',len(old.data.vertices),len(old.data.polygons),flush=True)
