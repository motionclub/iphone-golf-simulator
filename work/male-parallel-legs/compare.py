"""python compare.py <renderdir> <out.png> [views] : per view  plate legs | mesh legs | outlines (mesh red, plate-mask green) | XOR.  Needs PIL+numpy (Blender python + PYTHONPATH=../male-micro1i/pylib)"""
import sys, json
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image, ImageDraw
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
D=sys.argv[1]; O=sys.argv[2]
views=sys.argv[3].split(',') if len(sys.argv)>3 else ['bald_front','bald_back','sheet_front','sheet_back','left','right','q3FL','q3FR','q3BL','q3BR']
cams={v['name']:v for v in json.load(open(R+'/work/male-silhouette/reference-cameras.json'))['views']}
Q3=json.load(open(R+'/work/male-parallel-legs/data/q3cams.json'))
for k,c_ in Q3.items(): cams[k]=dict(metres_per_pixel=c_['mpp'],sole_y=int(c_['sole']),centre_x=c_['ox'])
pl={'bald':Image.open(R+'/ArtDir/hero/base_lock/male_body_bald.jpg').convert('RGB'),'sheet':Image.open(R+'/ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')}
def edge(m):
    e=np.zeros_like(m); e[1:-1,1:-1]=m[1:-1,1:-1]&~(m[:-2,1:-1]&m[2:,1:-1]&m[1:-1,:-2]&m[1:-1,2:]); return e
def tgt(view):
    from PIL import Image as I
    p=R+(f'/work/male-parallel-legs/data/plate_mask_{view}.png' if view.startswith('q3') else f'/work/male-silhouette/{view}_target.png')
    a=np.array(I.open(p).convert('L')); return a>127
rows=[]
for v in views:
    c=cams[v]; mpp=c['metres_per_pixel']; sole=c['sole_y']; cx=c['centre_x']
    y0=int(sole-0.80/mpp); y1=sole+8
    half=0.34/mpp if v.startswith('bald') else 0.30/mpp
    if v.startswith('q3'): half=0.34/mpp
    if v in('left','right'): half=0.30/mpp
    x0=int(cx-half); x1=int(cx+half)
    plate=np.array(pl['bald' if v.startswith('bald') else 'sheet']).copy()
    mesh=np.array(Image.open(f'{D}/{v}.png').convert('RGBA'))
    m=mesh[:,:,3]>127
    t=tgt(v)
    bg=np.full_like(plate,(54,54,58)); mrgb=bg.copy(); mrgb[m]=mesh[m,:3]
    ov=plate.copy(); ov[edge(t)]=(60,255,60); ov[edge(m)]=(255,40,40)
    xr=np.zeros_like(plate); xr[m&t]=(70,70,70); xr[m&~t]=(255,60,60); xr[~m&t]=(60,160,255)
    sc=4 if not v.startswith('bald') else 3
    tiles=[Image.fromarray(a[y0:y1,x0:x1]).resize(((x1-x0)*sc,(y1-y0)*sc),Image.LANCZOS) for a in (plate,mrgb,ov,xr)]
    W=sum(t.width for t in tiles); sh=Image.new('RGB',(W,tiles[0].height)); xx=0
    for t_ in tiles: sh.paste(t_,(xx,0)); xx+=t_.width
    ImageDraw.Draw(sh).text((6,6),v,fill=(255,255,0))
    rows.append(sh)
    sh.save(O.replace('.png',f'_{v}.png'))
print('done')
