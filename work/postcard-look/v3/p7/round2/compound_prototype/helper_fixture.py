import bpy,sys,json,importlib.util,hashlib
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[5];sys.path.insert(0,str(ROOT/'blender/scripts'))
import postcard_lib as P,postcard_look_lib as L,postcard_look_verify as Q
D=P.start('hole09_design',out_dir=str(OUT/'helper_stage'));bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/postcard-look/v3/hole09/stage/hole_09.blend'));D.terrain=bpy.data.objects[D.terrain_name]
loops=L.terrain_top_loops(D,D.terrain);D.loops=[[(float(x),float(y)) for x,y in p] for p,_ in loops];D.loop_kinds=['outer' if P.signed_area(np.array(p))>0 else 'hole' for p in D.loops];D._distfield=None
spec=importlib.util.spec_from_file_location('H9_round2_draft',OUT/'draft_hole09_look.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
scn=dict(tufts=[o for o in bpy.data.objects if o.name.startswith('PLANT_TUFT') and all(c.name!='ASSET_LIBRARY' for c in o.users_collection)])
res=H.merge_shared_tuft_clumps(D,scn);des,dp=Q.load_design(9);C=Q.Ctx(9,des,dp,{});S=Q.Snap('blend',C)
checks={fn.__name__:fn(S,C) for fn in [Q.g_prop_budget,Q.g_plants_material,Q.g_plants_instanced,Q.g_plant_sway_colors,Q.g_plant_sway_caps]}
checks['SCENERY_REFERENCES_LIVE_AND_UNIQUE']=[all(o.name in bpy.data.objects for o in scn['tufts']) and len({o.name for o in scn['tufts']})==len(scn['tufts']),f'{len(scn["tufts"])} live unique tuple renderers']
expected=json.loads((OUT/'result.json').read_text());checks['PROTOTYPE_AND_REUSABLE_HELPER_IDENTICAL_CENSUS']=[res['plants_after']==expected['plants_after'] and res['compound_renderers']==expected['compound_renderers'] and res['triangles_after']==248868,f'{res["plants_after"]} plants/{res["compound_renderers"]} compound renderers/{res["triangles_after"]} triangles']
result=dict(helper_source_sha=hashlib.sha256((OUT/'draft_hole09_look.py').read_bytes()).hexdigest(),checks=checks,summary={k:v for k,v in res.items() if k!='groups'},production_applied=False)
(OUT/'helper_fixture.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
