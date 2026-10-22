from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json
W=Path(__file__).resolve().parents[1]
def lin(v):
 v=np.asarray(v,dtype=np.float64)/255
 return np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)
def erode(m,n=2):
 for _ in range(n):m=m&np.roll(m,1,0)&np.roll(m,-1,0)&np.roll(m,1,1)&np.roll(m,-1,1)
 return m
out={}
for sex in ['male','female']:
 for variant,path in [('before',W/'before_verified'),('after',W/'after_final')]:
  if not (path/(sex+'_shimmer')).exists():continue
  means=[];sizes=[];frames=[]
  for i in range(180):
   f=f'{i:04d}';a=np.array(Image.open(path/(sex+'_shimmer')/(f+'.png')));m=np.array(Image.open(path/(sex+'_shimmer_mask')/(f+'_mask.png')))
   sel=erode((m[:,:,0]>245)&(m[:,:,1]<10)&(m[:,:,2]<10),3)
   y=lin(a[sel])@np.array([.2126,.7152,.0722]);means.append(float(y.mean()));sizes.append(int(sel.sum()))
   if i in [0,30,60,90,120,150,179]:
    yy,xx=np.where(sel);rect=(int(xx.min())-10,int(yy.min())-10,int(xx.max())+11,int(yy.max())+11);crop=Image.fromarray(a).crop(rect);crop.thumbnail((230,250));frames.append((i,crop))
  v=np.array(means);flicker=float(np.sqrt(np.mean(np.diff(v,2)**2))/np.sqrt(6));out[sex+'_'+variant]={'frames':180,'fps':60,'metric':'RMS second temporal difference of linear Rec.709 shirt interior mean / sqrt(6)','linear_luma_flicker':flicker,'shirt_mean_luma':float(v.mean()),'shirt_pixels_min':min(sizes),'shirt_pixels_max':max(sizes),'frame_luma_means':means}
  sheet=Image.new('RGB',(7*240,290),'#eff1f4');d=ImageDraw.Draw(sheet)
  for j,(i,img) in enumerate(frames):sheet.paste(img,(j*240,25));d.text((j*240+5,5),f'{sex} {variant} {i/60:.2f}s',fill='black')
  dest=W/'sheets';dest.mkdir(exist_ok=True);sheet.save(dest/f'SHIMMER_{sex}_{variant}.png')
 forvariant=[out.get(sex+'_'+x) for x in ['before','after']]
 if all(forvariant):out[sex+'_pass']=forvariant[1]['linear_luma_flicker']<=forvariant[0]['linear_luma_flicker']
(W/'shimmer_measurement.json').write_text(json.dumps(out,indent=2))
print({k:v if isinstance(v,bool) else v['linear_luma_flicker'] for k,v in out.items()})
