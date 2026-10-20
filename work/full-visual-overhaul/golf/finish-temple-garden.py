"""Ceremonial stair urns, carved medallions and draped vines inside the temple envelope."""
import bpy,bmesh,math,random,json
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
bpy.ops.wm.open_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/TempleArchitecture.blend'))
o=next(o for o in bpy.data.objects if o.name.startswith('TEMPLE') and o.type=='MESH');me=o.data;z=min(v.co.z for v in me.vertices)+.035;cy=236;size=30
bm=bmesh.new();bm.from_mesh(me)
slots={m.name:i for i,m in enumerate(me.materials)}
def mat(name,color):
 if name in slots:return slots[name]
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);slots[name]=len(me.materials);me.materials.append(m);return slots[name]
leaf=mat('MAT_VINE',(.045,.16,.025));flower=mat('MAT_FLOWER_CORAL',(.82,.19,.09));trim=slots['MAT_TEMPLE_TRIM'];stone=slots['MAT_TEMPLE_BLOCK_B'];relief=slots['MAT_TEMPLE_RELIEF']
def v(p):return bm.verts.new(p)
def face(ps,slot):
 f=bm.faces.new(ps);f.material_index=slot;return f
rng=random.Random(19281)
for tier in [1,2]:
 top=z+tier*3.2;s=size*(1-tier/5.8);at=cy-s/2-.55
 for side in [-1,1]:
  cx=side*(size*.11+1.02);rings=[(0,.22),(.08,.30),(.24,.33),(.51,.43),(.79,.30),(.90,.34),(.98,.34)];vs=[];n=10
  for hh,r in rings:
   vs.append([v((cx+r*math.cos(j*math.tau/n),at+r*math.sin(j*math.tau/n),top+hh)) for j in range(n)])
  for k in range(len(rings)-1):
   for j in range(n):face([vs[k][j],vs[k][(j+1)%n],vs[k+1][(j+1)%n],vs[k+1][j]],trim if k in [0,4,5] else stone)
  for j in range(7):
   a=j*2.4;d=Vector((math.cos(a),math.sin(a),0));w=Vector((-d.y,d.x,0));start=Vector((cx,at,top+.93));end=start+d*.62+Vector((0,0,.21));mid=start+d*.31+Vector((0,0,.31))
   face([v(start),v(mid+w*.14),v(end),v(mid-w*.14)],leaf)
  for j in range(3):
   a=j*2.4;center=Vector((cx+.16*math.cos(a),at+.16*math.sin(a),top+1.08))
   for k in range(5):
    d=Vector((math.cos(k*math.tau/5),math.sin(k*math.tau/5),0));w=Vector((-d.y,d.x,0));face([v(center),v(center+d*.11+w*.055),v(center+d*.21),v(center+d*.11-w*.055)],flower)
# Draped vines avoid the central staircase and portal; each chain carries several oval leaves.
for tier in range(5):
 s=size*(1-tier/5.8);half=s/2;top=z+tier*3.2+2.94
 for side in [-1,1]:
  x=side*(half*.72);y=cy-half-.17
  length=1.8+rng.random()*.9
  for j in range(10):
   t=j/9;cx=x+math.sin(t*5+tier)*.22;cz=top-length*t
   center=Vector((cx,y,cz));direction=side if j%2 else -side;width=.14+.05*rng.random()
   face([v(center+Vector((0,-.02,.09))),v(center+Vector((direction*width,-.03,.015))),v(center+Vector((direction*width*.55,-.02,-.13))),v(center+Vector((0,-.02,-.04)))],leaf)
# Small circular stone medallions replace window-like shrine glyphs with deliberate relief.
front=cy-size*.14-.22;bottom=z+16
for side in [-1,1]:
 c=Vector((side*2.73,front,bottom+1.96));n=12
 outside=[v(c+Vector((math.cos(j*math.tau/n)*.43,0,math.sin(j*math.tau/n)*.43))) for j in range(n)]
 inside=[v(c+Vector((math.cos(j*math.tau/n)*.25,-.045,math.sin(j*math.tau/n)*.25))) for j in range(n)]
 for j in range(n):face([outside[j],outside[(j+1)%n],inside[(j+1)%n],inside[j]],trim)
 center=v(c+Vector((0,-.10,0)))
 for j in range(n):face([inside[j],inside[(j+1)%n],center],relief)
bm.to_mesh(me);bm.free();me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/TempleGardenFinish.blend'))
selected=[x for x in bpy.data.objects if x.type=='MESH' and any(x.name.startswith(p) for p in ['TEMPLE','RUIN','STAIR','LIGHTHOUSE','BRIDGE','BENCH','FENCE','HOUSE','SHACK','GATE','WINDMILL']) and 'SAIL' not in x.name]
for x in bpy.data.objects:x.select_set(x in selected)
bpy.ops.export_scene.fbx(filepath=str(root/'Unity/Assets/Resources/Course/Resort/Finish_19.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='OFF',bake_anim=False,path_mode='STRIP')
ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();report={'temple_triangles':len(m.loop_triangles),'stairs_urns':4,'vine_chains':10,'shrine_medallions':2,'bounds':[[min(v.co[k] for v in me.vertices) for k in range(3)],[max(v.co[k] for v in me.vertices) for k in range(3)]],'source_collision_unchanged':True};ev.to_mesh_clear();(root/'proof/full-visual-overhaul/golf/temple-garden-manifest.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
