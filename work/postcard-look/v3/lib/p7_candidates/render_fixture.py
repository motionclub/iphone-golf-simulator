"""Scratch candidate on actual compact columns, unchanged proof pixel gates."""
import os,sys,json,math,random,types,hashlib
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts')
sys.path.insert(0,ROOT+'/work/postcard-look/v3/hole10/prototypes')
import bpy,numpy as np
from mathutils import Vector
import postcard_lib as P
import postcard_look_lib as L
import postcard_props_lib as PL
import hole10_look as H
import golf_look_textures as T
from compact_columns import compact_ring_tile
OUT=os.path.join(os.path.dirname(__file__),'bounded_v6','fixture');os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
D=P.start('hole10_design',out_dir=OUT);L.look_materials(D)
candidate=os.path.dirname(OUT)
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
shots=[]
for az in (0,35,-35):
 a=math.radians(az)
 cam=bpy.data.objects.new('REF_CAM',bpy.data.cameras.new('REF_CAM'));sc.collection.objects.link(cam)
 cam.location=(math.sin(a)*48,-math.cos(a)*48,14)
 cam.rotation_euler=(Vector((0,3,8))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=42;cam.data.clip_end=6000;sc.camera=cam
 path=OUT+'/az'+str(az)+'.png';sc.render.filepath=path;bpy.ops.render.render(write_still=True)
 px=T.read_png(path);rgb=px[:,:,:3];mask=px[:,:,3]>250
 shot=types.SimpleNamespace(px=rgb,idmask=lambda cat,m=mask:m)
 metrics=proof['basalt_metrics'](shot)
 shots.append(dict(name='az'+str(az),metrics=metrics,ok=bool(metrics and proof['basalt_shot_ok'](metrics)),image=path))
 print('GATE: BLENDER_BASALT_'+str(az),'PASS' if shots[-1]['ok'] else 'FAIL',json.dumps(metrics),flush=True)
 bpy.data.objects.remove(cam,do_unlink=True)
sk=sum(s['metrics'].get('glow_skeleton_px',0) for s in shots if s['metrics']);j=sum(s['metrics'].get('glow_junction_clusters',0) for s in shots if s['metrics'])
network=proof['basalt_network_ok'](sk,j)
result=dict(scope='Actual Blender EEVEE scenery; same P1 fixed lighting; unchanged v2/proof pixel predicates. Actual Unity Game view UNVERIFIED.',shots=shots,network=dict(ok=network,skeleton_pixels=sk,junction_clusters=j,junction_per100=100*j/max(sk,1)),geometry=counts,uv_stats=stats,source_sha256=hashlib.sha256(open(ROOT+'/work/postcard-look/v3/hole10/prototypes/compact_columns.py','rb').read()).hexdigest(),all_blender_gates=all(s['ok'] for s in shots) and network)
with open(OUT+'/result.json','w') as f:json.dump(result,f,indent=2)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=OUT+'/fixture.blend')
print('GATE: BLENDER_BASALT_NETWORK','PASS' if network else 'FAIL',sk,j,flush=True)
sys.exit(0 if result['all_blender_gates'] else 1)
