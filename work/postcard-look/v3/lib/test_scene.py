"""Goal15 library fixture. Actual generated geometry, fixed inherited gates.
Blender previews are shape/UV evidence; Unity must repeat colour/caps/mowing.
All outputs are local v3/lib; only export_look_fbx LINEAR writes fixtures.
"""
import os, sys, json, math, types
sys.dont_write_bytecode=True
import numpy as np
import bpy
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, ROOT+'/blender/scripts')
import postcard_lib as P
import postcard_look_lib as L
import postcard_props_lib as PL
import golf_look_textures as T
OUT=ROOT+'/work/postcard-look/v3/lib'
RESULT={'kind':'Blender actual-generator fixture; Game view unverified','gates':[],'renders':[]}

def gate(name,ok,detail):
    row=dict(name=name,ok=bool(ok),detail=detail)
    RESULT['gates'].append(row)
    print('GATE:',name,'PASS' if ok else 'FAIL',detail,flush=True)

def fresh(tag):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    PL._COUNTERS.clear();PL.reset_scatter(None)
    D=P.start('hole08_design',out_dir=OUT+'/'+tag)
    L.look_materials(D)
    sc=bpy.context.scene
    sc.render.engine='BLENDER_EEVEE'
    sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
    sc.render.film_transparent=True
    sc.view_settings.view_transform='Standard'
    if sc.world is None:sc.world=bpy.data.worlds.new('REF_WORLD')
    sc.world.use_nodes=True
    sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.30,.35,.4,1)
    sc.world.node_tree.nodes['Background'].inputs[1].default_value=.40
    light=bpy.data.lights.new('REF_KEY','SUN');light.energy=1.6
    ob=bpy.data.objects.new('REF_KEY',light);sc.collection.objects.link(ob)
    ob.rotation_euler=(math.radians(40),0,math.radians(-30))
    return D

def render(tag,loc,target):
    sc=bpy.context.scene
    cam=bpy.data.objects.new('REF_CAM',bpy.data.cameras.new('REF_CAM'))
    sc.collection.objects.link(cam);cam.location=loc
    cam.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    cam.data.lens=48;cam.data.clip_end=6000;sc.camera=cam
    path=OUT+'/'+tag+'.png';sc.render.filepath=path
    bpy.ops.render.render(write_still=True)
    # Read the written PNG bytes exactly. The decoder sets Non-Color so these
    # values match the proof's PNG samples, without a second gamma conversion.
    px=T.read_png(path)
    rgb=px[:,:,:3]
    mask=px[:,:,3]>250
    RESULT['renders'].append(path)
    bpy.data.objects.remove(cam,do_unlink=True)
    return rgb,mask

# Independent decoded texture bands; normal/sheens are recorded separately.
for nm,K,cap in [('Fairway',T.BAND_P['fw_K'],.12),('Green',T.BAND_P['gr_K'],.08)]:
    a=T.read_png(ROOT+'/Unity/Assets/Resources/Course/Look/'+nm+'_C.png').astype(float)/255
    y=T.lum(a[:,:,:3]);p=(np.arange(y.shape[1])+.5)/y.shape[1]*K%1
    light=float(y[:,np.minimum(p,1-p)<.12].mean());dark=float(y[:,np.abs(p-.5)<.12].mean())
    gap=(light-dark)/light
    gate('MOW_BAND_CONTRAST_TEXTURE_'+nm,gap<=cap,dict(light=light,dark=dark,gap=gap,cap=cap,game_view='UNVERIFIED'))

# Library plant data and fixture export: colours/caps measured per real mesh.
D=fresh('plants')
plant_rows=[]
for i,k in enumerate(sorted(PL.PLANT_KINDS)):
    ob=PL.place(D,k,(i*3,0,6),0,1,allow_low=True)
    sw=PL.mesh_sway(ob.data);cls=sw['cls'];R,G=sw['R'],sw['G']
    V=PL._np_mesh(ob.data)[0]
    if cls=='vine':root=V[:,2]>=-.03
    elif cls=='agave':root=np.linalg.norm(V-np.array([0,0,.04]),axis=1)<=.06
    else:root=V[:,2]<=.02
    cap=PL.SWAY_CAP_YD[cls]
    row=dict(kind=k,root=float(R[root].max()),tip=float(R.max()),cap=cap,max_yards=float(R.max()*.06),phase_range=[float(G.min()),float(G.max())])
    plant_rows.append(row)
gate('PLANT_SWAY_COLORS',all(x['root']<=.05 and x['tip']>=PL.SWAY_TIP_MIN[PL.sway_class(x['kind'])] and x['phase_range'][1]>x['phase_range'][0] for x in plant_rows),plant_rows)
gate('PLANT_SWAY_CAPS_AUTHORING',all(x['max_yards']<=x['cap'] for x in plant_rows),dict(rows=plant_rows,model='R x fixed .06yd full wind; Unity GPU check required'))
L.export_look_fbx(D,OUT+'/plants_fixture.fbx',colors_type='LINEAR')

# One genuinely generated sea needle, three azimuths.
D=fresh('needle')
res=PL.build_needle(D,(0,0,0),18,4.5,seed=3,surf=True)
o=res['needle']
co,tris,_=PL._np_mesh(o.data)
widths=[]
for z in np.linspace(0,1.8,17):
    sec=PL.mesh_section(co,tris,z)[:,:2]
    if len(sec):
        # All azimuth widths, rather than only axis-aligned bounds.
        widths.extend(float(np.ptp(sec@np.array([math.cos(a),math.sin(a)]))) for a in np.linspace(0,math.pi,36,endpoint=False))
bw=max(widths);hr=float(co[:,2].max())/bw
shape=PL.rock_shape_report(o.data);taper=PL.seastack_report(o.data)
gate('NEEDLE_HEIGHT_BASE',hr>=3,dict(height=float(co[:,2].max()),base_width=bw,ratio=hr,shape_factor=o['lk_v3_shape_factor']))
gate('NEEDLE_ROCK_SHAPE',shape['ok'],shape)
gate('NEEDLE_TAPERED',taper['ok'],taper)
L.export_look_fbx(D,OUT+'/needle_fixture.fbx')
for az in (0,120,240):
    a=math.radians(az)
    render('needle_az'+str(az),(math.sin(a)*43,-math.cos(a)*43,15),(0,0,8))

# Actual column generator with its own UVs. Pixel gates reuse exact proof code.
D=fresh('basalt')
obs=PL.build_column_wall(D,[(-11,0),(-4,.3),(3,-.2),(11,.1)],[15,18,16,19],-.6,seed=5)
cols=[c for o in obs for c in json.loads(o['lk_v3_columns'])]
gate('COLUMN_WIDTH_SIDES',all(.6<=c['width']<=1.8 and c['sides'] in (5,6) for c in cols),dict(columns=len(cols),width_min=min(c['width'] for c in cols),width_max=max(c['width'] for c in cols),chipped=sum(c['chipped'] for c in cols),distinct_tops=len({round(c['top'],2) for c in cols})))
L.export_look_fbx(D,OUT+'/basalt_fixture.fbx')
# All funcs/thresholds unchanged; this adapter does not use PIL file loading.
proof={ '__name__':'library_pixel_measure', '__file__':ROOT+'/work/postcard-look/v2/proof/measure.py' }
source=open(proof['__file__']).read().replace('from PIL import Image','')
exec(compile(source,proof['__file__'],'exec'),proof)
metrics=[]
for az in (0,35,-35):
    a=math.radians(az)
    rgb,mask=render('basalt_az'+str(az),(math.sin(a)*38,-math.cos(a)*38,12),(0,0,8))
    sh=types.SimpleNamespace(px=rgb,idmask=lambda cat,m=mask:m)
    stat=proof['basalt_metrics'](sh)
    metrics.append(stat)
    np.save(OUT+'/basalt_az'+str(az)+'_rgb.npy',rgb)
    np.save(OUT+'/basalt_az'+str(az)+'_mask.npy',mask)
sk=sum(x.get('glow_skeleton_px',0) for x in metrics if x)
j=sum(x.get('glow_junction_clusters',0) for x in metrics if x)
RESULT['basalt_metrics']=metrics
gate('BASALT_JOINTS',all(x and proof['basalt_shot_ok'](x) for x in metrics) and proof['basalt_network_ok'](sk,j),dict(shots=metrics,skeleton_pixels=sk,junctions=j,junctions_per100=100*j/max(sk,1),renderer='Blender EEVEE actual geometry; Unity Game view pending'))

# Needle cliff section: frozen terrain then the shared function, three views.
D=fresh('cliff')
P.build_terrain(D);P.build_play_surfaces(D)
snap=L.snapshot_ground(D)
L.retarget_materials(D)
skins=L.build_postcard_cliff(D,'needle',seed=2)
L.assign_uvs(D)
gate('CLIFF_SCORING_UNCHANGED',L.compare_ground(D,snap)[0],L.compare_ground(D,snap)[1])
outline_rows=[]
for entry in D.__dict__.get('postcard_outline',[]):
    xy=np.asarray(entry['xy']);n=len(xy)
    seg=np.linalg.norm(np.roll(xy,-1,axis=0)-xy,axis=1)
    longest=0.0
    # A straight run means the intervening outline remains within10cm of
    # its chord. Test every start, including runs crossing the loop seam.
    for start in range(n):
        chain=[];run=0.0
        for count in range(1,min(n,100)):
            end=(start+count)%n;chain.append(xy[end]);run+=seg[(end-1)%n]
            if count>1:
                delta=xy[end]-xy[start];d=float(np.linalg.norm(delta))
                if d<1e-8:break
                mid=np.asarray(chain)-xy[start]
                dev=np.abs(mid[:,0]*delta[1]-mid[:,1]*delta[0])/d
                if dev.max()>.10:break
            longest=max(longest,run)
    outline_rows.append(dict(loop=entry['loop'],points=n,max_straight_run_m=longest))
gate('CLIFF_OUTLINE_RUN',bool(outline_rows) and all(x['max_straight_run_m']<=4.0 for x in outline_rows),dict(rows=outline_rows,chord_deviation_m=.10,limit_m=4.0))
RESULT['cliff_outline']=D.__dict__.get('postcard_outline',[])
L.export_look_fbx(D,OUT+'/cliff_fixture.fbx')
keep_for_layout=skins[0]
keep_for_layout_name=keep_for_layout.name
layout_W=np.array([(keep_for_layout.matrix_world@v.co)[:] for v in keep_for_layout.data.vertices])
layout_cen=(layout_W.min(0)+layout_W.max(0))/2
layout_span=float(np.ptp(layout_W,axis=0).max())
# Isolate the first actual chunk to make the bedding/overhangs inspectable.
keep=skins[0]
for ob in bpy.data.objects:
    if ob.type=='MESH' and ob is not keep:ob.hide_render=True
W=np.array([(keep.matrix_world@v.co)[:] for v in keep.data.vertices])
mn,mx=W.min(0),W.max(0);cen=(mn+mx)/2
span=max(mx[0]-mn[0],mx[1]-mn[1],mx[2]-mn[2])
for az in (0,120,240):
    a=math.radians(az)
    render('cliff_az'+str(az),cen+np.array([math.sin(a)*span*1.8,-math.cos(a)*span*1.8,span*.65]),cen)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/cliff_fixture.blend')
with open(OUT+'/test_scene.json','w') as f:json.dump(RESULT,f,indent=2,default=lambda v:v.tolist() if hasattr(v,'tolist') else str(v))

# One combined export for a native Unity fixture: original-sized generated
# needle, columns, one cliff chunk, and two grass swatches. No course file writes.
D=fresh('unity_fixture')
PL.build_needle(D,(-34,0,0),18,4.5,seed=3,surf=True)
PL.build_column_wall(D,[(-11,0),(-4,.3),(3,-.2),(11,.1)],[15,18,16,19],-.6,seed=5)
with bpy.data.libraries.load(OUT+'/cliff_fixture.blend',link=False) as (fr,to):
    to.objects=[keep_for_layout_name]
chunk=to.objects[0]
PL._collection_for('ROCK_').objects.link(chunk)
chunk.parent=P.get_root()
chunk.location+=Vector(np.array([34,0,8])-layout_cen)
for index,(name,mat) in enumerate([('FAIRWAY','LK_FAIRWAY'),('GREEN','LK_GREEN')]):
    me=bpy.data.meshes.new(name+'_FIXTURE')
    x=-18 if index==0 else 18
    me.from_pydata([(x-14,-45,0),(x+14,-45,0),(x+14,-15,0),(x-14,-15,0)],[],[(0,1,2,3)])
    me.materials.append(bpy.data.materials[mat]);uv=me.uv_layers.new(name='UVMap')
    for li,co in enumerate(((0,0),(2,0),(2,2),(0,2))):uv.data[li].uv=co
    ob=bpy.data.objects.new(name,me);bpy.data.collections['COURSE'].objects.link(ob);ob.parent=P.get_root()
L.export_look_fbx(D,OUT+'/p1_fixture.fbx',colors_type='LINEAR')
layout={'fbx':OUT+'/p1_fixture.fbx','axes':'Blender xyz -> Unity xzy, FBX forward -Z/up Y; inspect imported bounds before captures','cameras_blender':[
    {'name':'basalt_az'+str(az),'location':[math.sin(math.radians(az))*38,-math.cos(math.radians(az))*38,12],'target':[0,0,8],'lens_mm':48,'category':'basalt'} for az in (0,35,-35)]}
layout['cameras_blender'] += [dict(name='needle_az'+str(az),location=[-34+math.sin(math.radians(az))*43,-math.cos(math.radians(az))*43,15],target=[-34,0,8],lens_mm=48,category='needle') for az in (0,120,240)]
layout['cameras_blender'] += [dict(name='cliff_az'+str(az),location=[34+math.sin(math.radians(az))*layout_span*1.8,-math.cos(math.radians(az))*layout_span*1.8,8+layout_span*.65],target=[34,0,8],lens_mm=48,category='cliff') for az in (0,120,240)]
layout['cameras_blender'] += [dict(name=name.lower()+'_lawn',location=[x,-42,32],target=[x,-30,0],lens_mm=48,category='mow') for name,x in [('FAIRWAY',-18),('GREEN',18)]]
with open(OUT+'/fixture_layout_blender.json','w') as f:json.dump(layout,f,indent=2)
def unity_point(a):return [a[0],a[2],a[1]]
shots=[dict(name=s['name'],model='Assets/Editor/PostcardV3Scratch/fixtures/p1_fixture.fbx',hole=10 if s['category']=='basalt' else 8,
            pos=unity_point(s['location']),look=unity_point(s['target']),fov=39.5977527,requireBands=s['category']=='mow') for s in layout['cameras_blender']]
with open(OUT+'/fixture_camera.json','w') as f:json.dump({'shots':shots},f,indent=2)
# Keep fixtures reviewable with raw metadata and explicit FAILs.
with open(OUT+'/test_scene.json','w') as f:json.dump(RESULT,f,indent=2,default=lambda v:v.tolist() if hasattr(v,'tolist') else str(v))
fails=[g['name'] for g in RESULT['gates'] if not g['ok']]
print('SUMMARY testscene',len(RESULT['gates'])-len(fails),'/',len(RESULT['gates']),'PASS; FAIL',fails,flush=True)
sys.stdout.flush();os._exit(1 if fails else 0)
