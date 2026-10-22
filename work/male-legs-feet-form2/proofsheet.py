"""python proofsheet.py <before_dir> <after_dir> <out.png> <view,view,...> [rows: 'full'|'feet']
rows of: plate | BEFORE | AFTER | outlines (after red, plate-mask green) ; legs crop z 0..0.80 (feet crop z 0..0.26)"""
import sys, json
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image, ImageDraw
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
B,A,OUT,views=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4].split(',')
mode=sys.argv[5] if len(sys.argv)>5 else 'full'
cams={v['name']:v for v in json.load(open(R+'/work/male-legs-feet-form2/data/plates/reference-cameras.json'))['views']}
Q3=json.load(open(R+'/work/male-legs-feet-form2/data/plates/q3cams.json'))
for k,c_ in Q3.items(): cams[k]=dict(metres_per_pixel=c_['mpp'],sole_y=int(c_['sole']),centre_x=c_['ox'])
pl={'bald':Image.open(R+'/ArtDir/hero/base_lock/male_body_bald.jpg').convert('RGB'),'sheet':Image.open(R+'/ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')}
def edge(m):
    e=np.zeros_like(m); e[1:-1,1:-1]=m[1:-1,1:-1]&~(m[:-2,1:-1]&m[2:,1:-1]&m[1:-1,:-2]&m[1:-1,2:]); return e
def tgt(v):
    p=R+f'/work/male-legs-feet-form2/data/plates/'+(f'plate_mask_{v}.png' if v.startswith('q3') else f'{v}_target.png')
    return np.array(Image.open(p).convert('L'))>127
def comp(path):
    im=Image.open(path).convert('RGBA'); bg=Image.new('RGBA',im.size,(54,54,58,255)); bg.alpha_composite(im); return np.array(bg.convert('RGB')),np.array(im)[:,:,3]>127
tiles_rows=[]
for v in views:
    c=cams[v]; mpp=c['metres_per_pixel']; sole=c['sole_y']; cx=c['centre_x']
    top=0.80 if mode=='full' else 0.26
    y0=int(sole-top/mpp); y1=sole+8
    half=(0.34 if (v.startswith('bald') or v.startswith('q3')) else 0.30)/mpp
    if mode=='feet': half=0.40/mpp if v!='left' and v!='right' else 0.30/mpp
    x0=int(cx-half); x1=int(cx+half)
    plate=np.array(pl['bald' if v.startswith('bald') else 'sheet']).copy()
    rb,mb=comp(f'{B}/{v}.png'); ra,ma=comp(f'{A}/{v}.png'); t=tgt(v)
    ov=plate.copy(); ov[edge(t)]=(60,255,60); ov[edge(mb)]=(90,160,255); ov[edge(ma)]=(255,50,50)
    sc=3 if (v.startswith('bald')) else 4
    if mode=='feet': sc=5 if v.startswith('bald') else 6
    tl=[Image.fromarray(a[y0:y1,x0:x1]).resize(((x1-x0)*sc,(y1-y0)*sc),Image.LANCZOS) for a in (plate,rb,ra,ov)]
    labs=['PLATE '+v,'PASS (current ArtDir)','FORM2 (this job)','outlines: plate green | PASS blue | FORM2 red']
    W=sum(t_.width for t_ in tl)+6*3; row=Image.new('RGB',(W,tl[0].height),(20,20,24)); xx=0
    for t_,lb in zip(tl,labs):
        row.paste(t_,(xx,0)); ImageDraw.Draw(row).text((xx+4,4),lb,fill=(255,255,0)); xx+=t_.width+6
    tiles_rows.append(row)
H=sum(r.height for r in tiles_rows)+6*(len(tiles_rows)-1); W=max(r.width for r in tiles_rows)
sh=Image.new('RGB',(W,H),(20,20,24)); yy=0
for r in tiles_rows: sh.paste(r,(0,yy)); yy+=r.height+6
sh.save(OUT); print(OUT,sh.size)
