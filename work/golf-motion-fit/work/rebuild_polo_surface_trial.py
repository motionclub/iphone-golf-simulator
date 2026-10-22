"""Body-lineage golf knit shell, plus the approved separate collar/trim construction.
The base body is never changed. Boundary trims remain editable modular pieces.
"""
import bpy,bmesh,sys,json,math
import numpy as np
from mathutils import Vector,Matrix
sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_'+('F' if sex=='Female' else 'M')];old=bpy.data.objects['Golf_Polo']
old.name='Golf_PoloReference_High';old.hide_render=True;old.hide_set(True);old.data.shape_keys.animation_data_clear() if old.data.shape_keys else None
# Connected construction islands: retain collar, placket, cuffs, buttons, hems.
adj=[[] for v in old.data.vertices]
for edge in old.data.edges:
 a,b=edge.vertices;adj[a].append(b);adj[b].append(a)
seen=set();groups=[]
for start in range(len(adj)):
 if start in seen:continue
 stack=[start];ids=[];seen.add(start)
 while stack:
  i=stack.pop();ids.append(i)
  for j in adj[i]:
   if j not in seen:seen.add(j);stack.append(j)
 groups.append(ids)
main=max(groups,key=len);details=set(range(len(adj)))-set(main)
# Refit the copied cuff construction to this shell's short-sleeve boundary.
from mathutils.kdtree import KDTree
for ids in groups:
 if ids==main:continue
 center=sum((old.data.vertices[i].co for i in ids),Vector())/len(ids)
 armMass=sum(sum(g.weight for g in old.data.vertices[i].groups if any(n in old.vertex_groups[g.group].name for n in ['UpperArm','LowerArm','Shoulder'])) for i in ids)/len(ids)
 if abs(center.x)<.17 or armMass<.5 or not 1.0<center.z<1.35:continue
 side='Left' if center.x>0 else 'Right';a=rig.data.bones[side+'UpperArm'].head_local;b=rig.data.bones[side+'LowerArm'].head_local;axis=(b-a).normalized();length=(b-a).length
 target=a+(b-a)*.70;shift=axis*(target-center).dot(axis)
 eligible=[v for v in body.data.vertices if sum(g.weight for g in v.groups if body.vertex_groups[g.group].name in [side+'UpperArm',side+'LowerArm'])>.5 and abs((v.co-target).dot(axis))<.045]
 kd=KDTree(len(eligible))
 for j,v in enumerate(eligible):kd.insert(v.co,j)
 kd.balance()
 for i in ids:
  v=old.data.vertices[i];v.co+=shift
  _,near,_=kd.find(v.co);src=eligible[near];delta=v.co-src.co
  if delta.length<.03:v.co=src.co+src.normal*.010
  for vg in old.vertex_groups:vg.remove([i])
  allowed=[g for g in src.groups if body.vertex_groups[g.group].name in [side+'UpperArm',side+'LowerArm',side+'Shoulder','UpperChest']];total=sum(g.weight for g in allowed)
  for g in allowed:old.vertex_groups[body.vertex_groups[g.group].name].add([i],g.weight/total,'REPLACE')
 print('CUFF_REFIT',sex,side,len(ids),flush=True)

# Refit waist hems and side-seam construction to the new shell, using only
# torso-region body vertices. Old tennis trim coordinates do not follow this
# golf shell's tuck boundary and must not retain nearby arm influences.
torso=[v for v in body.data.vertices if .925<v.co.z<1.39 and abs(v.co.x)<.235 and sum(g.weight for g in v.groups if body.vertex_groups[g.group].name in ['Hips','Spine','Chest','UpperChest'])>.65]
torsoKD=KDTree(len(torso))
for j,v in enumerate(torso):torsoKD.insert(v.co,j)
torsoKD.balance()
for ids in groups:
 if ids==main:continue
 center=sum((old.data.vertices[i].co for i in ids),Vector())/len(ids)
 if min(old.data.vertices[i].co.z for i in ids)>.975+ .08 or abs(center.x)>.22:continue
 for i in ids:
  v=old.data.vertices[i]
  _,near,distance=torsoKD.find(v.co)
  src=torso[near];v.co=src.co+src.normal*(.004 if src.co.z<1.04 else .009)
  for vg in old.vertex_groups:vg.remove([i])
  allowed=[g for g in src.groups if body.vertex_groups[g.group].name in ['Hips','Spine','Chest','UpperChest','LeftUpperLeg','RightUpperLeg']];total=sum(g.weight for g in allowed)
  for g in allowed:old.vertex_groups[body.vertex_groups[g.group].name].add([i],g.weight/total,'REPLACE')
print('CONSTRUCTION_ISLANDS',[(len(g),min(old.data.vertices[i].co.z for i in g),max(old.data.vertices[i].co.z for i in g)) for g in groups],flush=True)
# Build in a temporary A-pose so an arm touching the waist at rest never
# becomes a fabric bridge from the sleeve to the torso.
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[sys.argv.index('--python')+1]).resolve().parent))
from polo_surface import build_surface
verts,faces,rows=build_surface(body,rig)
mesh=bpy.data.meshes.new('Golf_Polo_Lineage');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('Golf_Polo',mesh);bpy.context.scene.collection.objects.link(o)
for mat in old.data.materials:mesh.materials.append(mat)
for p in mesh.polygons:p.use_smooth=True
names={b.name for b in rig.data.bones};vgs={n:o.vertex_groups.new(name=n) for n in names}
for i,row in enumerate(rows):
 row=sorted([(n,w) for n,w in row.items() if n in names and w>1e-6],key=lambda a:a[1],reverse=True)[:4];total=sum(w for n,w in row)
 for n,w in row:vgs[n].add([i],w/total,'REPLACE')
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
dec=o.modifiers.new('Golf shell budget','DECIMATE');dec.ratio=min(1,5000/max(1,sum(len(p.vertices)-2 for p in o.data.polygons)));bpy.ops.object.modifier_apply(modifier=dec.name)
# Preserve real construction on the collar and trims by joining its separate islands.
if details:
 dd=sorted(details);dr={i:j for j,i in enumerate(dd)};dm=bpy.data.meshes.new('ApprovedPoloDetails');dm.from_pydata([old.data.vertices[i].co[:] for i in dd],[],[tuple(dr[i] for i in p.vertices) for p in old.data.polygons if all(i in details for i in p.vertices)]);dm.update();d=bpy.data.objects.new('Golf_PoloDetails',dm);bpy.context.scene.collection.objects.link(d)
 for mat in old.data.materials:dm.materials.append(mat)
 selected=[p for p in old.data.polygons if all(i in details for i in p.vertices)]
 for p,src in zip(dm.polygons,selected):p.material_index=src.material_index;p.use_smooth=src.use_smooth
 for vg in old.vertex_groups:d.vertex_groups.new(name=vg.name)
 for j,i in enumerate(dd):
  for g in old.data.vertices[i].groups:d.vertex_groups[g.group].add([j],g.weight,'REPLACE')
 d.select_set(True);bpy.ops.object.join()
# Close the garment's thickness; retain the source weights on both walls.
solid=o.modifiers.new('Closed knit edge','SOLIDIFY');solid.thickness=.0015;solid.offset=-1;bpy.ops.object.modifier_apply(modifier=solid.name)
o.parent=rig;o.matrix_world=Matrix.Identity(4);o.modifiers.new('CurrentHero','ARMATURE').object=rig
print('LINEAGE_POLO',sex,len(o.data.vertices),sum(len(p.vertices)-2 for p in o.data.polygons),flush=True)
