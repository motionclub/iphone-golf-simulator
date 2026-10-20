import bpy,math,numpy as np,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,'Tools/HeroBase');from plate_profiles import MALE,FEMALE
D=Path('ArtDir/hero/base_lock').resolve();O=Path('work/hero-base/face-relief-trials').resolve()
for sex,suf,p in [('Male','M',MALE),('Female','F',FEMALE)]:
 for amp in [0,.7,1.4]:
  bpy.ops.wm.open_mainfile(filepath=str(D/'blender'/('HeroBase_'+sex+'.blend')));ob=bpy.data.objects['Body_'+suf];me=ob.data;sp=1.7/p['height'];guide=np.load(O/(suf+'_relief.npy'));me.calc_loop_triangles()
  old=np.zeros((len(me.vertices),3));hits=np.zeros(len(me.vertices))
  for loop,n in zip(me.loops,me.corner_normals):old[loop.vertex_index]+=np.array(n.vector);hits[loop.vertex_index]+=1
  old/=np.maximum(hits[:,None],1);change=[]
  for vert in me.vertices:
   x=vert.co.x/sp;y=p['sole']-vert.co.z/sp;z=vert.co.y/sp
   if z>=0 or y<=p['eye_y']-15 or y>=max(r[0] for r in p['head']):continue
   ix=x+65;iy=y
   if not 0<=ix<guide.shape[1]-1 or not 0<=iy<guide.shape[0]-1:continue
   a,b=int(ix),int(iy);fx,fy=ix-a,iy-b
   d=guide[b,a]*(1-fx)*(1-fy)+guide[b,a+1]*fx*(1-fy)+guide[b+1,a]*(1-fx)*fy+guide[b+1,a+1]*fx*fy
   if abs(d)>1e-5:vert.co.y-=amp*d*sp;change.append(vert.index)
  me.update()
  # Retain the analytic body normals while updating the changed face surfaces.
  auto=[tuple(v.normal) for v in me.vertices]
  normal=[tuple(v) for v in old]
  for ix in change:normal[ix]=auto[ix]
  me.normals_split_custom_set_from_vertices(normal)
  # Repair the known collar UV discontinuity in these trial renders.
  for poly in me.polygons:
   if poly.material_index!=1:continue
   for ix in poly.loop_indices:
    v=me.vertices[me.loops[ix].vertex_index].co;y=p['sole']-v.z/sp
    me.uv_layers.active.data[ix].uv=(.02,.02) if sex=='Female' and y>=620 else ((math.atan2(v.x,-v.y)/math.tau+.5),(182-y)/158)
  scene=bpy.context.scene;scene.cycles.samples=24
  for view,angle in [('front',0),('threequarter',math.pi/5)]:
   cam=scene.camera;cam.location=(math.sin(angle)*5,-math.cos(angle)*5,(p['sole']-360)*sp);cam.rotation_euler=(Vector((0,0,cam.location.z))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(O/(suf+'_'+str(amp)+'_'+view+'.png'));bpy.ops.render.render(write_still=True)
  print('FACE_RELIEF_TRIAL',sex,amp,len(change))
