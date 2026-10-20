"""heat map of a displacement field sampled on the zone vertices (front or back), model coords"""
import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/tools')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
FONT=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
def colormap(v,vmin,vmax):
    t=np.clip((v-vmin)/(vmax-vmin+1e-12),0,1)
    r=np.clip(2*t,0,1); g=np.clip(2-2*np.abs(2*t-1)*1.0,0,1)*0.9; b=np.clip(2*(1-t),0,1)
    return (np.stack([r,g*0.8,b],-1)*255).astype(np.uint8)
def plot(x,z,val,mask,xr,zr,scale=1800,vr=None,title='',contours=None):
    W=int((xr[1]-xr[0])*scale)+60; H=int((zr[1]-zr[0])*scale)+40
    im=Image.new('RGB',(W,H),(20,20,24)); d=ImageDraw.Draw(im)
    vr=vr or (val[mask].min(),val[mask].max())
    cols=colormap(val,*vr)
    for i in np.where(mask)[0]:
        u=30+(x[i]-xr[0])*scale; v=H-20-(z[i]-zr[0])*scale
        d.ellipse([u-5,v-5,u+5,v+5],fill=tuple(int(c) for c in cols[i]))
    for xm in np.arange(np.ceil(xr[0]*20)/20,xr[1],0.05): d.line([(30+(xm-xr[0])*scale,0),(30+(xm-xr[0])*scale,H)],fill=(60,60,70)); d.text((30+(xm-xr[0])*scale+2,H-16),f'{xm*100:.0f}',font=FONT,fill=(200,200,200))
    for zm in np.arange(np.ceil(zr[0]*20)/20,zr[1],0.05): d.line([(0,H-20-(zm-zr[0])*scale),(W,H-20-(zm-zr[0])*scale)],fill=(60,60,70)); d.text((2,H-20-(zm-zr[0])*scale-14),f'{zm:.2f}',font=FONT,fill=(200,200,200))
    d.text((8,4),f'{title}  [{vr[0]*1000:.1f} .. {vr[1]*1000:.1f} mm]',font=FONT,fill=(255,255,255))
    return im
