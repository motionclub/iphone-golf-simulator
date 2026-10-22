import json, numpy as np
from PIL import Image, ImageDraw, ImageFont
FONT='/System/Library/Fonts/Helvetica.ttc'
def font(sz,bold=False):
    try: return ImageFont.truetype(FONT,sz,index=1 if bold else 0)
    except Exception: return ImageFont.load_default()
M=json.load(open('data/metrics_final.json')); A=json.load(open('data/audit_final.json'))
PL=Image.open('../../ArtDir/hero/base_lock/female_body_plain.jpg').convert('RGB')
MA=Image.open('../../ArtDir/hero/base_lock/female_multiangle_body.jpg').convert('RGB')
def header(W,h,title,sub=None,bg=(28,28,32)):
    im=Image.new('RGB',(W,h),bg); d=ImageDraw.Draw(im); d.text((16,10),title,font=font(26,True),fill=(255,255,255))
    if sub: d.text((16,10+34),sub,font=font(16),fill=(190,190,200))
    return im
def stack(parts,gap=0,bg=(28,28,32)):
    W=max(p.width for p in parts); H=sum(p.height for p in parts)+gap*(len(parts)-1)
    out=Image.new('RGB',(W,H),bg); y=0
    for p in parts: out.paste(p,(0,y)); y+=p.height+gap
    return out
def label(im,text,pos=(8,6),sz=18,fill=(255,255,255),bg=(0,0,0)):
    d=ImageDraw.Draw(im); w=d.textlength(text,font=font(sz,True)); d.rectangle((pos[0]-4,pos[1]-3,pos[0]+w+6,pos[1]+sz+5),fill=bg); d.text(pos,text,font=font(sz,True),fill=fill); return im
# ---------- 01 front/back vs plate
def col(p,cx): return p.crop((cx-170,0,cx+170,720))
f=Image.open('proof/r_final_front.png').convert('RGB'); b=Image.open('proof/r_final_back.png').convert('RGB')
bf=Image.open('proof/r_base_front.png').convert('RGB'); bb=Image.open('proof/r_base_back.png').convert('RGB')
row=Image.new('RGB',(340*6,720))
for i,im in enumerate([col(PL,440),col(bf,440),col(f,440),col(PL,847),col(bb,847),col(b,847)]): row.paste(im,(340*i,0))
for i,t in enumerate(['PLATE front','BASELINE front','LIMBS front','PLATE back','BASELINE back','LIMBS back']): label(row,t,(340*i+8,6))
hdr=header(340*6,70,'FEMALE LIMBS — plate vs baseline vs new limbs (plate framing, 0.002595 m/px)','Workbench render; head/torso are NOT in this zone (other chats). Limbs: arms, hands, legs, feet.')
stack([hdr,row]).save('proof/01_limbs_vs_plate_front_back.png')
# ---------- 02 silhouette overlay before/after
s0=Image.open('proof/base_sil.png').convert('RGB'); s1=Image.open('proof/final_sil.png').convert('RGB')
def sline(tag):
    m=M[tag]; return (f"front: legs {m['front_legs_xor_pct']:.1f}  feet {m['front_feet_xor_pct']:.1f}  arms {m['front_arms_xor_pct']:.1f}  hands {m['front_hands_xor_pct']:.1f}   |   "
                      f"back: legs {m['back_legs_xor_pct']:.1f}  feet {m['back_feet_xor_pct']:.1f}  arms {m['back_arms_xor_pct']:.1f}  hands {m['back_hands_xor_pct']:.1f}   (XOR % per zone)")
canvas=Image.new('RGB',(1380,720+120),(28,28,32)); canvas.paste(s0,(10,110)); canvas.paste(s1,(700,110))
d=ImageDraw.Draw(canvas); d.text((16,8),'Silhouette vs plate polygons: green overlap, red = plate only, blue = model only',font=font(22,True),fill=(255,255,255))
d.text((16,44),'BASELINE  '+sline('baseline'),font=font(13),fill=(255,190,190)); d.text((16,72),'NEW LIMBS '+sline('final'),font=font(13),fill=(190,255,190))
label(canvas,'baseline (front | back)',(14,116)); label(canvas,'new limbs (front | back)',(704,116))
canvas.save('proof/02_silhouette_overlay_before_after.png')
# ---------- 03 side profile
def prof_img(p): return Image.open(p).convert('RGB')
S=0.005916/3
c=MA.crop((700,45,830,345)).resize((390,900),Image.LANCZOS)
pcs=[c,prof_img('proof/pc_base.png'),prof_img('proof/pc_final.png')]
W=Image.new('RGB',(390*3+40,900+190),(28,28,32))
for i,p in enumerate(pcs): W.paste(p,(10+400*i,110))
for i,t in enumerate(['PLATE left profile','BASELINE','NEW LIMBS']): label(W,t,(16+400*i,116))
d=ImageDraw.Draw(W); d.text((16,8),'Side profile at plate scale — lower-leg depth, ankle, foot length, hand position',font=font(22,True),fill=(255,255,255))
pb=M['profile_baseline']; pf=M['profile_final']
d.text((16,44),f"shank depth deviation vs plate (z 0.17–0.46 m):  baseline mean {pb['mean_abs_depth_dev_mm']:.1f} mm, max edge {pb['max_abs_edge_dev_mm']:.1f} mm   ->   new mean {pf['mean_abs_depth_dev_mm']:.1f} mm, max edge {pf['max_abs_edge_dev_mm']:.1f} mm",font=font(14),fill=(200,255,200))
d.text((16,70),'(new targets use the plate edges pulled in 5 mm per side because the profile plate shows two slightly yawed legs)',font=font(12),fill=(180,180,190))
# table under images
rows=list(zip(pb['z'],pb['depth_dev_mm'],pf['depth_dev_mm']))
txt='z(m): '+'  '.join(f'{z:.2f}' for z,_,_ in rows[::3])
d.text((16,1018),txt,font=font(12),fill=(200,200,200))
d.text((16,1036),'base depth err mm: '+'  '.join(f'{a:+.0f}' for _,a,_ in rows[::3]),font=font(12),fill=(255,190,190))
d.text((16,1054),'new  depth err mm: '+'  '.join(f'{b:+.0f}' for _,_,b in rows[::3]),font=font(12),fill=(190,255,190))
W.save('proof/03_profile_vs_plate.png')
# ---------- 04 hands
def cr(p,box,s=3): c=p.crop(box); return c.resize((c.width*s,c.height*s),Image.LANCZOS)
PF_=lambda box:cr(PL,box)
zf=Image.open('proof/zfinal_hand_front.png'); zb_=Image.open('proof/zfinal_hand_back.png')
r1=Image.new('RGB',(1500,320),(28,28,32)); r1.paste(zf,(0,10)); r1.paste(zb_,(780,10))
label(r1,'PLATE front | LIMBS front',(8,14)); label(r1,'PLATE back | LIMBS back',(788,14))
cl=Image.new('RGB',(1500,1000),(28,28,32))
names=[('handR',['front','side','q']),('handL',['front','side','q'])]
for ri,(t,vs) in enumerate(names):
    for ci,v in enumerate(vs): cl.paste(Image.open(f'proof/c_final_{t}_{v}.png').convert('RGB'),(500*ci,500*ri))
for ri,t in enumerate(['RIGHT hand','LEFT hand']): label(cl,t+' (new) — front | side | 3/4',(8,500*ri+8))
hdr=header(1500,70,'HANDS — plate vs new (4 fingers + thumb, relaxed, palm turned ~55°)',f"length wrist->tip 0.154 m (plate 0.153); 5 persistent extremities per hand; grey Base_Grey_F; front view shows the thumb side like the plate")
stack([hdr,r1,cl]).save('proof/04_hands_vs_plate.png')
# ---------- 05 feet
ff=Image.open('proof/zfinal_foot_front.png'); fb=Image.open('proof/zfinal_foot_back.png')
r1=Image.new('RGB',(1040,300),(28,28,32)); r1.paste(ff,(0,0)); 
r2=Image.new('RGB',(1040,300),(28,28,32)); r2.paste(fb,(0,0))
label(r1,'PLATE front | LIMBS front',(8,8)); label(r2,'PLATE back | LIMBS back',(8,8))
cl=Image.new('RGB',(1500,1000),(28,28,32))
for ri,t in enumerate(['footR','footL']):
    for ci,v in enumerate(['front','side','q']): cl.paste(Image.open(f'proof/c_final_{t}_{v}.png').convert('RGB'),(500*ci,500*ri))
for ri,t in enumerate(['RIGHT foot','LEFT foot']): label(cl,t+' (new) — front | side | 3/4',(8,500*ri+8))
tt=Image.new('RGB',(1500,270),(28,28,32))
for ci,k in enumerate(['frontR','qR','frontL','qL']):
    im=Image.open(f'proof/toes_final_{k}.png').convert('RGB').resize((375,225)); tt.paste(im,(375*ci,10))
label(tt,'toe rows (R front, R 3/4, L front, L 3/4): 5 toes per foot',(8,236))
hdr=header(1500,70,'FEET — plate vs new (5 toes, arch/instep wedge, round heel, skin Skin_F)','length heel->toe 0.240 m (plate 0.241); foot axis toe-out ~7°; sole on z=0; ankle seam straight on the existing z=0.15728 ring')
stack([hdr,stack([r1,r2]),cl,tt]).save('proof/05_feet_vs_plate.png')
# ---------- 06 before/after 3D
def pair(a,b,sz=(500,500)): 
    im=Image.new('RGB',(sz[0]*2+10,sz[1]),(28,28,32)); im.paste(Image.open(a).convert('RGB'),(0,0)); im.paste(Image.open(b).convert('RGB'),(sz[0]+10,0)); return im
rows=[pair('proof/c_base_handR_side.png','proof/c_final_handR_side.png'),pair('proof/c_base_footR_q.png','proof/c_final_footR_q.png'),
      pair('proof/c_base_handL_q.png','proof/c_final_handL_q.png'),pair('proof/c_base_footL_side.png','proof/c_final_footL_side.png')]
g=Image.new('RGB',(1010*2,1010),(28,28,32))
for i,r in enumerate(rows): g.paste(r,(1010*(i%2),510*(i//2)))
for i,t in enumerate(['R hand: BEFORE | AFTER','R foot: BEFORE | AFTER','L hand: BEFORE | AFTER','L foot: BEFORE | AFTER']): label(g,t,(1010*(i%2)+8,510*(i//2)+8))
lg=Image.new('RGB',(1800,900),(28,28,32))
for i,k in enumerate(['q1','side','q2']): lg.paste(Image.open(f'proof/lg_base_{k}.png').convert('RGB').resize((600,900)),(600*i,0))
lg2=Image.new('RGB',(1800,900),(28,28,32))
for i,k in enumerate(['q1','side','q2']): lg2.paste(Image.open(f'proof/lg_final_{k}.png').convert('RGB').resize((600,900)),(600*i,0))
hdr=header(2020,70,'BEFORE / AFTER — hands, feet and lower legs','left of each pair = baseline (start SHA 200dc3b9…), right = new limbs')
legs=Image.new('RGB',(2020,900),(28,28,32)); legs.paste(lg.resize((1000,500)),(0,0)); legs.paste(lg2.resize((1000,500)),(1010,0)); label(legs,'legs BEFORE (rear-right, side, front-left)',(8,8)); label(legs,'legs AFTER',(1018,8))
stack([hdr,g,legs.crop((0,0,2020,500))]).save('proof/06_before_after_limbs.png')
print('ok')
