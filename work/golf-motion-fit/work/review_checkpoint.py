import bpy,sys
from pathlib import Path
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1]
source=(W/'scripts/render_review.py').read_text()
for family in ['Drive','Putt','BallPickup','NeutralIdle']:
 for hand in ['RH','LH']:
  sys.argv=['blender','--',sex,family,hand,'--fast','--all']
  exec(compile(source,'review_checkpoint','exec'),{'__file__':str(W/'scripts/render_review.py')})
print('CHECKPOINT_REVIEW_COMPLETE',sex,flush=True)
