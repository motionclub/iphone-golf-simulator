import sys; sys.path.insert(0,'tools')
from fplate import *
from PIL import Image, ImageDraw, ImageFont
FONT=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
def grid_image(view,z0,z1,x0,x1,scale=8,enh=True,sig=1.0,gain=3.0,contour=False):
    """crop of the bald plate in model coords: x in [x0,x1] (m, + = viewer-right for front, viewer-left for back), z in [z0,z1]"""
    vw=View(view)
    # pixel box
    def col_of(x): return vw.cx+x*(1 if view=='front' else -1)/S
    cA,cB=sorted([col_of(x0),col_of(x1)]); r0=SOLE-z1/S; r1=SOLE-z0/S
    crop=Image.fromarray(BALD.astype(np.uint8)).crop((int(cA),int(r0),int(cB),int(r1)))
    a=np.asarray(crop).astype(float)
    if enh:
        big=Image.fromarray(BALD.astype(np.uint8)).crop((int(cA)-30,int(r0)-30,int(cB)+30,int(r1)+30))
        bl=np.asarray(big.filter(__import__('PIL.ImageFilter',fromlist=['x']).GaussianBlur(10))).astype(float)[30:-30,30:-30]
        a=np.clip(128+(a-bl)*gain*2,0,255)
    im=Image.fromarray(a.astype(np.uint8)).resize((int(a.shape[1]*scale),int(a.shape[0]*scale)),Image.BICUBIC).convert('RGB')
    d=ImageDraw.Draw(im)
    # grid: every 2 cm in x, every 2 cm in z
    sgn=1 if view=='front' else -1
    for xm in np.arange(np.ceil(x0*50)/50,x1+1e-9,0.02):
        u=(vw.cx+xm*sgn/S-int(cA))*scale
        d.line([(u,0),(u,im.height)],fill=(255,80,80) if abs(xm)<1e-9 else (80,160,255),width=1)
        d.text((u+2,2),f'{xm*100:+.0f}',fill=(255,255,0),font=FONT)
    for zm in np.arange(np.ceil(z0*50)/50,z1+1e-9,0.02):
        v=(SOLE-zm/S-int(r0))*scale
        d.line([(0,v),(im.width,v)],fill=(80,200,120),width=1)
        d.text((2,v+1),f'{zm:.2f}',fill=(255,255,0),font=FONT)
    return im
if __name__=='__main__':
    a=grid_image('front',1.10,1.36,-0.16,0.16,scale=7)
    a.save('data/grid_front_chest.png'); print(a.size)
    b=grid_image('back',0.74,1.06,-0.20,0.20,scale=6)
    b.save('data/grid_back_glute.png'); print(b.size)
