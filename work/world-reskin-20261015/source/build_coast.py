import bpy, math, random, pathlib, json
from mathutils import noise, Vector
OUT=pathlib.Path(__file__).resolve().parents[1]/'assets'; OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
# Broad asymmetric ridge masses with eroded spurs; meters, Y is landscape depth.
peaks=[(-322,625,86,65,68),(-238,690,148,68,85),(-136,652,92,52,57),(-38,705,118,56,76),(71,686,168,57,72),(166,720,110,58,86),(262,660,74,65,60),(352,729,124,67,76)]
verts=[];faces=[]; nx=241;ny=101
for j in range(ny):
 y=450+j*4.2
 for i in range(nx):
  x=-480+i*4
  values=[h*math.exp(-(((x-cx)/sx)**2+((y-cy)/sy)**2)*.65) for cx,cy,h,sx,sy in peaks]
  broad=max(values)+sum(values)*.07
  n=noise.fractal(Vector((x*.018,y*.018,7.1)),1.0,2.1,4)
  ridge=1-abs(noise.noise_vector(Vector((x*.028,y*.028,4.3)))[0])
  fade=max(0,min(1,(broad-4)/25))
  z=-7+broad+(n*15+(ridge-.6)*12)*fade
  # Drainage channels vary with elevation and run along the major fall line.
  z-=abs(math.sin(x*.067+y*.043+noise.noise(Vector((x*.01,y*.01,3)))*3))*6*fade
  verts.append((x,y,z*.70))
for j in range(ny-1):
 for i in range(nx-1):
  a=j*nx+i;faces.extend([(a,a+1,a+nx+1),(a,a+nx+1,a+nx)])
mesh=bpy.data.meshes.new('Coastal eroded ridge mesh');mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new('Luminous_Ridge',mesh);bpy.context.collection.objects.link(obj)
for p in mesh.polygons:p.use_smooth=True
mat=bpy.data.materials.new('LuminousCoastRockForest');mat.diffuse_color=(.30,.44,.30,1);obj.data.materials.append(mat)
# Vertex biome paint: limestone ribs, forest on ledges, baked crevice darkening.
col=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
for v in mesh.vertices:
 x,y,z=v.co;n=v.normal
 variation=noise.noise(Vector((x*.021,y*.021,z*.025)))
 cliff=max(0,min(1,(.68-n.z)*4.8))
 high=max(0,min(1,(z-60)/70))
 rock=max(cliff, high*.22)*.9
 green=Vector((.085,.25,.11));chalk=Vector((.56,.59,.49))
 c=green.lerp(chalk,rock)*(0.94+variation*.13)
 col.data[v.index].color=(*c,1)
# Compact modeled forest canopies catch light and break the terrain silhouette.
random.seed(531)
cv=[];cf=[];cc=[]
for v in mesh.vertices:
 x,y,z=v.co
 if z<4 or z>115 or v.normal.z<.79 or random.random()>.16: continue
 for lobe in range(2):
  cx=x+random.uniform(-2,2);cy=y+random.uniform(-2,2);cz=z+random.uniform(2.2,3.8)
  radius=random.uniform(1.7,2.8);height=radius*random.uniform(.8,1.25)
  base=len(cv);tint=random.uniform(.75,1.1)
  for j in range(4):
   a=math.pi*j/3
   for k in range(6):
    b=k*math.tau/6
    cv.append((cx+radius*math.sin(a)*math.cos(b),cy+radius*math.sin(a)*math.sin(b),cz+height*math.cos(a)))
    cc.append((.15*tint,.29*tint,.11*tint,1))
  for j in range(3):
   for k in range(6):
    a=base+j*6+k;b=base+j*6+(k+1)%6;c=base+(j+1)*6+(k+1)%6;d=base+(j+1)*6+k
    if j==0:cf.append((a,c,d))
    elif j==2:cf.append((a,b,d))
    else:cf.extend([(a,b,c),(a,c,d)])
cf=[tuple(reversed(f)) for f in cf]
forest=bpy.data.meshes.new('Forest silhouette canopy');forest.from_pydata(cv,[],cf);forest.update()
fo=bpy.data.objects.new('Luminous_Forest',forest);bpy.context.collection.objects.link(fo);fo.data.materials.append(mat)
for p in forest.polygons:p.use_smooth=True
fc=forest.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
for i,c in enumerate(cc):fc.data[i].color=c
forest.color_attributes.active_color=fc
mesh.color_attributes.active_color=col
fo.select_set(True)
bpy.context.view_layer.objects.active=obj;obj.select_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'LuminousCoast.blend'))
bpy.ops.export_scene.fbx(filepath=str(OUT/'LuminousCoast.fbx'),use_selection=True,axis_forward='-Z',axis_up='Y',global_scale=1,apply_unit_scale=True,bake_anim=False,add_leaf_bones=False,object_types={'MESH'},mesh_smooth_type='FACE')
(OUT/'mesh-budget.json').write_text(json.dumps({'triangles':len(faces)+len(cf),'vertices':len(verts)+len(cv),'colliders':0,'materials':1,'source':'build_coast.py'},indent=2))
