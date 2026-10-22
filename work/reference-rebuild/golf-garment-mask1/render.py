import bpy,sys,numpy as np
from mathutils import Vector
sys.path.insert(0,'work/reference-rebuild/golf-garment-panel1');from common import *
W=R/'work/reference-rebuild/golf-garment-mask1'
def material(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF'];b.inputs['Base Color'].default_value=(*c,1);b.inputs['Roughness'].default_value=.7;return m
def mesh(n,p,t,m,dx,dz):
 q=np.column_stack([p[:,0]+dx,-p[:,2],p[:,1]+dz]);me=bpy.data.meshes.new(n);me.from_pydata(q.tolist(),[],t.tolist());me.update();me.materials.append(m);ob=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(ob)
 for f in me.polygons:f.use_smooth=True
 return ob
choices=[('Driver','top'),('Putter','contact'),('PitchingWedge','contact'),('Driver','follow')]
for sex in ('male','female'):
 for view in ('front','back'):
  bpy.ops.wm.read_factory_settings(use_empty=True);sm=material('Same skin',(.53,.24,.115));cm=material('Same golf cloth',(.14,.42,.48));body,top,raw=source(sex.title());full=body;br=xf(np.array(body['rendererToRoot']).reshape(4,4),arr(full,'vertices',3));bt=arr(full,'triangles',3).astype(int);show=(br[:,1]>.865)&(br[:,1]<1.475);bt=bt[show[bt].all(1)]
  for row,(club,phase) in enumerate(choices):
   pose=json.loads((D/f'poses/{sex}_{club}_{phase}.json').read_text());target=np.array(pose['parts'][1]['skinMatrices']);candidates=list((D/'matrices').glob(f'{sex}_{club}_*.json'));p=min(candidates,key=lambda p:np.linalg.norm(np.array(json.loads(p.read_text())['parts'][1]['skinMatrices'])-target));q=dict(np.load(W/(p.stem+'.npz')));b,t,bottom=pose['parts'];q['body']=xf(np.array(b['rendererToRoot']).reshape(4,4),arr(b,'posedVertices',3)/UNITS);q['before']=q['after']=xf(np.array(t['rendererToRoot']).reshape(4,4),arr(t,'posedVertices',3)/UNITS);bp=xf(np.array(bottom['rendererToRoot']).reshape(4,4),arr(bottom,'posedVertices',3)/UNITS);bb=xf(np.array(bottom['rendererToRoot']).reshape(4,4),arr(bottom,'vertices',3));btri=arr(bottom,'triangles',3).astype(int);btri=btri[(bb[:,1]>.82)[btri].all(1)]
   for col,var in enumerate(('before','after')):
    # Show original production coverage. Filter full surface by explicit original body triangle positions.
    active=q['bodyTriangles'] if var=='before' else q['afterBodyTriangles'];lookup={tuple(np.round(v*1e6).astype(int)):i for i,v in enumerate(arr(full,'vertices',3))};cv=arr(body,'vertices',3);mapped=np.array([lookup.get(tuple(np.round(v*1e6).astype(int)),-1) for v in cv]);ats=mapped[active];ats=ats[(ats>=0).all(1)];ats=ats[show[ats].all(1)]
    mesh(f'{row}_{var}_UnchangedBody',q['body'],ats,sm,col*.72,-row*.80);mesh(f'{row}_{var}_UnchangedBottom',bp,btri,cm,col*.72,-row*.80);mesh(f'{row}_{var}_GolfTop',q[var],q['beforeTriangles'] if var=='before' else q['topTriangles'],cm,col*.72,-row*.80)
   print(sex,view,club,phase,'nearestSample',p.stem,flush=True)
  sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=1300;sc.render.resolution_y=2300;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('Studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.42,.43,.45,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.5;sc.view_settings.view_transform='AgX';target=Vector((.36,0,-.035));sign=-1 if view=='front' else 1
  for pos,power,size in [((-.8,sign*2,2.5),400,3),((2,-sign,1),150,3)]:
   bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
  bpy.ops.object.camera_add(location=(.36,sign*4.5,.05));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=3.62;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam;sc.render.filepath=str(W/f'{sex}_{view}_before-after-hem-safe.png');bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{sex}_{view}_SourceComparison.blend'))
