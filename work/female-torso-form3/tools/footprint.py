"""overlay the added-volume footprint (final surface minus base surface, mm) on the plate. python3 tools/footprint.py coords.npy out.png [base.npy]"""
import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form3/tools')
from torso2 import *
from fplate import BALD, S, FRONT_CX, BACK_CX, SOLE
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
FONT=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
def grid_surface(co,side,xs,zs,sig=0.007):
    sel=T&((co[:,1]<0) if side=='front' else (co[:,1]>0))&(TT<0.62 if side=='front' else TT>0.38)
    P=co[sel]; out=np.zeros((len(zs),len(xs)))
    X,Z=np.meshgrid(xs,zs)
    for r in range(len(zs)):
        d2=(X[r][:,None]-P[None,:,0])**2+(Z[r][:,None]-P[None,:,2])**2
        w=np.exp(-d2/(2*sig**2)); out[r]=(w*P[None,:,1]).sum(1)/np.maximum(w.sum(1),1e-12)
    return out
def overlay(co,base,side,box_z,box_x,out,levels=(0.003,0.010,0.020),scale=5):
    xs=np.arange(box_x[0],box_x[1],0.002); zs=np.arange(box_z[0],box_z[1],0.002)
    ya=grid_surface(co,side,xs,zs); yb=grid_surface(base,side,xs,zs)
    d=(yb-ya) if side=='front' else (ya-yb)          # + = added volume (forward for front, backward for back)
    cx=FRONT_CX if side=='front' else BACK_CX; sg=1 if side=='front' else -1
    u0=cx+sg*box_x[0]/S; u1=cx+sg*box_x[1]/S
    ul,ur=min(u0,u1),max(u0,u1); v0=SOLE-box_z[1]/S; v1=SOLE-box_z[0]/S
    plate=Image.fromarray(BALD.astype(np.uint8)).crop((int(ul),int(v0),int(ur),int(v1))).convert('RGB')
    plate=ImageEnhance.Contrast(plate).enhance(1.8).resize((plate.width*scale,plate.height*scale),Image.LANCZOS)
    dr=ImageDraw.Draw(plate,'RGBA')
    cols=[(80,200,255,60),(40,120,255,70),(255,80,200,80)]
    for lev,col in zip(levels,cols):
        m=d>lev
        for r in range(len(zs)):
            for c in range(len(xs)):
                if m[r,c]:
                    x=xs[c]; z=zs[r]; u=(cx+sg*x/S-int(ul))*scale; v=(SOLE-z/S-int(v0))*scale
                    dr.rectangle([u-scale*0.5*0.002/S*1.0,v-scale*0.5*0.002/S,u+scale*0.5*0.002/S,v+scale*0.5*0.002/S],fill=col)
    # grid ticks
    for xm in np.arange(np.ceil(box_x[0]*50)/50,box_x[1],0.02):
        u=(cx+sg*xm/S-int(ul))*scale; dr.line([(u,0),(u,plate.height)],fill=(255,255,0,70)); dr.text((u+2,2),f'{xm*100:+.0f}',font=FONT,fill=(255,255,0,255))
    for zm in np.arange(np.ceil(box_z[0]*50)/50,box_z[1],0.02):
        v=(SOLE-zm/S-int(v0))*scale; dr.line([(0,v),(plate.width,v)],fill=(0,255,120,70)); dr.text((2,v+1),f'{zm:.2f}',font=FONT,fill=(0,255,120,255))
    plate.save(out); print(out,plate.size,'max added mm',round(d.max()*1000,1))
if __name__=='__main__':
    co=np.load(WD/sys.argv[1]); base=np.load(WD/sys.argv[3]) if len(sys.argv)>3 else build2(dict(b_on=0.0,g_on=0.0))
    overlay(co,base,'front',(1.10,1.34),(-0.15,0.15),WD/(sys.argv[2]+'_front.png'))
    overlay(co,base,'back',(0.78,1.04),(-0.19,0.19),WD/(sys.argv[2]+'_back.png'),levels=(0.004,0.012,0.024),scale=5)
