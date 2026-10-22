from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,sys
W=Path(__file__).resolve().parents[1];D=W/(sys.argv[1] if len(sys.argv)>1 else 'after_final');rois=json.loads((W/'fold_rois.json').read_text());res={};sheet=Image.new('RGB',(1500,len(rois)*300),'#eff1f4');draw=ImageDraw.Draw(sheet)
def lin(a):
 a=np.asarray(a,dtype=float)/255
 return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
for i,(name,roi) in enumerate(rois.items()):
 sex,feature=name.split('_');stem=sex+'_fold_'+feature;on=np.array(Image.open(D/(stem+'.png')));off=np.array(Image.open(D/(stem+'_noao.png')));data=np.array(Image.open(D/(stem+'_data_mask.png')));m=np.array(Image.open(D/(stem+'_mask.png')))
 role=1 if feature=='crotch' else 0;main=(m[:,:,role]>245)&(m[:,:,2]<10)&(m[:,:,1-role]<10)
 sel=main&(lin(data)[:,:,1]<=.85);crop=np.zeros(sel.shape,bool);x0,y0,x1,y1=roi;crop[y0:y1,x0:x1]=True;sel &= crop
 y1a=lin(on)@np.array([.2126,.7152,.0722]);y0a=lin(off)@np.array([.2126,.7152,.0722]);delta=(y0a-y1a)/np.maximum(y0a,1e-9)
 pct=float((y0a[sel].mean()-y1a[sel].mean())/y0a[sel].mean()*100);maxdark=float(delta[main & (y0a>.2)].max()*100)
 res[name]={'crop_xyxy':roi,'AO_threshold':.85,'crease_pixels':int(sel.sum()),'luma_noAO':float(y0a[sel].mean()),'luma_AO':float(y1a[sel].mean()),'darkening_percent':pct,'max_visible_lit_main_percent':maxdark,'pass':8<=pct<=20 and maxdark<=30}
 overlay=on.copy();overlay[sel]=[255,20,50]
 for j,arr in enumerate([off,on,overlay]):
  im=Image.fromarray(arr).crop(roi);im.thumbnail((465,245));sheet.paste(im,(j*500+10,i*300+30))
 draw.text((10,i*300+5),name+' AO off',fill='black');draw.text((510,i*300+5),f'AO on: {pct:.2f}% darker',fill='black');draw.text((1010,i*300+5),f'Measured texels {int(sel.sum())}; ROI {roi}',fill='black')
(W/'fold_measurement.json').write_text(json.dumps(res,indent=2));(W/'sheets').mkdir(exist_ok=True);sheet.save(W/'sheets/FOLDS_SHEET.png');print(json.dumps(res,indent=2))
