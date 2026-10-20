import sys, numpy as np
from PIL import Image
d='work/character-shader/proof/'
for n in sys.argv[1:]:
    a=np.asarray(Image.open(d+n+'.png').convert('RGB')).astype(int); b=np.asarray(Image.open(d+n+'_norim.png').convert('RGB')).astype(int)
    diff=np.abs(a-b).sum(2)
    # court-ish pixels: blue dominant
    court=(b[:,:,2]>b[:,:,0]+60)&(b[:,:,2]>b[:,:,1]+40)
    print(f'{n}: changed>6 {int((diff>6).sum())} px, max {diff.max()}; court px {int(court.sum())}, court changed>3 {int((diff[court]>3).sum())}, court max {diff[court].max() if court.any() else 0}')
    Image.fromarray(np.clip(diff*4,0,255).astype('uint8')).save(d+n+'_rimdiff.png')
