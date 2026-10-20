import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/tools')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
WD='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/'
FONT=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
T=np.load(WD+'data/zone_chat7.npz')['torso']
O=np.load(WD+'data/orig.npz')['co'].astype(np.float64)
def plot_back(zs,arrs,half=0.006,scale=3300,W_=1800,H_=470,out='data/xsec_back.png',front=False):
    """arrs: list of (coords, color). back half (y>0) or front half (front=True: y<0, plotted with front up)"""
    rows=(len(zs)+2)//3
    im=Image.new('RGB',(W_,H_*rows),(20,20,24)); d=ImageDraw.Draw(im)
    for k,z in enumerate(zs):
        ox=(k%3)*(W_//3); oy=(k//3)*H_; cx=ox+W_//6
        d.rectangle([ox,oy,ox+W_//3-1,oy+H_-1],outline=(60,60,70))
        d.text((ox+6,oy+4),f'z={z:.3f} {"front (front=down)" if front else "back (back=down)"} slab ±{half*1000:.0f} mm  grid 2 cm',font=FONT,fill=(255,255,255))
        for xm in np.arange(-0.2,0.201,0.02): d.line([(cx+xm*scale,oy+20),(cx+xm*scale,oy+H_)],fill=(40,40,50))
        for ym in np.arange(0.0,0.16,0.02): d.line([(ox,oy+30+ym*scale),(ox+W_//3,oy+30+ym*scale)],fill=(40,40,50)); d.text((ox+2,oy+32+ym*scale),f'{ym*100:.0f}',font=FONT,fill=(120,120,130))
        for a,col in arrs:
            sel=(a[:,1]<0) if front else (a[:,1]>0)
            m=T&(np.abs(a[:,2]-z)<half)&sel
            for i in np.where(m)[0]:
                yy=-a[i,1] if front else a[i,1]
                u=cx+a[i,0]*scale; v=oy+30+yy*scale
                d.ellipse([u-2,v-2,u+2,v+2],fill=col)
    im.save(WD+out); print(WD+out)
if __name__=='__main__':
    new=np.load(WD+sys.argv[1])
    plot_back([0.82,0.84,0.86,0.88,0.90,0.94],[(O,(255,140,60)),(new,(120,220,255))])
