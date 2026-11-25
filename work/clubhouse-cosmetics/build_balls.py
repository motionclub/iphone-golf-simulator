from PIL import Image,ImageDraw
from pathlib import Path
import math
R=Path(__file__).resolve().parents[2]
for style in ['orbit','melon','checker','sunset']:
 im=Image.new('RGB',(512,256));px=im.load()
 for y in range(256):
  v=y/255
  for x in range(512):
   u=x/512
   if style=='orbit':
    c=(240,240,248)
    if abs(v-.5)<.105:c=(98,53,196)
    if .115<abs(v-.5)<.14:c=(39,210,194)
   elif style=='melon':
    c=(247,98,131)
    if abs(v-.5)>.35:c=(38,140,85) if abs(v-.5)>.39 else (216,245,159)
    if abs(v-.5)<.28 and ((u*18)%1-.5)**2/.018+((v*9)%1-.5)**2/.075<1:c=(46,39,62)
   elif style=='checker':
    c=(250,244,223)
    if abs(v-.5)<.18:c=(30,49,62) if (int(u*24)+int(v*16))%2 else (250,244,223)
    if .19<abs(v-.5)<.215:c=(255,139,54)
   else:
    stops=[(255,234,149),(255,161,91),(240,91,125),(143,75,180)]
    t=v*3;i=min(2,int(t));f=min(1,t-i);c=tuple(int(a*(1-f)+b*f) for a,b in zip(stops[i],stops[i+1]))
    if abs(v-.5)<.016:c=(255,245,215)
   px[x,y]=c
 for d in [R/'Unity/Assets/Resources/Cosmetics',R/'GolfArcade/Unity/CharacterAssets']:
  im.save(d/f'ball_{style}.png')
print('Four seamless 512x256 ball patterns')
