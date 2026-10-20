"""Build the hands proof sheets: python3 proof_hands.py <tag>"""
import subprocess, sys, os
from PIL import Image, ImageDraw
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-arms-hands-form2'
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
sys.path.insert(0,W)
from sheetlib import font
tag=sys.argv[1]
def run(cmd,**kw): return subprocess.run(cmd,capture_output=True,text=True,cwd=W,**kw)
# ---- A/B: before/after hand views (R, L)
views='dorsal,palmar,radial,ulnar,q_dorsal_radial,q_palmar_radial'
for side in ('R','L'):
    run(['python3',W+'/cmp2.py','base',tag,side,f'{W}/proof/final/_hands_{side}.png',views,'0.26','0.0,0.0,0.065'])
# ---- C: plate | before | after at the locked plate cameras (8 ROIs)
od={}
for t in ('base',tag):
    cand='base' if t=='base' else f'{W}/data/cand_{t}.npz'
    d=f'{W}/proof/it/{t}_plate'; od[t]=d
    r=run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup',f'{W}/baseline/HeroBase_Male_Silhouette.blend','--python',f'{W}/platerender.py','--',cand,d])
bald=Image.open(R+'/ArtDir/hero/base_lock/male_body_bald.jpg').convert('RGB'); multi=Image.open(R+'/ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
ROIS=[('bald front, char R hand',bald,'bald_front',(100,300,205,395)),('bald front, char L hand',bald,'bald_front',(500,300,605,395)),
      ('bald back, char L hand',bald,'bald_back',(670,300,775,395)),('bald back, char R hand',bald,'bald_back',(1060,300,1165,395)),
      ('multi front, R hand',multi,'sheet_front',(45,160,125,225)),('multi front, L hand',multi,'sheet_front',(250,160,330,225)),
      ('multi back, L hand',multi,'sheet_back',(355,160,435,225)),('multi back, R hand',multi,'sheet_back',(545,160,625,225))]
sc=4; tiles=[]
for name,plate,view,roi in ROIS:
    ims=[plate.crop(roi), Image.open(f'{od["base"]}/{view}.png').convert('RGB').crop(roi), Image.open(f'{od[tag]}/{view}.png').convert('RGB').crop(roi)]
    ims=[i.resize((i.width*sc,i.height*sc),Image.LANCZOS) for i in ims]
    w=ims[0].width; h=ims[0].height
    t=Image.new('RGB',(w*3+12,h+22),(20,20,22))
    for k,i in enumerate(ims): t.paste(i,(k*(w+6),22))
    d=ImageDraw.Draw(t); d.text((4,3),name+'   |  PLATE  |  BEFORE  |  AFTER',fill=(255,230,120),font=font(13)); tiles.append(t)
cw=max(t.width for t in tiles); ch=max(t.height for t in tiles)
S=Image.new('RGB',(2*cw,4*ch),(20,20,22))
for i,t in enumerate(tiles): S.paste(t,((i%2)*cw,(i//2)*ch))
S.save(f'{W}/proof/final/_plate3.png'); print('plate3',S.size)
# ---- D: silhouette overlays
run([W+'/py.sh',W+'/silov.py','base',tag])
print('done')
