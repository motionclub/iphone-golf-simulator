from pathlib import Path
from PIL import Image
import numpy as np,json,sys
W=Path(__file__).resolve().parents[1];D=W/(sys.argv[1] if len(sys.argv)>1 else 'after_final');out={}
def lin(a):
 a=a/255.;return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
for sex in ['male','female']:
 im=np.array(Image.open(D/f'{sex}_match_phone.png'),float);m=np.array(Image.open(D/f'{sex}_match_phone_mask.png'));y=lin(im)@np.array([.2126,.7152,.0722]);L=np.where(y>216/24389,116*np.cbrt(y)-16,24389/27*y)
 for j,role in enumerate(['shirt','bottom','trim']):
  mask=(m[:,:,j]>245)&(m[:,:,(j+1)%3]<10)&(m[:,:,(j+2)%3]<10);v=L[mask];bounds=[90,95] if role=='shirt' else [88,95] if role=='bottom' else [8,20];out[sex+'_'+role]={'pixels':int(mask.sum()),'mean_Lstar':float(v.mean()),'median_Lstar':float(np.median(v)),'range_required':bounds,'pass':bool(bounds[0]<=v.mean()<=bounds[1])}
(W/'white_measurement.json').write_text(json.dumps(out,indent=2));print({k:(round(v['mean_Lstar'],3),v['pass']) for k,v in out.items()})
