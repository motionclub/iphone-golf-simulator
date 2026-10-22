from pathlib import Path
import numpy as np
from PIL import Image
W=Path(__file__).parent
w,h=1536,768; xs=np.arange(w)/w;ys=np.arange(h)/h;u,v=np.meshgrid(xs,ys)
rows=4;columns=4
row=np.floor(v*rows).astype(int);shift=(row%2)*.5
x=(u*columns+shift)%1;y=(v*rows)%1;col=np.floor(u*columns+shift).astype(int)%columns
# Weathered ivory ashlar, roughly 0.72m x0.32m stones and a 9mm joint.
gapx=.013;gapy=.029
edgex=np.minimum(x,1-x);edgey=np.minimum(y,1-y)
bevel=np.clip(np.minimum((edgex-gapx)/.031,(edgey-gapy)/.045),0,1);bevel=bevel*bevel*(3-2*bevel)
joint=(edgex<gapx)|(edgey<gapy)
rng=np.random.default_rng(37);tone=rng.uniform(-.03,.025,(rows,columns))[row,col]
broad=.009*np.sin(u*2*np.pi*7+v*2*np.pi*2)+.006*np.cos(v*2*np.pi*11-u*2*np.pi*3)
grains=rng.normal(0,.002,(h,w));base=np.stack([.89+tone+broad+grains,.87+tone+broad+grains,.79+tone+broad+grains],-1)
base*= (.92+.08*bevel)[...,None];base[joint]=[.58,.59,.54]
height=.005*bevel + .00017*np.sin(u*2*np.pi*30)*np.sin(v*2*np.pi*19)
du=(np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))*(w/(2*2.88));dv=(np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))*(h/(2*1.28))
normal=np.stack([-du,-dv,np.ones((h,w))],-1);normal/=np.linalg.norm(normal,axis=-1)[...,None]
Image.fromarray(np.uint8(np.clip(base,0,1)*255)).save(W/'LimestoneAshlar_C.png')
Image.fromarray(np.uint8((normal*.5+.5)*255)).save(W/'LimestoneAshlar_N.png')
Image.fromarray(np.uint8(bevel*255)).save(W/'LimestoneAshlar_Height.png')
print('authored seamless limestone albedo/height/normal, physical repeat2.88x1.28m')
