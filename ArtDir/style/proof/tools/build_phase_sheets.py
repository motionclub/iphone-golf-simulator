"""Unretouched actual Unity BEFORE | AFTER | REF sheets plus fixed-ROI measurements.
Usage: build_phase_sheets.py BEFORE AFTER OUTPUT [--documentation-only]
All source frames keep original aspect; r4/r5 reference quadrants are labeled.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import argparse,json,hashlib,colorsys,numpy as np
p=argparse.ArgumentParser();p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('output',type=Path);p.add_argument('--documentation-only',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parents[4];refs=root/'ArtDir/style/refs';a.output.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
def reference(name):
 ref='r2';quadrant=None
 if name.startswith('hub'):ref='r1'
 elif name.startswith('golf'):ref='r3'
 if 'skyscraper' in name:ref='r4';quadrant=0
 elif 'volcano' in name:ref='r4';quadrant=1
 elif any('golf_'+n+'_' in name for n in ['10','16','21','22','23']):ref='r4';quadrant=3
 elif 'golf_17_' in name:ref='r4';quadrant=2
 for q,w in enumerate(['rain','storm','fog','gusty']):
  if '_'+w+'_' in name:ref='r5';quadrant=q
 im=Image.open(refs/(ref+'.png')).convert('RGB')
 if quadrant is not None:
  w,h=im.size;x=(quadrant%2)*w//2;y=(quadrant//2)*h//2;im=im.crop((x,y,x+w//2,y+h//2))
 return im,ref+(' panel '+str(quadrant+1) if quadrant is not None else '')
def stats(im,box):
 w,h=im.size;roi=np.array(im.crop(tuple(int(x*d) for x,d in zip(box,(w,h,w,h))))).reshape(-1,3);rgb=np.median(roi,axis=0)/255
 hue,L,S=colorsys.rgb_to_hls(*rgb);c=roi.astype(float)/255;linear=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4);lum=linear@np.array([.2126,.7152,.0722]);labL=116*np.where(lum>(6/29)**3,np.cbrt(lum),lum/(3*(6/29)**2)+4/29)-16
 return {'box':box,'hex':'#%02X%02X%02X'%tuple(np.rint(rgb*255).astype(int)),'HSL':[round(hue*360,2),round(S*100,2),round(L*100,2)],'linearLuminanceMedian':round(float(np.median(lum)),4),'LabRangeP90P10':round(float(np.percentile(labL,90)-np.percentile(labL,10)),2)}
rows=[]
for after in sorted(a.after.glob('*.png')):
 name=after.stem
 if not name.startswith(('tennis_','golf_','hub_')) or '.mask' in name:continue
 before=a.before/after.name
 if not before.exists():continue
 bi=Image.open(before).convert('RGB');ai=Image.open(after).convert('RGB');ri,rl=reference(name)
 sheet=Image.new('RGB',(1920,445),'#f2f3f5');d=ImageDraw.Draw(sheet)
 for col,(im,label) in enumerate([(bi,'BEFORE'),(ai,'AFTER — documentation only; render unchanged' if a.documentation_only else 'AFTER'),(ri,'REF — '+rl)]):
  sheet.paste(im.resize((640,360),Image.Resampling.LANCZOS),(col*640,45));d.text((col*640+10,12),label,font=font,fill='#141921')
 d.text((10,418),name+' | Actual Unity captures; reference is an appearance target, not an identical scene.',font=small,fill='#263341')
 sheet.save(a.output/(name+'_before_after_ref.jpg'),quality=94)
 # Fixed regions for transparent drift alerts. Not automatic artistic acceptance.
 boxes={'upper_sky':(.45,.04,.55,.10),'near_surface':(.62,.80,.72,.88),'scene_range':(.05,.15,.95,.90)}
 rows.append({'shot':name,'beforeSHA256':hashlib.sha256(before.read_bytes()).hexdigest(),'afterSHA256':hashlib.sha256(after.read_bytes()).hexdigest(),'reference':rl,'before':{k:stats(bi,v) for k,v in boxes.items()},'after':{k:stats(ai,v) for k,v in boxes.items()}})
(a.output.parent/'measurements.json').write_text(json.dumps(rows,indent=2)+'\n');print(len(rows),'sheets',a.output)
