"""Apply only the two draft smoke calls in memory on the actual P7 stage.

Runs the unchanged original smoke camera and alpha predicates. No save,
export, source application, texture generation or material/runtime edit.
"""
import ast
import hashlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True
import bpy
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[5]
sys.path.insert(0, str(ROOT / 'blender/scripts'))
import postcard_look_verify as Q
import hole10_look as HL

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

plan = json.loads((OUT / 'apply_plan.json').read_text())
for row in plan['entries']:
    for path, expected in ((row['target'],row['old_sha256']),
                           (row['old_snapshot'],row['old_sha256']),
                           (row['draft'],row['new_sha256'])):
        if sha(path) != expected:
            raise RuntimeError('Source SHA guard failed: '+path)
for row in plan['protected']:
    if sha(row['path']) != row['sha256']:
        raise RuntimeError('Protected SHA guard failed: '+row['path'])

stage = ROOT / 'work/postcard-look/v3/p7/round1/rebuild/hole10/stage/hole_10.blend'
before = sha(stage)
bpy.ops.wm.open_mainfile(filepath=str(stage),load_ui=False)
design, dp = Q.load_design(10)
C = Q.Ctx(10,design,dp,{})
S = Q.Snap('blend',C)
old_gate = Q.g_smoke_frames(S,C)
old_shares = Q.smoke_frame_shares(S,C)

def card_record(ob):
    me=ob.data
    co=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',co)
    uv=np.empty(len(me.uv_layers[0].data)*2);me.uv_layers[0].data.foreach_get('uv',uv)
    return dict(name=ob.name,group=int(ob.get('lk_v3_smoke_group',-1)),
        anchor=list(ob.get('lk_v3_vent_anchor',[])),location=list(ob.location),
        scale=list(ob.scale),rotation=list(ob.rotation_euler),verts=co.tolist(),
        polygons=[list(p.vertices) for p in me.polygons],uv=uv.tolist(),
        materials=[m.name for m in me.materials],
        triangle_count=sum(len(p.vertices)-2 for p in me.polygons))

groups={seed:sorted((o for o in bpy.data.objects if o.type=='MESH'
                    and o.name.startswith('DRESS_SMOKE')
                    and int(o.get('lk_v3_smoke_group',-1))==seed),key=lambda o:o.name)
        for seed in (1,2,3)}
if [len(groups[s]) for s in (1,2,3)] != [3,3,3]:
    raise RuntimeError('Actual stage does not contain exactly three bound three-card groups')
records={seed:[card_record(o) for o in groups[seed]] for seed in (1,2,3)}
for seed in (2,3):
    for ob in groups[seed]:bpy.data.objects.remove(ob,do_unlink=True)

# Parse the real proposed source. Execute its unchanged camera assignment and
# the two actual group calls, rather than a separately authored substitute.
draft = OUT / 'hole10_build.py'
tree = ast.parse(draft.read_text())
camera_assignment=[]
calls=[]
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Tuple)
        and [e.id for e in t.elts if isinstance(e,ast.Name)]==['TEE_CAM','APP_CAM','RIM_CAM']
        for t in node.targets):camera_assignment.append(node)
    if (isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='smoke'
        and isinstance(node.value,ast.Call)):
        seed=next((ast.literal_eval(k.value) for k in node.value.keywords if k.arg=='seed'),None)
        if seed in (2,3):calls.append(node)
if len(camera_assignment)!=1 or len(calls)!=2:
    raise RuntimeError('Unexpected proposed smoke call structure')
scope=dict(D=SimpleNamespace(number=10),HL=HL,smoke=[])
exec(compile(ast.Module(body=camera_assignment+calls,type_ignores=[]),str(draft),'exec'),scope)
bpy.context.view_layer.update()
candidate=scope['smoke']
new_records={seed:[card_record(o) for o in candidate if int(o.get('lk_v3_smoke_group',-1))==seed]
             for seed in (2,3)}
checks=[]
geometry_fields=('group','anchor','location','scale','verts','polygons','uv','materials','triangle_count')
for seed in (2,3):
    current=new_records[seed]
    if len(current)!=3:raise RuntimeError('Unexpected new group size')
    unchanged=all(all(old[k]==new[k] for k in geometry_fields)
                  for old,new in zip(records[seed],current))
    heading=float(current[0]['rotation'][2])
    parallel=all(r['rotation'][:2]==[0.,0.] and r['rotation'][2]==heading for r in current)
    normal=np.array([-math.sin(heading),math.cos(heading),0.])
    depth=[float(np.dot(np.array(r['location']),normal)) for r in current]
    separations=[abs(depth[j]-depth[i]) for i in range(3) for j in range(i+1,3)]
    checks.append(dict(group=seed,geometry_uv_dimensions_rng_positions_anchor_exact=unchanged,
        common_rigid_heading_exact=parallel,heading_rad=heading,
        distinct_depth_offsets_m=depth,min_center_plane_separation_m=min(separations),
        old_yaws_rad=[r['rotation'][2] for r in records[seed]],
        new_yaws_rad=[r['rotation'][2] for r in current],
        old=records[seed],new=current))

S=Q.Snap('blend',C)
new_gate=Q.g_smoke_frames(S,C)
new_shares=Q.smoke_frame_shares(S,C)
tee_after=[card_record(o) for o in groups[1]]
tee_unchanged=tee_after==records[1]
for row in plan['entries']:
    if sha(row['target'])!=row['old_sha256']:raise RuntimeError('Production source drifted during fixture')
guards_equal=all(sha(row['path'])==row['sha256'] for row in plan['protected'])
result=dict(production_applied=False,scene_saved_or_exported=False,native_unmeasured=True,
    visual_star_cross_result='UNMEASURED: requires fresh actual Game-view review',
    stage=str(stage),stage_sha_before=before,stage_sha_after=sha(stage),
    original_checker_sha256=sha(ROOT/'blender/scripts/postcard_look_verify.py'),
    original_smoke_constants=Q.SMOKE_VIS,original_runtime_alpha=Q.smoke_runtime_spec(),
    original_camera_cfg=Q.STILL_CFG,original_camera_cfg_sha256=sha(Q.STILL_CFG),
    old_gate=old_gate,old_shares=old_shares,candidate_gate=new_gate,candidate_shares=new_shares,
    original_per_camera_status={k:'PASS' if v>=Q.SMOKE_VIS['share_min'] else 'FAIL'
                               for k,v in new_shares[0].items()},
    existing_tee_three_cards_exact=tee_unchanged,guards_equal_after=guards_equal,
    groups=checks,
    geometry_check_pass=tee_unchanged and guards_equal and before==sha(stage)
        and all(c['geometry_uv_dimensions_rng_positions_anchor_exact']
                and c['common_rigid_heading_exact'] and c['min_center_plane_separation_m']>0
                for c in checks))
result['cpu_status']='PASS' if result['geometry_check_pass'] and bool(new_gate[0]) else 'FAIL'
out=OUT/'result.json'
if out.exists():raise RuntimeError('Refusing existing fixture result')
out.write_text(json.dumps(result,indent=2)+'\n')
print('ORIGINAL_GATE '+str(old_gate),flush=True)
print('CANDIDATE_GATE '+str(new_gate),flush=True)
print('CANDIDATE_SHARES '+json.dumps(new_shares),flush=True)
print('GEOMETRY_CHECK '+str(result['geometry_check_pass']),flush=True)
print('RESULT '+result['cpu_status']+' native_unmeasured=True',flush=True)
if result['cpu_status']!='PASS':raise RuntimeError('Candidate original gate/geometry check FAIL')
