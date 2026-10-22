"""Clean opaque seated background people. Rigid art joints, no legacy skin binding."""
import bpy,math,json,random
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');WORK=ROOT/'work/full-visual-overhaul/tennis';PROOF=ROOT/'proof/full-visual-overhaul/tennis'
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
palette=mat('SPECTATOR_VERTEX_PALETTE',(1,1,1));manifest=[]
for i in range(6):
 skin=mat('Skin_'+str(i),skins[i]);shirt=mat('Sport shirt_'+str(i),shirts[i]);bottom=mat('Sport navy_'+str(i),(.055,.10,.16));white=mat('Ivory_'+str(i),(.86,.87,.79));hair=mat('Hair_'+str(i),(.045+.025*i,.035+.018*i,.025+.012*i));eye=mat('Eye_'+str(i),(.032,.041,.047));sole=mat('Sole_'+str(i),(.06,.08,.085));trim=mat('Trim_'+str(i),(.85,.68,.34))
 root=bpy.data.objects.new('FAN_'+str(i),None);bpy.context.collection.objects.link(root);root.location=(i*2.6,0,0)
 # Seat surface is z=0. Facing -Y. Main anatomy is adult sporting proportions.
 body=[];female=i%2==1;shoulder=.235 if female else .265
 body += [ellipsoid('Seated hips',(0,.075,.16),(.24,.20,.18),bottom),ellipsoid('Fitted polo',(0,.045,.53),(.24 if female else .27,.155,.32),shirt),link('Neck',(0,.035,.76),(0,.035,.89),.072,.068,skin)]
 body += [ellipsoid('Polo collar',(-.047,-.075,.785),(.07,.055,.029),white),ellipsoid('Polo collar',(.047,-.075,.785),(.07,.055,.029),white)]
 for side in [-1,1]:
  x=side*.145
  body += [link('Shorts thigh',(x,.015,.15),(x,-.36,.13),.13,.105,bottom),ellipsoid('Shorts cuff',(x,-.33,.13),(.108,.061,.10),bottom),link('Lower bare thigh',(x,-.34,.13),(x,-.43,.085),.095,.093,skin),ellipsoid('Knee',(x,-.43,.065),(.095,.10,.11),skin),link('Shin',(x,-.43,.05),(x,-.46,-.38),.075,.05,skin),link('Sport sock',(x,-.46,-.24),(x,-.46,-.43),.06,.058,white),ellipsoid('Shoe sole',(x,-.55,-.46),(.09,.16,.035),sole),ellipsoid('Sport shoe',(x,-.55,-.435),(.087,.155,.066),white),link('Shoe trim',(x-side*.074,-.52,-.395),(x-side*.077,-.62,-.405),.012,.012,trim,8)]
 bodyob=join('BODY',body,(0,0,0),root)
 # A real profile, ears, nose and brows make faces readable without decals.
 head=[];h=(0,.024,1.035)
 head += [ellipsoid('Cranium',h,(.138,.136,.164),skin),ellipsoid('Face',(0,-.067,1.017),(.12,.086,.128),skin),ellipsoid('Chin',(0,-.074,.935),(.077,.06,.045),skin),ellipsoid('Nose',(0,-.148,1.017),(.025,.038,.032),skin)]
 for side in [-1,1]:
  head += [ellipsoid('Ear',(side*.134,.025,1.025),(.023,.039,.051),skin,10,6),ellipsoid('Eye white',(side*.049,-.139,1.049),(.025,.012,.018),white,10,6),ellipsoid('Iris',(side*.049,-.151,1.049),(.011,.006,.012),eye,10,6),link('Brow',(side*.028,-.142,1.085),(side*.071,-.140,1.083),.006,.006,hair,8)]
 head += [link('Mouth',(-.032,-.143,.969),(.032,-.143,.969),.004,.004,hair,8)]
 # Opaque separate authored hair volume or visor, with ears and scalp retained.
 if i in [1,3,5]:
  head += [ellipsoid('Hair cap',(0,.036,1.135),(.145,.135,.08),hair),ellipsoid('Ponytail',(0,.164,1.041),(.066,.073,.13),hair)]
 elif i in [0,4]:
  head += [ellipsoid('Short hair',(0,.036,1.16),(.142,.13,.052),hair)]
 if i in [2,4]:head += [ellipsoid('Sports visor',(0,-.118,1.114),(.152,.108,.020),shirt)]
 headob=join('HEAD',head,(0,.024,.875),root)
 for side in [-1,1]:
  arm=[];a=(side*shoulder,.04,.71);b=(side*.34,-.07,.44);c=(side*.18,-.31,.29)
  arm += [link('Polo sleeve',a,(side*.305,-.002,.60),.087,.086,shirt),link('Upper arm',(side*.295,-.001,.61),b,.072,.061,skin),ellipsoid('Elbow',b,(.066,.066,.066),skin),link('Forearm',b,c,.057,.043,skin),ellipsoid('Relaxed palm',c,(.054,.07,.035),skin)]
  # Fingers close together around the lap; no torn blended fingers or displaced tips.
  for n in range(4):arm += [ellipsoid('Finger',(c[0]+(n-1.5)*.014,c[1]-.041,c[2]-.015),(.011,.037,.012),skin,8,6)]
  arm += [ellipsoid('Thumb',(c[0]-side*.049,c[1]-.009,c[2]-.008),(.018,.031,.016),skin,8,6)]
  join('ARM_L' if side<0 else 'ARM_R',arm,a,root)
 for child in root.children:child.matrix_parent_inverse.identity()
 manifest.append({'variant':i,'sex':'female' if female else 'male','skin':skins[i],'shirt':shirts[i],'triangles':sum(len(p.vertices)-2 for ob in root.children for p in ob.data.polygons)})
# Export all six templates, with four articulated rigid meshes each.
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(WORK/'TennisSpectators.fbx'),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,global_scale=1,bake_anim=False,add_leaf_bones=False,path_mode='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=str(WORK/'TennisSpectators.blend'))
(PROOF/'spectator-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# A direct source art proof with neutral lighting.
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1536;sc.render.resolution_y=640;sc.render.resolution_percentage=100
sc.world=bpy.data.worlds.new('Neutral spectator studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.28,.36,.46,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
# Blender proof uses vertex palette nodes, matching runtime shader semantics.
p=palette.node_tree.nodes.get('Principled BSDF');v=palette.node_tree.nodes.new('ShaderNodeVertexColor');v.layer_name='SpectatorPalette';palette.node_tree.links.new(v.outputs['Color'],p.inputs['Base Color'])
bpy.ops.object.light_add(type='AREA',location=(6,-4,5));bpy.context.object.data.energy=1700;bpy.context.object.data.size=10
bpy.ops.object.camera_add(location=(6.5,-12,3.8));cam=bpy.context.object;cam.rotation_euler=(Vector((6.5,-.1,.4))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=16;sc.camera=cam;sc.view_settings.view_transform='AgX';sc.render.filepath=str(PROOF/'spectators-source.png');bpy.ops.render.render(write_still=True)
print('PREMIUM_SPECTATORS_STAGED',json.dumps(manifest))
