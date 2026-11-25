"""Original party club silhouettes, four club lengths, exact installed Club bind.
Blender -b --factory-startup --python this.py. Does not edit heroes or animations.
"""
import bpy,sys,json,math,pathlib
from mathutils import Matrix,Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'blender/scripts'));import golf_clubs,golf_swing
OUT=ROOT/'Unity/Assets/Resources/Golf/Equipment/Party';OUT.mkdir(parents=True,exist_ok=True)
NATIVE=ROOT/'GolfArcade/Unity/CharacterAssets';WORK=ROOT/'work/clubhouse-cosmetics'
styles=['hockey','slugger','balloon','candy']
if '--' in sys.argv: styles=sys.argv[sys.argv.index('--')+1:]
def clear():
 for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
def mat(name,c,rough=.45,metal=0,texture=None):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True
 m.diffuse_color=(*c,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 m['texture']=texture or '';m['colour']=list(c);m['rough']=rough;m['metal']=metal
 if texture:
  t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ROOT/f'Unity/Assets/Resources/Cosmetics/Cosmetic_{texture}.png'),check_existing=True)
  mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*c,1)
  m.node_tree.links.new(t.outputs['Color'],mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],p.inputs['Base Color'])
 return m
navy=mat('Party_navy',(.025,.045,.085),.36,0,'woven');cream=mat('Party_cream',(.95,.92,.82));mint=mat('Party_mint',(.04,.8,.62),.27)
wood=mat('Party_caramel',(.76,.43,.17),.42,0,'wood');chrome=mat('Party_chrome',(.72,.82,.9),.24,.75,'metal');pink=mat('Party_pink',(.94,.14,.28),.22);purple=mat('Party_violet',(.38,.1,.83),.23);red=mat('Party_red',(.94,.09,.13),.25)
gold=mat('Party_gold',(.98,.48,.035),.26,.65);lime=mat('Party_lime',(.65,.95,.035),.28)
ice=mat('Party_ice',(.025,.52,.92),.16,.15);ice_light=mat('Party_iceLight',(.35,.86,1),.19,.08)
yellow=mat('Party_yellow',(1,.66,.025),.19);black=mat('Party_black',(.018,.012,.035),.24)
pink_back=mat('Party_pinkBack',(.94,.14,.28),.22)
cyan=mat('Party_cyan',(.02,.93,1),.24)
# V2: authored at game scale; no oversized concept model is squeezed into a tiny head.
violet_metal=mat('Party_violetMetal',(.24,.065,.56),.29,.5)
ice_mid=mat('Party_iceMid',(.04,.44,.78),.25,.12)
ice_dark=mat('Party_iceDark',(.018,.15,.32),.38,.25)
stripe=mat('Party_coralStripe',(.94,.14,.28),.25)
grip_white=mat('Party_gripWhite',(.79,.83,.84),.66,0,'leather')
grip_violet=mat('Party_gripViolet',(.075,.025,.17),.62,0,'leather')
grip_amber=mat('Party_gripAmber',(.96,.52,.035),.58,0,'leather')
grip_mint=mat('Party_gripMint',(.025,.48,.38),.61,0,'leather')
parts=[]
def finish(o,m):
 o.data.materials.append(m);parts.append(o)
 for p in o.data.polygons:p.use_smooth=True
 return o
def tube(name,a,b,r,m,r2=None):
 d=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=r,radius2=r if r2 is None else r2,depth=d.length,location=(Vector(a)+Vector(b))/2)
 o=bpy.context.object;o.name=name;o.rotation_mode='QUATERNION';o.rotation_quaternion=d.to_track_quat('Z','Y');return finish(o,m)
def orb(name,p,s,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=28,ring_count=16,location=p);o=bpy.context.object;o.name=name;o.scale=s;return finish(o,m)
def box(name,p,s,m,bevel=.012):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=s;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 mod=o.modifiers.new('Soft edges','BEVEL');mod.width=bevel;mod.segments=3;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name);return finish(o,m)
def hockey_shaft(bottom):
 # Dense axial rings allow the existing lie correction to bend the lower hosel continuously.
 verts=[];faces=[];ring=[]
 for cx,cy,base in [(.0085,.0055,0),(-.0085,.0055,90),(-.0085,-.0055,180),(.0085,-.0055,270)]:
  for j in range(4):
   a=math.radians(base+j*30);ring.append((cx+.005*math.cos(a),cy+.005*math.sin(a)))
 n=len(ring)
 for k in range(49):
  z=-.16+(bottom+.16)*k/48
  verts.extend((x,y,z) for x,y in ring)
 for k in range(48):
  for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
 faces.extend([tuple(reversed(range(n))),tuple(48*n+j for j in range(n))])
 me=bpy.data.meshes.new('Composite shaft');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Composite shaft',me);bpy.context.collection.objects.link(o);finish(o,navy)

def lathe(name,profile,m,segments=24):
 verts=[];faces=[]
 for z,r in profile:
  for j in range(segments):
   a=j/segments*math.tau;verts.append((r*math.cos(a),r*math.sin(a),z))
 for i in range(len(profile)-1):
  for j in range(segments):faces.append((i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j))
 faces.extend([tuple(reversed(range(segments))),tuple((len(profile)-1)*segments+j for j in range(segments))])
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return finish(o,m)
def torus(name,p,r,thick,m,axis='Z'):
 bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=thick,major_segments=36,minor_segments=8,location=p)
 o=bpy.context.object;o.name=name
 if axis=='Y':o.rotation_euler.x=math.pi/2
 return finish(o,m)
def crystal_blade(end):
 outline=[(-.025,end+.02),(.04,end),(.18,end+.005),(.26,end+.025),(.28,end+.20),(.24,end+.165),(.22,end+.105),(.18,end+.14),(.145,end+.07),(.11,end+.10),(.065,end+.045),(-.02,end+.07)]
 vs=[(x,y,z) for y in [-.024,.024] for x,z in outline];n=len(outline)
 fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 me=bpy.data.meshes.new('Ice crystal blade');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Ice crystal blade',me);bpy.context.collection.objects.link(o);finish(o,ice);o.data.materials.append(ice_light)
 for poly in o.data.polygons:poly.use_smooth=False;poly.material_index=poly.index%2
 mod=o.modifiers.new('Ice facets','BEVEL');mod.width=.005;mod.segments=1;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 # Broad glacial ridges are actual bevelled low-poly solid wedges.
 for x,h in [(.08,.055),(.15,.09),(.235,.15)]:
  bpy.ops.mesh.primitive_cone_add(vertices=5,radius1=.025,radius2=0,depth=h,location=(x,-.027,end+.04+h/2));finish(bpy.context.object,ice_light)
def armor_panel(end,angle):
 vs=[];steps=8
 for z,r in [(end+.08,.057),(end+.31,.055)]:
  for radius in [r,r+.006]:
   for j in range(steps+1):
    a=angle+math.radians(-24+48*j/steps);vs.append((radius*math.cos(a),radius*math.sin(a),z))
 n=steps+1;fs=[]
 for j in range(steps):
  fs.extend([(j,j+1,2*n+j+1,2*n+j),(n+j,3*n+j,3*n+j+1,n+j+1),(j,n+j,n+j+1,j+1),(2*n+j,2*n+j+1,3*n+j+1,3*n+j)])
 fs.extend([(0,2*n,3*n,n),(steps,n+steps,3*n+steps,2*n+steps)])
 me=bpy.data.meshes.new('Barrel armor');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Barrel armor',me);bpy.context.collection.objects.link(o);finish(o,purple)
 mod=o.modifiers.new('Armor bevel','BEVEL');mod.width=.003;mod.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
def candy_face(center,radius,back=False):
 # Three sculpted spiral sectors meet at continuous boundaries on a shallow domed face.
 for k,m in enumerate([pink_back if back else pink,cream,mint]):
  vs=[];fs=[];nr=18;na=12
  for i in range(nr+1):
   r=max(.0004,radius*i/nr)
   for j in range(na+1):
    a=math.tau*(k+j/na)/3 + (r/radius)*2.1
    vs.append((center[0]+r*math.cos(a),center[1]+(.008 if back else -.008)*(1-(r/radius)**2),center[2]+r*math.sin(a)))
  for i in range(nr):
   for j in range(na):
    a=i*(na+1)+j;fs.append((a,a+na+1,a+na+2,a+1))
  fs=[tuple(reversed(f)) for f in fs] if back else fs
  me=bpy.data.meshes.new('Sculpted candy swirl');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Sculpted candy swirl',me);bpy.context.collection.objects.link(o);finish(o,m)

def mesh_part(name,vertices,faces,material):
 me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.update()
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);return finish(ob,material)
def smooth01(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def shaft_v2(name,end,bottom,x_end,y_end,material,radius=.0055,square=False,striped=False):
 n=24 if not square else 16;steps=160 if striped else 64;vs=[];fs=[]
 for k in range(steps+1):
  t=k/steps;z=-.148+(bottom+.148)*t;curve=smooth01((-.16-z)/max(.01,-.16-(end+.14)))
  cx=x_end*curve;cy=y_end*curve
  for j in range(n):
   a=math.tau*(j/n-z/.075) if striped else math.tau*j/n
   if square:
    x=radius*math.copysign(abs(math.cos(a))**.3,math.cos(a));y=radius*.72*math.copysign(abs(math.sin(a))**.3,math.sin(a))
   else:x=radius*math.cos(a);y=radius*math.sin(a)
   vs.append((cx+x,cy+y,z))
 for k in range(steps):
  for j in range(n):fs.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
 fs.extend([tuple(reversed(range(n))),tuple(steps*n+j for j in range(n))])
 ob=mesh_part(name,vs,fs,material)
 if square:
  ob.data.materials.append(cyan)
  for k in range(steps):
   z=-.148+(bottom+.148)*(k+.5)/steps
   if -.68<z<-.24 and min(abs(z-t) for t in [-.29,-.44,-.59])>.012:
    for j in [11,12]:ob.data.polygons[k*n+j].material_index=1
 if striped:
  ob.data.materials.append(stripe);ob.data.materials.append(mint)
  for k in range(steps):
   z=-.148+(bottom+.148)*(k+.5)/steps
   for j in range(n):
    phase=(j+.5)/n
    ob.data.polygons[k*n+j].material_index=1 if phase<.24 else 2 if .27<phase<.38 else 0
 return ob

def original_bounds(c):
 if c not in BASE_BOUNDS:
  reference=base_object(c);BASE_BOUNDS[c]=[(min(v.co[i] for v in reference.data.vertices),max(v.co[i] for v in reference.data.vertices)) for i in range(3)];bpy.data.objects.remove(reference,do_unlink=True)
 return BASE_BOUNDS[c]
def elliptical_profile(name,profile,material,segments=40):
 vs=[];fs=[]
 for z,rx,ry,cx,cy in profile:
  for j in range(segments):
   a=j/segments*math.tau;vs.append((cx+rx*math.cos(a),cy+ry*math.sin(a),z))
 for i in range(len(profile)-1):
  for j in range(segments):fs.append((i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j))
 fs.extend([tuple(reversed(range(segments))),tuple((len(profile)-1)*segments+j for j in range(segments))])
 return mesh_part(name,vs,fs,material)
def ellipse_band(name,cx,cy,z,rx,ry,height,material):
 return elliptical_profile(name,[(z-height/2,rx,ry,cx,cy),(z+height/2,rx,ry,cx,cy)],material,40)
def armor_v2(end,cx,cy,rx,ry,angle):
 n=12;vs=[]
 for z in [end+.065,end+.23]:
  for depth in [0,.0012]:
   for j in range(n+1):
    a=angle+math.radians(-29+58*j/n);vs.append((cx+(rx+depth)*math.cos(a),cy+(ry+depth*.5)*math.sin(a),z))
 q=n+1;fs=[]
 for j in range(n):fs.extend([(j,j+1,2*q+j+1,2*q+j),(q+j,3*q+j,3*q+j+1,q+j+1),(j,q+j,q+j+1,j+1),(2*q+j,2*q+j+1,3*q+j+1,3*q+j)])
 fs.extend([(0,2*q,3*q,q),(n,q+n,3*q+n,2*q+n)])
 ob=mesh_part('Inset barrel armor',vs,fs,violet_metal)
 mod=ob.modifiers.new('Machined armor bevel','BEVEL');mod.width=.0012;mod.segments=3;bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
def balloon(name,point,scale,material,angle=0):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=14,location=point)
 ob=bpy.context.object;ob.name=name;ob.scale=scale;ob.rotation_euler.y=angle;return finish(ob,material)
def swirl_v2(cx,cy,cz,radius,depth,back=False):
 for k in range(6):
  m=[pink_back if back else pink,cream,mint][k%3];nr=20;na=8;vs=[];fs=[]
  for i in range(nr+1):
   r=max(.00008,radius*i/nr)
   for j in range(na+1):
    a=math.tau*(k+j/na)/6+3.7*(1-r/radius)
    y=cy+(1 if back else -1)*(depth/2+.0018*(1-(r/radius)**2)+.0009*math.sin(math.pi*j/na)**2)
    vs.append((cx+r*math.cos(a),y,cz+r*math.sin(a)))
  for i in range(nr):
   for j in range(na):
    a=i*(na+1)+j;f=(a,a+na+1,a+na+2,a+1);fs.append(tuple(reversed(f)) if back else f)
  mesh_part('Raised peppermint swirl',vs,fs,m)

def build(style,c):
 global parts;parts=[];end=golf_clubs.SOLE[c]
 # Exact original grip extent: hands and two-hand constraint never move.
 tube('Wrapped grip',(0,0,-.16),(0,0,.07),.014,navy,r2=.015)
 for z in [-.14,-.105,-.07,-.035,0,.035,.065]:tube('Grip binding',(0,0,z),(0,0,z+.004),.0156,cream)
 target=original_bounds(c);width=target[0][1]-target[0][0];depth=target[1][1]-target[1][0]
 cx=(target[0][0]+target[0][1])/2;cy=(target[1][0]+target[1][1])/2;scale=width/.0967
 if style=='hockey':
  shaft_v2('Composite hockey shaft',end,end+.033,cx-width*.35,cy,navy,.0063,True)
  # A continuous swept blade, cut facets and a light raised edge instead of unrelated cones.
  points=[(-.46,.012),(-.29,.002),(.16,0),(.46,.011),(.49,.054),(.29,.039),(-.08,.031),(-.39,.033)]
  outline=[(cx+x*width,end+z*scale) for x,z in points];n=len(outline);half=min(depth*.37,.015)
  vs=[(x,cy+y,z) for y in [-half,half] for x,z in outline]
  vs.extend([(cx+width*.025,cy-half-.0014,end+.024*scale),(cx+width*.025,cy+half+.0014,end+.024*scale)])
  fs=[(i,(i+1)%n,2*n) for i in range(n)]+[(i+n,2*n+1,(i+1)%n+n) for i in range(n)]+[(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
  ob=mesh_part('Swept faceted ice blade',vs,fs,ice_mid);ob.data.materials.append(ice_light);ob.data.materials.append(ice_dark)
  for f in ob.data.polygons:
   f.use_smooth=False
   f.material_index=(1 if f.index%n in [3,4,5] else 0) if f.index<2*n else 2
  mod=ob.modifiers.new('Cut crystal edge','BEVEL');mod.width=.0012;mod.segments=2;bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
  # Embedded shaft channels and short segmented collars remain legible from the game camera.
  ellipse_band('Orange ferrule',cx-width*.35,cy,end+.065,.008,.006,.009,gold)
  tube('Ferrule rivet',(cx-width*.35,cy-.005,end+.066),(cx-width*.35,cy-.007,end+.066),.002,chrome)
 elif style=='slugger':
  rx=width*.355;ry=min(depth*.415,.025)
  profile=[(-.148,.009,.009,0,0),(-.25,.010,.009,0,0),(-.39,.016,.010,cx*.25,cy*.25),(end+.40,rx*.66,ry*.80,cx*.65,cy),(end+.32,rx*.88,ry*.96,cx*.90,cy),(end+.24,rx,ry,cx,cy),(end+.065,rx,ry,cx,cy),(end+.023,rx*.88,ry*.90,cx,cy),(end+.006,rx*.55,ry*.60,cx,cy),(end,0,0,cx,cy)]
  elliptical_profile('Shaped maple barrel',profile,wood)
  for angle in [math.radians(-62),math.radians(-120),math.radians(65)]:armor_v2(end,cx,cy,rx,ry,angle)
  for z in [end+.058,end+.238]:ellipse_band('Lime guard rail',cx,cy,z,rx+.0013,ry+.0006,.004,lime)
  for z in [end+.11,end+.19]:tube('Recessed barrel bolt',(cx+.010,cy-ry,z),(cx+.010,cy-ry-.0016,z),.0038,chrome)
  # Cut-in lightning badge, broad enough to read without tiny text.
  y=cy-ry-.00025;verts=[(cx-.005,y,end+.310),(cx+.004,y,end+.310),(cx-.001,y,end+.292),(cx+.006,y,end+.292),(cx-.006,y,end+.274),(cx-.002,y,end+.291),(cx-.008,y,end+.291)]
  mesh_part('Lightning inlay',verts,[tuple(reversed(range(7)))],ice_dark)
 elif style=='balloon':
  sx=scale;sy=min(depth*.82,.036)/.030
  def dog(name,x,y,z,dx,dy,dz,m,angle=0):return balloon(name,(cx+x*sx,cy+y*sy,end+z*sx),(dx*sx,dy*sy,dz*sx),m,angle)
  shaft_v2('Lacquered balloon baton',end,end+.068,cx-.021*sx,cy,violet_metal,.0057)
  dog('Inflated body',.009,0,.038,.031,.010,.014,pink)
  for x in [-.010,.030]:
   for y in [-.006,.006]:dog('Twisted balloon leg',x,y,.014,.008,.006,.014,yellow,(-.24 if x<0 else .24))
  dog('Neck',-.022,0,.061,.010,.010,.021,yellow)
  dog('Long inflated muzzle',-.034,0,.079,.017,.010,.010,pink)
  for y in [-.006,.006]:dog('Loop ear',-.020,y,.101,.0065,.0057,.019,pink,-.10)
  dog('Balloon tail',.042,0,.060,.0065,.007,.017,yellow,.42)
  for sign in [-1,1]:
   dog('Glossy eye',-.029,sign*.0093,.083,.003,.0016,.0035,black)
   dog('Eye catchlight',-.030,sign*.0105,.084,.0008,.00045,.001,cream)
  tube('Tied nose',(cx-.050*sx,cy,end+.079*sx),(cx-.054*sx,cy,end+.079*sx),.0032*sx,pink,r2=.0017*sx)
  ellipse_band('Collar clasp',cx-.022*sx,cy,end+.052*sx,.011*sx,.0105*sy,.004*sx,gold)
  for z in [-.23,-.39,-.55]:
   curve=smooth01((-.16-z)/max(.01,-.16-(end+.14)))
   ellipse_band('Baton accent',(cx-.021*sx)*curve,cy*curve,z,.0063,.0063,.003,gold)
 else:
  radius=width*.435;disc_depth=min(depth*.62,.025);cz=end+radius
  shaft_v2('Solid striped candy cane',end,end+radius*1.91,cx,cy,cream,.0054,False,True)
  tube('Candy body',(cx,cy-disc_depth/2,cz),(cx,cy+disc_depth/2,cz),radius,cream)
  swirl_v2(cx,cy,cz,radius*.96,disc_depth,False);swirl_v2(cx,cy,cz,radius*.96,disc_depth,True)
  for sign in [-1,1]:torus('Rolled candy lip',(cx,cy+sign*disc_depth/2,cz),radius*.98,.0014,cream,'Y')
  elliptical_profile('Folded golden wrapper',[(end+radius*1.89,.0064,.0058,cx,cy),(end+radius*2.03,.010,.0068,cx,cy),(end+radius*2.08,.0062,.0055,cx,cy)],gold,12)
 discarded=('Wrapped grip','Grip binding','Purple grip','Yellow grip','Golden butt','Grip stitch','Grip twist','Mint grip','Grip rib')
 for item in parts[:]:
  if item.name.startswith(discarded):parts.remove(item);bpy.data.objects.remove(item,do_unlink=True)
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.join();o=bpy.context.object;o.name='CLUB_'+c.upper()
 bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 # Recalculate outward winding on closed custom parts; retain authored front winding on open swirl sectors.
 import bmesh
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 # Mesh coordinates must be relative to original grip, never the first selected part.
 o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4)
 # Substitute the exact original grip mesh: hand geometry is a hard animation contract.
 import bmesh
 for vertex in o.data.vertices:
  if vertex.co.z>=-.16001:
   radius=math.hypot(vertex.co.x,vertex.co.y)
   if radius>.0105:vertex.co.x*=.0105/radius;vertex.co.y*=.0105/radius
   # Bury the novelty shaft inside the exact original grip, keeping connected faces.
   vertex.co.z=min(vertex.co.z,.06)
 reference=base_object(c);reference.data=reference.data.copy();reference.name='Exact original grip';bpy.context.collection.objects.link(reference)
 bm=bmesh.new();bm.from_mesh(reference.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z<-.16001],context='VERTS');bm.to_mesh(reference.data);bm.free()
 grip_colour={'hockey':grip_white,'slugger':grip_violet,'balloon':grip_amber,'candy':grip_mint}[style]
 for i,m in enumerate(reference.data.materials):reference.data.materials[i]=grip_colour if m.name=='CLUB grip' else gold if m.name=='CLUB accent' else navy
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);reference.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.join()
 # Explicit cylindrical UVs for the scanned wood and woven shaft detail.
 uv=o.data.uv_layers.active or o.data.uv_layers.new(name='UVMap')
 for face in o.data.polygons:
  material=o.data.materials[face.material_index]
  texture=material.get('texture','')
  if texture not in ['wood','woven','leather']:continue
  coords=[]
  for li in face.loop_indices:
   v=o.data.vertices[o.data.loops[li].vertex_index].co
   offset=cx*smooth01((-.16-v.z)/.40) if texture=='wood' else 0
   coords.append([math.atan2(v.y-cy if texture=='wood' else v.y,v.x-offset)/math.tau+.5,(v.z-golf_clubs.SOLE[c])/(.0715-golf_clubs.SOLE[c])])
  if max(x[0] for x in coords)-min(x[0] for x in coords)>.5:
   for x in coords:
    if x[0]<.5:x[0]+=1
  for li,coord in zip(face.loop_indices,coords):uv.data[li].uv=(coord[0]*(4 if texture in ['woven','leather'] else 1),coord[1]*(4 if texture in ['woven','leather'] else 1))
 fit_to_original(o,c)
 return o

BASE_BOUNDS={};BASE_MESHES={}
def base_object(c):
 if c not in BASE_MESHES:
  ob=golf_clubs.build(c);BASE_MESHES[c]=ob.data.copy();bpy.data.objects.remove(ob,do_unlink=True)
 me=BASE_MESHES[c];return bpy.data.objects.new('Baseline_'+c,me)
def fit_to_original(o,c,prepared=False):
 key=c+('_prepared' if prepared else '')
 if key not in BASE_BOUNDS:
  reference=base_object(c)
  if prepared:
   reference.data=reference.data.copy();golf_swing.prepare_club_mesh(reference,golf_swing.LIE[c])
  BASE_BOUNDS[key]=[(min(v.co[i] for v in reference.data.vertices),max(v.co[i] for v in reference.data.vertices)) for i in range(3)]
  bpy.data.objects.remove(reference,do_unlink=True)
 target=BASE_BOUNDS[key];vs=o.data.vertices
 cut=golf_clubs.SOLE[c]+.37
 head=[v for v in vs if v.co.z<cut]
 bounds=[(min(v.co[i] for v in head),max(v.co[i] for v in head)) for i in range(3)]
 scale=min(1.0,*[(target[i][1]-target[i][0])/max(1e-6,bounds[i][1]-bounds[i][0]) for i in [0,1]])
 source_center=[(a+b)/2 for a,b in bounds];target_center=[(a+b)/2 for a,b in target]
 bottom=min(v.co.z for v in vs)
 for v in vs:
  original=v.co.copy();z=original.z
  if z<-.16001:
   w=max(0,min(1,(-.16-z)/max(.01,-.16-cut)));w=w*w*(3-2*w)
   mapped=Vector((target_center[0]+(original.x-source_center[0])*scale,
                  target_center[1]+(original.y-source_center[1])*scale,
                  target[2][0]+(z-bottom)*scale))
   v.co=original.lerp(mapped,w)
  # The original grip establishes the top. No skin may extend beyond the original envelope.
  for i in range(3):v.co[i]=max(target[i][0],min(target[i][1],v.co[i]))
 o.data.update()

def export_json(o,style,c):
 me=o.data;me.calc_loop_triangles();pos=[];norm=[];uv=[];groups=[[] for _ in me.materials]
 def native(v):return [round(v.x,6),round(v.z,6),round(-v.y,6)]
 # Existing primitive UVs; joined parts retain per-part material and UV identity.
 for tri in me.loop_triangles:
  for li in tri.loops:
   ix=len(pos)//3;pos.extend(native(me.vertices[me.loops[li].vertex_index].co));norm.extend(native(me.corner_normals[li].vector));groups[tri.material_index].append(ix)
   uv.extend(list(me.uv_layers.active.data[li].uv) if me.uv_layers.active else [0,0])
 mats=[]
 for m,idx in zip(me.materials,groups):
  mats.append(dict(name=m.name,color=list(m['colour']),metallic=m['metal'],roughness=m['rough'],texture=m['texture'],indices=idx))
 x=dict(id=style+'_'+c,positions=pos,normals=norm,uvs=uv,materials=mats,soleY=golf_clubs.SOLE[c],loftDegrees=golf_clubs.LOFT[c])
 (NATIVE/f'NativeGolfEquipment_{style}_{c}.json').write_text(json.dumps(x,separators=(',',':')))
 return len(pos)//9
report=[]
for style in styles:
 clear()
 for c in golf_clubs.CLUBS:
  o=build(style,c);report.append(dict(style=style,club=c,triangles=export_json(o,style,c)))
 # Editable canonical source, before lie preparation and bind conversion.
 bpy.ops.wm.save_as_mainfile(filepath=str(WORK/(style+'.blend')),compress=True)
 for sex,tag in [('Male','m'),('Female','f')]:
  clear();bpy.ops.import_scene.fbx(filepath=str(ROOT/f'Unity/Assets/Resources/Hero/golfer_{tag}.fbx'))
  rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.data.pose_position='REST'
  for o in list(bpy.data.objects):
   if o!=rig:bpy.data.objects.remove(o,do_unlink=True)
  objects=[rig];rest=rig.data.bones['Club'].matrix_local.copy()
  for c in golf_clubs.CLUBS:
   o=build(style,c)
   if style in ['hockey','candy']:golf_swing.prepare_club_mesh(o,golf_swing.LIE[c])
   else:
    # Same authored handedness conversion as the original club, without bending the solid barrel/animal.
    import bmesh
    for vertex in o.data.vertices:vertex.co.y=-vertex.co.y
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
   fit_to_original(o,c,prepared=True);o.data.transform(rest);o.parent=rig;o.matrix_parent_inverse=Matrix.Identity(4)
   o.vertex_groups.new(name='Club').add(list(range(len(o.data.vertices))),1,'REPLACE');o.modifiers.new('Club bind','ARMATURE').object=rig;objects.append(o)
  bpy.ops.object.select_all(action='DESELECT')
  for o in objects:o.select_set(True)
  bpy.context.view_layer.objects.active=rig;d=OUT/style;d.mkdir(exist_ok=True)
  bpy.ops.export_scene.fbx(filepath=str(d/(sex+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,armature_nodetype='NULL',bake_anim=False,path_mode='AUTO')
catalog=[]
for m in [navy,cream,mint,wood,chrome,pink,purple,red,gold,lime,ice,ice_light,yellow,black,cyan,pink_back,violet_metal,ice_mid,ice_dark,stripe,grip_white,grip_violet,grip_amber,grip_mint]:
 catalog.append(dict(name=m.name,color=list(m['colour']),roughness=m['rough'],metallic=m['metal'],texture=m['texture']))
(ROOT/'Unity/Assets/Resources/Cosmetics/materials.json').write_text(json.dumps(dict(materials=catalog),indent=2))
(WORK/'base-size-contract.json').write_text(json.dumps(BASE_BOUNDS,indent=2))
report_path=WORK/'geometry-report.json'
old_report=json.loads(report_path.read_text()) if report_path.exists() else []
report=[r for r in old_report if r['style'] not in styles]+report
report_path.write_text(json.dumps(report,indent=2));print('PARTY_EQUIPMENT_DONE',report)
