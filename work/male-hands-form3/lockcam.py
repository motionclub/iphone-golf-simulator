"""Orthographic locked-camera projection + numpy/PIL rasteriser for the 6 reference views (matches the blend's Locked_* cameras)."""
import numpy as np
from PIL import Image, ImageDraw
CAMS={ # name: (cx,cy,cz, rz_rad, ortho_scale)
 'bald_front':(0.822765588760376,-5.0,0.8428330421447754,0.0,3.6694772243499756),
 'bald_back':(0.7958828806877136,5.0,0.8398981094360352,3.141592502593994,3.694397211074829),
 'left':(5.0,-0.9142611622810364,-0.09931271523237228,1.5707963705062866,7.477663040161133),
 'right':(-5.0,2.5003435611724854,-0.09931271523237228,-1.5707963705062866,7.477663040161133),
 'sheet_front':(2.651883602142334,-5.0,-0.09315068274736404,0.0,7.452054977416992),
 'sheet_back':(-0.9329623579978943,5.0,-0.09315068274736404,3.141592502593994,7.452054977416992),
}
W,H=1280,720
def project(V,name):
    cx,cy,cz,rz,osc=CAMS[name]; s=W/osc
    right=np.array([np.cos(rz),np.sin(rz),0.0])
    px=W/2+((V-np.array([cx,cy,cz]))@right)*s
    py=H/2-(V[:,2]-cz)*s
    return px,py
def raster(V,T,name,sel=None,ss=2,roi=None):
    px,py=project(V,name)
    x0,y0,x1,y1=(0,0,W,H) if roi is None else roi
    w,h=x1-x0,y1-y0
    im=Image.new('L',(w*ss,h*ss),0); d=ImageDraw.Draw(im)
    TT=T if sel is None else T[sel]
    sx=(px-x0)*ss; sy=(py-y0)*ss
    # cull triangles outside ROI
    xs=sx[TT]; ys=sy[TT]
    keep=(xs.max(1)>=0)&(xs.min(1)<=w*ss)&(ys.max(1)>=0)&(ys.min(1)<=h*ss)
    TT=TT[keep]
    P=np.stack([sx[TT[:,0]],sy[TT[:,0]],sx[TT[:,1]],sy[TT[:,1]],sx[TT[:,2]],sy[TT[:,2]]],1)
    for p in P: d.polygon([(p[0],p[1]),(p[2],p[3]),(p[4],p[5])],fill=255)
    im=im.resize((w,h),Image.BOX)
    return np.array(im)>127
