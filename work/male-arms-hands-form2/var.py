"""build + render zoom variants side by side.  python3 var.py <group> <views> <scale> <center> name1='{json}' name2='{json}' ..."""
import subprocess, sys, os, json
from PIL import Image, ImageDraw
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-arms-hands-form2'
sys.path.insert(0,W)
from sheetlib import font
group=sys.argv[1]; views=sys.argv[2]; scale=sys.argv[3]; center=sys.argv[4]; side=os.environ.get('SIDE','R')
vs=[a.split('=',1) for a in sys.argv[5:]]
rows=[]
for name,js in vs:
    tag=f'{group}_{name}'
    r=subprocess.run([W+'/py.sh',W+'/asm3.py',tag,js],capture_output=True,text=True,cwd=W)
    if 'saved' not in r.stdout: print(r.stdout[-800:],r.stderr[-1200:]); sys.exit(1)
    r=subprocess.run(['python3',W+'/rv2.py',tag,side,views,scale,center],capture_output=True,text=True,cwd=W,env=dict(os.environ))
    img=Image.open(f'{W}/proof/it/{tag}_zoom_{side}.png').convert('RGB')
    d=ImageDraw.Draw(img); d.text((img.width-260,8),tag,fill=(255,230,120),font=font(18)); rows.append(img)
w=max(i.width for i in rows); h=sum(i.height for i in rows)
S=Image.new('RGB',(w,h)); y=0
for i in rows: S.paste(i,(0,y)); y+=i.height
out=f'{W}/proof/it/var_{group}.png'; S.save(out); print(out,S.size)
