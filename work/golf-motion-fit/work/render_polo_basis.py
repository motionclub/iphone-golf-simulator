import bpy,sys
from pathlib import Path
W=Path(__file__).resolve().parents[1];source=(W/'scripts/render_review.py').read_text();source=source.replace('sc.frame_set(int(t*120),subframe=t*120-int(t*120))','sc.frame_set(int(t*120),subframe=t*120-int(t*120));\n for o in bpy.data.objects:\n  if o.type==\'MESH\' and o.data.shape_keys:\n   o.data.shape_keys.animation_data_clear()\n   for key in o.data.shape_keys.key_blocks:key.value=0\n')
exec(compile(source,'basis','exec'),{'__file__':str(W/'scripts/render_review.py')})
