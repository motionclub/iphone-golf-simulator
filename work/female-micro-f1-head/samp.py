import sys
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image
a=np.asarray(Image.open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/female_head_detail.jpg').convert('RGB')).astype(float)
def S(name,x,y,r=3):
    p=a[y-r:y+r+1,x-r:x+r+1].reshape(-1,3).mean(0); print(f'{name:14s} ({x},{y}) rgb {tuple(int(v) for v in p)}  lin01 {tuple(round(float(v)/255,3) for v in p)}')
S('forehead',259,100); S('forehead_hi',280,90); S('forehead_lo',259,125); S('cheek_L',222,195); S('cheek_R',297,195); S('cheek_shade',205,215); S('nose_tip',259,193)
S('chin',259,238); S('neck',259,245); S('jaw_shade',215,225); S('temple_L',205,150); S('upper_lip',259,213); S('lower_lip',259,222); S('lip_low',259,225)
S('brow',230,141,1); S('brow2',290,140,1); S('iris',229,172,2); S('iris_hi',222,170,1); S('pupil',229,166,2); S('sclera_out',203,168,1); S('sclera_in',244,166,1); S('lash',215,153,1)
S('ear_in',190,178,2); S('ear_rim',186,170,1); S('top_dome',259,80); S('back_profile',690,150,3)
