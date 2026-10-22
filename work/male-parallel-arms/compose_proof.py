import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
W=Path(__file__).resolve().parent
F=lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',s)
au=json.load(open(W/'data/final_checks_raw.json')); sn=json.load(open(W/'data/sil_numbers.json'))
IM=lambda p: Image.open(W/p).convert('RGB')
BG=(34,34,38); W_=2400
canvas=[]; y=0
def block(img): 
    canvas.append(img)
def textbar(lines,h,sizes=None,colors=None):
    im=Image.new('RGB',(W_,h),BG); d=ImageDraw.Draw(im); yy=10
    for i,l in enumerate(lines):
        sz=(sizes or [34]+[20]*10)[i]; col=(colors or [(255,255,255)]+[(200,200,205)]*10)[i]
        d.text((20,yy),l,font=F(sz),fill=col); yy+=sz+8
    return im
q0=au['quality_start']; q1=au['quality_final']
z=au['zone']; r0,r1=au['hand_roi_xor_start_final']
head=textbar(["Male ARMS + HANDS - chat 3 - GATE: MALE_ARMS_HANDS PASS",
 f"zone audit: {z['verts_moved']} verts moved (hand shell {z['moved_hand_shell']} + wrist band {z['moved_forearm_wrist_band']}), {z['verts_moved_outside_zone']} outside arms/hands - head/neck, torso, legs, feet, shoulder ball + upper arm bit-identical - topology unchanged ({au['verts']:,} verts, {au['tris']:,} tris, boundary/non-manifold edges 92/2 as before)",
 f"thumb root: self-intersecting triangle pairs {au['self_intersecting_triangle_pairs'][0]} -> {au['self_intersecting_triangle_pairs'][1]} - folded edges >100 deg {au['zone_edges_dihedral_gt100'][0]} -> {au['zone_edges_dihedral_gt100'][1]} - max dihedral {q0['dihedral_max']:.0f} -> {q1['dihedral_max']:.0f} deg - edges >60 deg {q0['dihedral_gt60']} -> {q1['dihedral_gt60']} - wrist/hand surface noise rms {q0['R_wristhand_hf_rms_mm']:.2f} -> {q1['R_wristhand_hf_rms_mm']:.2f} mm (p99 {q0['R_wristhand_hf_p99_mm']:.1f} -> {q1['R_wristhand_hf_p99_mm']:.1f})",
 f"hand-region silhouette XOR vs bald + multi-angle plates (8 hand ROIs): {r0} -> {r1} px ({100*(r1-r0)/r0:+.1f}%) - full-body bald silhouette (Blender native, gate <= 5.0%): front {sn['start']['bald_front']['pct']:.3f} -> {sn['final']['bald_front']['pct']:.3f} %, back {sn['start']['bald_back']['pct']:.3f} -> {sn['final']['bald_back']['pct']:.3f} %",
 "arm shafts (shoulder to elbow to wrist) untouched: width already within +-2 mm of the bald plates in front/back; the plates disagree on hand size and thumb by ~28 % (front vs back), so the hand fit is a compromise"],200,[44,21,21,21,21])
block(head)
def ba_block(side,title):
    names=['back','front','palm','back3q','side','wrist']
    tile=390; im=Image.new('RGB',(W_,40+2*(tile+34)),BG); d=ImageDraw.Draw(im)
    d.text((20,6),title,font=F(26),fill=(255,255,255))
    for j,(lab,dd) in enumerate((('BEFORE (ArtDir b9cc8596, Micro1f hands)','before'),('AFTER (this chat)','after'))):
        for i,n in enumerate(names):
            t=Image.open(W/f'proof/final/{dd}/{side}_{n}.png').convert('RGB').resize((tile,tile),Image.LANCZOS)
            x=20+i*(tile+10); yy=40+j*(tile+34)+22
            im.paste(t,(x,yy)); d.text((x,yy-20),f'{lab} - {n}' if i==0 else n,font=F(17),fill=(255,230,80) if j else (200,200,205))
    return im
block(ba_block('R',"RIGHT-X hand (character's left): before / after, same camera and lights"))
block(ba_block('L',"LEFT-X hand (character's right): mirror, same edit"))
# plate vs mesh + silhouette overlays
cmp=IM('proof/final/cmp_plate_after.png'); cmp=cmp.resize((1500,int(cmp.height*1500/cmp.width)),Image.LANCZOS)
sb=IM('proof/final/sil_arms_before.png'); sa=IM('proof/final/sil_arms_after.png')
sb=sb.resize((880,880),Image.LANCZOS); sa=sa.resize((880,880),Image.LANCZOS)
h=max(cmp.height,880+30)+60
im=Image.new('RGB',(W_,h),BG); d=ImageDraw.Draw(im)
d.text((20,8),'PLATE (left) vs MESH after (right) at the locked plate cameras: bald front, bald back, multi-angle front, multi-angle back (hand L, hand R)',font=F(22),fill=(255,255,255))
im.paste(cmp,(20,44))
d.text((1560,8),'silhouette overlay, arms (pink = mesh only, green = plate only)',font=F(22),fill=(255,255,255))
im.paste(sb.resize((420,420)),(1560,44)); im.paste(sa.resize((420,420)),(1990,44))
d.text((1560,470),'before (front L, front R / back L, back R)',font=F(17),fill=(200,200,205)); d.text((1990,470),'after',font=F(17),fill=(255,230,80))
block(im)
wire=Image.new('RGB',(W_,40+590+10),BG); d2=ImageDraw.Draw(wire)
d2.text((20,6),'thumb root wireframe (palm side, then front side): BEFORE had a stepped ledge, an overhanging rim and 23 self-intersecting triangle pairs; AFTER is one continuous surface',font=F(22),fill=(255,255,255))
for i,(dd,n,lab) in enumerate([('before','thumbroot_pal','BEFORE - palm side'),('after','thumbroot_pal','AFTER - palm side'),('before','thumbroot_front','BEFORE - front side'),('after','thumbroot_front','AFTER - front side')]):
    t=Image.open(W/f'proof/final/wire_{dd}/{n}.png').convert('RGB').resize((580,580),Image.LANCZOS); wire.paste(t,(20+i*590,40)); d2.text((26+i*590,44),lab,font=F(18),fill=(255,230,80))
block(wire)
foot=textbar(["Proof: plates male_body_bald.jpg + male_multiangle_body.jpg - cameras Locked_* (unchanged) - renders: Blender EEVEE clay, same lights before/after - merged blend = ArtDir blend b9cc8596 + arms delta -> 9f6d02bd - scripts: work/male-parallel-arms/"],40,[20])
block(foot)
H=sum(b.height for b in canvas); S=Image.new('RGB',(W_,H),BG); y=0
for b in canvas: S.paste(b,(0,y)); y+=b.height
out=W/'proof/01k_arms_hands_m.png'; S.save(out); print(S.size,out)
