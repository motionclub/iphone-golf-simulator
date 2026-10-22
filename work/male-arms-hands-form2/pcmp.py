"""Plate-vs-candidate hand crops.  python3 pcmp.py <tag> [out.png]"""
import subprocess, sys, os
from PIL import Image, ImageDraw
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-arms-hands-form2')
from sheetlib import font
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-arms-hands-form2'
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
tag=sys.argv[1]; outp=sys.argv[2] if len(sys.argv)>2 else f'{W}/proof/it/{tag}_plate_cmp.png'
cand='base' if tag=='base' else f'{W}/data/cand_{tag}.npz'
od=f'{W}/proof/it/{tag}_plate'
if not os.path.exists(od+'/bald_front.png') or os.environ.get('RERENDER','1')=='1':
    cmd=['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup',f'{W}/baseline/HeroBase_Male_Silhouette.blend','--python',f'{W}/platerender.py','--',cand,od]
    r=subprocess.run(cmd,capture_output=True,text=True)
    if 'PLATE_DONE' not in r.stdout: print(r.stdout[-1500:],r.stderr[-1500:])
bald=Image.open(R+'/ArtDir/hero/base_lock/male_body_bald.jpg').convert('RGB'); multi=Image.open(R+'/ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
# (plate image, our render name, roi) ; rois from handobj
ROIS=[('bald_front L',bald,'bald_front',(100,300,205,395)),('bald_front R',bald,'bald_front',(500,300,605,395)),
      ('bald_back L',bald,'bald_back',(670,300,775,395)),('bald_back R',bald,'bald_back',(1060,300,1165,395)),
      ('multi front L',multi,'sheet_front',(45,160,125,225)),('multi front R',multi,'sheet_front',(250,160,330,225)),
      ('multi back L',multi,'sheet_back',(355,160,435,225)),('multi back R',multi,'sheet_back',(545,160,625,225))]
sc=4; tiles=[]
for name,plate,view,roi in ROIS:
    mine=Image.open(f'{od}/{view}.png').convert('RGB')
    a=plate.crop(roi); b=mine.crop(roi)
    a=a.resize((a.width*sc,a.height*sc),Image.LANCZOS); b=b.resize((b.width*sc,b.height*sc),Image.LANCZOS)
    t=Image.new('RGB',(a.width*2+6,a.height+22),(20,20,22)); t.paste(a,(0,22)); t.paste(b,(a.width+6,22))
    ImageDraw.Draw(t).text((4,2),name+'   plate | candidate '+tag,fill=(255,230,120),font=font(14)); tiles.append(t)
cw=max(t.width for t in tiles); ch=max(t.height for t in tiles)
cols=2; rows=(len(tiles)+1)//2
S=Image.new('RGB',(cols*cw,rows*ch),(20,20,22))
for i,t in enumerate(tiles): S.paste(t,((i%cols)*cw,(i//cols)*ch))
S.save(outp); print(outp,S.size)
