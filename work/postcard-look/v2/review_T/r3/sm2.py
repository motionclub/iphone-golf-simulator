import numpy as np
from PIL import Image
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/'
a=np.asarray(Image.open(R+'Smoke_C.png').convert('RGBA')).astype(float)
al=a[...,3]/255
for lo,hi in ((0,0.0001),(0.0001,.02),(.02,.1),(.1,.25),(.25,.4),(.4,.6)):
    m=(al>=lo)&(al<hi) if lo>0 else (al==0)
    if m.sum(): print('alpha [%.3f,%.3f) n=%d rgb mean'%(lo,hi,m.sum()),a[...,:3][m].mean(0).round(1),'std',a[...,:3][m].std(0).round(1))
# alpha histogram of colour levels quantisation: 8-bit alpha steps -> banding?
u=np.unique(a[...,3]); print('unique alpha levels',len(u),'max',u.max())
# gradient
gy,gx=np.gradient(al); print('max step %.4f'%np.hypot(gx,gy).max())
# radial roundness: centroid, second moment, convexity of >.1 region
m=al>.1; ys,xs=np.nonzero(m); print('bbox',xs.min(),xs.max(),ys.min(),ys.max(),'area frac %.3f'%m.mean())
# left-right edge columns/rows of >0.01
print('alpha>0.005 bbox', np.nonzero(al.max(0)>.005)[0][[0,-1]], np.nonzero(al.max(1)>.005)[0][[0,-1]])
# rim ring: darker colour at alpha .02-.1 vs interior?
