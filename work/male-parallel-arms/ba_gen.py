"""generic before/after: py.sh ba_gen.py <tag_after> <out.png> <target x,y,z> <ortho> view1:dx,dy,dz[:lp:ly] ..."""
import sys, subprocess, os
from pathlib import Path
from PIL import Image, ImageDraw
W=Path(__file__).resolve().parent
tag,out,tgt,osc=sys.argv[1:5]; vs=sys.argv[5:]
B='/Applications/Blender.app/Contents/MacOS/Blender'
views=[]
for v in vs:
    p=v.split(':'); views.append(f"{p[0]}:{tgt}:{p[1]}:{osc}:{p[2] if len(p)>2 else 55}:{p[3] if len(p)>3 else -40}")
def rend(name,coords):
    env=dict(os.environ); env['CLIP']=os.environ.get('CLIP','0.25')
    if coords: env['COORDS']=str(coords)
    d=W/f'proof/bag/{name}'; d.mkdir(parents=True,exist_ok=True)
    subprocess.run([B,'-b',str(W/'baseline/HeroBase_Male_Silhouette.blend'),'--python',str(W/'closeup.py'),'--',str(d)]+views,env=env,capture_output=True)
    return d
d0=rend('before',None); d1=rend(tag,W/f'data/{tag}.npy' if (W/f'data/{tag}.npy').exists() else W/f'data/it/{tag}_cur.npy')
names=[v.split(':')[0] for v in views]; n=len(names); s=420
S=Image.new('RGB',(n*s,2*s+30),(24,24,28)); dr=ImageDraw.Draw(S)
for i,nm in enumerate(names):
    for j,(lab,d) in enumerate((('BEFORE',d0),('AFTER',d1))):
        S.paste(Image.open(d/f'{nm}.png').convert('RGB').resize((s,s)),(i*s,j*(s+30)))
        dr.text((i*s+6,j*(s+30)+4),f'{lab} · {nm}',fill=(255,255,0))
S.save(out); print(S.size)
