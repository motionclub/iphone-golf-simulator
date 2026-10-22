"""Only changed evidence: rerun original full verifier on actual native stills."""
import contextlib,json,os,runpy,sys,time,traceback
sys.dont_write_bytecode=True
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.abspath(os.path.join(HERE,'../../../..'))
os.chdir(ROOT)
sys.path.insert(0,ROOT+'/blender/scripts')
results=json.load(open(HERE+'/check_stage_results.json'))
for name,script,args in [
 ('verifier_required','blender/scripts/postcard_look_verify.py',['9','--blend',HERE+'/stage/hole_09.blend','--fbx',HERE+'/stage/hole_09.fbx','--json',HERE+'/verify_required.json','--stills-dir',HERE+'/gate_stills','--require-stills']),
 ('scenery','work/postcard-look/v3/hole09/scenery_metrics.py',['--blend',HERE+'/stage/hole_09.blend','--json',HERE+'/scenery_metrics.json'])]:
    print('CHECK_START '+name,flush=True)
    t=time.time();code=0;error=None
    sys.argv=[ROOT+'/'+script,'--']+args
    with open(HERE+'/'+name+'.log','w') as h,contextlib.redirect_stdout(h),contextlib.redirect_stderr(h):
        try:runpy.run_path(ROOT+'/'+script,run_name='__main__')
        except SystemExit as exc:code=int(exc.code or 0)
        except BaseException as exc:code=2;error=repr(exc);traceback.print_exc()
    row=dict(name=name,exit_code=code,seconds=time.time()-t,error=error)
    results=[row if old['name']==name else old for old in results]
    json.dump(results,open(HERE+'/check_stage_results.json','w'),indent=2)
    print('CHECK_DONE '+json.dumps(row),flush=True)
print('CHECK_BATCH_FINISHED',flush=True)
