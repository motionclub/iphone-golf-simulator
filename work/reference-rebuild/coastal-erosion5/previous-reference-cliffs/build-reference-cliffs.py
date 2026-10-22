import bpy,bmesh,json,math,bisect,random
from pathlib import Path
from mathutils import Vector
R=Path.cwd();W=R/'work/reference-rebuild';out=W/'coastal-scan';out.mkdir(exist_ok=True)
ident='coastal_cliff_02'
bpy.ops.wm.open_mainfile(filepath=str(W/'vendor'/ident/(ident+'_2k.blend')))
src=bpy.data.objects[ident+'_LOD3']
bpy.ops.object.select_all(action='DESELECT');src.select_set(True);bpy.context.view_layer.objects.active=src
bm=bmesh.new();bm.from_mesh(src.data);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=.00005);bm.to_mesh(src.data);bm.free()
dec=src.modifiers.new('Game silhouette detail','DECIMATE');dec.ratio=.18
bpy.ops.object.modifier_apply(modifier=dec.name)
template=src.data.copy();template.use_fake_user=True
for img in bpy.data.images:
    if img.source=='FILE':
        p=W/'vendor'/ident/'textures'/Path(img.filepath).name
        if p.exists():img.filepath=str(p);img.reload()
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.import_scene.fbx(filepath=str(R/'Unity/Assets/Resources/Course/hole_12.fbx'),use_anim=False)
scene=bpy.context.scene; originals=list(scene.objects)
rimdata=json.loads((R/'ArtDir/golf/coastal12-cliff-manifest.json').read_text())['turfBoundary']
def warp(y):
    if y<=8 or y>=110:return y
    return 8+(y-8)*6/52 if y<=60 else 14+(y-60)*96/50
def mapped(p):return Vector((p.x,warp(p.y),p.z))
lo=Vector(tuple(min(v.co[k] for v in template.vertices) for k in range(3)))
hi=Vector(tuple(max(v.co[k] for v in template.vertices) for k in range(3)))
envelope=[-1e9]*65
for v in template.vertices:
    i=min(64,int((v.co.x-lo.x)/(hi.x-lo.x)*64));envelope[i]=max(envelope[i],v.co.z)
for i in range(65):
    if envelope[i]<-1e8:envelope[i]=hi.z
created=[]
for island,record in enumerate(rimdata):
    rim=[Vector(p) for p in record['sourceOuterRim']];s=[0.]
    for i,p in enumerate(rim):s.append(s[-1]+(rim[(i+1)%len(rim)]-p).length)
    length=s[-1]
    def sample(t):
        t=t%length;i=min(len(rim)-1,bisect.bisect_right(s,t)-1)
        a,b=rim[i],rim[(i+1)%len(rim)];p=a.lerp(b,(t-s[i])/max(.0001,s[i+1]-s[i]))
        tangent=b-a;tangent.z=0;tangent.normalize()
        return p,Vector((tangent.y,-tangent.x,0))
    count=max(3,round(length/48));span=length/count
    for k in range(count):
        mesh=template.copy();obj=bpy.data.objects.new(f'REFERENCE_CLIFF_{island}_{k:02}',mesh);scene.collection.objects.link(obj)
        for v in mesh.vertices:
            q=v.co.copy();u=(q.x-lo.x)/(hi.x-lo.x)
            p,n=sample((k+u*1.035)*span)
            e=u*64;i=min(63,int(e));top=envelope[i]*(1-(e-i))+envelope[i+1]*(e-i)
            z=min(1,max(0,(q.z-lo.z)/max(.01,top-lo.z)))
            # The scan is allowed to protrude below the crest; the existing turf
            # still owns the playable surface. Every module has a submerged foot.
            depth=(hi.y-q.y)*.52-1.1
            pos=p+n*depth;pos.z=-2+(p.z+1.92)*z
            v.co=mapped(pos)
        for p in mesh.polygons:p.use_smooth=True
        mesh.update();created.append(obj)
    # Recessed opaque backing closes tiny joins behind overlapping natural faces.
    vs=[mapped(p-Vector((0,0,.04))) for p in rim]+[mapped(Vector((p.x,p.y,-2.5))) for p in rim]
    fs=[(i,(i+1)%len(rim),(i+1)%len(rim)+len(rim),i+len(rim)) for i in range(len(rim))]
    m=bpy.data.meshes.new('Reference interior backing');m.from_pydata(vs,[],fs);m.update()
    o=bpy.data.objects.new(f'REFERENCE_CLIFF_CORE_{island}',m);scene.collection.objects.link(o);created.append(o)
anchors=[]
for suffix in ['TEE','PIN','UP']:
    old=bpy.data.objects['MARKER_'+suffix];o=bpy.data.objects.new('COASTAL12_ANCHOR_'+suffix,None);scene.collection.objects.link(o);o.matrix_world=old.matrix_world.copy();o.location=mapped(o.location);anchors.append(o)
for o in originals:o.hide_render=True
bpy.ops.object.select_all(action='DESELECT')
for o in created+anchors:o.select_set(True)
bpy.context.view_layer.objects.active=created[0]
bpy.ops.export_scene.fbx(filepath=str(out/'ReferenceCliffs12.fbx'),use_selection=True,object_types={'MESH','EMPTY'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='STRIP')
scene.use_nodes=False;scene.render.film_transparent=False;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=100
world=bpy.data.worlds.new('Coastal source daylight');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.45,.62,.79,1);world.node_tree.nodes['Background'].inputs[1].default_value=.8
sun=bpy.data.lights.new('Coastal sunlight','SUN');sun.energy=2.4;sun.angle=.07;so=bpy.data.objects.new('Coastal sunlight',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.5)
cam=bpy.data.objects.new('Reference cliff camera',bpy.data.cameras.new('Reference cliff camera'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.lens=44
cam.location=(-75,55,28);target=Vector((0,152,11));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(out/'scanned-cliff-source.png');bpy.ops.render.render(write_still=True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out/'ReferenceCliffs12.blend'))
report={'source':'https://polyhaven.com/a/coastal_cliff_02','author':'Rob Tuytel','license':'CC0','sourceLod':'LOD3 reduced .18','moduleCount':len(created),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in created),'warpMetres':[[8,8],[60,14],[110,110]],'status':'SOURCE PILOT; Unity visual acceptance pending'}
(out/'reference-cliffs-manifest.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
