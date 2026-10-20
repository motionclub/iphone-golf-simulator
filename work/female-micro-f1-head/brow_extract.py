import sys
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image
P='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/'
a=np.asarray(Image.open(P+'female_head_detail.jpg').convert('RGB')).astype(float)
V=a.mean(axis=2)
dark=(V<115)
# left brow region cols 198..250, rows 128..152 ; right brow cols 268..320
for name,(c0,c1) in (('left',(198,250)),('right',(268,320))):
    print(name)
    for c in range(c0,c1,3):
        rows=np.where(dark[126:152,c])[0]+126
        print(c, (rows.min(),rows.max()) if len(rows) else None)
# eye lash line (black V<70) rows 148..182 cols 182..250 left
print('lash/eye dark extents left eye, top edge per col and bottom edge per col')
for c in range(184,252,4):
    rows=np.where(V[148:184,c]<80)[0]+148
    print(c, (rows.min(),rows.max()) if len(rows) else None)
