"""blender -b --factory-startup --python sil_render.py -- <blend> <outdir> [tag]  -> body masks + overlay crops of the legs (vs frozen plate masks)"""
import sys, json
from pathlib import Path
import numpy as np, bpy
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'); M=R/'work/male-silhouette'
argv=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out=Path(argv[1]); out.mkdir(parents=True,exist_ok=True)
sc=bpy.context.scene
sc.render.film_transparent=True; sc.render.image_settings.color_mode='RGBA'; sc.render.image_settings.file_format='PNG'
sc.render.resolution_x=1280; sc.render.resolution_y=720; sc.render.resolution_percentage=100
for o in bpy.data.objects:
    if o.type=='EMPTY': o.hide_render=True
face=bpy.data.objects.get('Face_M')
if face: face.hide_render=True
def alpha_of(path):
    img=bpy.data.images.load(str(path),check_existing=False)
    a=np.array(img.pixels[:],np.float32).reshape(img.size[1],img.size[0],4); bpy.data.images.remove(img); return a
res={}
for view in ('bald_front','bald_back'):
    sc.camera=bpy.data.objects['Locked_'+view]; p=out/f'{view}.png'; sc.render.filepath=str(p.resolve()); bpy.ops.render.render(write_still=True)
    r=alpha_of(p)[:,:,3]>0.5
    t=alpha_of(M/f'{view}_target.png'); tm=(t[:,:,3]>0.5) if t[:,:,3].min()<0.99 else (t[:,:,0]>0.5)
    np.save(out/f'{view}_mask.npy',r); np.save(out/f'{view}_target.npy',tm)
    d=int((r!=tm).sum()); u=int((r|tm).sum()); res[view]=100*d/u
    # leg-only (image y>= crotch row ~ 335 from top; arrays are bottom-up)
    H=r.shape[0]; ys=slice(0,H-335)   # rows (bottom-up) below y=335 px from top
    dl=int((r[ys]!=tm[ys]).sum()); ul=int((r[ys]|tm[ys]).sum()); res[view+'_legs']=100*dl/ul
print('SIL',json.dumps(res))
(out/'sil.json').write_text(json.dumps(res))
