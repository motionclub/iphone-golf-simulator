import sys
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image
P='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/'
im=np.asarray(Image.open(P+'female_head_detail.jpg').convert('RGB')).astype(float)
R,G,B=im[...,0],im[...,1],im[...,2]
skin=((R-B)>28)&(R>G)&(G>B)&(R>150)
print('skin px',skin.sum())
# panels
panels={'front':(85,55,430,342),'left':(440,55,800,342),'right':(830,55,1195,342),'q3L':(85,385,430,656),'q3R':(440,385,800,656),'top':(830,385,1195,656)}
for k,(x0,y0,x1,y1) in panels.items():
    m=skin[y0:y1,x0:x1]
    ys,xs=np.where(m)
    print(k,'skin bbox x',xs.min()+x0,xs.max()+x0,'y',ys.min()+y0,ys.max()+y0)
out=np.zeros(im.shape,np.uint8); out[skin]=255
Image.fromarray(out).save('plates/skin_mask_head.png')
for name in ['female_body_bald.jpg','female_multiangle_body.jpg']:
    a=np.asarray(Image.open(P+name).convert('RGB')).astype(float)
    s=((a[...,0]-a[...,2])>28)&(a[...,0]>a[...,1])&(a[...,1]>a[...,2])&(a[...,0]>150)
    o=np.zeros(a.shape,np.uint8); o[s]=255; Image.fromarray(o).save('plates/skin_mask_'+name.replace('.jpg','.png'))
