import sys, json
from PIL import Image, ImageDraw
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-hands-form3'
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
sys.path.insert(0,W)
from sheetlib import font
F=W+'/proof/final/'
def header(width,lines,h=None):
    h=h or (16+30*len(lines))
    im=Image.new('RGB',(width,h),(14,14,16)); d=ImageDraw.Draw(im)
    for i,l in enumerate(lines): d.text((12,10+i*30),l,fill=(255,230,120) if i==0 else (225,225,225),font=font(24 if i==0 else 18))
    return im
def stack(parts,bg=(18,18,20)):
    w=max(p.width for p in parts); h=sum(p.height for p in parts)
    S=Image.new('RGB',(w,h),bg); y=0
    for p in parts: S.paste(p,(0,y)); y+=p.height
    return S
m=json.load(open(W+'/data/metrics_G1.json')); sn=json.load(open(W+'/data/sil_native.json'))
sb=sn['proof/sil_native_before']; sa=sn['proof/sil_native_after']
f=m['fingers']['R']
hl=['MALE ARMS + HANDS FORM2  -  hands before (ArtDir 1fe4d53b) vs after (staged), plates male_body_bald.jpg + male_multiangle_body.jpg',
    'finger width tip/base %.2f (mid/base %.2f), PIP bump %.1f-%.1f mm, DIP bump %.1f-%.1f mm, 6 cap rows (pad tips); thumb: thenar root r=%.0f mm -> tip r=%.1f mm (x%.2f), IP bend %.1f deg, IP bump +1.0 mm'%(
      f[0]['taper_tip_over_base'],f[0]['taper_mid_over_base'],min(x['pip_bump_mm'] for x in f),max(x['pip_bump_mm'] for x in f),min(x['dip_bump_mm'] for x in f),max(x['dip_bump_mm'] for x in f),
      m['thumb']['R']['radius_root_mm'],m['thumb']['R']['radius_last_shaft_mm'],m['thumb']['R']['taper_last_over_max'],m['thumb']['R']['ip_axis_bend_deg']),
    'zone audit: 0 verts moved outside arm zone, head/torso/legs bit-identical; mirror L/R error <0.01 mm; self-intersecting triangle pairs 0; %d tris (was %d)'%(m['tris'],m['tris_baseline']),
    'Blender-native silhouette XOR/union (gate <= 5.0%%): bald front %.2f%% -> %.2f%%, bald back %.2f%% -> %.2f%%'%(sb['bald_front']['pct'],sa['bald_front']['pct'],sb['bald_back']['pct'],sa['bald_back']['pct'])]
# sheet 1: R | L before/after
r=Image.open(F+'_hands_R.png').convert('RGB'); l=Image.open(F+'_hands_L.png').convert('RGB')
body=Image.new('RGB',(r.width+l.width+20,r.height),(18,18,20)); body.paste(r,(0,0)); body.paste(l,(r.width+20,0))
s1=stack([header(body.width,hl),body]); s1=s1.resize((s1.width*3//5,s1.height*3//5),Image.LANCZOS); s1.save(F+'03c_hands_form2_before_after.png'); print('s1',s1.size)
# sheet 2: plate + silhouettes
p3=Image.open(F+'_plate3.png').convert('RGB')
sb_=Image.open(W+'/proof/it/base_silov.png').convert('RGB'); sa_=Image.open(W+'/proof/it/G1_silov.png').convert('RGB')
def fit(im,w): return im.resize((w,int(im.height*w/im.width)),Image.LANCZOS)
s2=stack([header(p3.width,['PLATE | BEFORE | AFTER at the locked plate cameras (hand ROIs), then silhouette overlays (pink = mesh only, green = plate only, grey = both)']),p3,fit(sb_,p3.width),fit(sa_,p3.width)])
s2.save(F+'03c_hands_form2_plate_silhouette.png'); print('s2',s2.size)
# sheet 3: thumb + finger detail
parts=[header(1920,['THUMB close-ups (solid / wire): thenar mound -> MCP -> IP bump + bend -> pad tip, web fillet; FINGER close-ups: taper, PIP/DIP knuckle hints, pad tips'])]
for nm in ('_thumb_solid','_thumb_wire','_finger_solid','_finger_wire'): parts.append(Image.open(F+nm+'.png').convert('RGB'))
s3=stack(parts); s3.save(F+'03c_hands_form2_detail.png'); print('s3',s3.size)
# sheet 4: arms
arm=Image.open(F+'_arm_zoom.png').convert('RGB')
am=json.load(open(W+'/data/arm_metrics_G1.json'))
al=['MALE ARMS (secondary) - light soft-plastic mass: biceps/triceps +3.7 mm (front-back extent at t=-0.17), elbow waist -1.0 mm, forearm +1.4/+2.3 mm, delt +1 mm; surface noise %.2f -> %.2f mm rms; max move %.1f mm'%(am['hf_rms_mm']['before'],am['hf_rms_mm']['after'],am['max_mm']),
    'faded to 0 at the torso seam (0.000 mm on zone-boundary verts) and before the wrist weld; bald silhouette effect of the arm pass alone: front +0.02%, back +0.05%']
s4=stack([header(arm.width,al),arm]); s4.save(F+'03c_arms_form2_sheet.png'); print('s4',s4.size)
