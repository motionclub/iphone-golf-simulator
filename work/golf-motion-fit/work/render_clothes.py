import sys,bpy
from pathlib import Path
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1]
source=(W/'scripts/render_review.py').read_text()
source=source.replace("for label,t in stages:","for o in bpy.data.objects:\n if o.name.startswith(('GolfClubFace','GolfHandle','GolfShaft')):o.hide_render=True\nstages=[('Outfit',0)]\nfor label,t in stages:")
source=source[:source.index('sc.frame_set(0);bpy.context.view_layer.update();hands=')]+"\nprint('CLOTHES_RENDER_COMPLETE',flush=True)\n"
sys.argv=['blender','--',sex,'NeutralIdle','RH']
exec(compile(source,'render_clothes','exec'),{'__file__':str(W/'scripts/render_review.py')})
