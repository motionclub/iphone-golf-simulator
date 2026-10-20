"""Source-only consistency audit under the unchanged orthographic cameras."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib
W=Path(__file__).parent;R=W.parents[1];S=R/'work/male-silhouette';P=R/'ArtDir/hero/base_lock/proof'
views=json.loads((S/'reference-cameras.json').read_text())['views'][:2];s=1.7/593
masks=[np.array(Image.open(S/(v['name']+'_target.png')))>127 for v in views]
def intervals(row,v):
    xs=np.where(row)[0]
    if not len(xs):return []
    groups=np.split(xs,np.where(np.diff(xs)>1)[0]+1);out=[]
    for g in groups:
        a=(g[0]-.5-v['centre_x'])*v['metres_per_pixel']/s;b=(g[-1]+.5-v['centre_x'])*v['metres_per_pixel']/s
        out.append([-b,-a] if v['angle_degrees']==180 else [a,b])
    return sorted(out)
spans=[[intervals(row,v) for row in mask] for mask,v in zip(masks,views)]
boundaries=np.unique(np.concatenate([654-(v['sole_y']-(np.arange(721)-.5))*v['metres_per_pixel']/s for v in views]))
area=[0.,0.];overlap=0.;regions=[]
def intersection(a,b):
    i=j=0;total=0.
    while i<len(a) and j<len(b):
        total+=max(0,min(a[i][1],b[j][1])-max(a[i][0],b[j][0]))
        if a[i][1]<b[j][1]:i+=1
        else:j+=1
    return total
for lo,hi in zip(boundaries[:-1],boundaries[1:]):
    y=(lo+hi)/2;rows=[]
    for i,v in enumerate(views):
        py=int(np.floor(v['sole_y']-(654-y)*s/v['metres_per_pixel']+.5))
        rows.append(spans[i][py] if 0<=py<720 else [])
    dy=hi-lo
    for i in [0,1]:area[i]+=sum(b-a for a,b in rows[i])*dy
    overlap+=intersection(*rows)*dy
union=sum(area)-overlap;distance=(sum(area)-2*overlap)/union
# Nearest pixel visualization only; the continuous area result above does not
# resample either mask. Original native masks remain untouched for the gate.
f,b=views;yy,xx=np.indices(masks[0].shape)
bx=np.rint(b['centre_x']-(xx-f['centre_x'])*f['metres_per_pixel']/b['metres_per_pixel']).astype(int)
by=np.rint(b['sole_y']-(f['sole_y']-yy)*f['metres_per_pixel']/b['metres_per_pixel']).astype(int)
back=masks[1][np.clip(by,0,719),np.clip(bx,0,1279)]&(by>=0)&(by<720)&(bx>=0)&(bx<1280)
front=masks[0];canvas=np.zeros((720,1280,3),np.uint8)+32
canvas[front&back]=[140,150,155];canvas[front&~back]=[45,230,170];canvas[back&~front]=[240,90,150]
proof=Image.new('RGB',(1280,825),(29,30,33));draw=ImageDraw.Draw(proof);font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',23)
draw.text((18,10),'Source-only front/back consistency · locked scale and origins',font=font,fill='white')
draw.text((18,42),f'Continuous world-space Jaccard distance: {100*distance:.4f}% · minimax lower bound: {50*distance:.4f}%',font=font,fill='white')
draw.text((18,75),'Green: front only   Pink: back only   Grey: both · display aligned to front camera',font=font,fill='white')
proof.paste(Image.fromarray(canvas),(0,105));proof.save(P/'MALE_FORM_REFERENCE_CONFLICT.png')
report={'authority':['bald_front','bald_back'],'unchanged_masks':True,'unchanged_cameras':True,
 'method':'Exact intersection/union of source pixel cells in world space under frozen camera scale/origin; back reflected into the same X/Z projection. No candidate mesh used. The contact image uses nearest source pixels for display only.',
 'continuous_world_space_reference_distance':distance,'continuous_world_space_minimax_lower_bound':distance/2,
 'native_pixel_gate_caveat':'The delivered gate is still measured separately at each native raster, alpha >127. The continuous bound explains the conflicting outlines; native sampling introduces subpixel boundary quantization.',
 'front_area_metres_squared':area[0]*s*s,'back_area_metres_squared':area[1]*s*s,'union_metres_squared':union*s*s,
 'mask_sha256':{v['name']:hashlib.sha256((S/(v['name']+'_target.png')).read_bytes()).hexdigest() for v in views}}
(P/'male-form-reference-limit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
