"""Read-only frozen P4 stage UVs sampled against scratch candidate emission."""
import os,sys,json,hashlib
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts')
import bpy,numpy as np
import golf_look_textures as T
HERE=os.path.dirname(__file__);candidate=HERE+'/bounded_v6_source'
STAGE=ROOT+'/work/postcard-look/v3/hole10/stage/hole_10.blend'
tool=ROOT+'/work/postcard-look/v2/hole10/tools/stage_gates.py'
source=open(tool).read();source=source[:source.index('\nif opt("--blend"):')]
ns={'__name__':'scratch_frozen_stage_uv','__file__':tool}
exec(compile(source,tool,'exec'),ns)
bpy.ops.wm.open_mainfile(filepath=STAGE)
obs=ns['stage_objects']('blend');meshes=[o for o in obs if o.type=='MESH']
E=T.read_png(candidate+'/Basalt_E.png')[:,:,:3];G=np.flipud(E.max(2)/255>.2)
ns['_E'].update(G=G,w=G.shape[1],h=G.shape[0],mean=float(G.mean()))
ter=bpy.data.objects.get('TERRAIN_CRATER')
base_sv=np.linalg.svd(np.array(ter.matrix_world)[:3,:3],compute_uv=False) if ter is not None else np.ones(3)
base_s=float(np.mean(base_sv))
ns['glow_gate']('scratch_candidate_on_frozen_blend',meshes,base_s)
result=dict(scope='Unchanged original H_GLOW_JOINTS predicate on complete read-only frozen P4 blend; only sampled source PNGs redirected to scratch. No stage/source writes.',gates=ns['RES'],stage=STAGE,stage_sha256=hashlib.sha256(open(STAGE,'rb').read()).hexdigest(),emission_sha256=hashlib.sha256(open(candidate+'/Basalt_E.png','rb').read()).hexdigest(),base_s=base_s)
json.dump(result,open(HERE+'/frozen_stage_uv.json','w'),indent=2)
sys.exit(0 if all(r['ok'] for r in result['gates']) else 1)
