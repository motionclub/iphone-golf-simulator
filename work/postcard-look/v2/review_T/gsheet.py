import numpy as np
from PIL import Image
exec(open('grass.py').read().split("for h in (8,9,10):")[0])
rows=[]
for h in (8,9,10):
    row=[]
    for k in 'FGRS':
        a=np.asarray(Image.open(L+files[k]).convert('RGB').resize((384,384),Image.BOX))/255.
        t=tints[h].get(k,(.94,.94,.94))
        o=l2s(np.clip(s2l(a)*s2l(rgb(*t))*light(h),0,1))
        row.append((o*255).astype(np.uint8))
    rows.append(np.concatenate(row,1))
Image.fromarray(np.concatenate(rows,0)).save('grass_sheet.png')
