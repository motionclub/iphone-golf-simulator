import sys
from PIL import Image
pre=sys.argv[1]
k=0.0013043874429196725; top=1.7046599388122559
im=Image.open('../../ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB'); px=im.load()
def skin(p): r,g,b=p; return (r-g>12) and (g-b>7) and r>65
def mesh_mask(path):
    m=Image.open(path).convert('RGBA'); a=m.split()[3]; return a
# FRONT: panel x22..432,y66..352 ; mesh render is 2x of panel (820x572) 
fa=mesh_mask(f'{pre}_front.png').load()
print('FRONT half-widths (m):  z | plate | mesh')
for y in range(76,330,8):
    z=top-(y-76)*k
    xs=[x for x in range(22,432) if skin(px[x,y])]
    pw=(max(xs)-min(xs))/2*k if xs else 0
    row=(y-66)*2
    mx=[x for x in range(820) if fa[x,row]>127]
    mw=(max(mx)-min(mx))/2/2*k if mx else 0
    print(f'{z:.3f}  {pw:.4f}  {mw:.4f}  diff {1000*(mw-pw):+.1f}mm')
la=mesh_mask(f'{pre}_left.png').load()
print('LEFT front-most / back-most y (m): z | plate front, back | mesh front, back')
for y in range(76,330,8):
    z=top-(y-76)*k
    xs=[x for x in range(440,834) if skin(px[x,y])]
    row=(y-66)*2
    mx=[x for x in range(788) if la[x,row]>127]
    if xs and mx:
        pf=0.065+(min(xs)-712)*k; pb=0.065+(max(xs)-712)*k
        mf=0.065+(440+min(mx)/2-712)*k; mb=0.065+(440+max(mx)/2-712)*k
        print(f'{z:.3f}  {pf:+.4f} {pb:+.4f} | {mf:+.4f} {mb:+.4f}  dfront {1000*(mf-pf):+.1f}mm dback {1000*(mb-pb):+.1f}mm')
