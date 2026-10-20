import sys,json; sys.path.insert(0,'tools'); sys.path.insert(0,'gate7')
import numpy as np, hashlib
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from sil import *
from torso2 import plate_front, plate_back
ROOT='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
FB='/System/Library/Fonts/Supplemental/Arial Bold.ttf'; FR='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(sz,b=True): return ImageFont.truetype(FB if b else FR,sz)
d0=np.load('data/orig.npz'); tri=d0['tri']
co_before=np.load('data/cand_co.npy'); co_after=np.load('data/co_FORM2_final.npy')
SHA_AFTER=hashlib.sha256(open('export/HeroBase_Female_torso_form2_candidate.blend','rb').read()).hexdigest()[:8]
plate_bald=Image.open(ROOT+'ArtDir/hero/base_lock/female_body_bald.jpg').convert('RGB')
plate_sheet=Image.open(ROOT+'ArtDir/hero/base_lock/female_multiangle_body.jpg').convert('RGB')
chk=json.load(open('export/form2_gate_scripts_checks.json'))
def banner(img,text,sub=None,h=54):
    Wd=Image.new('RGB',(img.width,img.height+h),(24,24,28)); Wd.paste(img,(0,h)); dr=ImageDraw.Draw(Wd); dr.text((14,8),text,font=font(24),fill=(255,255,255))
    if sub: dr.text((14,h-20),sub,font=font(13,False),fill=(190,190,200))
    return Wd
def label(img,t,xy=(8,6),col=(255,255,255),sz=18,bg=(0,0,0)):
    dr=ImageDraw.Draw(img); w=dr.textlength(t,font=font(sz)); dr.rectangle([xy[0]-4,xy[1]-3,xy[0]+w+6,xy[1]+sz+5],fill=bg); dr.text(xy,t,font=font(sz),fill=col); return img
names=['front','q3F','side','q3B','back']; nice=['front','3/4 front','side','3/4 back','back']
# ------------- P01 before/after (soft + clay)
for kind,kn in (('soft','soft plate-like light'),('clay','clay studio matcap (chat-7 style)')):
    rows=[]
    for tag,lab,bg in (('before','BEFORE: chat-7 torso candidate (696e1be4…) — REJECTED',(90,30,30)),('after',f'AFTER: FORM2 candidate ({SHA_AFTER}…)',(20,60,110))):
        Wd=Image.new('RGB',(640*5,860))
        for i,n in enumerate(names):
            im=Image.open(f'proof/final/{kind}_{tag}_{n}.png').convert('RGB'); label(im,nice[i],(8,8),sz=20); Wd.paste(im,(i*640,0))
        label(Wd,lab,(8,832),sz=22,bg=bg); rows.append(Wd)
    S_=Image.new('RGB',(3200,1720)); S_.paste(rows[0],(0,0)); S_.paste(rows[1],(0,860))
    banner(S_,f'FEMALE TORSO FORM2 — before / after ({kn})','Only chest→waist/pelvis shell vertices move (positions only); border, head/neck, arms, hands, legs, feet are bit-identical.').resize((2400,1320),Image.LANCZOS).save(f'proof/01_torso_before_after_{kind}.png')
# ------------- P02 side profile overlay
S2=1.7039/288.5; V0=338.5; X0=791.5
def side_uv(co): return np.stack([X0+co[:,1]/S2,V0-co[:,2]/S2],1)
box=(735,92,860,262); sc=6
def edge(mask):
    mi=Image.fromarray((mask*255).astype(np.uint8)); mx=np.asarray(mi.filter(ImageFilter.MaxFilter(3)))>0; mn=np.asarray(mi.filter(ImageFilter.MinFilter(3)))>0; return mx&~mn
def side_panel(co,col,title):
    base=plate_sheet.crop(box).resize(((box[2]-box[0])*sc,(box[3]-box[1])*sc),Image.LANCZOS); base=ImageEnhance.Contrast(base).enhance(1.5)
    M=raster(side_uv(co),tri,size=(1280,720),ss=6); E=Image.fromarray((edge(M)*255).astype(np.uint8)).crop(box).resize(base.size,Image.NEAREST)
    arr=np.asarray(base).copy(); e=np.asarray(E)>0; arr[e]=col; im=Image.fromarray(arr); dr=ImageDraw.Draw(im)
    for z in np.arange(0.84,1.301,0.02):
        v=(V0-z/S2-box[1])*sc
        for y in (plate_front(z),plate_back(z)):
            u=(X0+y/S2-box[0])*sc; dr.ellipse([u-5,v-5,u+5,v+5],outline=(255,215,0),width=2)
    label(im,title,(8,8),sz=22); return im
pa=side_panel(co_before,(255,60,60),'BEFORE chat 7 (red = model silhouette)'); pb=side_panel(co_after,(40,230,90),'AFTER form2 (green = model silhouette)')
Wd=Image.new('RGB',(pa.width*2,pa.height)); Wd.paste(pa,(0,0)); Wd.paste(pb,(pa.width,0))
sx=chk['side_profile_torso_band_xor_z0.82_1.30']; se=chk['side_contour_error_mm']
banner(Wd,'SIDE PROFILE vs PLATE (torso rows z 0.84–1.30)',f"yellow rings = plate contour table. Torso-band side XOR (chat-7 gate script) {100*sx['before']:.1f}% (orig) → {100*sx['after']:.1f}%  |  contour err front {se['after']['front_mean']:.1f} mm, back {se['after']['back_mean']:.1f} mm (mean)  — gate ≤5%").save('proof/02_side_profile_overlay.png')
# ------------- P03 front/back silhouette overlay
outs=[]
for view,cx,name in (('front',440,'F_front_target.png'),('back',847,'F_back_target.png')):
    T_=np.asarray(Image.open(ROOT+'ArtDir/hero/base_lock/proof/masks/'+name).convert('L'))>127
    M=raster(project(co_after,view),tri); arr=np.asarray(plate_bald).copy(); arr[edge(T_)]=(0,200,0); arr[edge(M)]=(255,0,0)
    crop=Image.fromarray(arr).crop((cx-125,125,cx+125,420)).resize((750,885),Image.NEAREST); label(crop,view.upper()+' (after)  red=model  green=plate',(8,8),sz=20); outs.append(crop)
Wd=Image.new('RGB',(1500,885)); Wd.paste(outs[0],(0,0)); Wd.paste(outs[1],(750,0))
b=chk['torso_visible_edge_run_xor_rows_z0.82_1.165']
banner(Wd,'FRONT / BACK SILHOUETTE vs PLATE (female_body_bald, project framing)',f"torso visible-edge XOR (rows below armpit, arms excluded; chat-7 gate script): front {100*b['after']['front']:.2f}%  back {100*b['after']['back']:.2f}%  (gate ≤5%; x untouched except ≤2.6 mm denoise)").save('proof/03_front_back_silhouette_overlay.png')
# ------------- P04 3/4 plate vs before vs after
S2b=1.7039/290.5; V0b=668.5; zc=1.02; half=0.30; y0=V0b-(zc+half)/S2b; y1=V0b-(zc-half)/S2b; centers=[168,472,775,1078]
tiles=[]
for cx in centers:
    w=half/S2b; c=plate_sheet.crop((int(cx-w),int(y0),int(cx+w),int(y1))).resize((700,700),Image.LANCZOS); tiles.append(ImageEnhance.Contrast(c).enhance(1.5))
for t,l in zip(tiles,['plate 3/4 front L','plate 3/4 front R','plate 3/4 back L','plate 3/4 back R']): label(t,l,(8,8))
Wd=Image.new('RGB',(2800,2100))
for i,t in enumerate(tiles): Wd.paste(t,(i*700,0))
for r,(tag,lab) in enumerate((('before','chat-7 (before)'),('after','form2 (after)'))):
    for i,(v,vl) in enumerate(zip(('y25','y-25','y-155','y155'),('+25°','-25°','back -155°','back +155°'))):
        im=Image.open(f'proof/final/q3_{tag}_{v}.png').convert('RGB'); label(im,f'{lab} {vl}',(8,8)); Wd.paste(im,(i*700,700*(r+1)))
banner(Wd,'3/4 VIEWS — plate (top) | chat-7 torso (middle) | FORM2 torso (bottom), soft plate-like light','Note: the multi-angle sheet figure has slightly larger hips/thighs and thinner arms than the bald plate; widths follow the bald plate.').resize((1750,1350),Image.LANCZOS).save('proof/04_plate_vs_model_3q.png')
# ------------- P05 chest + pelvis closeups
def plate_crop(zc,half,cx):
    p=plate_bald.crop((int(cx-half/S),int(679-(zc+half)/S),int(cx+half/S),int(679-(zc-half)/S))).resize((700,700),Image.LANCZOS); return ImageEnhance.Contrast(p).enhance(1.7)
for kind,kn in (('','soft light'),('C','clay studio')):
    ims=[plate_crop(1.22,0.25,440)]+[Image.open(f'proof/final/chest{kind}_{t}_{v}.png').convert('RGB') for t,v in (('before','front'),('after','front'),('after','y25'))]
    ims2=[plate_crop(0.92,0.275,847)]+[Image.open(f'proof/final/glute{kind}_{t}_{v}.png').convert('RGB') for t,v in (('before','back'),('after','back'),('after','y-155'))]
    labs1=['PLATE (front)','BEFORE (chat 7)','AFTER (form2)','AFTER (+25°)']; labs2=['PLATE (back)','BEFORE (chat 7)','AFTER (form2)','AFTER (back 3/4)']
    Wd=Image.new('RGB',(2800,1400))
    for i,(a,l) in enumerate(zip(ims,labs1)): label(a,l,(8,8)); Wd.paste(a,(i*700,0))
    for i,(a,l) in enumerate(zip(ims2,labs2)): label(a,l,(8,8)); Wd.paste(a,(i*700,700))
    banner(Wd,f'CHEST (bust) and PELVIS (glute + cleft) close-ups — {kn}','').resize((1750,925),Image.LANCZOS).save(f'proof/05_chest_glute_closeups{"_clay" if kind else ""}.png')
# ------------- P06 stripes
Wd=Image.new('RGB',(3600,1200))
for r,tag in enumerate(('before','after')):
    for i,v in enumerate(('front','y25','y-25')): Wd.paste(Image.open(f'proof/final/stripeC_{tag}_{v}.png').convert('RGB'),(i*600,r*600))
    for i,v in enumerate(('back','y155','y-155')): Wd.paste(Image.open(f'proof/final/stripeG_{tag}_{v}.png').convert('RGB'),(1800+i*600,r*600))
label(Wd,'BEFORE (chat 7)',(8,8),sz=22,bg=(90,30,30)); label(Wd,'AFTER (form2)',(8,608),sz=22,bg=(20,60,110))
banner(Wd,'SURFACE QUALITY — mirror-stripe test (regular rings = smooth domes/lobes; broken stripes = creases)','chat 7: broken stripes + pinched rings at the chest; form2: clean concentric rings at both domes and lobes. Remaining jumbles at the arm junction are inherited from the original mesh.').resize((2400,830),Image.LANCZOS).save('proof/06_smoothness_mirror_test.png')
print('proofs written')
