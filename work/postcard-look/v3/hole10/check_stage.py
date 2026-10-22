import contextlib,json,os,runpy,sys,time,traceback
sys.dont_write_bytecode=True
HERE=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.abspath(HERE+'/../../../..');os.chdir(ROOT);sys.path.insert(0,ROOT+'/blender/scripts')
STAGE=HERE+'/stage';blend=STAGE+'/hole_10.blend';fbx=STAGE+'/hole_10.fbx'
os.environ['POSTCARD_SCORING_STAGE_ROOT']='work/postcard-look/v3';os.environ['POSTCARD_SCORING_HOLES']='10';os.environ['POSTCARD_SCORING_OUTPUT_STEM']='scoring_exact_p4'
jobs=[('geometry_metrics','work/postcard-look/v3/hole10/geometry_metrics.py',[]),('verifier_required','blender/scripts/postcard_look_verify.py',['10','--blend',blend,'--fbx',fbx,'--json',HERE+'/verify_required.json','--stills-dir',HERE+'/gate_stills','--require-stills']),('stage_gates','work/postcard-look/v2/hole10/tools/stage_gates.py',['--blend',blend,'--fbx',fbx,'--json',HERE+'/stage_gates.json']),('scoring_exact','work/postcard-look/v3/audit/scoring_exact.py',[])]
results=[]
for name,script,args in jobs:
 print('CHECK_START '+name,flush=True);t=time.time();code=0;error=None;sys.argv=[ROOT+'/'+script,'--']+args
 with open(HERE+'/'+name+'.log','w') as f:
  with contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
   try:runpy.run_path(ROOT+'/'+script,run_name='__main__')
   except SystemExit as exc:code=int(exc.code or 0)
   except BaseException as exc:code=2;error=repr(exc);traceback.print_exc()
 row=dict(name=name,exit_code=code,seconds=time.time()-t,error=error);results.append(row);json.dump(results,open(HERE+'/check_stage_results.json','w'),indent=2);print('CHECK_DONE '+json.dumps(row),flush=True)
