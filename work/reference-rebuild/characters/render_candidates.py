import bpy,pathlib,json,math
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/characters';V=R/'work/reference-rebuild/vendor/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
def mat(name,color,rough=.5):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=rough;n.inputs['Specular IOR Level'].default_value=.30;return m
cases=[('male_animation','GEO-head_animation_realistic',(.44,.24,.12)),('female_head_stylized','GEO-head_stylized',(.62,.36,.21)),('female_body_stylized','GEO-body_female_stylized',(.62,.36,.21))];out=[]
for label,name,skincolor in cases:
 bpy.ops.wm.open_mainfile(filepath=str(V));head=bpy.data.objects[name];parts=[o for o in bpy.data.objects if o.type=='MESH' and (o==head or o.name.startswith(name+'.'))];dg=bpy.context.evaluated_depsgraph_get();eyeParts=[o for o in parts if 'eye.' in o.name or 'sclera.' in o.name];eye=sum((o.matrix_world.translation for o in eyeParts),Vector())/len(eyeParts)
 copies=[]
 for o in parts:
  ev=o.evaluated_get(dg);me=bpy.data.meshes.new_from_object(ev);me.transform(o.matrix_world);me.transform(Matrix.Translation(-eye));me.update();ob=bpy.data.objects.new(o.name+'_Candidate',me);copies.append(ob)
 for o in list(bpy.data.objects):
  if o not in copies:bpy.data.objects.remove(o,do_unlink=True)
 sc=bpy.context.scene;sc.use_nodes=False;sc.render.film_transparent=False
 for ob in copies:sc.collection.objects.link(ob)
 skin=mat('WarmSkin',skincolor,.52);white=mat('IvorySclera',(.82,.84,.78),.27);brown=mat('BrownIris',(.135,.053,.018),.29);black=mat('DeepPupil',(.004,.003,.002),.15);lip=mat('NaturalLip',(.45,.15,.105) if 'male' in label else (.55,.23,.17),.46);brow=mat('DarkBrownBrow',(.035,.018,.008),.7)
 for ob in copies:
  ob.data.materials.clear()
  for p in ob.data.polygons:p.use_smooth=True
  if ob.name.startswith(name+'_'):
   ob.data.materials.append(skin);ob.data.materials.append(lip)
   # Leave face sculpture unchanged. Very restrained mouth tint follows only actual lip bulge.
   # No flat face features are added in this baseline comparison.
   su=ob.modifiers.new('Portrait subdivision','SUBSURF');su.levels=1 if 'animation' in label else 2;su.render_levels=su.levels
   head=ob
  elif '.iris.' in ob.name:
   ob.data.materials.append(brown);ob.data.materials.append(black);ob.data.transform(Matrix.Translation((0,-.0032,0)));ob.data.update();centre=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices)
   for p in ob.data.polygons:
    q=p.center-centre
    if math.hypot(q.x,q.z)<.0027:p.material_index=1
  else:
   ob.data.materials.append(white)
   if '.eye.' in ob.name:
    ob.data.materials.append(brown);ob.data.materials.append(black);ob.data.transform(Matrix.Translation((0,-.0032,0)));ob.data.update();centre=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices)
    # Existing sculpted eye topology gets semantic regions, without texture overlays.
    for p in ob.data.polygons:
     q=p.center-centre;rad=math.hypot(q.x,q.z)
     if q.y<-.017:
      if rad<.0065:p.material_index=2
      elif rad<.0170:p.material_index=1
   su=ob.modifiers.new('Eye subdivision','SUBSURF');su.levels=1;su.render_levels=1
 # A rounded dark pupil seals the artist eye's central aperture.
 for ob in list(copies):
  if '.eye.' in ob.name:
   c=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices);front=min(v.co.y for v in ob.data.vertices);bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=.0064,location=(c.x,front+.0020,c.z));pup=bpy.context.object;pup.name='Pupil_Candidate';pup.scale=(1,.45,1);pup.data.materials.append(black)
   for p in pup.data.polygons:p.use_smooth=True
 # Anatomical eye apertures anchor physical brows against the sculpt itself.
 # One low, tapered curved brow on each side, ray-fitted to actual forehead skin.
 ev=head.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();bv=BVHTree.FromPolygons([v.co for v in me.vertices],[p.vertices[:] for p in me.polygons]);ev.to_mesh_clear()
 centres=[]
 for ob in copies:
  if 'eye.' in ob.name or 'sclera.' in ob.name:
   c=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices);centres.append(c)
 for c in centres:
  width=.024 if 'animation' in label else .035;rise=.017 if 'animation' in label else .041
  vs=[];fs=[];steps=24
  for j in range(steps+1):
   a=j/steps;u=2*a-1;x=c.x+width*u;z=c.z+rise+.004*math.sin(math.pi*a);hit,n,_,_=bv.ray_cast(Vector((x,-1,z)),Vector((0,1,0)));y=hit.y-.0018 if hit is not None else c.y+.025
   rad=(.0025 if 'animation' in label else .0020)*max(.12,math.sin(math.pi*a)**.5)
   for k in range(8):
    th=2*math.pi*k/8;vs.append((x,y-math.cos(th)*rad*.38,z+math.sin(th)*rad))
  for j in range(steps):
   for k in range(8):a=j*8+k;b=j*8+(k+1)%8;fs.append((a,b,b+8,a+8))
  me=bpy.data.meshes.new('SculptedBrow');me.from_pydata(vs,[],fs);me.materials.append(brow);ob=bpy.data.objects.new('Brow_Candidate',me);sc.collection.objects.link(ob)
  for p in me.polygons:p.use_smooth=True
 # World & consistent studio recipe.
 sc.world=bpy.data.worlds.new('Studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.36,.42,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.30
 target=Vector((0,0,.006));
 for lname,loc,power,size,color in [('Key',(-.55,-.7,.75),25,1.0,(1,.91,.80)),('Fill',(.55,-.7,.20),18,1.0,(.80,.89,1)),('Rim',(.30,.35,.55),40,.75,(1,.89,.75))]:
  d=bpy.data.lights.new(lname,'AREA');d.energy=power;d.size=size;d.color=color;o=bpy.data.objects.new(lname,d);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
 d=bpy.data.cameras.new('Portrait');cam=bpy.data.objects.new('Portrait',d);sc.collection.objects.link(cam);sc.camera=cam;d.type='ORTHO';d.ortho_scale=.39 if 'animation' in label else .41
 sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=48;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=600;sc.render.resolution_y=700;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=-.6
 for angle,loc in [('front',(0,-1.1,.010)),('threequarter',(.58,-1.1,.025))]:
  cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'{label}_{angle}.png');bpy.ops.render.render(write_still=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(O/f'{label}_portrait.blend'));out.append(dict(label=label,source=name,parts=[o.name for o in copies],sourceEyeWorld=list(eye)))
(O/'comparison-manifest.json').write_text(json.dumps(out,indent=2))
