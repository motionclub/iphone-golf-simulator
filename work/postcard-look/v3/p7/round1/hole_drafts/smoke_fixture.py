import bpy,numpy as np,sys,json,importlib.util,hashlib
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[5]
sys.path.insert(0,str(ROOT/'blender/scripts'))
import postcard_look_verify as Q
stage=ROOT/'work/postcard-look/v3/hole10/stage/hole_10.blend';before=hashlib.sha256(stage.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(stage))
spec=importlib.util.spec_from_file_location('HL_P7_DRAFT',OUT/'candidate1/drafts/hole10_look.py');HL=importlib.util.module_from_spec(spec);spec.loader.exec_module(HL)
design,dp=Q.load_design(10);C=Q.Ctx(10,design,dp,{});S=Q.Snap('blend',C)
old=Q.g_smoke_frames(S,C)
for ob in list(bpy.data.objects):
 if ob.name.startswith('DRESS_SMOKE'):bpy.data.objects.remove(ob,do_unlink=True)
cone=bpy.data.objects['DRESS_CONE'];bvh=BVHTree.FromObject(cone,bpy.context.evaluated_depsgraph_get())
D=SimpleNamespace(number=10)
def vent(dx,dy):
 x,y=170.+dx,440.+dy;hit=bvh.ray_cast(Vector((x,y,200.)),Vector((0,0,-1)))
 if hit[0] is None:raise RuntimeError('vent has no surface')
 return (x,y,float(hit[0].z)+.1)
vents=[vent(-85.,-85.),(305.,118.,0.),vent(85.,-85.)]
for cam,p,wh,seed in [((-.87,-4.02),vents[0],(85.,85.),1),((93.82,145.52),vents[1],(90.,90.),2),((64.01,98.76),vents[2],(100.,95.),3)]:HL.smoke_group(D,cam,p,wh,3,seed=seed,spread=.035)
bpy.context.view_layer.update();S=Q.Snap('blend',C);new=Q.g_smoke_frames(S,C);shares=Q.smoke_frame_shares(S,C)
result=dict(old_gate=old,candidate_gate=new,candidate_shares=shares,vents=vents,stage_sha_before=before,stage_sha_after=hashlib.sha256(stage.read_bytes()).hexdigest(),saved_or_exported=False,geometry_candidate_count=1,production_applied=False)
(OUT/'smoke_fixture.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
