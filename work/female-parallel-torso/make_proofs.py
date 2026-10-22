import numpy as np, sys, json
sys.path.insert(0,'.')
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from sil import *
FB='/System/Library/Fonts/Supplemental/Arial Bold.ttf'; FR='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(sz,b=True): return ImageFont.truetype(FB if b else FR,sz)
d=np.load('data/start.npz'); tri=d['tri']; co0=d['co']; co1=np.load('data/torso_final.npy').astype(np.float32).astype(np.float64)
checks=json.load(open('checks.json'))
plate_bald=Image.open('../../ArtDir/hero/base_lock/female_body_bald.jpg').convert('RGB')
plate_sheet=Image.open('../../ArtDir/hero/base_lock/female_multiangle_body.jpg').convert('RGB')
def banner(img,text,sub=None,h=54):
    W=Image.new('RGB',(img.width,img.height+h),(24,24,28)); W.paste(img,(0,h))
    dr=ImageDraw.Draw(W); dr.text((14,8),text,font=font(24),fill=(255,255,255))
    if sub: dr.text((14,h-20),sub,font=font(13,False),fill=(190,190,200))
    return W
def label(img,t,xy=(8,6),col=(255,255,255),sz=18,bg=(0,0,0)):
    dr=ImageDraw.Draw(img); w=dr.textlength(t,font=font(sz)); dr.rectangle([xy[0]-4,xy[1]-3,xy[0]+w+6,xy[1]+sz+5],fill=bg); dr.text(xy,t,font=font(sz),fill=col); return img
# ---------------- P01 before/after 5 views
names=['front','q3F','side','q3B','back']; nice=['front','3/4 front','side','3/4 back','back']
rows=[]
for tag,lab in (('start','BEFORE  (start SHA 200dc3b9…)'),('final','AFTER  (torso candidate)')):
    W=Image.new('RGB',(640*5,860))
    for i,n in enumerate(names):
        im=Image.open(f'proof/final/clay_{tag}_{n}.png').convert('RGB'); label(im,nice[i],(8,8),sz=20); W.paste(im,(i*640,0))
    label(W,lab,(8,832),sz=22,bg=(20,60,110) if tag=='final' else (90,30,30)); rows.append(W)
S_=Image.new('RGB',(3200,1720)); S_.paste(rows[0],(0,0)); S_.paste(rows[1],(0,860))
banner(S_,'FEMALE TORSO — before / after (clay, same cameras)','Only chest→waist/pelvis shell vertices move. Head/neck, arms, hands, legs, feet are bit-identical.').resize((2400,1320),Image.LANCZOS).save('proof/01_torso_before_after.png')
# ---------------- P02 side profile overlay on plate
S2=1.7039/288.5; V0=338.5; X0=791.5
def side_uv(co): return np.stack([X0+co[:,1]/S2,V0-co[:,2]/S2],1)
box=(735,92,860,262); sc=6
def edge(mask):
    mi=Image.fromarray((mask*255).astype(np.uint8)); mx=np.asarray(mi.filter(ImageFilter.MaxFilter(3)))>0; mn=np.asarray(mi.filter(ImageFilter.MinFilter(3)))>0; return mx&~mn
def side_panel(co,col,title):
    base=plate_sheet.crop(box).resize(((box[2]-box[0])*sc,(box[3]-box[1])*sc),Image.LANCZOS)
    base=ImageEnhance.Contrast(base).enhance(1.5)
    M=raster(side_uv(co),tri,size=(1280,720),ss=6)
    E=Image.fromarray((edge(M)*255).astype(np.uint8)).crop(box).resize(base.size,Image.NEAREST)
    arr=np.asarray(base).copy(); e=np.asarray(E)>0; arr[e]=col
    im=Image.fromarray(arr)
    dr=ImageDraw.Draw(im)
    # plate contour (gradient edges) dots
    for r in checks['side_contour_table_after']:
        v=(V0-r['z']/S2-box[1])*sc
        for key in ('plate_front','plate_back'):
            u=(X0+r[key]/S2-box[0])*sc; dr.ellipse([u-5,v-5,u+5,v+5],outline=(255,215,0),width=2)
    label(im,title,(8,8),sz=22)
    return im
pa=side_panel(co0,(255,60,60),'BEFORE  (red = model silhouette)'); pb=side_panel(co1,(40,230,90),'AFTER  (green = model silhouette)')
W=Image.new('RGB',(pa.width*2,pa.height)); W.paste(pa,(0,0)); W.paste(pb,(pa.width,0))
s=checks['side_profile_torso_band_xor_z0.82_1.30']; e=checks['side_contour_error_mm']
sub=f"yellow rings = plate contour (female_multiangle_body, left+right profile avg).  torso-band side XOR {100*s['before']:.1f}% → {100*s['after']:.1f}%   |  contour err front {e['before']['front_mean']:.0f}→{e['after']['front_mean']:.0f} mm, back {e['before']['back_mean']:.0f}→{e['after']['back_mean']:.0f} mm (mean)"
banner(W,'SIDE PROFILE vs PLATE (torso rows z 0.84–1.30)',sub).save('proof/02_side_profile_overlay.png')
# ---------------- P03 front/back silhouette overlay (after)
outs=[]
for view,cx,name in (('front',440,'F_front_target.png'),('back',847,'F_back_target.png')):
    T=np.asarray(Image.open('../../ArtDir/hero/base_lock/proof/masks/'+name).convert('L'))>127
    M=raster(project(co1,view),tri); arr=np.asarray(plate_bald).copy(); arr[edge(T)]=(0,200,0); arr[edge(M)]=(255,0,0)
    crop=Image.fromarray(arr).crop((cx-125,125,cx+125,420)).resize((750,885),Image.NEAREST)
    label(crop,view.upper()+' (after)  red=model  green=plate',(8,8),sz=20); outs.append(crop)
W=Image.new('RGB',(1500,885)); W.paste(outs[0],(0,0)); W.paste(outs[1],(750,0))
b=checks['torso_visible_edge_run_xor_rows_z0.82_1.165']
sub=f"torso visible-edge (rows below armpit, arms excluded) XOR: front {100*b['before']['front']:.1f}→{100*b['after']['front']:.1f}%  back {100*b['before']['back']:.1f}→{100*b['after']['back']:.1f}%  (gate ≤5%; torso x-widths already matched the plate and are kept)"
banner(W,'FRONT / BACK SILHOUETTE vs PLATE (female_body_bald, project framing)',sub).save('proof/03_front_back_silhouette_overlay.png')
# ---------------- P04 3/4 plate vs model
S2b=1.7039/290.5; V0b=668.5; zc=1.02; half=0.30
y0=V0b-(zc+half)/S2b; y1=V0b-(zc-half)/S2b; centers=[168,472,775,1078]
tiles=[]
for cx in centers:
    w=half/S2b; c=plate_sheet.crop((int(cx-w),int(y0),int(cx+w),int(y1))).resize((700,700),Image.LANCZOS); tiles.append(ImageEnhance.Contrast(c).enhance(1.5))
for t,l in zip(tiles,['plate 3/4 front L','plate 3/4 front R','plate 3/4 back L','plate 3/4 back R']): label(t,l,(8,8))
mods=[Image.open(f'proof/final/q3_final_{v}.png').convert('RGB') for v in ('y25','y-25','y-155','y155')]
for t,l in zip(mods,['model +25°','model -25°','model back -155°','model back +155°']): label(t,l,(8,8))
W=Image.new('RGB',(2800,1400))
for i,t in enumerate(tiles): W.paste(t,(i*700,0))
for i,t in enumerate(mods): W.paste(t,(i*700,700))
banner(W,'3/4 VIEWS — plate (top) vs torso candidate (bottom)','Note: multi-angle sheet figure has slightly larger hips/thighs and thinner arms than the bald plate; widths follow the bald plate (authority for ≤5% silhouette).').resize((1750,925),Image.LANCZOS).save('proof/04_plate_vs_model_3q.png')
# ---------------- P05 reflection QA before/after
rows=[]
for tag,lab in (('start','BEFORE'),('final','AFTER')):
    W=Image.new('RGB',(640*5,860))
    for i,n in enumerate(names): W.paste(Image.open(f'proof/final/refl_{tag}_{n}.png').convert('RGB'),(i*640,0))
    label(W,lab+' — mirror-stripe smoothness test',(8,8),sz=22); rows.append(W)
S_=Image.new('RGB',(3200,1720)); S_.paste(rows[0],(0,0)); S_.paste(rows[1],(0,860))
banner(S_,'SURFACE QUALITY (mirror-stripe test: regular stripes = no creases/lumps)','After: two bust mounds and two glute lobes read as clean local rings; the only other deviation is a mild stripe bend where the chest wraps toward the arm (7.5 cm armpit taper). No wrinkles, no tears at neck/leg seams.').resize((2400,1320),Image.LANCZOS).save('proof/05_smoothness_mirror_test.png')
# ---------------- P06 zone map
Z=np.load('data/zone.npz'); Tm=Z['torso']; Wt=Z['w']; arm=Z['arm']
def zmap(axis,title):
    Wd,H=620,980; im=Image.new('RGB',(Wd,H),(18,18,22)); px=im.load()
    def plot(idx,colfun):
        for i in idx:
            u=int(Wd/2+co0[i,axis]*540); v=int(H-30-co0[i,2]*540)
            for dx in (0,1):
                for dy in (0,1):
                    if 0<=u+dx<Wd and 0<=v+dy<H: px[u+dx,v+dy]=colfun(i)
    other=np.where(~Tm)[0]; plot(other,lambda i:(95,95,105))
    plot(np.where(arm&~Tm)[0],lambda i:(70,140,230))
    def heat(i):
        w=Wt[i]; return (int(40+215*w),int(60+170*w),int(60*(1-w)))
    plot(np.where(Tm)[0],heat)
    dr=ImageDraw.Draw(im); dr.text((10,8),title,font=font(18),fill=(255,255,255)); return im
za=zmap(0,'front'); zb=zmap(1,'side (face left)')
leg=Image.new('RGB',(560,980),(18,18,22)); dr=ImageDraw.Draw(leg)
lines=[('ZONE MAP — female torso',(255,255,255),22),('',None,10),(f"torso zone vertices  {int(Tm.sum()):,}",(255,210,70),18),(f"moved (|Δ|>0)        {json.load(open('outside_zone_audit.json'))['moved_vertex_count']:,}",(255,210,70),16),('colour = weight w (dark→bright yellow)',(200,200,200),15),('',None,8),('blue  = arms (not touched)',(70,140,230),17),('grey  = head/neck, legs, feet, hands (not touched)',(150,150,160),17),('',None,8),('rules',(255,255,255),18),('• crotch plane z=0.795 (legs separate below)',(210,210,210),15),('• w=0 at z≤0.795, full by z≥0.88',(210,210,210),15),('• neck base z=1.37; w=0 for z≥1.34',(210,210,210),15),('• below armpit (z<1.165): arms = separate',(210,210,210),15),('  connected components',(210,210,210),15),('• above armpit: arm = |x| > X_B(z)=0.124',(210,210,210),15),('  (ramps to 0.17 at z=1.34)',(210,210,210),15),('• w tapers to 0 over 7.5 cm toward the arm',(210,210,210),15),('• vertex count / order / topology unchanged',(210,210,210),15),('• outside-zone vertices: Δ = 0.0 (bit-identical)',(120,230,140),16)]
y=14
for t,c,sz in lines:
    if c is not None: dr.text((14,y),t,font=font(sz,False if sz<18 else True),fill=c)
    y+=sz+9
W=Image.new('RGB',(620*2+560,980)); W.paste(za,(0,0)); W.paste(zb,(620,0)); W.paste(leg,(1240,0))
banner(W,'TORSO VERTEX ZONE','Merge key: export/torso_delta.npz (moved_idx, start_co, new_co, zone_mask, weights)').save('proof/06_zone_map.png')
# ---------------- P07 chest + glute closeups vs plate
def plate_crop(zc,half,cx):
    S=0.0025954198473282443
    p=plate_bald.crop((int(cx-half/S),int(679-(zc+half)/S),int(cx+half/S),int(679-(zc-half)/S))).resize((700,700),Image.LANCZOS)
    return ImageEnhance.Contrast(p).enhance(1.7)
ims=[plate_crop(1.22,0.25,440)]+[Image.open(f'proof/final/chest_{t}_{v}.png').convert('RGB') for t,v in (('start','front'),('final','front'),('final','y25'))]
ims2=[plate_crop(0.92,0.275,847)]+[Image.open(f'proof/final/glute_{t}_{v}.png').convert('RGB') for t,v in (('start','back'),('final','back'),('final','y-155'))]
labs1=['PLATE (front)','BEFORE','AFTER','AFTER (+25°)']; labs2=['PLATE (back)','BEFORE','AFTER','AFTER (back 3/4)']
W=Image.new('RGB',(2800,1400))
for i,(a,l) in enumerate(zip(ims,labs1)): label(a,l,(8,8)); W.paste(a,(i*700,0))
for i,(a,l) in enumerate(zip(ims2,labs2)): label(a,l,(8,8)); W.paste(a,(i*700,700))
banner(W,'CHEST (bust) and PELVIS (glute + cleft) close-ups','').resize((1750,925),Image.LANCZOS).save('proof/07_chest_glute_closeups.png')
print("proofs written")
