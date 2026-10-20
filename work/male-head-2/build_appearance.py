"""Actual Blender appearance preview on the saved male body, in a separate file."""
import bpy,bmesh,math,hashlib,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
D=R/'ArtDir/hero/base_lock';O=Path('/Users/adnanyonathan/Documents/Codex/2026-09-30/open-3/outputs/Male_Head_2/appearance');O.mkdir(parents=True,exist_ok=True)
source=D/'blender/HeroBase_Male_Silhouette.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(source)
bpy.ops.wm.open_mainfile(filepath=str(source));body=bpy.data.objects['Body_M'];original=[tuple(v.co) for v in body.data.vertices]
for o in bpy.data.objects:
    if o.type=='EMPTY':o.hide_render=True
bm=bmesh.new();bm.from_mesh(body.data);tree=BVHTree.FromBMesh(bm);bm.free()
def surface(x,z):
    hit,normal,index,dist=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)
    if hit is None:raise ValueError(('Feature missed head',x,z))
    return hit.y
def linear(c):return tuple(((v+.055)/1.055)**2.4 if v>.04045 else v/12.92 for v in c)
def material(name,c,rough=.62):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*linear(c),1)
    n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=m.diffuse_color;n.inputs['Roughness'].default_value=rough;n.inputs['Metallic'].default_value=0;n.inputs['Specular IOR Level'].default_value=.27
    return m
skin=(.77,.54,.38);grey=(.48,.485,.49)
skinmat=material('Preview_Skin',skin);whitemat=material('Preview_Eye_White',(.91,.895,.855),.34)
irismat=material('Preview_Iris_Brown',(.27,.15,.077),.40);pupilmat=material('Preview_Pupil',(.018,.012,.009),.30)
browmat=material('Preview_Brow',(.15,.115,.08),.66);lipmat=material('Preview_Lips',(.66,.435,.335),.63)
seammat=material('Preview_Closed_Smile',(.32,.17,.12),.72);nostrilmat=material('Preview_Nostril',(.27,.155,.103),.75)
bodymat=material('Preview_GreyBody_SkinHead',grey)
nodes=bodymat.node_tree.nodes;links=bodymat.node_tree.links;n=nodes.get('Principled BSDF')
pos=nodes.new('ShaderNodeNewGeometry');xyz=nodes.new('ShaderNodeSeparateXYZ');rng=nodes.new('ShaderNodeMapRange');rng.clamp=True;rng.interpolation_type='SMOOTHSTEP'
rng.inputs['From Min'].default_value=1.401;rng.inputs['From Max'].default_value=1.411
mix=nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(*linear(grey),1);mix.inputs[2].default_value=(*linear(skin),1)
links.new(pos.outputs['Position'],xyz.inputs[0]);links.new(xyz.outputs['Z'],rng.inputs['Value']);links.new(rng.outputs['Result'],mix.inputs[0]);links.new(mix.outputs[0],n.inputs['Base Color'])
n.inputs['Subsurface Weight'].default_value=.025;n.inputs['Subsurface Radius'].default_value=(.012,.006,.003)
body.data.materials.clear();body.data.materials.append(bodymat)
for p in body.data.polygons:p.material_index=0
features=bpy.data.collections.new('Preview_Facial_Features');bpy.context.scene.collection.children.link(features)
def mesh(name,verts,faces,mat):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);features.objects.link(o);me.materials.append(mat)
    b=bmesh.new();b.from_mesh(me);bmesh.ops.recalc_face_normals(b,faces=b.faces);b.to_mesh(me);b.free()
    for f in me.polygons:f.use_smooth=True
    return o
def patch(name,cx,cz,rx,top,bottom,depth,mat,n=48,k=6,almond=False):
    verts=[(cx,depth(cx,cz),cz)];rings=[];faces=[]
    for j in range(1,k+1):
        rho=j/k;ring=[]
        for i in range(n):
            a=math.tau*i/n;si=math.sin(a);x=cx+rho*rx*math.cos(a)
            z=cz+rho*(top if si>=0 else bottom)*si*(abs(si)**.22 if almond else 1)
            ring.append(len(verts));verts.append((x,depth(x,z),z))
        rings.append(ring)
    for i in range(n):faces.append((0,rings[0][i],rings[0][(i+1)%n]))
    for a,b in zip(rings,rings[1:]):
        for i in range(n):faces.append((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
    back=len(verts);verts.append((cx,surface(cx,cz)+.003,cz))
    for i in range(n):faces.append((rings[-1][(i+1)%n],rings[-1][i],back))
    return mesh(name,verts,faces,mat)
def line(name,pts,widths,mat,depth_ratio=.55,n=10):
    verts=[];faces=[];rings=[]
    for i,point in enumerate(pts):
        p=Vector(point);axis=(Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(0,i-1)])).normalized()
        side=axis.cross(Vector((0,1,0))).normalized();out=side.cross(axis).normalized();ring=[]
        for j in range(n):
            a=math.tau*j/n;ring.append(len(verts));verts.append(tuple(p+side*(widths[i]*math.cos(a))+out*(widths[i]*depth_ratio*math.sin(a))))
        rings.append(ring)
    for a,b in zip(rings,rings[1:]):
        for j in range(n):faces.append((a[j],a[(j+1)%n],b[(j+1)%n],b[j]))
    faces.extend([tuple(reversed(rings[0])),tuple(rings[-1])]);return mesh(name,verts,faces,mat)
s=1.7/593;eye_z=(654-102)*s;eye_x=14*s;rx=7.0*s;up=3.7*s;down=2.8*s
def eye_depth(cx,x,z):
    v=((x-cx)/rx)**2+((z-eye_z)/(up if z>=eye_z else down))**2
    return surface(x,z)-.0008-.0026*math.sqrt(max(0,1-v))
for sign in [-1,1]:
    cx=sign*eye_x;side='L' if sign<0 else 'R'
    patch('Sclera_'+side,cx,eye_z,rx,up,down,lambda x,z:eye_depth(cx,x,z),whitemat,almond=True)
    patch('Iris_'+side,cx,eye_z,.0088,.0090,.008,lambda x,z:eye_depth(cx,x,z)-.00035,irismat,n=40,k=4)
    patch('Pupil_'+side,cx,eye_z,.0048,.0050,.0045,lambda x,z:eye_depth(cx,x,z)-.00065,pupilmat,n=32,k=3)
    for upper in [True,False]:
        pts=[];width=[]
        for i in range(41):
            a=math.pi*i/40;x=cx+rx*math.cos(a);h=(up if upper else -down);z=eye_z+h*math.sin(a)**1.22
            pts.append((x,eye_depth(cx,x,z)-.00055,z));width.append(.0003+(.00135 if upper else .0010)*math.sin(a)**.7)
        line(('UpperLid_' if upper else 'LowerLid_')+side,pts,width,skinmat,n=8)
    pts=[];width=[]
    for i in range(41):
        t=-1+2*i/40;x=cx+.025*t;z=eye_z+.023+.005*(1-t*t)+.002*(sign*t)
        pts.append((x,surface(x,z)-.0015,z));width.append(.0004+.0032*math.sin(math.pi*i/40)**.65)
    line('Brow_'+side,pts,width,browmat,n=10)
mouth_z=(654-132.8)*s+.010;mouth_w=.038
for upper in [True,False]:
    pts=[];width=[]
    for i in range(61):
        t=-1+2*i/60;x=mouth_w*t;full=max(0,1-t*t)**.65;smile=.0045*t*t
        cupid=.0005*math.exp(-((abs(t)-.25)/.23)**2)
        z=mouth_z+smile+(.0011*full+cupid if upper else -.0017*full)
        pts.append((x,surface(x,z)-.0012,z));width.append(.0002+(.0011 if upper else .00155)*full)
    line('Upper_Lip' if upper else 'Lower_Lip',pts,width,lipmat,n=8)
pts=[];width=[]
for i in range(61):
    t=-1+2*i/60;x=mouth_w*t;z=mouth_z+.0045*t*t
    pts.append((x,surface(x,z)-.0023,z));width.append(.00015+.00065*math.sin(math.pi*i/60)**.8)
line('Closed_Smile',pts,width,seammat,n=8)
for sign in [-1,1]:
    x=sign*.011;z=(654-122.6)*s+.008
    patch('Nostril_'+str(sign),x,z,.0022,.00125,.0011,lambda x,z:surface(x,z)-.00065,nostrilmat,n=24,k=3)
# The base mesh remains exactly the delivered blockout. Cosmetic surfaces are
# separate, editable geometry. This preview does not replace the silhouette gate.
assert [tuple(v.co) for v in body.data.vertices]==original
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0;scene.view_settings.gamma=1
world=bpy.data.worlds.new('Preview_Studio_World');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.13,.13,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
def area(name,loc,power,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1.45))-o.location).to_track_quat('-Z','Y').to_euler();return o
lights=[area('Preview_Key',(-2.0,-3,3.5),300,3),area('Preview_Fill',(2.5,-2,2),190,3),area('Preview_Rim',(0,2,3),330,2.5)]
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.001));floor=bpy.context.object;floor.name='Preview_Floor';floor.data.materials.append(material('Preview_Floor_Grey',(.34,.345,.35),.8))
data=bpy.data.cameras.new('Preview_Camera');cam=bpy.data.objects.new('Preview_Camera',data);scene.collection.objects.link(cam);cam.data.type='ORTHO';scene.camera=cam
def shot(name,angle,centre,scale,width,height,elevation=0):
    a=math.radians(angle);e=math.radians(elevation);target=Vector((0,-.045,centre));cam.location=target+Vector((math.sin(a)*4*math.cos(e),-math.cos(a)*4*math.cos(e),4*math.sin(e)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.resolution_x=width;scene.render.resolution_y=height;scene.render.resolution_percentage=100;scene.render.filepath=str(O/(name+'.png'))
    turn=mathutils.Quaternion((0,0,1),a)
    for light,loc in zip(lights,[(-2,-3,3.5),(2.5,-2,2),(0,2,3)]):light.location=turn@Vector(loc);light.rotation_euler=(Vector((0,0,1.45))-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.render.render(write_still=True)
import mathutils
for name,a in [('face_front',0),('face_threequarter',45),('face_left',90),('face_back_left',135),('face_back',180),('face_back_right',225),('face_right',270),('face_front_right',315)]:shot(name,a,1.505,.45,1000,1000)
shot('face_top',0,1.505,.45,1000,1000,80)
for name,a in [('body_front',0),('body_back',180),('body_left',90),('body_right',-90),('body_threequarter',35)]:shot(name,a,.84,2.06,800,1100)
# Save separate appearance study and verify the authorized gate source untouched.
bpy.ops.wm.save_as_mainfile(filepath=str(O/'HeroBase_Male_Face_Preview.blend'));assert sha(source)==before
body.data.calc_loop_triangles();report={'source_sha256':before,'source_unchanged':True,'body_vertices_unchanged':True,'body_triangles':len(body.data.loop_triangles),
 'preview_file':str(O/'HeroBase_Male_Face_Preview.blend'),'preview_sha256':sha(O/'HeroBase_Male_Face_Preview.blend'),'hair':False,'stubble':False,'female_work':False,
 'feature_objects':[o.name for o in features.objects],'preview_only':True,'note':'Actual Blender render of the delivered body with skin materials and separate eyes, lids, brows, lips and nostril surfaces. Body/head coordinates unchanged. Not a new silhouette/likeness PASS.'}
(O/'preview-audit.json').write_text(json.dumps(report,indent=2));print('FACE_PREVIEW_COMPLETE',json.dumps(report))
