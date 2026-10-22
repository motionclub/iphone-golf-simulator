import numpy as np, sys
from PIL import Image, ImageFilter
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
plate=Image.open(R+'ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')
BOX={'q3L':(5,390,433,668),'q3R':(433,390,834,668)}
ROI={'q3L':(120,440,250,600),'q3R':(520,440,670,600)}     # plate px (x0,y0,x1,y1): eyes..chin, nose..ear
def dark_map(img_rgb, mask=None):
    g=np.asarray(img_rgb.convert('L')).astype(float)
    b=np.asarray(img_rgb.convert('L').filter(ImageFilter.GaussianBlur(5))).astype(float)
    d=np.clip(b-g,0,None)
    if mask is not None: d=d*mask
    return d
def run(name):
    box=BOX[name]; x0,y0,x1,y1=ROI[name]
    p=plate.crop(box).resize(((box[2]-box[0])*2,(box[3]-box[1])*2),Image.LANCZOS)
    # plate dark map restricted to skin-ish neighbourhood: dark features, ignore bg (bg has no local contrast so OK)
    dp=dark_map(p)
    # remove edges of the head against the background: mask = eroded skin mask
    pa=np.asarray(p).astype(float)
    skin=((pa[...,0]-pa[...,2])>30)&(pa[...,0]>90)
    skin=np.asarray(Image.fromarray((skin*255).astype(np.uint8)).filter(ImageFilter.MinFilter(15)))>127
    dp=dp*skin
    rx0,ry0,rx1,ry1=[int((v-(box[0] if i%2==0 else box[1]))*2) for i,v in enumerate((x0,y0,x1,y1))]
    best=[]
    for az in range(24,50,2):
        m=Image.open(R+f'work/male-micro1h/r/yaw/{name}_{az}.png').convert('RGBA')
        bg=Image.new('RGBA',m.size,(190,140,105,255)); mm=Image.alpha_composite(bg,m).convert('RGB')
        al=np.asarray(m)[...,3]>127
        al=np.asarray(Image.fromarray((al*255).astype(np.uint8)).filter(ImageFilter.MinFilter(15)))>127
        dm=dark_map(mm)*al
        # translation search
        sc=-1; bs=None
        A=dp[ry0:ry1,rx0:rx1]
        for dy in range(-16,17,2):
            for dx in range(-24,25,2):
                B=dm[ry0+dy:ry1+dy,rx0+dx:rx1+dx]
                if B.shape!=A.shape: continue
                a=A-A.mean(); b=B-B.mean()
                c=(a*b).sum()/np.sqrt((a*a).sum()*(b*b).sum()+1e-9)
                if c>sc: sc=c; bs=(dx,dy)
        best.append((az,sc,bs))
    return best
for n in ('q3L','q3R'):
    print(n)
    for az,sc,bs in run(n): print('  az %2d  corr %.3f  shift(dx,dy 2x px) %s'%(az,sc,bs))
