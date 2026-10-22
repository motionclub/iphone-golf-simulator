"""blender -b --factory-startup --python fit_q3.py -- <blend> <out.json>   (PYTHONPATH must include male-micro1i/pylib for PIL)
Fit orthographic cameras (yaw, mpp, cx, sole_y) of the 4 body 3/4 views of male_multiangle_body.jpg by silhouette IoU."""
import sys, json, math
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
from pathlib import Path
import numpy as np, bpy
from PIL import Image, ImageDraw
from mathutils import Vector
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
argv=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); outj=Path(argv[1])
plate=np.array(Image.open(R/'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('L')).astype(np.float32)
ROIS={'q3FL':(58,375,318,682),'q3FR':(350,375,625,682),'q3BL':(655,375,905,682),'q3BR':(960,375,1215,682)}
def _label(mask):
    """largest 8-connected component (python BFS; images are small)"""
    from collections import deque
    H,W=mask.shape; seen=np.zeros_like(mask,bool); best=None; bestn=0
    for y0_ in range(H):
        for x0_ in np.nonzero(mask[y0_]&~seen[y0_])[0]:
            if seen[y0_,x0_]: continue
            q=deque([(y0_,x0_)]); seen[y0_,x0_]=True; pts=[]
            while q:
                y,x=q.popleft(); pts.append((y,x))
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        yy,xx=y+dy,x+dx
                        if 0<=yy<H and 0<=xx<W and mask[yy,xx] and not seen[yy,xx]: seen[yy,xx]=True; q.append((yy,xx))
            if len(pts)>bestn: bestn=len(pts); best=pts
    out=np.zeros_like(mask,bool)
    for y,x in best: out[y,x]=True
    return out
def plate_mask(roi):
    x0,y0,x1,y1=roi; a=plate[y0:y1,x0:x1]
    bgL=np.median(a[:,:6],axis=1); bgR=np.median(a[:,-6:],axis=1)
    t=np.linspace(0,1,a.shape[1])[None,:]; bg=bgL[:,None]*(1-t)+bgR[:,None]*t
    m=_label((a-bg)>7.5)
    inv=_label(~m)              # background component touching the corner (largest)
    m=~inv                      # fills holes
    full=np.zeros(plate.shape,bool); full[y0:y1,x0:x1]=m
    return full
masks={k:plate_mask(v) for k,v in ROIS.items()}
for k,m in masks.items():
    ys,xs=np.nonzero(m); print(k,'plate mask',m.sum(),'bbox',xs.min(),ys.min(),xs.max(),ys.max())
    Image.fromarray((m*255).astype(np.uint8)).save(R/f'work/male-parallel-legs/data/plate_mask_{k}.png')
face=bpy.data.objects.get('Face_M')
for o in bpy.data.objects:
    if o.type in('EMPTY','CAMERA'): o.hide_render=True
body=bpy.data.objects['Body_M']
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'; sc.render.film_transparent=True; sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGBA'
sc.display.shading.light='FLAT'; sc.display.shading.color_type='SINGLE'
cd=bpy.data.cameras.new('c'); cd.type='ORTHO'; co=bpy.data.objects.new('c',cd); sc.collection.objects.link(co); sc.camera=co
W,H=1280,720
sc.render.resolution_x=W; sc.render.resolution_y=H; sc.render.resolution_percentage=100
MPP=0.00585
LEG=548
cd.ortho_scale=W*MPP    # ortho_scale = width of the view for landscape
def render_mask(az, ox, sole):
    # camera aimed so the world point (0,0,0) projects to pixel (ox, sole); view centre pixel is (W/2,H/2)
    a=math.radians(az); d=Vector((math.sin(a),-math.cos(a),0.0))
    right=Vector((math.cos(a),math.sin(a),0)); up=Vector((0,0,1))
    # camera centre world pos on the view plane: origin shifted so that pixel (ox,sole) shows origin
    # pixel x = W/2 + (p-c).right/MPP ; pixel y(from top) = H/2 - (p-c).up/MPP
    cpt=Vector((0,0,0))-right*((ox-W/2)*MPP)-up*((H/2-sole)*MPP)*(-1)
    # origin at pixel (ox,sole): (0-c).right/MPP = ox-W/2 -> c.right = -(ox-W/2)*MPP ; (0-c).up = (sole-H/2)*(-MPP)... solve:
    cr=-(ox-W/2)*MPP; cu=(sole-H/2)*MPP   # (0-c).up=-(c.up) = (H/2-sole)*MPP -> c.up=(sole-H/2)*MPP
    cpt=right*cr+up*cu
    co.location=cpt+d*5.0; co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath='/tmp/_q3fit.png'; bpy.ops.render.render(write_still=True)
    img=Image.open('/tmp/_q3fit.png'); return np.array(img)[:,:,3]>127
res={}
for k,m in masks.items():
    ys,xs=np.nonzero(m); cxp=0.5*(xs.min()+xs.max()); sole=ys.max()+1
    best=None
    for az in list(range(-75,-9,3))+list(range(9,76,3)):
        # initial guess origin centre: ox = bbox centre; sole from mask
        r=render_mask(az,cxp,sole)
        # slide search in x
        for dx in range(-14,15,2):
            r2=np.roll(r,dx,axis=1)
            for dy in (-3,0,3):
                r3=np.roll(r2,dy,axis=0)
                iou=(r3[LEG:]&m[LEG:]).sum()/max(1,(r3[LEG:]|m[LEG:]).sum())
                if best is None or iou>best[0]: best=(iou,az,cxp+dx,sole+dy)
    print(k,'coarse',best)
    # refine
    iou0,az0,ox0,so0=best
    for az in np.arange(az0-3,az0+3.01,1):
        r=render_mask(az,ox0,so0)
        for dx in range(-4,5):
            r2=np.roll(r,dx,axis=1)
            for dy in range(-3,4):
                r3=np.roll(r2,dy,axis=0); iou=(r3[LEG:]&m[LEG:]).sum()/max(1,(r3[LEG:]|m[LEG:]).sum())
                if iou>best[0]: best=(iou,float(az),ox0+dx,so0+dy)
    print(k,'refined',best); res[k]=dict(iou=float(best[0]),az=float(best[1]),ox=float(best[2]),sole=float(best[3]),mpp=MPP)
outj.write_text(json.dumps(res,indent=1))
