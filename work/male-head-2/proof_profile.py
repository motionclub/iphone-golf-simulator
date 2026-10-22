from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json
W=Path(__file__).resolve().parent;R=W.parents[1];D=R/'ArtDir/hero/base_lock';P=D/'proof'
cal=json.loads((W/'profile-calibration.json').read_text());stats=json.loads((W/'depth/profile-comparison.json').read_text());k=cal['metres_per_reference_pixel'];top=cal['top_height_metres'];mpp=.45/800
ref=Image.open(D/'male_head_detail.jpg').convert('RGB').crop((505,72,730,329));arr=np.array(ref).astype(float)
rm=((arr[:,:,0]-arr[:,:,1]>12)&(arr[:,:,1]-arr[:,:,2]>7)&(arr[:,:,0]>65))|(arr.mean(axis=2)>75)
def boundary(m):
 interior=m.copy();interior[1:-1,1:-1]&=m[1:-1,:-2]&m[1:-1,2:]&m[:-2,1:-1]&m[2:,1:-1];return m&~interior
def overlay(path):
 # Resample display only into the fixed diagnostic head-detail calibration.
 src=Image.open(path).convert('RGBA');a=k/mpp;bx=400+(.110+(505-712)*k)/mpp;by=400-(top-(72-76)*k-1.505)/mpp
 warped=src.transform(ref.size,Image.Transform.AFFINE,(a,0,bx,0,a,by),Image.Resampling.BICUBIC);mm=np.array(warped.getchannel('A'))>127
 out=np.array(ref).copy();z=top-(np.arange(ref.height)+72-76)*k;scope=(z>=1.390)&(z<=1.520)
 re=boundary(rm)&scope[:,None];me=boundary(mm)&scope[:,None];out[re]=[30,235,160];out[me]=[245,65,145];return Image.fromarray(out)
before=Path('/Users/adnanyonathan/Documents/Codex/2026-09-30/open-3/outputs/Male_Head_1/head_native/left.png');after=P/'male_form_d/head_all_around/left.png'
panels=[('Reference',ref),('Before · jaw/neck outline',overlay(before)),('After · jaw/neck outline',overlay(after))]
font=lambda n:ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',n)
im=Image.new('RGB',(2025,1005),(36,36,39));dr=ImageDraw.Draw(im);dr.text((18,12),'Jaw / neck profile · fixed head-detail diagnostic calibration',font=font(28),fill='white')
dr.text((18,55),'Green: reference contour   Pink: model contour   ·   Primary bald masks and cameras unchanged',font=font(21),fill=(220,220,220))
for i,(label,q) in enumerate(panels):
 dr.text((i*675+18,102),label,font=font(23),fill='white');im.paste(q.resize((675,771),Image.Resampling.LANCZOS),(i*675,140))
dr.text((18,920),f'8 front jaw/throat calipers: mean |depth gap| {stats["jaw_throat_caliper_mean_absolute_error_mm_before"]:.2f} to {stats["jaw_throat_caliper_mean_absolute_error_mm_after"]:.2f} mm',font=font(22),fill='white')
dr.text((18,955),f'5 rear neck calipers: {stats["rear_neck_caliper_mean_absolute_error_mm_before"]:.2f} to {stats["rear_neck_caliper_mean_absolute_error_mm_after"]:.2f} mm · Diagnostic only; not the full-body 2% gate',font=font(22),fill='white')
im.save(P/'01f_jaw_neck_profile_m.png')
print('PROFILE_PROOF',P/'01f_jaw_neck_profile_m.png')
