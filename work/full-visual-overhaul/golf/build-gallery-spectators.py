"""Standing golf spectators derived from the shared six human crowd art direction. No legacy binding."""
import bpy,math,json,random
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');WORK=ROOT/'work/full-visual-overhaul/golf';PROOF=ROOT/'proof/full-visual-overhaul/golf'
bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.58;return m
skins=[(.76,.44,.27),(.93,.70,.51),(.38,.20,.12),(.63,.38,.24),(.83,.57,.37),(.95,.75,.59)]
shirts=[(.06,.35,.42),(.91,.33,.18),(.91,.89,.78),(.19,.32,.63),(.34,.52,.18),(.66,.22,.37)]
parts=[]
def ellipsoid(name,centre,radii,material,segments=14,rings=8):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=centre);o=bpy.context.object;o.name=name;o.scale=radii;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o

def link(name,a,b,r1,r2,material,verts=12):
 a=Vector(a);b=Vector(b);d=b-a;bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r1,radius2=r2,depth=d.length,location=(a+b)*.5);o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o

def join(name,objects,pivot,parent):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();ob=bpy.context.object;ob.name=name
 # Store actual palette as vertex colours, one draw per rigid piece in Unity.
 colour=ob.data.color_attributes.new(name='SpectatorPalette',type='FLOAT_COLOR',domain='CORNER')
 for p in ob.data.polygons:
  c=ob.data.materials[p.material_index].diffuse_color
  for li in p.loop_indices:colour.data[li].color=c
 ob.data.materials.clear();ob.data.materials.append(palette)
 bpy.context.scene.cursor.location=pivot;bpy.ops.object.origin_set(type='ORIGIN_CURSOR');ob.parent=parent;ob.matrix_parent_inverse=parent.matrix_world.inverted();return ob
palette=mat('GALLERY_VERTEX_PALETTE',(1,1,1));manifest=[]
for i in range(6):
 skin=mat('Skin_'+str(i),skins[i]);shirt=mat('Sport shirt_'+str(i),shirts[i]);bottom=mat('Sport navy_'+str(i),(.055,.10,.16));white=mat('Ivory_'+str(i),(.86,.87,.79));hair=mat('Hair_'+str(i),(.045+.025*i,.035+.018*i,.025+.012*i));eye=mat('Eye_'+str(i),(.032,.041,.047));sole=mat('Sole_'+str(i),(.06,.08,.085));trim=mat('Trim_'+str(i),(.85,.68,.34))
 root=bpy.data.objects.new('FAN_'+str(i),None);bpy.context.collection.objects.link(root);root.location=(i*2.6,0,0)
 body=[];female=i%2==1;shoulder=.225 if female else .25
 # Adult standing proportions; an authored tapered garment avoids a swollen oval torso.
 body += [ellipsoid('Standing hips',(0,.020,.94),(.205 if female else .22,.13,.14),bottom),link('Neck',(0,.025,1.42),(0,.025,1.55),.062,.059,skin)]
 verts=[];faces=[]
 profile=[(.91,.175,.105),(.95,.175,.11),(1.04,.18,.12),(1.16,.205,.135),(1.29,.22 if female else .24,.14),(1.39,shoulder,.13),(1.46,.13,.105)]
 for z,rx,ry in profile:
  for j in range(16):
   angle=j*math.tau/16;verts.append((math.cos(angle)*rx,.025+math.sin(angle)*ry,z))
 for k in range(len(profile)-1):
  for j in range(16):faces.append((k*16+j,k*16+(j+1)%16,(k+1)*16+(j+1)%16,(k+1)*16+j))
 faces.extend([tuple(reversed(range(16))),tuple((len(profile)-1)*16+j for j in range(16))])
 mesh=bpy.data.meshes.new('Fitted polo');mesh.from_pydata(verts,[],faces);mesh.update();mesh.materials.append(shirt);ob=bpy.data.objects.new('Fitted polo',mesh);bpy.context.collection.objects.link(ob)
 for f in mesh.polygons:f.use_smooth=True
 body.append(ob)
 body += [ellipsoid('Polo collar',(-.045,-.073,1.443),(.065,.05,.024),white),ellipsoid('Polo collar',(.045,-.073,1.443),(.065,.05,.024),white),link('Polo placket',(0,-.113,1.43),(0,-.117,1.31),.012,.012,white,8)]
 for z in [1.405,1.36,1.32]:body += [ellipsoid('Polo button',(0,-.13,z),(.006,.005,.006),trim,8,4)]
 for side in [-1,1]:
  x=side*.125;hip=(x,.018,.93);knee=(x,-.004,.50);ankle=(x,.012,.135)
  if female:
   body += [link('Tailored shorts',hip,(x,.005,.69),.108,.096,bottom),ellipsoid('Shorts cuff',(x,.005,.69),(.097,.09,.023),bottom),link('Bare thigh',(x,.005,.69),knee,.090,.070,skin),ellipsoid('Knee',knee,(.073,.073,.065),skin),link('Calf',knee,ankle,.066,.045,skin)]
  else:
   body += [link('Straight trousers',hip,knee,.105,.077,bottom),ellipsoid('Trouser knee',knee,(.079,.077,.055),bottom),link('Tapered trouser leg',knee,ankle,.077,.060,bottom),ellipsoid('Trouser cuff',ankle,(.063,.06,.022),bottom)]
  body += [link('Sport sock',(x,.012,.17),(x,.012,.095),.054,.052,white),ellipsoid('Shoe sole',(x,-.043,.030),(.085,.142,.030),sole),ellipsoid('Sport shoe',(x,-.043,.068),(.081,.137,.054),white),link('Shoe trim',(x-side*.072,-.017,.095),(x-side*.074,-.104,.075),.010,.010,trim,8)]
  for y in [-.043,-.064,-.085]:body += [link('Sport laces',(x-.027,y,.116),(x+.027,y,.116),.0035,.0035,white,6)]
 bodyob=join('BODY',body,(0,0,0),root)
 # Shared opaque facial volume, profile, eyes and brows. Standing head is .66m above seated source.
 head=[];h=(0,.024,1.695)
 head += [ellipsoid('Cranium',h,(.132,.128,.158),skin),ellipsoid('Face',(0,-.066,1.677),(.114,.083,.123),skin),ellipsoid('Chin',(0,-.074,1.595),(.074,.057,.042),skin),ellipsoid('Nose',(0,-.146,1.677),(.024,.035,.030),skin)]
 for side in [-1,1]:
  head += [ellipsoid('Ear',(side*.127,.025,1.685),(.022,.035,.047),skin,10,6),ellipsoid('Eye white',(side*.047,-.136,1.709),(.024,.010,.016),white,10,6),ellipsoid('Iris',(side*.047,-.146,1.709),(.010,.005,.011),eye,10,6),link('Brow',(side*.026,-.139,1.743),(side*.068,-.137,1.741),.0055,.0055,hair,8)]
 head += [link('Mouth',(-.030,-.140,1.629),(.030,-.140,1.629),.0035,.0035,hair,8)]
 if i in [1,3,5]:head += [ellipsoid('Hair cap',(0,.036,1.795),(.138,.128,.075),hair),ellipsoid('Ponytail',(0,.155,1.701),(.060,.067,.125),hair)]
 elif i in [0,4]:head += [ellipsoid('Short hair',(0,.036,1.82),(.135,.124,.048),hair)]
 if i in [2,4]:head += [ellipsoid('Sports visor',(0,-.115,1.774),(.145,.104,.019),shirt)]
 join('HEAD',head,(0,.024,1.535),root)
 for side in [-1,1]:
  arm=[];a=(side*shoulder,.025,1.395);b=(side*.29,-.025,1.09);c=(side*.25,-.085,.87)
  arm += [ellipsoid('Sleeve shoulder',a,(.082,.090,.085),shirt),link('Polo sleeve',a,(side*.275,.001,1.275),.082,.072,shirt),link('Upper arm',(side*.27,.001,1.275),b,.065,.053,skin),ellipsoid('Elbow',b,(.054,.054,.054),skin),link('Forearm',b,c,.050,.036,skin),ellipsoid('Relaxed palm',c,(.040,.035,.060),skin)]
  for n in range(4):arm += [ellipsoid('Finger',(c[0]+(n-1.5)*.012,c[1]-.006,c[2]-.057),(.009,.015,.031),skin,8,6)]
  arm += [ellipsoid('Thumb',(c[0]-side*.035,c[1]-.016,c[2]-.014),(.015,.015,.030),skin,8,6)]
  join('ARM_L' if side<0 else 'ARM_R',arm,a,root)
 for child in root.children:child.matrix_parent_inverse.identity()
 manifest.append({'variant':i,'sex':'female' if female else 'male','skin':skins[i],'shirt':shirts[i],'triangles':sum(len(p.vertices)-2 for ob in root.children for p in ob.data.polygons),'rigid_parts':[ob.name for ob in root.children]})
# Persist palette-node display in the editable source as well as runtime vertex colours.
p=palette.node_tree.nodes.get('Principled BSDF');v=palette.node_tree.nodes.new('ShaderNodeVertexColor');v.layer_name='SpectatorPalette';palette.node_tree.links.new(v.outputs['Color'],p.inputs['Base Color'])
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(WORK/'GolfGallerySpectators.fbx'),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,global_scale=1,bake_anim=False,add_leaf_bones=False,path_mode='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'GolfGallerySpectators.blend'))
(PROOF/'gallery-spectator-source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Authored source renders are optional so source export can run without a GPU bake.
if '--render-proof' in __import__('sys').argv:
 sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1536;sc.render.resolution_y=768;sc.render.resolution_percentage=100
 sc.world=bpy.data.worlds.new('Gallery neutral studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.28,.36,.46,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
 p=palette.node_tree.nodes.get('Principled BSDF');v=palette.node_tree.nodes.new('ShaderNodeVertexColor');v.layer_name='SpectatorPalette';palette.node_tree.links.new(v.outputs['Color'],p.inputs['Base Color'])
 bpy.ops.object.light_add(type='AREA',location=(6,-4,5));bpy.context.object.data.energy=1700;bpy.context.object.data.size=10
 bpy.ops.object.camera_add(location=(6.5,-12,3.1));cam=bpy.context.object;cam.rotation_euler=(Vector((6.5,-.1,.93))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=16;sc.camera=cam;sc.view_settings.view_transform='AgX';sc.render.filepath=str(PROOF/'gallery-spectators-source.png');bpy.ops.render.render(write_still=True)
print('GOLF_GALLERY_SOURCE_READY',json.dumps(manifest))
