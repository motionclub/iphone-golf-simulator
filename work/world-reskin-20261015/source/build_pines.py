import bpy, math, random, json
from mathutils import Vector
from pathlib import Path
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
mat=bpy.data.materials.new('Luminous Pine');mat.diffuse_color=(.18,.37,.15,1)
budget={}
for variant in range(4):
 for lod in range(2):
  rng=random.Random(4100+variant);verts=[];faces=[];cols=[]
  def tube(a,b,r0,r1):
   a,b=Vector(a),Vector(b);axis=(b-a).normalized();side=axis.cross(Vector((0,1,0))).normalized();up=axis.cross(side).normalized();start=len(verts);n=7
   for t,r in [(0,r0),(1,r1)]:
    for k in range(n):
     q=a.lerp(b,t)+(side*math.cos(k*math.tau/n)+up*math.sin(k*math.tau/n))*r
     verts.append(tuple(q));cols.append((.12+rng.random()*.025,.07+rng.random()*.02,.035,1))
   for k in range(n): faces.append((start+k,start+(k+1)%n,start+n+(k+1)%n,start+n+k))
  def crown(center,scale,seed):
   rr=random.Random(seed);n=10 if lod==0 else 7; rings=6 if lod==0 else 4;start=len(verts)
   for j in range(rings+1):
    phi=math.pi*(j+.03)/(rings+.06)
    for k in range(n):
     theta=k*math.tau/n;noise=1+rr.uniform(-.15,.15);q=(math.sin(phi)*math.cos(theta),math.sin(phi)*math.sin(theta),math.cos(phi))
     verts.append(tuple(center[d]+q[d]*scale[d]*noise for d in range(3)))
     light=.64+.36*(q[2]*.5+.5);v=rr.uniform(.9,1.1)
     cols.append((.045*light*v,.14*light*v,.025*light*v,1))
   for j in range(rings):
    for k in range(n):faces.append((start+j*n+k,start+(j+1)*n+k,start+(j+1)*n+(k+1)%n,start+j*n+(k+1)%n))
  lean=Vector((.25*(variant-1),.15,0));tube((0,0,0),lean+Vector((0,0,5.5)),.32,.14)
  for b in range(7):
   angle=b*math.tau/7+variant*.23;rad=2.1+rng.random()*.8
   end=Vector((math.cos(angle)*rad,math.sin(angle)*rad,6.4+rng.random()*.7));base=lean+Vector((0,0,3.8+rng.random()*.8));joint=base.lerp(end,.6)+Vector((0,0,.35));tube(base,joint,.14,.085);tube(joint,end,.085,.025)
   for c in range(15):
    theta=angle+c*2.4;pos=end+Vector((math.cos(theta)*rng.uniform(.3,1.5),math.sin(theta)*rng.uniform(.3,1.5),rng.uniform(-.25,.6)))
    crown(pos,(rng.uniform(.45,.85),rng.uniform(.45,.85),rng.uniform(.25,.45)),variant*10000+b*100+c)
  for c in range(12):crown((rng.uniform(-1,1),rng.uniform(-1,1),7.2+rng.random()*.4),(.8,.7,.4),100000+variant*100+c)
  name='CONIFER_'+chr(65+variant)+('_FAR' if lod else '')
  mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(mat);mesh.update()
  attr=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
  for i,c in enumerate(cols):attr.data[i].color=c
  ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
  for p in mesh.polygons:p.use_smooth=True
  mesh.calc_loop_triangles();budget[name]=len(mesh.loop_triangles)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/world-reskin-20261015/assets/CoastalPines.blend'))
bpy.ops.export_scene.fbx(filepath=str(root/'Unity/Assets/Resources/Environment/LuminousCoast/CoastalPines.fbx'),use_selection=False,apply_unit_scale=True,axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False,path_mode='AUTO')
(root/'work/world-reskin-20261015/assets/pine-budget.json').write_text(json.dumps(budget,indent=2))
