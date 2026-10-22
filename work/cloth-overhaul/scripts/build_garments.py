"""Low silhouette construction + high construction surface, existing rig/weights only."""
import bpy,bmesh,math,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path(sys.argv[sys.argv.index('--')+1]);W=R/'work/cloth-overhaul';E=W/'export';E.mkdir(exist_ok=True)
report=json.loads((W/'geometry_changes.json').read_text()) if (W/'geometry_changes.json').exists() else {}
def components(m):
 adj=[[] for v in m.vertices]
 for e in m.edges:
  a,b=e.vertices;adj[a].append(b);adj[b].append(a)
 seen=set();out=[]
 for i in range(len(adj)):
  if i in seen:continue
  q=[i];seen.add(i);ids=[]
  while q:
   v=q.pop();ids.append(v)
   for j in adj[v]:
    if j not in seen:seen.add(j);q.append(j)
  out.append(ids)
 return sorted(out,key=len,reverse=True)
def normal_smooth(m):
 m.update();N=np.array([v.normal[:] for v in m.vertices]);edge=np.array([e.vertices[:] for e in m.edges]);a,b=edge.T
 ok=(N[a]*N[b]).sum(1)>.65;a=a[ok];b=b[ok]
 for _ in range(3):
  acc=N.copy()*2;cnt=np.ones(len(N))*2
  np.add.at(acc,a,N[b]);np.add.at(acc,b,N[a]);np.add.at(cnt,a,1);np.add.at(cnt,b,1)
  N=acc/cnt[:,None];N/=np.maximum(np.linalg.norm(N,axis=1)[:,None],1e-8)
 for p in m.polygons:p.use_smooth=True
 m.normals_split_custom_set_from_vertices(N.tolist())
def curve_mesh(name,pts,radius,mat):
 bpy.ops.object.select_all(action='DESELECT')
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=radius;cu.bevel_resolution=0;cu.resolution_u=1
 sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for v,p in zip(sp.points,pts):v.co=(*p,1)
 o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.data.materials.append(mat)
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o=bpy.context.object
 return o
for sex in (sys.argv[sys.argv.index('--')+2:] or ['Male','Female']):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(W/f'rollback/Unity/Assets/Characters/MatchHeroKit/{sex}_Kit.fbx'))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');kit=[o for o in bpy.data.objects if o.type=='MESH'];rows=[]
 for o in kit:
  m=o.data;cs=components(m);before=sum(len(p.vertices)-2 for p in m.polygons)
  # Remove the redundant wrap flap and its narrow seam overlay. The retained A-line skirt is closed.
  removed=0
  if sex=='Female' and o.name=='Kit_Bottom':
   kill=[]
   for ids in cs:
    P=np.array([m.vertices[i].co[:] for i in ids]);
    if 1700<len(ids)<2100 or (120<len(ids)<180 and P[:,2].min()<.65 and P[:,2].max()>.95):kill.extend(ids)
   bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in kill],context='VERTS');bm.to_mesh(m);bm.free();removed=len(kill);cs=components(m)
  if o.name=='Kit_Top':
   # Roll the existing real collar without moving its tips or changing body vertices.
   ids=cs[1];z0=min(m.vertices[i].co.z for i in ids);z1=max(m.vertices[i].co.z for i in ids)
   for i in ids:
    v=m.vertices[i];t=(v.co.z-z0)/(z1-z0);rad=Vector((v.co.x,v.co.y,0));
    if rad.length: v.co += rad.normalized() * (.0045*math.sin(math.pi*t)**2)
  if sex=='Female' and o.name=='Kit_Bottom':
   ids=[i for group in cs if min(m.vertices[j].co.z for j in group)<.70 for i in group]
   for i in ids:
    v=m.vertices[i];theta=math.atan2(v.co.y,v.co.x);phase=(theta/(2*math.pi)*12)%1
    knife=phase/.72 if phase<.72 else (1-phase)/.28
    taper=max(0,min(1,(.945-v.co.z)/.24));r=Vector((v.co.x,v.co.y,0))
    if r.length:v.co += r.normalized()*(.018*taper*knife)
    v.co.z -= .0022*taper*math.sin(theta*12)**2
  if o.name in ['Kit_Top','Kit_Bottom']:
   ids=cs[0];Nbefore=[v.normal.copy() for v in m.vertices]
   for i in ids:
    v=m.vertices[i];x,y,z=v.co;front=max(0,min(1,-y/.06));n=Nbefore[i]
    if o.name=='Kit_Top':
     waist=math.exp(-((z-(1.018 if sex=='Male' else 1.035)-.10*abs(x))/.026)**2)
     armpit=math.exp(-((abs(x)-(.19 if sex=='Male' else .125))/.065)**2-((z-(1.20 if sex=='Male' else 1.16))/.08)**2)
     d=.0018*front*(waist*math.sin(x*85)+armpit*math.sin(z*105+x*20))
    elif sex=='Male': d=.0018*front*math.exp(-((z-.84)/.08)**2)*math.sin(50*x+80*z)
    else:d=0
    v.co+=n*d
  if sex=='Male' and o.name=='Kit_Bottom':
   # Small real drawcord. New vertices copy normalized existing waistband weights by nearest vertex.
   originals=[v.co.copy() for v in m.vertices];weights=[[ (o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in m.vertices]
   kd=KDTree(len(originals))
   for i,p in enumerate(originals):kd.insert(p,i)
   kd.balance();new=[]
   for side in [-1,1]:
    pts=[]
    for i in range(18):
     t=i/17;pts.append((side*(.009+.010*t+.004*math.sin(math.pi*t)), -.195-.003*math.sin(math.pi*t), .940-.047*t))
    c=curve_mesh('Drawcord',pts,.0016,bpy.data.materials.get('Kit_Shorts'));c.matrix_world=o.matrix_world.copy()
    for v in c.data.vertices:
     _,idx,_=kd.find(v.co)
     for name,w in weights[idx]:
      vg=c.vertex_groups.get(name) or c.vertex_groups.new(name=name);vg.add([v.index],w,'REPLACE')
    new.append(c)
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
   for c in new:c.select_set(True)
   bpy.context.view_layer.objects.active=o;bpy.ops.object.join();m=o.data
  if sex=='Male' and o.name=='Kit_Top':
   # A real small side hem vent through both walls, above the overlapping shorts waist.
   bm=bmesh.new();bm.from_mesh(m)
   cuts=[f for f in bm.faces if abs(f.calc_center_median().x)>.16 and abs(f.calc_center_median().y+.045)<.0035 and f.calc_center_median().z<.965]
   bmesh.ops.delete(bm,geom=cuts,context='FACES');bm.to_mesh(m);bm.free()
  if sex=='Male' and o.name=='Kit_Bottom':
   sys.path.insert(0,str(W/'scripts'));from pocket_construction import construct_pockets
   construct_pockets(o);m=o.data
  normal_smooth(m)
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=.4,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
  m.calc_loop_triangles();P=np.array([v.co[:] for v in m.vertices]);lv=np.array([l.vertex_index for l in m.loops]);CN=np.array([n.vector[:] for n in m.corner_normals]);UV=np.array([u.uv[:] for u in m.uv_layers[0].data]);tri=np.array([t.vertices[:] for t in m.loop_triangles]);tl=np.array([t.loops[:] for t in m.loop_triangles]);mi=np.array([t.material_index for t in m.loop_triangles])
  np.savez(E/f'{sex}_{o.name}.npz',P=P,normal=CN,uv=UV,tri=tri,triloops=tl,material=mi,materials=np.array([s.name for s in m.materials]))
  rows.append({'piece':o.name,'beforeTris':before,'afterTris':len(tri),'removedWrapVerts':removed,'vertices':len(P)})
 # Actual high meshes stored separately, never exported to Unity and never bound to new bones.
 highcol=bpy.data.collections.new('Construction_High_BakeOnly');bpy.context.scene.collection.children.link(highcol)
 for o in kit:
  h=o.copy();h.data=o.data.copy();h.name=o.name+'_High';highcol.objects.link(h)
  for mod in list(h.modifiers):h.modifiers.remove(mod)
  sub=h.modifiers.new('High construction subdivision','SUBSURF');sub.subdivision_type='SIMPLE';sub.levels=1
  bpy.context.view_layer.objects.active=h;bpy.ops.object.modifier_apply(modifier=sub.name)
  # Fine high construction displacement; the analytic baker samples this same field.
  sys.path.insert(0,str(W/'scripts'))
  from surface_field import field
  P=np.array([v.co[:] for v in h.data.vertices]);heights=field(P,o.name,sex)[0]
  N=np.array([v.normal[:] for v in h.data.vertices]);h.data.vertices.foreach_set('co',(P+N*heights[:,None]).ravel())
  h.hide_render=True;h.hide_set(True)
 bpy.ops.wm.save_as_mainfile(filepath=str(E/f'Cloth_{sex}.blend'))
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
 for o in kit:o.select_set(True)
 bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(E/f'{sex}_Kit.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
 report[sex]=rows;print('BUILT',sex,flush=True)
(W/'geometry_changes.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
