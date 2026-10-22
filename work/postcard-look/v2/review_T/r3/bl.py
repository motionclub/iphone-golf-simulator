import numpy as np
from PIL import Image
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
def s2l(x): x=np.asarray(x,float); return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def l2s(x): x=np.clip(x,0,1); return np.where(x<=.0031308,x*12.92,1.055*x**(1/2.4)-.055)
tint=np.array([.52,.80,.92]); tl=s2l(tint)
for name,d in (('v3',R+'work/postcard-look/v2/tex/v4/before/'),('v4',R+'Unity/Assets/Resources/Course/Look/')):
    C=np.asarray(Image.open(d+'Basalt_C.png').convert('RGB'))/255.
    N=np.asarray(Image.open(d+'Basalt_N.png').convert('RGB'))/255.*2-1
    nz=np.sqrt(np.clip(1-N[...,0]**2-N[...,1]**2,0,1)); n=np.stack([N[...,0],N[...,1],nz],-1)
    lin=s2l(C)
    # key light fitted constants WALL_LIGHT (3.674,1.3065,.736) flat (no normal)
    WL=np.array([3.674,1.3065,.736])
    flat=lin*tl*WL
    # lit with normal: use directional light from several azimuths, average
    res=[]
    for k in [(0,0,1),(-.5,.3,.8),(.5,.3,.8),(0,.5,.85),(.7,0,.7)]:
        k=np.array(k,float);k/=np.linalg.norm(k)
        nl=np.clip((n*k).sum(-1),0,1)
        L=lin*tl*WL*nl[...,None]
        sr=l2s(np.clip(L,0,1))*255
        lum=(sr*[.2126,.7152,.0722]).sum(-1)
        res.append((np.median(lum),sr.reshape(-1,3).mean(0).round(0)))
    sf=l2s(np.clip(flat,0,1))*255
    lum=(sf*[.2126,.7152,.0722]).sum(-1)
    print(name,'albedo mean',(C*255).reshape(-1,3).mean(0).round(1),'flat lit median lum %.1f mean'%np.median(lum),sf.reshape(-1,3).mean(0).round(1),'mean(nz) %.3f'%nz.mean())
    for r in res: print('   key lit',r)
