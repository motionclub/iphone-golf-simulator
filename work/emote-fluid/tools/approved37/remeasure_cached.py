"""Remeasure immutable traces with current gate definitions; no FBX edits."""
import sys,json,os
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from fluid_audit import measure,W,native_curve_info
import fbx_curves as FB
from fluid_spec import CLIPS
args=sys.argv[sys.argv.index('--')+1:];phase=args[0];out=W/'data'/phase;res={}
for tag in ['male','female']:
 for clip in CLIPS:
  p=out/f'trace_{tag}_{clip}.npz';z=np.load(p);old_ci=json.loads(str(z['curve_info']));fbx=(W/'rollback/fbx' if phase=='before' else W/'candidate/fbx')/f'{tag.title()}_{clip}.fbx';raw,version,models,channels=FB.read(fbx);ci=native_curve_info(channels,len(z['M']),clip,old_ci.get('blender_derived_linear_keys',0));res[f'{tag}/{clip}']=measure(z,ci,clip)
(out/'audit_remeasured.json').write_text(json.dumps(res,indent=2))
print('REMEASURED',len(res),'immutable traces')
