"""Deterministic tileable geological albedo/normal assets, not edits of reference images."""
from pathlib import Path
import numpy as np
from PIL import Image
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');out=root/'Unity/Assets/Resources/Course/Resort'
size=512;rng=np.random.default_rng(20261007)
def noise(cells):
 grid=rng.random((cells+1,cells+1)).astype(np.float32);grid[-1,:]=grid[0,:];grid[:,-1]=grid[:,0]
 axis=np.linspace(0,cells,size,endpoint=False);lo=axis.astype(int);f=axis-lo;f=f*f*(3-2*f)
 a=grid[lo[:,None],lo[None,:]];b=grid[lo[:,None],(lo+1)[None,:]];c=grid[(lo+1)[:,None],lo[None,:]];d=grid[(lo+1)[:,None],(lo+1)[None,:]]
 return (a*(1-f[None,:])+b*f[None,:])*(1-f[:,None])+ (c*(1-f[None,:])+d*f[None,:])*f[:,None]
for name,low,high in [('Limestone',(120,116,99),(198,192,161)),('ResortBasalt',(37,43,49),(91,96,99))]:
 broad=noise(5);detail=noise(19);fine=noise(61)
 value=np.clip(broad*.58+detail*.29+fine*.13,0,1)
 # Discontinuous capillary cracks follow an irregular noise contour, not vertical rows.
 contour=noise(9)+noise(23)*.21
 cracks=np.clip((.018-np.abs(contour-.58))/.018,0,1)*np.clip((detail-.30)*2,0,1)
 value=np.clip(value-cracks*.16,0,1)
 rgb=np.asarray(low)[None,None,:]+value[:,:,None]*(np.asarray(high)-np.asarray(low))[None,None,:]
 alpha=(cracks*85).astype(np.uint8) if name=='ResortBasalt' else np.full((size,size),255,dtype=np.uint8)
 Image.fromarray(np.dstack([rgb.astype(np.uint8),alpha]),'RGBA').save(out/(name+'_C.png'))
 height=detail*.32+fine*.08-cracks*.10
 dx=(np.roll(height,-1,1)-np.roll(height,1,1))*1.6;dy=(np.roll(height,-1,0)-np.roll(height,1,0))*1.6
 n=np.dstack([-dx,-dy,np.ones_like(dx)]);n/=np.sqrt((n*n).sum(axis=2,keepdims=True))
 Image.fromarray(np.uint8((n*.5+.5)*255),'RGB').save(out/(name+'_N.png'))
print('RESORT_GEOLOGY_TEXTURES_COMPLETE')
