import numpy as np, sys
from PIL import Image
L='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/'
def s2l(x): x=np.asarray(x,float); return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def l2s(x): x=np.clip(x,0,1); return np.where(x<=.0031308,x*12.92,1.055*x**(1/2.4)-.055)
Lc=np.array([1.421,.866,.742])
C=np.asarray(Image.open(L+'Lava_C.png').convert('RGB'))/255.; E=np.asarray(Image.open(L+'Lava_E.png').convert('RGB'))/255.
lin=s2l(C)*s2l(np.array([.75]*3))*Lc+s2l(E)*np.array([1,.65,.5])
g=(l2s(np.clip(lin,0,1))*255).astype(np.uint8)
t=np.tile(g,(3,3,1)); Image.fromarray(t).resize((1200,1200),Image.LANCZOS).save('lava_3x3_actual.png')
g2=(l2s(np.clip(s2l(C)*Lc+s2l(E)*1.1,0,1))*255).astype(np.uint8)
Image.fromarray(np.tile(g2,(3,3,1))).resize((1200,1200),Image.LANCZOS).save('lava_3x3_builder.png')
# grazing: perspective warp of 4x4 tile 
t4=Image.fromarray(np.tile(g,(4,4,1))).resize((1600,1600))
W,H=900,500
out=np.zeros((H,W,3),np.uint8)
a=np.asarray(t4)
for y in range(H):
    d=1.0/(0.06+ (y/H)*0.94)  # depth
    for x in range(0,W):
        pass
ys=np.arange(H); xs=np.arange(W)
Y,X=np.meshgrid(ys,xs,indexing='ij')
depth=1.0/(0.05+0.95*(Y/H))
u=((X-W/2)/W*depth*0.8+0.5)%1; v=(depth*0.35)%1
out=a[(v*1599).astype(int),(u*1599).astype(int)]
Image.fromarray(out).save('lava_grazing_actual.png')
