import numpy as np
from PIL import Image
L='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/'
def s2l(x): x=np.asarray(x,float); return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def l2s(x): x=np.clip(x,0,1); return np.where(x<=.0031308,x*12.92,1.055*x**(1/2.4)-.055)
C=np.asarray(Image.open(L+'Basalt_C.png').convert('RGB'))/255.; N=np.asarray(Image.open(L+'Basalt_N.png').convert('RGB'))/255.*2-1; E=np.asarray(Image.open(L+'Basalt_E.png').convert('RGB'))/255.
print('C mean',(C*255).reshape(-1,3).mean(0).round(1),'max',(C*255).reshape(-1,3).max(0),'E mean',(E*255).reshape(-1,3).mean(0).round(2),'E max',(E*255).reshape(-1,3).max(0))
# lit view: key from upper-left-front at crater-like angle, plus ambient; with normal map; emission mult (1,.5,.35)
nz=np.sqrt(np.clip(1-N[...,0]**2-N[...,1]**2,0,1)); n=np.stack([N[...,0],N[...,1],nz],-1)
def lit(n,key=(-.5,.3,.8),keyc=(1.0,.80,.58)*1 ,I=2.3,amb=(.34,.24,.40),emul=(1,.8,.5)):
    k=np.array(key); k=k/np.linalg.norm(k)
    nl=np.clip((n*k).sum(-1),0,1)
    lin=s2l(C)*(s2l(np.array(keyc))*I*nl[...,None]*.9+s2l(np.array(amb))*1.2)+s2l(E)*np.array(emul)
    return (l2s(np.clip(lin,0,1))*255).astype(np.uint8)
g=lit(n)
Image.fromarray(g).save('basalt2_1x.png')
Image.fromarray(np.tile(g,(3,3,1))).resize((1200,1200),Image.LANCZOS).save('basalt2_3x3.png')
Image.fromarray(np.tile((C*255).astype(np.uint8),(3,3,1))).resize((1200,1200),Image.LANCZOS).save('basalt2_3x3_albedo.png')
# Tall box: 8 m tile; wall 6m wide x 12 m tall -> 0.75 x 1.5 tiles -> crop
t=np.tile(g,(2,2,1)); Image.fromarray(t[:int(1024*1.5),:768]).save('basalt2_wall.png')
# shade per plane: group columns?
lum=C.mean(2)
