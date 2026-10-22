"""before/after hand sheet. usage: py.sh ba_sheet.py <tag_after> <out.png>"""
import sys, subprocess, os
from pathlib import Path
from PIL import Image, ImageDraw
W=Path(__file__).resolve().parent
tag=sys.argv[1]; out=sys.argv[2]
B='/Applications/Blender.app/Contents/MacOS/Blender'
T="0.60,-0.105,0.89"
views=["back:%s:0.768,0,0.642:0.28:55:-40"%T,"thumbside:%s:-0.07,-1,0.09:0.28:55:-40"%T,"palm3q:%s:-0.55,0.7,-0.45:0.28:55:-40"%T,"front3q:%s:0.5,-0.75,0.4:0.28:55:-40"%T,"wrist:0.50,-0.10,0.97:-0.3,-0.85,0.2:0.28:55:-40"]
def rend(name,coords):
    env=dict(os.environ); env['CLIP']='0.18'
    if coords: env['COORDS']=str(coords)
    d=W/f'proof/ba/{name}'; d.mkdir(parents=True,exist_ok=True)
    subprocess.run([B,'-b',str(W/'baseline/HeroBase_Male_Silhouette.blend'),'--python',str(W/'closeup.py'),'--',str(d)]+views,env=env,capture_output=True)
    return d
d0=rend('before',None); d1=rend(tag,W/f'data/it/{tag}_cur.npy')
names=[v.split(':')[0] for v in views]
S=Image.new('RGB',(len(names)*420,2*420+30),(24,24,28)); dr=ImageDraw.Draw(S)
for i,n in enumerate(names):
    for j,(lab,d) in enumerate((('BEFORE (Micro1f)',d0),('AFTER '+tag,d1))):
        im=Image.open(d/f'{n}.png').convert('RGB').resize((420,420)); S.paste(im,(i*420,j*420+30*(j)))
        dr.text((i*420+6,j*(420+30)+4 if j==0 else 420+30*1+4),f'{lab} · {n}',fill=(255,255,0))
S.save(out); print(S.size)
