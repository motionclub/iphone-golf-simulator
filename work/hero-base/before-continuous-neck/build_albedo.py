"""Deterministic pigment-only head atlases. No source photograph or baked illumination."""
from pathlib import Path
import numpy as np
from PIL import Image
from plate_profiles import MALE,FEMALE
P=Path(__file__).resolve().parents[2]/'ArtDir/hero/base_lock/unity_import/Textures';P.mkdir(parents=True,exist_ok=True)
N=2048;u=(np.arange(N)+.5)/N;v=(np.arange(N)+.5)/N;ang=(u-.5)*np.pi*2;x=48*np.sin(ang);y=24+v*158
for sex,profile in [('Male',MALE),('Female',FEMALE)]:
 color=profile['skin']
 a=np.broadcast_to(np.array(color,dtype=np.float32),(N,N,3)).copy();Y=y[:,None];X=x[None,:];front=np.exp(-(ang[None,:]/1.0)**8)
 if sex=='Male':
  beard=np.clip((Y-121)/15,0,1)*np.clip((156-Y)/6,0,1)*front
  mouth=np.exp(-(X/24)**6-((Y-131)/5)**6);beard*=1-mouth
  rng=np.random.default_rng(912);dots=(rng.random((N,N))>.90).astype(np.float32);grain=rng.random((N,N)).astype(np.float32)
  pigment=beard*(.16+.05*dots+.015*grain);a-=pigment[:,:,None]*np.array([.38,.31,.26])
  # A continuous pigment boundary forms the oval skin/grey collar without
  # quantizing the curve to the body mesh's coarse surface-net rows.
  collar=(177-9*(X/32)**2)*front+157*(1-front)
  grey=np.clip((Y-collar+.6)/1.2,0,1)*np.clip((Y-154)/2,0,1)
  a=a*(1-grey[:,:,None])+np.array([.48,.48,.48])*grey[:,:,None]
 else:
  blush=(np.exp(-((X-27)/12)**2-((Y-96)/9)**2)+np.exp(-((X+27)/12)**2-((Y-96)/9)**2))*front
  a+=blush[:,:,None]*np.array([.020,-.004,-.002])
  collar=135.5*front+135*(1-front)
  grey=np.clip((Y-collar+.6)/1.2,0,1)
  a=a*(1-grey[:,:,None])+np.array(profile['grey'])*grey[:,:,None]
 Image.fromarray(np.uint8(np.clip(a,0,1)*255)).save(P/('Head_'+sex+'_Albedo.png'))
