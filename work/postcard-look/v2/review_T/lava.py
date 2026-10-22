import numpy as np, colorsys
from PIL import Image
L='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/'
def s2l(x): x=np.asarray(x,float); return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def l2s(x): x=np.clip(x,0,1); return np.where(x<=.0031308,x*12.92,1.055*x**(1/2.4)-.055)
C=np.asarray(Image.open(L+'Lava_C.png').convert('RGB'))/255.; E=np.asarray(Image.open(L+'Lava_E.png').convert('RGB'))/255.
Lc=np.array([1.421,.866,.742])
def hsv(m): return colorsys.rgb_to_hsv(*(m/255))
for name,tint,mult in [('builder-assumed (no tint, x1.1)',(1,1,1),(1.1,1.1,1.1)),('builder old mult (1.3,.85,.55) no tint',(1,1,1),(1.3,.85,.55)),('ACTUAL file: tint .75, mult (1,.65,.5)',(.75,.75,.75),(1.0,.65,.5)),('tint .75 mult 1.1 scalar',(.75,.75,.75),(1.1,1.1,1.1)),('tint .75 old mult',(.75,.75,.75),(1.3,.85,.55))]:
    lin=s2l(C)*s2l(np.array(tint))*Lc+s2l(E)*np.array(mult)
    o=l2s(np.clip(lin,0,1))*255
    m=o.reshape(-1,3).mean(0); lum=(o*[.299,.587,.114]).sum(2)
    dark=(o.max(2)<90).mean(); glow=((o[...,0]>180)).mean()
    h,s,v=hsv(m)
    print(name,'mean',m.round(0),'hue %.0f S %.2f V %.2f'%(h*360,s,v),'dark<90 %.3f'%dark,'R>180 %.3f'%glow,'p50 R',np.percentile(o[...,0],50).round(0),'clipR %.3f'%(lin[...,0]>1).mean(),'G>200&B>110 %.4f'%((o[...,1]>200)&(o[...,2]>110)).mean())
print('E max',E.reshape(-1,3).max(0),'C mean',(C*255).reshape(-1,3).mean(0).round(0),'E mean',(E*255).reshape(-1,3).mean(0).round(1))
