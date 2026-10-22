from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,sys,subprocess
r=Path(__file__).resolve().parents[1];stage=sys.argv[1];out=r/stage/'proof';out.mkdir(exist_ok=True)
refs=Path('/Users/adnanyonathan/Documents/Codex/2026-10-06/open-4/outputs/reference-check')
subprocess.run([sys.executable,str(r/'tools/landmark_grid.py'),stage],check=True)
# Manually traced on the native-resolution reference and registered front render.
# The uncertainty is one reference pixel per edge, not automated landmark detection.
ref_boxes={'male':{'eye L':[84,110,118,124],'eye R':[144,110,179,124],'brow L':[76,94,118,107],'brow R':[143,94,184,107],'nose':[110,127,150,162],'mouth':[99,169,162,188]},'female':{'eye L':[119,114,161,137],'eye R':[187,114,230,137],'brow L':[118,96,161,108],'brow R':[191,96,231,108],'nose':[157,140,188,167],'mouth':[148,174,198,190]}}
# Updated from final front grid before report generation.
ours_boxes={'male':{'eye L':[83,112,117,126],'eye R':[146,112,181,126],'brow L':[75,93,116,108],'brow R':[148,93,188,108],'nose':[112,128,150,160],'mouth':[100,171,164,188]},'female':{'eye L':[117,116,161,139],'eye R':[189,116,230,139],'brow L':[116,96,159,108],'brow R':[191,96,232,108],'nose':[158,141,185,164],'mouth':[148,173,198,188]}}
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',16);small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',12)
rows=[];colors=[]
def lab(rgb):
 c=np.asarray(rgb)/255;c=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
 xyz=np.array([[.4124564,.3575761,.1804375],[.2126729,.7151522,.0721750],[.0193339,.1191920,.9503041]])@c/np.array([.95047,1,1.08883]);v=np.where(xyz>.008856,xyz**(1/3),7.787*xyz+16/116)
 return np.array([116*v[1]-16,500*(v[0]-v[1]),200*(v[1]-v[2])])
for sex in ['male','female']:
 ref=Image.open(refs/f'{sex}-target.png').convert('RGB');ours=Image.open(r/stage/f'{sex}_registered.png').convert('RGB')
 blend=Image.blend(ref,ours,.5).resize((ref.width*3,ref.height*3),Image.Resampling.LANCZOS);d=ImageDraw.Draw(blend)
 for label,b in ref_boxes[sex].items():
  a=ours_boxes[sex][label];rv=np.array(b);av=np.array(a);wh=rv[2:]-rv[:2];awh=av[2:]-av[:2];cent=(av[:2]+av[2:]-rv[:2]-rv[2:])/2
  values=[abs(awh[0]/wh[0]-1)*100,abs(awh[1]/wh[1]-1)*100,abs(cent[0])/wh[0]*100,abs(cent[1])/wh[1]*100]
  rows.append({'hero':sex,'feature':label,'reference_bbox_px':b,'current_bbox_px':a,'width_error_percent':round(values[0],2),'height_error_percent':round(values[1],2),'center_x_percent_of_feature_width':round(values[2],2),'center_y_percent_of_feature_height':round(values[3],2),'pass':bool(max(values)<=5)})
  d.rectangle(tuple(x*3 for x in b),outline='#00ccff',width=2);d.rectangle(tuple(x*3 for x in a),outline='#ff4466',width=2);d.text((b[0]*3,b[1]*3-14),label,fill='#003344',font=small)
 board=Image.new('RGB',(blend.width,blend.height+72),'#ece8df');board.paste(blend,(0,72));draw=ImageDraw.Draw(board);draw.text((12,10),f'{sex.upper()} front / uniform crown-chin registration',fill='black',font=font);draw.text((12,32),'50% overlay: cyan reference / red current; manual bounds ±1 px',fill='black',font=small);draw.text((12,49),'Width, height and centre errors measured against feature dimensions.',fill='black',font=small);board.save(out/f'{sex}_front_overlay.png')
 pts={'forehead':(132,65),'left cheek':(91,146),'right cheek':(174,146),'jaw':(132,205),'lip':(131,181)} if sex=='male' else {'forehead':(174,65),'left cheek':(139,151),'right cheek':(212,151),'jaw':(174,206),'lip':(174,184)}
 for name,(x,y) in pts.items():
  a=np.asarray(ref)[y-2:y+3,x-2:x+3].mean(axis=(0,1));b=np.asarray(ours)[y-2:y+3,x-2:x+3].mean(axis=(0,1));colors.append({'hero':sex,'patch':name,'center_px':[x,y],'reference_RGB':a.round(1).tolist(),'current_RGB':b.round(1).tolist(),'deltaE76':round(float(np.linalg.norm(lab(a)-lab(b))),2)})
(out/'landmarks.json').write_text(json.dumps({'method':'Manual native-reference-pixel bounds; ±1 px edge uncertainty. Uniform scale and translation only. Width/height errors relative to reference feature size, centre errors normalized by corresponding feature dimension. No perspective correction. Bounds include apertures, not just irises. Nose bounds include bridge/alar form and carry more uncertainty than eye edges.','measurements':rows,'G2':'PASS' if all(x['pass'] for x in rows) else 'FAIL'},indent=2))
(out/'skin-patches.json').write_text(json.dumps({'method':'Mean sRGB of 5×5 reference-pixel patches; CIE76 distance, D65. No exposure/colour normalization. Different studio/court lighting is a material confound; this does not isolate albedo.','measurements':colors},indent=2))
print('G2','PASS' if all(x['pass'] for x in rows) else 'FAIL','max deviation',max(max(x[k] for k in ['width_error_percent','height_error_percent','center_x_percent_of_feature_width','center_y_percent_of_feature_height']) for x in rows))
