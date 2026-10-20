"""python feetcmp.py <renderdir> <out.png> : near/far foot crops of the 4 three-quarter plates vs mesh (bigger margins)"""
import sys, json
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
Q3=json.load(open(R+'/work/male-parallel-legs/data/q3cams.json'))
plate=Image.open(R+'/ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
D=sys.argv[1]; z=6
rows=[]
for v in ('q3FL','q3FR','q3BL','q3BR'):
    c=Q3[v]; mpp=c['mpp']; sole=c['sole']; ox=c['ox']
    y0=int(sole-0.20/mpp); y1=int(sole+10); x0=int(ox-0.46/mpp); x1=int(ox+0.46/mpp)
    mesh=Image.open(f'{D}/{v}.png').convert('RGBA'); bg=Image.new('RGBA',mesh.size,(54,54,58,255)); bg.alpha_composite(mesh)
    a=plate.crop((x0,y0,x1,y1)).resize(((x1-x0)*z,(y1-y0)*z),Image.LANCZOS); b=bg.convert('RGB').crop((x0,y0,x1,y1)).resize(((x1-x0)*z,(y1-y0)*z),Image.LANCZOS)
    r=Image.new('RGB',(a.width,a.height*2+4)); r.paste(a,(0,0)); r.paste(b,(0,a.height+4)); rows.append(r)
W=rows[0].width; H=rows[0].height
sh=Image.new('RGB',(W*2+6,H*2+6))
for i,r in enumerate(rows): sh.paste(r,((i%2)*(W+6),(i//2)*(H+6)))
sh.save(sys.argv[2]); print(sh.size)
