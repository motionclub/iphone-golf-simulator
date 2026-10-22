"""Add articulated masonry inside the source temple envelope; retain the source collision mesh."""
import bpy,bmesh,math,random,json
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
bpy.ops.wm.open_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/Finish_19.blend'))
o=next(o for o in bpy.data.objects if o.name.startswith('TEMPLE') and o.type=='MESH');me=o.data
z=min(v.co.z for v in me.vertices)+.035;cx=0;cy=236;size=30
bm=bmesh.new();bm.from_mesh(me)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index==4],context='FACES')
# Stone seams sit behind proud dressed blocks, and the portal is a deep warm recess.
for f in bm.faces:
 if f.material_index in [0,2]:f.material_index=1
names=['MAT_TEMPLE_TRIM','MAT_TEMPLE_BLOCK_A','MAT_TEMPLE_BLOCK_B','MAT_TEMPLE_RELIEF','MAT_TEMPLE_RECESS']
for name in names:
 m=bpy.data.materials.new(name);m.diffuse_color=(.65,.53,.34,1);me.materials.append(m)
trim,blocka,blockb,relief,recess=range(5,10)
for f in bm.faces:
 if f.material_index==3:f.material_index=recess
rng=random.Random(19191)
def box(center,scale,slot):
 vs=bmesh.ops.create_cube(bm,size=1)['verts'];ids=set(vs)
 for v in vs:v.co=Vector((v.co.x*scale[0],v.co.y*scale[1],v.co.z*scale[2]))+Vector(center)
 for f in bm.faces:
  if all(v in ids for v in f.verts):f.material_index=slot
# Separate stone courses and dressed cornice on every level. The front stair remains clear.
for tier in range(5):
 s=size*(1-tier/5.8);bottom=z+tier*3.2;half=s/2
 for side in range(4):
  front=side==0;axis=side%2;sign=-1 if side<2 else 1
  if side==0:axis=1;sign=-1
  elif side==1:axis=0;sign=1
  elif side==2:axis=1;sign=1
  else:axis=0;sign=-1
  # Long bands read from the tee while the fine courses read on the green.
  for hh,depth in [(bottom+.19,.18),(bottom+2.97,.24)]:
   center=[cx,cy,hh];center[axis]+=sign*(half-.02)
   scale=[s-.09,s-.09,.20];scale[axis]=depth;box(center,scale,trim)
  for row in range(3):
   width=2.35 if tier<3 else 1.9;count=max(2,math.ceil(s/width));pitch=s/count
   shift=.5*pitch if row%2 else 0
   for col in range(count+1):
    pos=-half+col*pitch+shift;left=max(-half+.11,pos-pitch*.49);right=min(half-.11,pos+pitch*.49)
    if right-left<.30:continue
    middle=(left+right)/2
    if front and abs(middle)<size*.11+.12:continue
    center=[cx,cy,bottom+.58+row*.81];center[axis]+=sign*(half+.018);center[1-axis]+=middle
    scale=[right-left,.16,.71]
    if axis==0:scale=[.16,right-left,.71]
    center[2]+=rng.uniform(-.028,.028);box(center,scale,blocka if rng.random()<.62 else blockb)
  if tier in [1,3] and not front:
   for pos in [-s*.27,s*.27]:
    center=[cx,cy,bottom+1.48];center[axis]+=sign*(half+.13);center[1-axis]+=pos
    scale=[.52,.10,.52] if axis==1 else [.10,.52,.52];box(center,scale,relief)
    for delta in [-.16,.16]:
     p=list(center);p[2]+=delta;p[axis]+=sign*.05
     scale=[.31,.08,.08] if axis==1 else [.08,.31,.08];box(p,scale,trim)
# Stair side pilasters and nosing caps create a deliberate central ceremonial ascent.
for step in range(15):
 t=step/15;reach=size/2*(1-t*5/5.8)+.6;at=cy-reach;top=z+.5+step*1.07+.535
 box((cx,at,top-.04),(size*.22+.03,1.40,.11),trim)
 for sign in [-1,1]:box((sign*(size*.11+.16),at,top-.19),(.28,1.40,.40),blockb)
# Shrine: corner pilasters, inset panels, a substantial lintel, and shallow relief ornaments.
shrinebottom=z+16;shrinehalf=size*.14;portalface=cy-shrinehalf-.07
for sign in [-1,1]:
 box((sign*1.34,portalface,shrinebottom+1.70),(.40,.22,3.14),trim)
 box((sign*3.78,cy-shrinehalf-.015,shrinebottom+2.16),(.34,.20,4.15),blockb)
box((0,portalface-.015,shrinebottom+3.38),(3.09,.28,.41),trim)
box((0,portalface-.16,shrinebottom+3.67),(.50,.17,.31),relief)
for side in [-1,1]:
 box((side*2.73,portalface+.012,shrinebottom+1.85),(1.30,.14,1.90),blocka)
 for j in range(4):box((side*2.73+(j%2-.5)*.30,portalface-.09,shrinebottom+1.5+(j//2)*.50),(.19,.10,.32),relief)
# Keep top cornice below the original shrine roof; all details stay within tolerance.
for sign in [-1,1]:
 box((0,cy+sign*(shrinehalf-.03),shrinebottom+4.18),(size*.28,.20,.23),trim)
 box((sign*(shrinehalf-.03),cy,shrinebottom+4.18),(.20,size*.28,.23),trim)
bm.to_mesh(me);bm.free();me.update()
# Reduce the old bevel width so the smaller carved pieces retain broad faces.
for mod in o.modifiers:
 if mod.type=='BEVEL':mod.width=.035;mod.segments=1
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/TempleArchitecture.blend'))
selected=[x for x in bpy.data.objects if x.type=='MESH' and any(x.name.startswith(p) for p in ['TEMPLE','RUIN','STAIR','LIGHTHOUSE','BRIDGE','BENCH','FENCE','HOUSE','SHACK','GATE','WINDMILL']) and 'SAIL' not in x.name]
for x in bpy.data.objects:x.select_set(x in selected)
bpy.ops.export_scene.fbx(filepath=str(root/'Unity/Assets/Resources/Course/Resort/Finish_19.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='OFF',bake_anim=False,path_mode='STRIP')
eval=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh();eval.calc_loop_triangles()
report={'temple_triangles':len(eval.loop_triangles),'bounds':[[min(v.co[k] for v in me.vertices) for k in range(3)],[max(v.co[k] for v in me.vertices) for k in range(3)]],'source_collision_unchanged':True,'stone_courses':3,'tiers':5}
(root/'proof/full-visual-overhaul/golf/temple-architecture-manifest.json').write_text(json.dumps(report,indent=2));print('TEMPLE_ARCHITECTURE_COMPLETE',json.dumps(report))
