import bpy,sys,runpy,json,time,contextlib,traceback
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[5];sys.path.insert(0,str(ROOT/'blender/scripts'))
import postcard_lib as P,postcard_look_lib as L
D=P.start('hole09_design',out_dir=str(OUT/'stage'));bpy.ops.wm.open_mainfile(filepath=str(OUT/'compound_unverified.blend'));D.terrain=bpy.data.objects[D.terrain_name]
L.export_look_fbx(D,str(OUT/'compound_unverified.fbx'),colors_type='LINEAR')
jobs=[('verifier','blender/scripts/postcard_look_verify.py',['9','--blend',str(OUT/'compound_unverified.blend'),'--fbx',str(OUT/'compound_unverified.fbx'),'--json',str(OUT/'verifier.json'),'--stills-dir',str(ROOT/'work/postcard-look/v3/hole09/gate_stills'),'--require-stills']),('hole_qa','blender/scripts/hole09_qa.py',['--blend',str(OUT/'compound_unverified.blend'),'--fbx',str(OUT/'compound_unverified.fbx'),'--json',str(OUT/'hole_qa.json')])]
res=[]
for name,script,args in jobs:
 print('CHECK_START '+name,flush=True);t=time.time();code=0;err=None;sys.argv=[str(ROOT/script),'--']+args
 with (OUT/(name+'.log')).open('w') as f:
  with contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
   try:runpy.run_path(str(ROOT/script),run_name='__main__')
   except SystemExit as e:code=int(e.code or 0)
   except BaseException as e:code=2;err=repr(e);traceback.print_exc()
 res.append(dict(name=name,exit_code=code,error=err,seconds=time.time()-t));(OUT/'check_export_results.json').write_text(json.dumps(res,indent=2)+'\n');print('CHECK_DONE '+json.dumps(res[-1]),flush=True)
