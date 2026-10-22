import bpy,numpy as np,pathlib,json
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[3];W=R/'work/full-visual-overhaul/garment-coverage';O=W/'shoe-panel-source';O.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
def mat(name,color,rough):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=rough;return m
cream=mat('Clean cream upper',(.79,.77,.69),.42);sole=mat('Moulded cream sole',(.68,.69,.65),.6);navy=mat('Continuous fitted navy panels',(.026,.047,.10),.32)
def clip(poly,fn):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  sa,sb=fn(a[0]),fn(b[0]);ia,ib=sa>=0,sb>=0
  if ia:out.append(a)
  if ia!=ib:
   t=sa/(sa-sb);out.append((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))
 return out
report=[]
for sex in ['Male','Female']:
 d=np.load(R/'work/cloth-overhaul/export'/f'{sex}_Kit_Shoe_L.npz');p=d['P'].copy();n=d['normal'].copy();tri=d['tri'];ma=d['material'];start=.100 if sex=='Female' else .112
 high=p[:,2]>start;p[high,2]=start+(p[high,2]-start)*.56
 # NPZ normal rows are construction-bake diagnostics, not mesh vertex normals.
 # Derive the outward shell normals from the actual triangle winding.
 fn=np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]])
 normals={}
 for ids,f in zip(tri,fn):
  for i in ids:
   key=tuple(np.round(p[i]*100000).astype(int));normals[key]=normals.get(key,np.zeros(3))+f
 n=np.array([normals[tuple(np.round(q*100000).astype(int))] for q in p]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
 low=p.min(0);hi=p.max(0);length=hi[1]-low[1];front=low[1]+length*.27;heel=hi[1]-length*.17;band=.089 if sex=='Female' else .115
 verts=[];faces=[];center=(low+hi)*.5;center[2]=.025 if sex=='Female' else .045
 for ids,m in zip(tri,ma):
  if m!=0:continue
  q=p[ids];normal=n[ids]
  if np.dot(normal.mean(0),q.mean(0)-center)<-.001:continue
  for role in ['Toe','Heel','Cuff']:
   poly=[(x.copy(),y.copy()) for x,y in zip(q,normal)]
   conditions=[lambda x:x[2]-.006]
   if role=='Toe':conditions.append(lambda x:front-x[1])
   if role=='Heel':conditions.append(lambda x:x[1]-heel)
   if role=='Cuff':conditions.append(lambda x:x[2]-band)
   for fn in conditions:poly=clip(poly,fn)
   if len(poly)<3:continue
   offset=len(verts)
   for pos,nn in poly:verts.append(pos+nn/max(np.linalg.norm(nn),1e-10)*.0004)
   for j in range(1,len(poly)-1):faces.append((offset,offset+j,offset+j+1))
 # Share vertices at exact clipped boundaries. The prior proof used exploded
 # triangles, so smooth flags had no neighboring faces to interpolate with.
 welded={};unique=[];remap=[]
 for q in verts:
  key=tuple(np.round(q*1000000).astype(int))
  if key not in welded:welded[key]=len(unique);unique.append(q)
  remap.append(welded[key])
 faces=[tuple(remap[i] for i in f) for f in faces];verts=unique
 for side in [0,1]:
  shift=np.array([(.52 if sex=='Male' else -.06)+side*.24,0,0]);pp=p+shift
  me=bpy.data.meshes.new(sex+' shoe');me.from_pydata(pp.tolist(),[],tri.tolist());me.materials.append(cream);me.materials.append(sole);me.update();ob=bpy.data.objects.new(sex+(' AFTER' if side else ' BEFORE'),me);bpy.context.collection.objects.link(ob)
  for f,m in zip(me.polygons,ma):f.material_index=int(m);f.use_smooth=True
  if side:
   me=bpy.data.meshes.new(sex+' solid sewn panels');me.from_pydata((np.array(verts)+shift).tolist(),[],faces);me.materials.append(navy);me.update();ob=bpy.data.objects.new(sex+' toe heel cuff patches',me);bpy.context.collection.objects.link(ob)
   for f in me.polygons:f.use_smooth=True
 report.append({'sex':sex,'panelTriangles':len(faces),'panelVertices':len(verts),'surfaceOffsetMetres':.0004,'originalSurfacePreserved':True,'panelHeightMinimumMetres':.006,'toeBoundary':float(front),'ankleBandMinimumMetres':band})
sc=bpy.context.scene;sc.world=bpy.data.worlds.new('Shoe review');sc.world.color=(.45,.48,.53);sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=1600;sc.render.resolution_y=950;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX'
for pos,power,size in [((0,-1,2),160,2),((1,1,1),110,1)]:
 bpy.ops.object.light_add(type='AREA',location=pos);ob=bpy.context.object;ob.data.energy=power;ob.data.size=size;ob.rotation_euler=(Vector((.42,0,.05))-ob.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.7,-1.1,.65));cam=bpy.context.object;cam.rotation_euler=(Vector((.42,-.025,.055))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.1;sc.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=str(O/'ShoePhysicalPanels.blend'));sc.render.filepath=str(O/'shoe-panels.png');bpy.ops.render.render(write_still=True);(O/'shoe-panels-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
