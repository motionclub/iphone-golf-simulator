import bpy,math,json
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
# Reuse the agreed material names and weighted opaque leaf construction.
code=(root/'work/full-visual-overhaul/golf/build-resort-kit.py').read_text().split('# Meshes use')[0]
exec(code)
OUT=root/'work/full-visual-overhaul/tennis';PROOF=root/'proof/full-visual-overhaul/tennis'
OUT.mkdir(parents=True,exist_ok=True);PROOF.mkdir(parents=True,exist_ok=True)
reset()
prev=Vector((0,0,0))
for k in range(14):
 t=(k+1)/14;p=Vector((.08*t*t,.035*math.sin(t*math.pi),t*.72))
 tube(prev,p,.038*(1-t*.4),.038*(1-t*.43),0,10)
 prev=p
 # Small bark collars give the trunk visible construction at close distance.
 if k%2==0:tube(p-Vector((0,0,.006)),p+Vector((0,0,.006)),.039*(1-t*.4),.039*(1-t*.4),0,10)
for frond in range(10):
 a=frond*math.tau/10+.13*(frond%2);d=Vector((math.cos(a),math.sin(a),0));L=.75+.08*(frond%3)
 def stem(t):return prev+d*(L*t)+Vector((0,0,.25*math.sin(t*math.pi*.9)-.13*t*t))
 for j in range(6):tube(stem(j/6),stem((j+1)/6),.012*(1-j/7),.010*(1-j/7),1+frond%3,5)
 for j in range(12):
  t=.12+j*.069;p=stem(t)
  for side in [-1,1]:
   length=(.19+.06*math.sin(t*math.pi))*(1-.52*t)
   leaf(p,a+side*(1.08-.22*t),length,.052*(1-.30*t),.040,1+(frond+j)%3,3)
 # A few upright inner spears fill the crown without alpha cards.
 if frond%2==0:leaf(prev+Vector((0,0,.015)),a,.30,.105,.17,2+frond%2,4)
for j in range(4):bulb((prev.x+.034*math.cos(j*2),prev.y+.034*math.sin(j*2),.68),(.035,.035,.048),0,3,7)
mesh('PALM')
reset()
tube((0,0,0),(0,0,.36),.075,.022,0,9)
for k in range(11):
 a=k*2.4;c=Vector((.32*math.cos(a),.32*math.sin(a),.49+.13*math.sin(k*1.8)))
 tube((0,0,.30),c,.026,.009,0,7)
 bulb(c+Vector((0,0,.02)),(.34+.04*math.sin(k),.28+.05*math.cos(k),.18+.04*math.sin(k*1.7)),1+k%3,4,9)
 # Sculpted overlapping leaf shells, rather than a flattened green sphere.
 for j in range(6):
  phi=j*math.tau/6+k*.3
  leaf(c,phi,.40,.15,.17,1+(j+k)%3,4)
 for j in range(4):
  phi=j*math.tau/4+k*.7
  leaf(c+Vector((0,0,.14)),phi,.28,.13,.14,1+(j+k)%3,4)
mesh('CANOPY')
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
for i,o in enumerate(objects):o.location=(i*2,0,0)
report={}
for o in objects:
 o.data.calc_loop_triangles();report[o.name]={'triangles':len(o.data.loop_triangles),'vertices':len(o.data.vertices)}
print(report)
# Export prototypes at origin, axis conversion handled by runtime prototype matrix.
for o in objects:o.location=(0,0,0)
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
asset=root/'Unity/Assets/Resources/Tennis/Premium';asset.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.fbx(filepath=str(OUT/'TennisBotanicalKit-v2.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,global_scale=1,bake_anim=False,add_leaf_bones=False,path_mode='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'TennisBotanicalKit-v2.blend'))
(PROOF/'tennis-botanical-kit-manifest-v2.json').write_text(json.dumps(report,indent=2))
