"""Isolated P4 draft. Never writes Unity or original hero assets.

Run headless with inputs/HeroBase_<Sex>_Dressed.blend open, -- Male|Female.
Final swing deformation, UV bakes, fabric IDs and runtime install await G0.
"""
import bpy, bmesh, hashlib, json, math, sys
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

W = Path(__file__).resolve().parents[1]
SEX = sys.argv[-1]
FEMALE = SEX == 'Female'
rig = bpy.data.objects['Rig_' + SEX]
body = bpy.data.objects['Body_F' if FEMALE else 'Body_M']
sc = bpy.context.scene
if rig.animation_data: rig.animation_data.action = None
rig.data.pose_position = 'REST'
for pb in rig.pose.bones:
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
    pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
bpy.context.view_layer.update()

def mesh_fingerprint(o):
    return hashlib.sha256(repr(([(tuple(v.co), [(g.group, round(g.weight, 8)) for g in v.groups]) for v in o.data.vertices],
                                [tuple(p.vertices) for p in o.data.polygons])).encode()).hexdigest()

before = mesh_fingerprint(body)
bone_before = [(b.name, tuple(b.head_local), tuple(b.tail_local), tuple(map(tuple, b.matrix_local))) for b in rig.data.bones]
kd = KDTree(len(body.data.vertices))
for v in body.data.vertices: kd.insert(v.co, v.index)
kd.balance()
bone_names = {b.name for b in rig.data.bones}
body_groups = {g.index: g.name for g in body.vertex_groups}

def lin(c): return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in c)

def material(name, rgb, rough=.75):
    m = bpy.data.materials.new(name); m.diffuse_color = (*lin(rgb), 1); m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = m.diffuse_color
    bs.inputs['Roughness'].default_value = rough
    return m

mats = {n: material('Golf_' + n, c, s) for n, c, s in [
    ('Main', (.93, .93, .93), .78), ('Bottom', (.065, .069, .077), .83),
    ('Trim', (.035, .035, .04), .85), ('Glove', (.93, .93, .93), .68),
    ('Sole', (.07, .07, .075), .95), ('Buckle', (.72, .73, .74), .52)]}
made = []

def activate(o):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o

def apply(o, mod):
    activate(o); bpy.ops.object.modifier_apply(modifier=mod.name)

def bind(o, rigid=None, keep_weights=False, allowed=None):
    # Bone names, rest matrices and sockets remain unchanged. Up to four influences.
    saved=[{o.vertex_groups[g.group].name:g.weight for g in v.groups
            if o.vertex_groups[g.group].name in bone_names} for v in o.data.vertices] if keep_weights else None
    for vg in list(o.vertex_groups): o.vertex_groups.remove(vg)
    groups = {n: o.vertex_groups.new(name=n) for n in bone_names}
    tree=kd
    if allowed:
        candidates=[v for v in body.data.vertices if sum(g.weight for g in v.groups if body_groups.get(g.group) in allowed)>.35]
        tree=KDTree(len(candidates))
        for v in candidates:tree.insert(v.co,v.index)
        tree.balance()
    for v in o.data.vertices:
        if rigid: weights = {rigid: 1.0}
        elif saved is not None: weights=saved[v.index]
        else:
            weights = {}
            for _, i, dist in tree.find_n(v.co, 3):
                for g in body.data.vertices[i].groups:
                    n = body_groups.get(g.group)
                    if n in bone_names and (not allowed or n in allowed): weights[n] = weights.get(n, 0) + g.weight / max(.0001, dist)**2
        weights = dict(sorted(weights.items(), key=lambda x: x[1], reverse=True)[:4])
        if not weights: weights = {'Hips': 1.0}
        total = sum(weights.values())
        for n, w in weights.items(): groups[n].add([v.index], w / total, 'REPLACE')
    for m in list(o.modifiers):
        if m.type == 'ARMATURE': o.modifiers.remove(m)
    mod = o.modifiers.new('Same match rig', 'ARMATURE'); mod.object = rig
    o.parent = rig
    if o not in made: made.append(o)
    return o

def finish(o, mat, rigid=None, thickness=0, keep_weights=False, allowed=None):
    o.data.materials.clear(); o.data.materials.append(mat)
    if thickness:
        for old in list(o.modifiers):
            if old.type=='ARMATURE':o.modifiers.remove(old)
        mod = o.modifiers.new('Real inward hem thickness', 'SOLIDIFY'); mod.thickness = thickness; mod.offset = -1
        apply(o, mod)
    for p in o.data.polygons: p.use_smooth = True
    return bind(o, rigid, keep_weights, allowed)

def mesh(name, verts, faces, mat, rigid=None, thickness=0, source_indices=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    if source_indices is not None:
        groups={n:o.vertex_groups.new(name=n) for n in bone_names}
        for dst,src in enumerate(source_indices):
            for g in body.data.vertices[src].groups:
                n=body_groups.get(g.group)
                if n in groups:groups[n].add([dst],g.weight,'REPLACE')
    return finish(o, mat, rigid, thickness, keep_weights=source_indices is not None)

def cube(name, centre, scale, mat, rigid=None, bevel=.002):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre); o=bpy.context.object; o.name=name
    o.scale=scale; activate(o); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # Bake placement into the mesh so transfer coordinates are in body-local metres.
    o.data.transform(o.matrix_world); o.matrix_world.identity()
    if bevel:
        mod=o.modifiers.new('Rounded construction edge','BEVEL'); mod.width=bevel; mod.segments=2; apply(o,mod)
    return finish(o,mat,rigid)

def tube(name, points, radius, mat, rigid=None, sides=5):
    verts=[]; faces=[]
    for i,p in enumerate(points):
        p=Vector(p); t=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        if t.length < 1e-8: t=Vector((0,0,1))
        t.normalize(); u=t.cross(Vector((0,0,1)))
        if u.length<.01:u=t.cross(Vector((0,1,0)))
        u.normalize(); v=t.cross(u)
        for j in range(sides): verts.append(tuple(p+radius*(u*math.cos(j*2*math.pi/sides)+v*math.sin(j*2*math.pi/sides))))
    for i in range(len(points)-1):
        for j in range(sides):
            a=i*sides+j; b=i*sides+(j+1)%sides; faces.append((a,b,b+sides,a+sides))
    return mesh(name,verts,faces,mat,rigid)

def copied(o, name, ratio=1):
    new=o.copy();new.data=o.data.copy();sc.collection.objects.link(new);new.name=name
    new.parent=None;new.matrix_world=o.matrix_world.copy()
    for m in list(new.modifiers):new.modifiers.remove(m)
    if ratio<1:
        mod=new.modifiers.new('Draft mesh budget','DECIMATE');mod.ratio=ratio;apply(new,mod)
    return new

def lower_shell(name,hem,waist,ratio=.5,ease=.018):
    # Pelvis vertices include Spine as well as Hips. Excluding Spine removed
    # glute faces from the earlier trousers and left visible skin holes.
    lower={g.index for g in body.vertex_groups if any(x in g.name for x in ['UpperLeg','LowerLeg','Hips','Spine'])}
    keep={v.index for v in body.data.vertices if .04<v.co.z<waist+.07 and abs(v.co.x)<.33 and
          sum(g.weight for g in v.groups if g.group in lower)>.35}
    polys=[p for p in body.data.polygons if all(i in keep for i in p.vertices)]
    used=sorted({i for p in polys for i in p.vertices});remap={i:j for j,i in enumerate(used)}
    verts=[tuple(body.data.vertices[i].co+body.data.vertices[i].normal*ease) for i in used]
    o=mesh(name,verts,[tuple(remap[i] for i in p.vertices) for p in polys],mats['Bottom'],source_indices=used)
    bm=bmesh.new();bm.from_mesh(o.data)
    for z,normal in [(hem,(0,0,1)),(waist,(0,0,-1))]:
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,z),plane_no=normal,clear_inner=True,dist=.00001)
    bm.to_mesh(o.data);bm.free()
    for mod in list(o.modifiers):o.modifiers.remove(mod)
    mod=o.modifiers.new('Garment mesh budget','DECIMATE');mod.ratio=ratio;apply(o,mod)
    return o

def trouser_pockets(o):
    bm=bmesh.new();bm.from_mesh(o.data)
    guides=[]
    for side in [-1,1]:
        a=Vector((side*.115,0,.936));b=Vector((side*.222,0,.818));t=(b-a).normalized()
        n=Vector((-t.z,0,t.x));length=(b-a).length;half=.0035
        for point,normal in [(a,t),(b,-t),(a+n*half,n),(a-n*half,-n)]:
            bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=point,plane_no=normal,dist=.000001)
        cut=[]
        for f in bm.faces:
            c=f.calc_center_median();d=c-a
            if 0<d.dot(t)<length and abs(d.dot(n))<half-.00001 and c.y<-.035:cut.append(f)
        if cut:bmesh.ops.delete(bm,geom=cut,context='FACES')
        points=[]
        for j in range(11):
            p=a.lerp(b,j/10);p.y=front_y(p.z,o,x=p.x);points.append(p)
        guides.append((side,points,n))
    bm.to_mesh(o.data);bm.free();o.data.update()
    # The bag is real inset geometry behind the slit, with two sewn lips.
    for side,points,n in guides:
        vs=[];fs=[]
        for p in points:
            for s in [-1,1]:vs.append(tuple(p+n*(s*.009)+Vector((0,.008,0))))
        for j in range(len(points)-1):fs.append((j*2,j*2+1,j*2+3,j*2+2))
        mesh('Golf_PocketBag_'+str(side),vs,fs,mats['Trim'],thickness=.001)
        for sign in [-1,1]:tube(f'Golf_PocketLip_{side}_{sign}',[tuple(p+n*(sign*.0045)) for p in points],.00065,mats['Bottom'])

# Preserve the source base + face, hide source tennis clothing and racket.
for o in list(bpy.data.objects):
    if o.type=='MESH' and o not in [body, bpy.data.objects.get('Face_F' if FEMALE else 'Face_M'), bpy.data.objects.get('Hair_F')]:
        o.hide_render=True

# Resume from the construction contract released by 29, retaining the frozen body/rig.
# Appending a garment mesh never imports or changes the source rig.
cloth_source=W.parents[1]/f'work/cloth-overhaul/export/Cloth_{SEX}.blend'
before_append=set(bpy.data.objects)
with bpy.data.libraries.load(str(cloth_source),link=False) as (src,dst):
    dst.objects=['Kit_Top']
source_top=dst.objects[0]
sc.collection.objects.link(source_top)
source_top.name='Golf_PostClothTopSource';source_top.hide_render=True
polo=copied(source_top,'Golf_Polo',1)
for loaded in list(bpy.data.objects):
    if loaded not in before_append and loaded!=polo:bpy.data.objects.remove(loaded,do_unlink=True)
for v in polo.data.vertices:
    # Added ease across torso and sleeves, with a longer rear tail.
    # The source is already a closed shell. Move its inner and outer walls in
    # the SAME outward body direction, preserving existing thickness.
    _,near,_=kd.find(v.co)
    v.co += body.data.vertices[near].normal*.004
    if abs(v.co.x)<.19 and v.co.z<1.32:
        v.co.x*=1.035; v.co.y*=1.06
        if v.co.z<1.015 and v.co.y>0: v.co.z-=.018
bm=bmesh.new();bm.from_mesh(polo.data)
zmin=min(v.co.z for v in bm.verts)
cut=[f for f in bm.faces if abs(f.calc_center_median().x)>.155 and abs(f.calc_center_median().y)<.018 and f.calc_center_median().z<zmin+.055]
if cut:bmesh.ops.delete(bm,geom=cut,context='FACES')
bm.to_mesh(polo.data);bm.free()
finish(polo,mats['Main'],keep_weights=True)

# The final 29 top already contains three buttons and its continuous placket.
# Reuse that construction instead of stacking separate boxes over it.
def front_y(z, o=polo, x=0):
    vs=[v for v in o.data.vertices if abs(v.co.x-x)<.04 and abs(v.co.z-z)<.04]
    return min([v.co.y for v in vs] or [-.14])-.003

if FEMALE:
    sys.path.insert(0,str(W/'scripts'))
    from garment_fit import hip_envelope,support_ring,skirt_weights
    cloud,env=hip_envelope(rig,body,W/'export/Golf_Female_SwingProof.blend')
    rings=[];verts=[];faces=[];ns=64
    skirt_z=[.995,.97,.94,.91,.87,.83,.79,.75,.71,.67]
    for j,z in enumerate(skirt_z):
        t=j/(len(skirt_z)-1)
        points,count=support_ring(cloud,z,ns=ns,margin=.008+.014*t*t)
        depth=.008*t*t
        for i in range(ns):
            # Four vertices form each folded pleat; both ridges and recessed
            # return folds are actual geometry, with a flat fitted waistband.
            fold=1 if i%4 in [2,3] else 0
            p=Vector((float(points[i,0]),float(points[i,1]),0));direction=p.normalized()
            p-=direction*(depth*fold)
            verts.append((p.x,p.y,z))
        rings.append(dict(z=z,width_m=float(points[:,0].max()-points[:,0].min()),depth_m=float(points[:,1].max()-points[:,1].min()),body_samples=count,fold_depth_m=depth))
    for j in range(len(skirt_z)-1):
        for i in range(ns):faces.append(((j+1)*ns+i,(j+1)*ns+(i+1)%ns,j*ns+(i+1)%ns,j*ns+i))
    bottom=mesh('Golf_PleatedSkort',verts,faces,mats['Bottom'],thickness=.002)
    # Use the body's actual pelvis/thigh weight field. A generic leg blend
    # over-rotated the hem and required an unacceptable oversized envelope.
    lower_ids={g.index for g in body.vertex_groups if any(n in g.name for n in ['Hips','Spine','UpperLeg','LowerLeg'])}
    candidates=[v for v in body.data.vertices if v.co.z<1.07 and abs(v.co.x)<.33 and sum(g.weight for g in v.groups if g.group in lower_ids)>.35]
    tree=KDTree(len(candidates))
    for v in candidates:tree.insert(v.co,v.index)
    tree.balance()
    for group in list(bottom.vertex_groups):bottom.vertex_groups.remove(group)
    groups={n:bottom.vertex_groups.new(name=n) for n in bone_names}
    for v in bottom.data.vertices:
        ws=skirt_weights(v.co.x,v.co.z)
        ws=dict(sorted(ws.items(),key=lambda x:x[1],reverse=True)[:4]);total=sum(ws.values())
        for n,w in ws.items():groups[n].add([v.index],w/total,'REPLACE')
    for p in bottom.data.polygons:p.use_smooth=True
    inner=lower_shell('Golf_InnerShorts',.705,.99,ratio=.32,ease=.012)
    finish(inner,mats['Bottom'],thickness=.0018,keep_weights=True)
    env['rings']=rings;env['status']='geometric pose envelope; not a full collision PASS'
    (W/'data/skirt_envelope_Female.json').write_text(json.dumps(env,indent=2)+'\n')
else:
    bottom=lower_shell('Golf_Trousers',.115,.975,ratio=.55,ease=.020)
    # Flatten the turned hem before solidifying; preserve a restrained front break.
    for v in bottom.data.vertices:
        if v.co.z<.145:
            t=max(0,min(1,(.145-v.co.z)/.03))
            v.co.z=(1-t)*v.co.z+t*(.118-.004*max(0,min(1,-v.co.y/.15)))
    # The pressed crease is a ridge in the trouser surface, not a floating tube.
    for v in bottom.data.vertices:
        if .14<v.co.z<.87:
            side='Left' if v.co.x>0 else 'Right'
            bone=rig.data.bones[side+('UpperLeg' if v.co.z>.48 else 'LowerLeg')]
            t=max(0,min(1,(v.co.z-bone.tail_local.z)/(bone.head_local.z-bone.tail_local.z)))
            x=bone.tail_local.x*(1-t)+bone.head_local.x*t
            if abs(v.co.x-x)<.015 and v.co.y<-.015:
                v.co.y-=.0022*(1-abs(v.co.x-x)/.015)
    trouser_pockets(bottom)
    # Keep shape soft while creating real cuff/waist rims.
    # Source vertex lineage keeps pelvis/Spine blends instead of discarding
    # them through a nearest-body filter at the waist.
    finish(bottom,mats['Bottom'],thickness=.0022,keep_weights=True)

# Belt, five loops, and an actual frame-shaped buckle. White/black default, logo-free.
waist=.985 if FEMALE else .968
ring=[v.co for v in bottom.data.vertices if waist-.052<v.co.z<waist+.005]
rx=max(abs(v.x) for v in ring)+.004
cy=(min(v.y for v in ring)+max(v.y for v in ring))/2
ry=(max(v.y for v in ring)-min(v.y for v in ring))/2+.004
verts=[];faces=[];ns=64
for z in [waist-.035,waist]:
    for i in range(ns):
        a=i*2*math.pi/ns;verts.append((rx*math.cos(a),cy+ry*math.sin(a),z))
for i in range(ns):faces.append((i,(i+1)%ns,(i+1)%ns+ns,i+ns))
mesh('Golf_Belt',verts,faces,mats['Trim'],'Hips',.002)
for i,a in enumerate([-.9,-2.24,.1,3.04,math.pi/2]):
    tube(f'Golf_BeltLoop_{i}',[(rx*math.cos(a),cy+ry*math.sin(a),waist-.042),(rx*math.cos(a),cy+ry*math.sin(a),waist+.008)],.005,mats['Bottom'],'Hips')
yb=cy-ry-.006;zb=waist-.018
for n,c,s in [('Top',(0,yb,zb+.013),(.038,.005,.004)),('Bottom',(0,yb,zb-.013),(.038,.005,.004)),('Left',(-.017,yb,zb),(.004,.005,.028)),('Right',(.017,yb,zb),(.004,.005,.028)),('Tongue',(0,yb,zb),(.003,.005,.028))]:
    cube('Golf_Buckle_'+n,c,s,mats['Buckle'],'Hips',.001)

for side in ['L','R']:
    o=copied(bpy.data.objects['Kit_Shoe_'+side],'Golf_Shoe_'+side,.38)
    centre_x=sum(v.co.x for v in o.data.vertices)/len(o.data.vertices)
    for v in o.data.vertices:
        v.co.x=centre_x+(v.co.x-centre_x)*.91
    # Existing shoe outline retained. The saddle is a cut overlay, not a jagged
    # selection of whole triangles crossing an arbitrary material boundary.
    oldmi=[p.material_index for p in o.data.polygons]
    o.data.materials.clear()
    for m in [mats['Main'],mats['Sole'],mats['Trim']]:o.data.materials.append(m)
    for p,mi in zip(o.data.polygons,oldmi):
        p.material_index=1 if mi else 0
    bind(o,keep_weights=True)
    saddle=copied(o,'Golf_SaddlePanel_'+side)
    bm=bmesh.new();bm.from_mesh(saddle.data)
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=0],context='FACES')
    if FEMALE:
        # The saddle is a narrow side accent; the tongue stays light.
        bmesh.ops.delete(bm,geom=[f for f in bm.faces if abs(f.calc_center_median().x-centre_x)<.029],context='FACES')
    for point,normal in [((0,-.075,0),(0,1,0)),((0,.02,0),(0,-1,0)),((0,0,.063),(0,0,1))]:
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=point,plane_no=normal,clear_inner=True,dist=.00001)
    loose=[v for v in bm.verts if not v.link_faces]
    if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
    bm.normal_update();bm.to_mesh(saddle.data);bm.free();saddle.data.update()
    for v in saddle.data.vertices:v.co+=v.normal*.0015
    finish(saddle,mats['Trim'],thickness=.0008,keep_weights=True)
    centre=sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
    for j in range(3):
        for k in range(5):
            cube(f'Golf_Nub_{side}_{j}_{k}',(centre.x+(j-1)*.034,centre.y+(k-2)*.047,-.029 if not FEMALE else -.024),(.014,.016,.008),mats['Sole'],'LeftFoot' if side=='L' else 'RightFoot',.001)

# Gloves duplicate the actual weighted hand surface, including all finger joints.
for side in ['Left','Right']:
    groups={g.index for g in body.vertex_groups if g.name.startswith(side) and ('Hand' in g.name or 'LowerArm' in g.name or any(x in g.name for x in ['Thumb','Index','Middle','Ring','Little']))}
    hb=rig.data.bones[side+'Hand'];axis=(hb.tail_local-hb.head_local).normalized();wrist=hb.head_local-axis*.025
    keep={v.index for v in body.data.vertices if (v.co-hb.head_local).dot(axis)>-.08 and sum(g.weight for g in v.groups if g.group in groups)>.55}
    polys=[p for p in body.data.polygons if all(i in keep for i in p.vertices)]
    used=sorted({i for p in polys for i in p.vertices});remap={i:j for j,i in enumerate(used)}
    o=mesh('Golf_Glove_'+side,[tuple(body.data.vertices[i].co+body.data.vertices[i].normal*.0028) for i in used],[tuple(remap[i] for i in p.vertices) for p in polys],mats['Glove'],source_indices=used)
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=wrist,plane_no=axis,clear_inner=True,dist=.000001)
    loose=[v for v in bm.verts if not v.link_faces]
    if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
    bm.to_mesh(o.data);bm.free();o.data.update()
    finish(o,mats['Glove'],thickness=.0007,keep_weights=True)
    # Exact source weights follow each finger; no nearest-neighbour finger mixing.
    o.hide_render=side=='Right'

# Head accessories are rigidly weighted to Head; no new bone or socket.
headgroups={g.index for g in body.vertex_groups if g.name=='Head'}
hp=[v.co for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in headgroups)>.7]
if not hp:hp=[v.co for v in body.data.vertices if v.co.z>1.48]
zmax=max(v.z for v in hp);yc=(min(v.y for v in hp)+max(v.y for v in hp))/2
rx=max(abs(v.x) for v in hp)+.011;ry=(max(v.y for v in hp)-min(v.y for v in hp))/2+.014
if FEMALE:
    hair=bpy.data.objects.get('Hair_F')
    if hair:
        hair.hide_render=False
band=zmax-.087;verts=[];faces=[];ns=60;nr=3 if FEMALE else 9
head_trees=[]
if FEMALE:
    for surface in [body,bpy.data.objects.get('Hair_F')]:
        if surface:
            surface.data.calc_loop_triangles()
            head_trees.append(BVHTree.FromPolygons([tuple(v.co) for v in surface.data.vertices],
                [tuple(t.vertices) for t in surface.data.loop_triangles],all_triangles=True))
for j in range(nr):
    t=j/(nr-1)
    f=1 if FEMALE else max(.02,math.cos(t*math.pi/2))
    z=band+.035*t if FEMALE else band+(zmax-band+.012)*math.sin(t*math.pi/2)
    for i in range(ns):
        a=i*2*math.pi/ns
        if FEMALE:
            direction=Vector((math.cos(a),math.sin(a),0));origin=Vector((0,yc,z))
            hits=[tree.ray_cast(origin,direction,.35)[0] for tree in head_trees]
            hits=[hit for hit in hits if hit is not None]
            radius=max(((hit-origin).length for hit in hits),default=min(rx,ry))+.0012
            p=origin+direction*radius;verts.append(tuple(p))
        else:verts.append((rx*f*math.cos(a),yc+ry*f*math.sin(a),z))
for j in range(nr-1):
    for i in range(ns):faces.append((j*ns+i,j*ns+(i+1)%ns,(j+1)*ns+(i+1)%ns,(j+1)*ns+i))
mesh('Golf_VisorBand' if FEMALE else 'Golf_CapCrown',verts,faces,mats['Trim'],'Head',.0025)
band_ring=verts[:ns]
def brim_start(a):
    if not FEMALE:return rx*math.cos(a),yc+ry*math.sin(a)
    k=(a%(2*math.pi))*ns/(2*math.pi);i=int(k)%ns;t=k-int(k)
    p=Vector(band_ring[i]).lerp(Vector(band_ring[(i+1)%ns]),t)
    return p.x,p.y
verts=[];faces=[]
for j in range(4):
    t=j/3
    for i in range(25):
        a=math.pi+math.pi*i/24
        x,y=brim_start(a)
        verts.append((x+.016*t*math.cos(a),y+.065*t*math.sin(a),band-.012*t-.012*t*math.cos(a)**2))
for j in range(3):
    for i in range(24):a=j*25+i;faces.append((a,a+1,a+26,a+25))
mesh('Golf_CurvedBrim',verts,faces,mats['Trim'],'Head',.003)
for row,t in enumerate([.25,.5,.75,.91]):
    points=[]
    for i in range(40):
        a=math.pi+math.pi*i/39
        x,y=brim_start(a)
        points.append((x+.016*t*math.cos(a),y+.065*t*math.sin(a),band-.012*t-.012*t*math.cos(a)**2+.001))
    tube('Golf_BrimStitch_'+str(row),points,.00065,mats['Buckle'],'Head',3)
if not FEMALE:
    for j in range(6):
        a=j*2*math.pi/6;pts=[]
        for k in range(14):
            t=k/13;f=max(.02,math.cos(t*math.pi/2));z=band+(zmax-band+.012)*math.sin(t*math.pi/2)
            pts.append(((rx+.0008)*f*math.cos(a),yc+(ry+.0008)*f*math.sin(a),z+.0005))
        tube('Golf_CapPanelSeam_'+str(j),pts,.0008,mats['Buckle'],'Head',3)

# UVs are per-garment prototypes. Final bake follows the not-yet-written GARMENT_SPEC.
for o in made:
    o.hide_render = o.name=='Golf_Glove_Right'
    activate(o)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.1,island_margin=.02)
    bpy.ops.object.mode_set(mode='OBJECT')

assert before==mesh_fingerprint(body), 'Body geometry or weights were edited'
assert bone_before==[(b.name, tuple(b.head_local), tuple(b.tail_local), tuple(map(tuple,b.matrix_local))) for b in rig.data.bones], 'Rig changed'
rig.data.pose_position='POSE'
if bpy.data.actions.get('ReadyIdle'):
    rig.animation_data_create();rig.animation_data.action=bpy.data.actions['ReadyIdle']
    if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
sc.frame_set(0)
rows=[]
for o in made:
    o.data.calc_loop_triangles()
    rows.append(dict(name=o.name,tris=len(o.data.loop_triangles),verts=len(o.data.vertices),visible=not o.hide_render,roles=[m.name for m in o.data.materials],max_influences=max((len(v.groups) for v in o.data.vertices),default=0)))
out=W/f'export/Golf_{SEX}_Draft.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
report=dict(sex=SEX,source=str(W/f'inputs/HeroBase_{SEX}_Dressed.blend'),body_unchanged=True,rig_unchanged=True,bones=len(rig.data.bones),new_bones=0,new_sockets=0,pieces=rows,visible_kit_tris=sum(r['tris'] for r in rows if r['visible']),status='DRAFT — G6/G7 not passed; full collision verification and final maps pending')
(W/f'data/build_{SEX}.json').write_text(json.dumps(report,indent=2)+'\n')
print('GOLF_DRAFT',SEX,report['visible_kit_tris'],'tris; body/rig unchanged; NOT a gate pass',flush=True)
