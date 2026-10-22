import numpy as np
from PIL import Image
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/'
N=np.asarray(Image.open(R+'Basalt_N.png').convert('RGB')).astype(float)/255*2-1
C=np.asarray(Image.open(R+'Basalt_C.png').convert('RGB')).astype(float).mean(2)
nx=N[...,0];ny=N[...,1]
print('nx pct',np.percentile(nx,[1,5,25,50,75,95,99]).round(2))
for lo,hi in ((-1,-.25),(-.25,.25),(.25,1)):
    m=(nx>lo)&(nx<=hi); print('nx in',lo,hi,'frac %.3f'%m.mean(),'albedo lum mean %.1f'%C[m].mean())
# column-wise nx sign runs along a middle row: width of bevel bands in px
row=nx[512]; s=np.sign(np.where(abs(row)>.25,row,0))
runs=[];cur=s[0];n=1
for v in s[1:]:
    if v==cur:n+=1
    else: runs.append((int(cur),n));cur=v;n=1
print(runs[:60])
# horizontal gradient per column: tone variance between columns
colmean=C.mean(0); print('col mean lum range',colmean.min().round(1),colmean.max().round(1))
# ny: horizontal cracks
print('|ny|>.35 frac %.4f'%(abs(ny)>.35).mean())
