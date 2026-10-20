import numpy as np
from PIL import Image
from pathlib import Path
import sys
sys.path.insert(0,'Tools/HeroBase');from plate_profiles import MALE,FEMALE
for suf,p in [('M',MALE),('F',FEMALE)]:
 f=Image.open('ArtDir/hero/base_lock/proof/masks/'+suf+'_front_target.png').crop((p['cx']-280,0,p['cx']+280,720));back=Image.open('ArtDir/hero/base_lock/proof/masks/'+suf+'_back_target.png').crop((p['back_cx']-280,0,p['back_cx']+280,720)).transpose(Image.Transpose.FLIP_LEFT_RIGHT);A=np.array(f)>0
 best=(1,None)
 for scale in np.arange(.97,1.011,.005):
  b=back.resize((round(560*scale),round(720*scale)),Image.Resampling.NEAREST)
  for dx in range(-5,6):
   for dy in range(-8,9,2):
    aligned=Image.new('L',(560,720));aligned.paste(b,((560-b.width)//2+dx,dy));B=np.array(aligned)>0;e=(A^B).sum()/(A|B).sum()
    if e<best[0]:best=(e,(float(scale),dx,dy))
 print(suf,best)
