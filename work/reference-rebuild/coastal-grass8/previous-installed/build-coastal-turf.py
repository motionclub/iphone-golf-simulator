"""Editable cut-turf tiles + seamless authored lamina maps, with no gameplay mesh edits."""
import bpy,bmesh,math,random,sys,argparse,json,hashlib
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--render',action='store_true');args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);OUT=Path(args.out);OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
asset=bpy.data.collections.new('EXPORT_CUT_TURF_TILES');scene.collection.children.link(asset);bake=bpy.data.collections.new('SEAMLESS_LAMINA_MAP_SOURCE');scene.collection.children.link(bake)
preview=bpy.data.collections.new('PROOF_PATCH_ONLY');scene.collection.children.link(preview)

def mesh_obj(name,verts,faces,coll):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);coll.objects.link(o);return o

def lamina(vertices,faces,x,y,angle,height,width,bend,shade,roles,flat=False):
 d=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-d.y,d.x,0));root=Vector((x,y,0));mid=root+d*bend*.53+Vector((0,0,height*.58));tip=root+d*bend+Vector((0,0,height))
 idx=len(vertices);points=[root-side*width*.5,root,root+side*width*.5,mid-side*width*.38,mid+Vector((0,0,width*.22)),mid+side*width*.38,tip]
 if flat:
  length=height;mid=root+d*length*.53+Vector((0,0,width*.16));tip=root+d*length+Vector((0,0,width*.03));points=[root-side*width*.5,root,root+side*width*.5,mid-side*width*.38,mid+Vector((0,0,width*.33)),mid+side*width*.38,tip]
 if flat:
  vertices.extend(tuple(a) for a in points);faces.extend(tuple(idx+i for i in f) for f in [(0,3,1),(1,3,4),(1,4,2),(2,4,5),(3,6,4),(4,6,5)]);roles.extend([(shade,t) for t in (0,0,0,.58,.58,.58,1)])
 else:
  # Tiny groomed blades use two triangles; density wins over unnecessary loops.
  points=[root-side*width*.5,root+side*width*.5,tip+side*width*.045,tip-side*width*.045]
  vertices.extend(tuple(a) for a in points);faces.extend([(idx,idx+3,idx+1),(idx+1,idx+3,idx+2)]);roles.extend([(shade,t) for t in (0,0,1,1)])

rng=random.Random(121250);seeds=[]
for i in range(2400):seeds.append((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(0,math.tau),rng.uniform(.010,.023),rng.uniform(.0022,.0045),rng.uniform(.006,.014),rng.uniform(.68,1.12)))
material=bpy.data.materials.new('MAT_CUT_TURF');material.use_nodes=True
nt=material.node_tree;uv=nt.nodes.new('ShaderNodeAttribute');uv.attribute_name='TurfShade';nt.links.new(uv.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color']);nt.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.83
for name,skip in [('TURF_NEAR',1),('TURF_FAR',10)]:
 v=[];f=[];roles=[]
 for seed in seeds[::skip]:lamina(v,f,*seed,roles)
 o=mesh_obj(name,v,f,asset);o.data.materials.append(material)
 color=o.data.color_attributes.new(name='TurfShade',type='FLOAT_COLOR',domain='POINT')
 uv2=o.data.uv_layers.new(name='TurfRole')
 for i,(shade,t) in enumerate(roles):color.data[i].color=(.063*shade+t*.03,.21*shade+t*.09,.026*shade+t*.014,1)
 for loop in o.data.loops:uv2.data[loop.index].uv=roles[loop.vertex_index]
 # Meters and Blender Z-up are exported identically to the other authored source kits.
 for poly in o.data.polygons:poly.use_smooth=False
bpy.context.view_layer.objects.active=bpy.data.objects['TURF_NEAR']
for o in scene.objects:o.select_set(o.name in ('TURF_NEAR','TURF_FAR'))
bpy.ops.export_scene.fbx(filepath=str(OUT/'CoastalTurf.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_anim=False,mesh_smooth_type='OFF',use_mesh_modifiers=True,path_mode='STRIP',embed_textures=False)
asset.hide_render=True
# Microblade map: a periodic half-meter field of actual folded planar blade surfaces.
v=[];f=[];roles=[];rng=random.Random(121251)
for i in range(3600):
 x,y=rng.uniform(-.25,.25),rng.uniform(-.25,.25);a=rng.uniform(0,math.tau);h=rng.uniform(.009,.022);w=rng.uniform(.0016,.0034);shade=rng.uniform(.65,1.13)
 for dx,dy in [(0,0),(-.5,0),(.5,0),(0,-.5),(0,.5),(-.5,-.5),(-.5,.5),(.5,-.5),(.5,.5)]:
  if abs(x+dx)>.29 or abs(y+dy)>.29:continue
  lamina(v,f,x+dx,y+dy,a,h,w,0,shade,roles,flat=True)
field=mesh_obj('AUTHOR_FOLDED_CUT_BLADE_MAP',v,f,bake)
color=field.data.color_attributes.new(name='BladeAlbedo',type='FLOAT_COLOR',domain='POINT')
for i,(shade,t) in enumerate(roles):color.data[i].color=(.054*shade+t*.019,.19*shade+t*.05,.023*shade+t*.014,1)
base=mesh_obj('AUTHOR_DENSE_TURF_UNDERSTORY',[(-.5,-.5,-.001),(.5,-.5,-.001),(.5,.5,-.001),(-.5,.5,-.001)],[(0,1,2,3)],bake)
for o in [field,base]:
 m=bpy.data.materials.new(o.name+' emission');m.use_nodes=True;o.data.materials.append(m);m.node_tree.nodes.clear();em=m.node_tree.nodes.new('ShaderNodeEmission');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(em.outputs[0],out.inputs[0])
 if o==field:
  att=m.node_tree.nodes.new('ShaderNodeAttribute');att.attribute_name='BladeAlbedo';m.node_tree.links.new(att.outputs['Color'],em.inputs['Color'])
 else:em.inputs['Color'].default_value=(.033,.105,.011,1)
camd=bpy.data.cameras.new('MAP_CAMERA');cam=bpy.data.objects.new('MAP_CAMERA',camd);scene.collection.objects.link(cam);scene.camera=cam;cam.location=(0,0,1);cam.rotation_euler=(0,0,0);camd.type='ORTHO';camd.ortho_scale=.5
world=bpy.data.worlds.new('Proof daylight');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.5,.65,.8,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5
for channel in ('C','N','R'):
 for o in [field,base]:
  nt=o.data.materials[0].node_tree;em=nt.nodes.get('Emission')
  for link in list(nt.links):
   if link.to_node==em:nt.links.remove(link)
  if channel=='C':
   if o==field:nt.links.new(nt.nodes.get('Attribute').outputs['Color'],em.inputs['Color'])
   else:em.inputs['Color'].default_value=(.033,.105,.011,1)
  elif channel=='N':
   geo=nt.nodes.new('ShaderNodeNewGeometry');scale=nt.nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=.5;add=nt.nodes.new('ShaderNodeVectorMath');add.operation='ADD';add.inputs[1].default_value=(.5,.5,.5);nt.links.new(geo.outputs['Normal'],scale.inputs[0]);nt.links.new(scale.outputs[0],add.inputs[0]);nt.links.new(add.outputs[0],em.inputs['Color'])
  else:em.inputs['Color'].default_value=(.87,.87,.87,1)
 scene.view_settings.view_transform='Standard' if channel=='C' else 'Raw';scene.view_settings.look='None';scene.render.filepath=str(OUT/f'CoastalTurf_{channel}.png');bpy.ops.render.render(write_still=True)
bake.hide_render=True;asset.hide_render=True
# Evaluated source patch proof at human eye scale, using the actual authored maps.
tex=bpy.data.images.load(str(OUT/'CoastalTurf_C.png'));normal=bpy.data.images.load(str(OUT/'CoastalTurf_N.png'));normal.colorspace_settings.name='Non-Color'
groundmat=bpy.data.materials.new('PROOF_TEXTURED_SHORT_TURF');groundmat.use_nodes=True;nt=groundmat.node_tree
node=nt.nodes.new('ShaderNodeTexImage');node.image=tex;coord=nt.nodes.new('ShaderNodeTexCoord');mapping=nt.nodes.new('ShaderNodeVectorMath');mapping.operation='SCALE';mapping.inputs[3].default_value=2;nt.links.new(coord.outputs['Object'],mapping.inputs[0]);nt.links.new(mapping.outputs[0],node.inputs['Vector']);nt.links.new(node.outputs[0],nt.nodes.get('Principled BSDF').inputs['Base Color']);norm=nt.nodes.new('ShaderNodeTexImage');norm.image=normal;nt.links.new(mapping.outputs[0],norm.inputs['Vector']);normmap=nt.nodes.new('ShaderNodeNormalMap');normmap.inputs['Strength'].default_value=.40;nt.links.new(norm.outputs[0],normmap.inputs['Color']);nt.links.new(normmap.outputs[0],nt.nodes.get('Principled BSDF').inputs['Normal']);nt.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.85
plane=mesh_obj('PROOF_GROUND',[(-3,-2,-.001),(3,-2,-.001),(3,2,-.001),(-3,2,-.001)],[(0,1,2,3)],preview);plane.data.materials.append(groundmat)
for ix in range(3):
 for iy in range(2):
  source=bpy.data.objects['TURF_NEAR'];o=bpy.data.objects.new(f'PROOF_TURF_{ix}_{iy}',source.data);preview.objects.link(o);o.location=(-2+ix*2,-1+iy*2,0)
sun=bpy.data.lights.new('PROOF_SUN','SUN');sun.energy=2.8;sun.angle=.07;so=bpy.data.objects.new('PROOF_SUN',sun);preview.objects.link(so);so.rotation_euler=(math.radians(25),math.radians(-30),math.radians(-35))
camd.type='PERSP';camd.lens=50;cam.location=(-1.55,-3.4,.95);cam.rotation_euler=(Vector((0,0,.01))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
if args.render:scene.render.filepath=str(OUT/'coastal-turf-source.png');bpy.ops.render.render(write_still=True)
# Packed map images and editable lamina geometry remain in the source.
tex.pack();normal.pack();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'CoastalTurf.blend'))
report={'status':'SOURCE CANDIDATE; actual Unity validation pending','tileSizeMeters':2,'nearBlades':2400,'nearTriangles':4800,'farBlades':240,'farTriangles':480,'grassHeightMeters':[.010,.023],'microTurfTileMeters':.5,'microTextureResolution':512,'maps':['CoastalTurf_C.png','CoastalTurf_N.png','CoastalTurf_R.png'],'geometryCap':{'nearCells':20,'patchRadiusMeters':12,'maximumCells':121,'maximumTriangles':20*4800+101*480,'shadowCasting':False,'expectedDrawSubmissions':2},'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*') if p.suffix in ('.png','.fbx','.blend')}}
(OUT/'coastal-turf-manifest.json').write_text(json.dumps(report,indent=2));print('COASTAL_TURF',json.dumps(report),flush=True)
