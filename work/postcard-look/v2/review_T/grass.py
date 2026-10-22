import numpy as np, colorsys
from PIL import Image
L='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/'
def s2l(x): x=np.asarray(x,float); return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def l2s(x): x=np.clip(x,0,1); return np.where(x<=.0031308,x*12.92,1.055*x**(1/2.4)-.055)
def rgb(*c): return np.array(c,float)
holes={
 8:dict(keys=[((1,.86,.66),2.3,30),((.80,.88,1),.8,35),((1,.78,.55),.5,10)],sky=(.42,.58,.86)),
 9:dict(keys=[((1,.95,.86),2.3,42),((.74,.85,1),.8,40),((1,.92,.80),.3,14)],sky=(.42,.58,.86)),
 10:dict(keys=[((1,.80,.58),2.3,32),((.62,.55,.90),.55,35)],sky=(.34,.24,.40)),
}
def light(h):
    d=holes[h]; Lc=np.zeros(3)
    for c,i,el in d['keys']:
        if h==10 and c==(.62,.55,.90): continue
        Lc+=s2l(rgb(*c))*i*np.sin(np.radians(el))
    sky=s2l(rgb(*d['sky']))
    if h==10: sky=sky+s2l(rgb(.62,.55,.90))*.55*np.sin(np.radians(35))
    return Lc+sky
tints={8:{},9:{'F':(.76,.84,.72),'G':(.76,.84,.72),'R':(.80,.86,.76)},10:{'F':(.90,1.15,.62),'G':(.90,1.15,.62),'R':(.90,1.10,.62)}}
files={'F':'Fairway_C.png','G':'Green_C.png','R':'Rough_C.png','S':'Scrub_C.png'}
def hue(c): 
    r,g,b=[x/255 for x in c]; h,s,v=colorsys.rgb_to_hsv(r,g,b); return h*360,s,v
for h in (8,9,10):
    Ls=light(h); print('hole',h,'L',Ls.round(3))
    for k,f in files.items():
        a=np.asarray(Image.open(L+f).convert('RGB').resize((256,256),Image.BOX))/255.
        t=tints[h].get(k,(.94,.94,.94))
        out=np.clip(s2l(a)*s2l(rgb(*t))*Ls,0,1)
        m=l2s(out).reshape(-1,3).mean(0)*255
        # also hue distribution
        hs=np.array([colorsys.rgb_to_hsv(*x)[0]*360 for x in l2s(out).reshape(-1,3)[::37]])
        print(' ',k,'tint',t,'mean',m.round(0),'hue %.1f S %.2f V %.2f'%hue(m),'texel hue p10/50/90',np.percentile(hs,[10,50,90]).round(0))
