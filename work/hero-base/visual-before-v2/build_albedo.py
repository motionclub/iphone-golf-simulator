"""Deterministic pigment-only head atlases. No source photograph or baked illumination."""
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[2]/'ArtDir/hero/base_lock/unity_import/Textures';P.mkdir(parents=True,exist_ok=True)
N=2048;u=(np.arange(N)+.5)/N;v=(np.arange(N)+.5)/N;ang=(u-.5)*np.pi*2;x=48*np.sin(ang);y=50+v*155
for sex,color in [('Male',(.705,.465,.305)),('Female',(.735,.515,.355))]:
 a=np.broadcast_to(np.array(color,dtype=np.float32),(N,N,3)).copy();Y=y[:,None];X=x[None,:];front=np.exp(-(ang[None,:]/1.0)**8)
 if sex=='Male':
  beard=np.clip((Y-130)/20,0,1)*np.clip((175-Y)/9,0,1)*front
  mouth=np.exp(-(X/24)**6-((Y-141)/9)**6);beard*=1-mouth
  rng=np.random.default_rng(912);dots=(rng.random((N,N))>.90).astype(np.float32);grain=rng.random((N,N)).astype(np.float32)
  pigment=beard*(.055+.11*dots+.015*grain);a-=pigment[:,:,None]*np.array([.36,.31,.26])
 else:
  blush=(np.exp(-((X-27)/12)**2-((Y-158)/11)**2)+np.exp(-((X+27)/12)**2-((Y-158)/11)**2))*front
  a+=blush[:,:,None]*np.array([.020,-.004,-.002])
 Image.fromarray(np.uint8(np.clip(a,0,1)*255)).save(P/('Head_'+sex+'_Albedo.png'))
