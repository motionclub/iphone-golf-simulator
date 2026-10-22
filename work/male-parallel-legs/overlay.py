"""python overlay.py <sildir> <out.png>  : legs overlay, plate + mesh(red)/target(green) outlines, front & back"""
import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image
D=sys.argv[1]; O=sys.argv[2]
plate=Image.open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/male_body_bald.jpg').convert('RGB')
def edge(m):
    e=np.zeros_like(m)
    e[1:-1,1:-1]=m[1:-1,1:-1]&~(m[:-2,1:-1]&m[2:,1:-1]&m[1:-1,:-2]&m[1:-1,2:]); return e
tiles=[]
for view,x0,x1 in (('bald_front',230,480),('bald_back',790,1040)):
    r=np.load(f'{D}/{view}_mask.npy')[::-1]; t=np.load(f'{D}/{view}_target.npy')[::-1]
    a=np.array(plate).copy()
    a[edge(t)]=(60,255,60); a[edge(r)]=(255,40,40)
    # XOR
    x=np.zeros_like(a); x[r&t]=(70,70,70); x[r&~t]=(255,60,60); x[~r&t]=(60,160,255)
    c=Image.fromarray(a[320:670,x0:x1]).resize(((x1-x0)*3,350*3),Image.NEAREST)
    cx=Image.fromarray(x[320:670,x0:x1]).resize(((x1-x0)*3,350*3),Image.NEAREST)
    tiles+= [c,cx]
W=sum(t.width for t in tiles); H=tiles[0].height
sh=Image.new('RGB',(W,H)); xx=0
for t in tiles: sh.paste(t,(xx,0)); xx+=t.width
sh.save(O); print(sh.size)
