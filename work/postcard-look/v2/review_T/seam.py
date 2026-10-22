import numpy as np,glob,os
from PIL import Image
L='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/'
for f in ['Fairway_C','Green_C','Rough_C','Scrub_C','Path_C','Lava_C','Lava_E','Lava_N','Basalt_C','Basalt_N','Basalt_E','Rock_C','Rock_N','Cliff_C','Cliff_N','CliffDark_C','CliffDark_N']:
    a=np.asarray(Image.open(L+f+'.png').convert('RGB')).astype(float)
    dx=np.abs(a[:,0]-a[:,-1]).mean(); dy=np.abs(a[0]-a[-1]).mean()
    ix=np.abs(a[:,1:]-a[:,:-1]).mean(); iy=np.abs(a[1:]-a[:-1]).mean()
    print('%-12s wrapx %.2f (interior %.2f, ratio %.2f) wrapy %.2f (interior %.2f ratio %.2f) %s'%(f,dx,ix,dx/ix,dy,iy,dy/iy,Image.open(L+f+'.png').size))
