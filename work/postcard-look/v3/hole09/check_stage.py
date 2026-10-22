"""Sequential unchanged checks of the staged H9; writes scratch evidence only."""
import contextlib,json,os,runpy,sys,time,traceback
sys.dont_write_bytecode=True
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.abspath(os.path.join(HERE,'../../../..'))
STAGE=HERE+'/stage'
os.chdir(ROOT)
sys.path.insert(0,ROOT+'/blender/scripts')
os.environ['POSTCARD_SCORING_STAGE_ROOT']='work/postcard-look/v3'
os.environ['POSTCARD_SCORING_HOLES']='9'
os.environ['POSTCARD_SCORING_OUTPUT_STEM']='scoring_exact_p3'
blend=STAGE+'/hole_09.blend';fbx=STAGE+'/hole_09.fbx'
jobs=[
 ('verifier_required','blender/scripts/postcard_look_verify.py',
  ['9','--blend',blend,'--fbx',fbx,'--json',HERE+'/verify_required.json','--stills-dir',HERE+'/proof','--require-stills']),
 ('hole_qa','blender/scripts/hole09_qa.py',
  ['--blend',blend,'--fbx',fbx,'--json',HERE+'/hole_qa.json']),
 ('ruin_blend','work/postcard-look/v2/hole09/tools/ruin_check.py',
  ['--blend',blend,'--json',HERE+'/ruin_blend.json']),
 ('ruin_fbx','work/postcard-look/v2/hole09/tools/ruin_check.py',
  ['--fbx',fbx,'--json',HERE+'/ruin_fbx.json']),
 ('pieces_blend','work/postcard-look/v3/lib/masonry/piece_classifier.py',
  ['--blend',blend,'--out',HERE+'/pieces_blend.json']),
 ('pieces_fbx','work/postcard-look/v3/lib/masonry/piece_classifier.py',
  ['--fbx',fbx,'--out',HERE+'/pieces_fbx.json']),
 ('scenery','work/postcard-look/v3/hole09/scenery_metrics.py',
  ['--blend',blend,'--json',HERE+'/scenery_metrics.json']),
 ('scoring_exact','work/postcard-look/v3/audit/scoring_exact.py',[]),
]
results=[]
for name,script,arguments in jobs:
    print('CHECK_START '+name,flush=True)
    t=time.time();code=0;error=None
    sys.argv=[ROOT+'/'+script,'--']+arguments
    with open(HERE+'/'+name+'.log','w') as handle:
        with contextlib.redirect_stdout(handle),contextlib.redirect_stderr(handle):
            try:runpy.run_path(ROOT+'/'+script,run_name='__main__')
            except SystemExit as exc:code=int(exc.code or 0)
            except BaseException as exc:
                code=2;error=repr(exc);traceback.print_exc()
    row=dict(name=name,exit_code=code,seconds=time.time()-t,error=error)
    results.append(row)
    with open(HERE+'/check_stage_results.json','w') as handle:json.dump(results,handle,indent=2)
    print('CHECK_DONE '+json.dumps(row),flush=True)
print('CHECK_BATCH_FINISHED',flush=True)
