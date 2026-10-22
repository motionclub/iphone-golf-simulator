import numpy as np
from PIL import Image
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
def s2l(x): x=np.asarray(x,float); return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def l2s(x): x=np.clip(x,0,1); return np.where(x<=.0031308,x*12.92,1.055*x**(1/2.4)-.055)
for name,d in (('v3',R+'work/postcard-look/v2/tex/v4/before/'),('v4',R+'Unity/Assets/Resources/Course/Look/')):
    E=np.asarray(Image.open(d+'Basalt_E.png').convert('RGB'))/255.
    el=s2l(E)*np.array([1,.8,.5])   # Emission color applied (maybe lin-converted)
    print(name,'E mean lin*mult',el.reshape(-1,3).mean(0), 'in sRGB units', (l2s(el.reshape(-1,3).mean(0))*255).round(1), 'frac E>20', (E.max(2)*255>20).mean())
