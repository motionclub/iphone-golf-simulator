"""Scratch candidate on actual compact columns, unchanged proof pixel gates."""
import os,sys,json,math,random,types,hashlib
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts')
sys.path.insert(0,ROOT+'/work/postcard-look/v3/hole10/prototypes')
sys.path.insert(0,os.path.dirname(__file__))
import bpy,numpy as np
from mathutils import Vector
import postcard_lib as P
import postcard_look_lib as L
import postcard_props_lib as PL
import hole10_look as H
import golf_look_textures as T
from compact_columns import compact_ring_tile
from paired_columns import author_paired_columns
import postcard_look_verify as V
OUT=os.path.dirname(__file__)+'/attempt1';os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
D=P.start('hole10_design',out_dir=OUT);L.look_materials(D)
candidate=os.path.dirname(os.path.dirname(__file__))+'/bounded_v6_source'
for node in bpy.data.materials['LK_BASALT'].node_tree.nodes:
 if node.type=='TEX_IMAGE' and node.image:
  suffix=os.path.basename(node.image.filepath).split('_')[-1]
  image=bpy.data.images.load(candidate+'/Basalt_'+suffix,check_existing=False)
  image.colorspace_settings.name='Non-Color' if suffix=='N.png' else 'sRGB'
  node.image=image
E=T.read_png(candidate+'/Basalt_E.png')[:,:,:3]
rng=np.random.default_rng(1010);r=rng.random((96,2));q=np.sqrt(r[:,0])
H._UV_GLOW_CACHE.update(G=np.flipud(E.max(2)/255>.2),w=E.shape[1],h=E.shape[0],bary=np.c_[1-q,q*(1-r[:,1]),q*r[:,1]])
obs=[];counts=[];stats=[]
for index in range(3):
 x=-14.0625+index*9.375
 res=compact_ring_tile(D,[(x,0),(x+9.375,0)],(15+index,18-index),bottom_z=-.6,rows=3,seed=5+index,name='ROCK_WALL_P7_%02d'%index)
 ob=res['object'];obs.append(ob)
 stats.append(H.author_uv(ob.data,random.Random(707+index),uf=.62,vf=.36,p_glow=.30))
 counts.append(dict(vertices=len(ob.data.vertices),faces=len(ob.data.polygons),triangles=sum(len(p.vertices)-2 for p in ob.data.polygons),columns=len(res['columns']),span=res['horizontal_span']))
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE'
sc.render.resolution_x=900;sc.render.resolution_y=1600;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=True
sc.view_settings.view_transform='Standard'
sc.world=bpy.data.worlds.new('REF_WORLD');sc.world.use_nodes=True
sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.30,.35,.4,1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value=.40
light=bpy.data.lights.new('REF_KEY','SUN');light.energy=1.6
ob=bpy.data.objects.new('REF_KEY',light);sc.collection.objects.link(ob);ob.rotation_euler=(math.radians(40),0,math.radians(-30))
proof={'__name__':'scratch_library_pixels','__file__':ROOT+'/work/postcard-look/v2/proof/measure.py'}
source=open(proof['__file__']).read().replace('from PIL import Image','')
exec(compile(source,proof['__file__'],'exec'),proof)

# Keep the exact original scoring meshes as hidden UV controls. They are not
# changed or used to pad scenery presence; original full presence gates still
# report this three-tile fixture as too small.
STAGE=ROOT+'/work/postcard-look/v3/hole10/stage/hole_10.blend'
with bpy.data.libraries.load(STAGE,link=False) as (fr,to):
    to.objects=[n for n in fr.objects if n.startswith(V.COLL_PREFIXES)]
controls=[]
for control in to.objects:
    sc.collection.objects.link(control);control.hide_render=True
    for slot in control.material_slots:
        if slot.material:
            base=slot.material.name.rsplit('.',1)[0] if slot.material.name.rsplit('.',1)[-1].isdigit() else slot.material.name
            if base in bpy.data.materials:slot.material=bpy.data.materials[base]
    controls.append(control)
def mesh_hash(ob,uv=False):
    h=hashlib.sha256()
    h.update(np.array([tuple(v.co) for v in ob.data.vertices],np.float32).tobytes())
    h.update(str([tuple(p.vertices) for p in ob.data.polygons]).encode())
    h.update(str([p.material_index for p in ob.data.polygons]).encode())
    if uv:h.update(np.array([tuple(v.uv) for v in ob.data.uv_layers.active.data],np.float32).tobytes())
    return h.hexdigest()
geo_before={ob.name:mesh_hash(ob) for ob in obs}
controls_before={ob.name:mesh_hash(ob,True) for ob in controls}
local_src=open(ROOT+'/work/postcard-look/v2/hole10/tools/stage_gates.py').read()
local_src=local_src[:local_src.index('\nif opt("--blend"):')]
SG={'__name__':'scratch_paired_stage_gates','__file__':ROOT+'/work/postcard-look/v2/hole10/tools/stage_gates.py'}
exec(compile(local_src,SG['__file__'],'exec'),SG)
G=np.flipud(E.max(2)/255>.2);SG['_E'].update(G=G,w=G.shape[1],h=G.shape[0],mean=float(G.mean()))
result=dict(scope='One scratch paired-side UV variant plus unchanged chart control. Exact geometry/textures and fixed lighting; no production writes or native Game view.',geometry=counts,texture_dir=candidate,phases=[])
for mode in ('independent_control','paired_variant1'):
    if mode=='paired_variant1':
        result['chart_records']=[author_paired_columns(ob,seed=707+index,uf=.38,vf=.32) for index,ob in enumerate(obs)]
    phase=dict(name=mode,shots=[],gates=[])
    snapshot=V.Snap('fixture',types.SimpleNamespace(hole=10,tag='10'))
    for name,fn in [('UV_DENSITY',V.g_uv),('GROUND_UV_LOCAL_SMEAR',V.g_uv_local_smear)]:
        ok,detail=fn(snapshot,types.SimpleNamespace(hole=10))
        phase['gates'].append(dict(name=name,ok=bool(ok),detail=detail));print('GATE:',mode,name,'PASS' if ok else 'FAIL',detail,flush=True)
    st=dict(side=0,glow=0,top=0,top_glow_free=0)
    for ob in obs:
        for p in ob.data.polygons:
            pts=np.array([tuple(ob.data.vertices[i].co) for i in p.vertices]);uv=np.array([tuple(ob.data.uv_layers.active.data[i].uv) for i in p.loop_indices]);share=H._face_glow(uv)
            if abs(H._newell(pts)[2])>=.8:st['top']+=1;st['top_glow_free']+=int(share<=2e-4)
            else:st['side']+=1;st['glow']+=int(share>0)
    fraction=st['glow']/max(st['side'],1)
    phase['uv_window_local']=dict(**st,side_glow_fraction=fraction,ok=st['top']==st['top_glow_free'] and .15<=fraction<=.45,scope='Original top/plain and15–45%side predicates; full H_UV_WINDOWS mesh-count requirement is absent in this fixture')
    captured={}
    def capture(frame,event,arg):
        if event=='return' and frame.f_code.co_name=='glow_gate':
            captured.update({k:frame.f_locals[k] for k in ('nobj','top_cov','side_cov','lit_share','streak','gmean','acc')})
    sys.setprofile(capture)
    try:SG['glow_gate'](mode,obs,1.)
    finally:sys.setprofile(None)
    local_ok=captured['top_cov']<=.005 and .25*captured['gmean']<=captured['side_cov']<=.6*captured['gmean'] and .10<=captured['lit_share']<=.50 and captured['streak']>=2.5
    phase['original_H_GLOW_JOINTS']=SG['RES'][-1]
    phase['H_GLOW_numeric_local']=dict(**captured,ok=bool(local_ok),scope='Exact unchanged numerical caps only; original whole-hole>=200object presence result remains FAIL')
    for az in (0,35,-35):
        a=math.radians(az)
        cam=bpy.data.objects.new('REF_CAM',bpy.data.cameras.new('REF_CAM'));sc.collection.objects.link(cam)
        cam.location=(math.sin(a)*48,-math.cos(a)*48,14)
        cam.rotation_euler=(Vector((0,3,8))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=42;cam.data.clip_end=6000;sc.camera=cam
        path=OUT+'/'+mode+'_az'+str(az)+'.png';sc.render.filepath=path;bpy.ops.render.render(write_still=True)
        px=T.read_png(path);rgb=px[:,:,:3];mask=px[:,:,3]>250
        shot=types.SimpleNamespace(px=rgb,idmask=lambda cat,m=mask:m)
        metrics=proof['basalt_metrics'](shot)
        phase['shots'].append(dict(name='az'+str(az),metrics=metrics,ok=bool(metrics and proof['basalt_shot_ok'](metrics)),image=path))
        print('GATE:',mode,'BLENDER_BASALT_'+str(az),'PASS' if phase['shots'][-1]['ok'] else 'FAIL',json.dumps(metrics),flush=True)
        bpy.data.objects.remove(cam,do_unlink=True)
    sk=sum(s['metrics'].get('glow_skeleton_px',0) for s in phase['shots'] if s['metrics']);j=sum(s['metrics'].get('glow_junction_clusters',0) for s in phase['shots'] if s['metrics'])
    phase['network']=dict(ok=bool(proof['basalt_network_ok'](sk,j)),skeleton_pixels=sk,junction_clusters=j,junction_per100=100*j/max(sk,1))
    phase['local_ok']=all(g['ok'] for g in phase['gates']) and phase['uv_window_local']['ok'] and phase['H_GLOW_numeric_local']['ok'] and all(s['ok'] for s in phase['shots']) and phase['network']['ok']
    result['phases'].append(phase)
    with open(OUT+'/result.json','w') as f:json.dump(result,f,indent=2)
result['geometry_unchanged']=geo_before=={ob.name:mesh_hash(ob) for ob in obs}
result['scoring_controls_unchanged']=controls_before=={ob.name:mesh_hash(ob,True) for ob in controls}
result['paired_local_ok']=result['phases'][-1]['local_ok'] and result['geometry_unchanged'] and result['scoring_controls_unchanged']
with open(OUT+'/result.json','w') as f:json.dump(result,f,indent=2)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=OUT+'/fixture.blend')
print('GATE: PAIRED_VARIANT1_LOCAL','PASS' if result['paired_local_ok'] else 'FAIL',flush=True)
sys.exit(0 if result['paired_local_ok'] else 1)
