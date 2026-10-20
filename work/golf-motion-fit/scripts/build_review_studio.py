"""One editable studio containing both locked hero rigs and all golf action banks."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
for sex,x in [('Male',-1.15),('Female',1.15)]:
 before=set(bpy.data.objects)
 with bpy.data.libraries.load(str(W/f'export/Golf_{sex}_Dressed.blend'),link=False) as (src,dst):dst.objects=list(src.objects)
 objects=[o for o in dst.objects if o];collection=bpy.data.collections.new(sex+' golf master');scene.collection.children.link(collection);owner=bpy.data.objects.new('GolfStudio_'+sex,None);collection.objects.link(owner)
 gear={}
 for o in objects:
  collection.objects.link(o)
  if o.parent is None:o.parent=owner
  if o.name.startswith(('GolfClub','GolfHandle','GolfShaft')):gear[o.name.split('.')[0]]=o.name;o.name='Studio_'+sex+'_'+o.name.split('.')[0]
  if o.type=='CAMERA':o.hide_render=True
  if o.type=='MESH' and ('_High' in o.name or o.name.startswith('Kit_')):o.hide_render=True;o.hide_set(True)
 owner.location.x=x
 owner['EquipmentObjects']=json.dumps({k:'Studio_'+sex+'_'+k for k in gear});owner['BodyLock']='Original mesh vertices, polygons, weights and rest skeleton retained.'
 for action in bpy.data.actions:
  if '_'+sex+'_' in action.name and not action.name.endswith('Equipment'):
   try:action.asset_mark()
   except Exception:pass
 # Pack the updated neutral maps for artist inspection and further editing.
 profiles=json.loads((W/f'export/material_profiles_{sex}.json').read_text())
 for p in profiles:
  for key in ['normalMap','maskMap']:
   path=W/'maps'/(p[key]+'.png')
   if path.exists():
    img=bpy.data.images.load(str(path),check_existing=True);img.colorspace_settings.name='Non-Color';img.pack()
text=bpy.data.texts.new('Golf_Studio_Controls.py');text.write('''# Run this text once, then call select_motion("Drive", "RH") in the console.
import bpy, json
from pathlib import Path
W=Path('''+repr(str(W))+''')
def select_motion(family="Drive",hand="RH",seconds=0):
 for sex in ["Male","Female"]:
  ident=family+"_"+sex+"_"+hand
  rig=bpy.data.objects["Rig_"+sex];rig.animation_data.action=bpy.data.actions[ident]
  club=bpy.data.objects["Studio_"+sex+"_GolfClub"];club.animation_data.action=bpy.data.actions[ident+"_Equipment"]
  entry=next(x for x in json.loads((W/("export/golf_manifest_"+sex+".json")).read_text())["clips"] if x["id"]==ident)
  for obj in bpy.data.collections[sex+" golf master"].objects:
   if obj.type=="MESH" and obj.data.shape_keys and obj.data.shape_keys.animation_data:
    original=obj.name.split(".")[0];action=bpy.data.actions.get(ident+"_"+original+"_Correctives")
    if action:obj.data.shape_keys.animation_data.action=action
   if obj.name.startswith("Golf_Glove_"):obj.hide_render=("Left" in obj.name)!=(hand=="RH")
   if obj.name.startswith("Studio_"+sex+"_GolfClubFace"):obj.location.y=entry["clubLength"];obj.hide_render=obj.get("GolfEquipment","iron")!=entry["equipment"]
  bpy.context.scene.frame_end=entry["frames"]-1
 bpy.context.scene.frame_set(round(seconds*120))
''')
scene.render.fps=120;scene.render.fps_base=1;scene.frame_set(0);scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=1280;scene.render.resolution_y=800;scene.render.resolution_percentage=100
world=bpy.data.worlds.new('Golf Studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.25,.30,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
for label,position,power,size in [('Key',(2,-4,4),650,4),('Fill',(-4,-2,3),400,4),('Rim',(0,3,4),500,3)]:
 l=bpy.data.lights.new(label,'AREA');l.energy=power;l.size=size;o=bpy.data.objects.new(label,l);scene.collection.objects.link(o);o.location=position;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
for angle in range(0,360,45):
 data=bpy.data.cameras.new('StudioReview_'+str(angle));data.type='ORTHO';data.ortho_scale=4.6;o=bpy.data.objects.new(data.name,data);scene.collection.objects.link(o);r=math.radians(angle);o.location=(6*math.sin(r),-6*math.cos(r),1.1);o.rotation_euler=(Vector((0,0,.95))-o.location).to_track_quat('-Z','Y').to_euler()
scene.camera=bpy.data.objects['StudioReview_0'];scene.view_settings.view_transform='AgX'
readme=bpy.data.texts.new('READ_ME');readme.write('Golf review studio: 24 families × 2 bodies × 2 explicit hands.\nAll 96 rig actions and associated equipment/corrective action banks are editable.\nRun Golf_Studio_Controls.py; use select_motion(family,hand,seconds).\nOriginal body meshes and rest skeletons are retained. golf_covered is reversible render coverage.\nReview cameras are 45 degrees apart. Packed N/M maps use golf fabric profile v2; tennis encoding stays v1.\nRuntime acceptance and visual review remain separate gates.\n')
bpy.ops.wm.save_as_mainfile(filepath=str(W/'export/Golf_Review_Studio.blend'));print('REVIEW_STUDIO_COMPLETE',flush=True)
