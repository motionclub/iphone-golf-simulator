from pathlib import Path
exec((Path(__file__).parent/'common.py').read_text())
import ctypes
from PIL import Image
lib=ctypes.CDLL(str(W/'raster.dylib'));lib.draw.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int]
def project(v):
 d=v-cam;z=d@fw;scale=600/np.tan(np.deg2rad(17));return np.ascontiguousarray(np.column_stack([450+d@camRight/z*scale,600-d@camUp/z*scale,z]))
def render(bp,tp,btri):
 z=np.full((1200,900),np.inf);ids=np.full((1200,900),-1,np.int32)
 for v,t,offset in [(bp,btri,0),(tp,tt,100000)]:
  t=np.ascontiguousarray(t,np.int32);lib.draw(project(v).ctypes.data,t.ctypes.data,len(t),900,1200,z.ctypes.data,ids.ctypes.data,offset)
 return ids
bp,tp=replay('female_Forehand_1');pic=render(bp,tp,bt[keep]);a=np.full((1200,900,3),218,np.uint8);a[(pic>=0)&(pic<100000)]=[220,155,100];a[pic>=100000]=[162,191,73];Image.fromarray(a).save(W/'camera-replay.png')
visible=np.unique(np.where(keep)[0][pic[(pic>=0)&(pic<100000)]]);central=(rest[:,1]>1.11)&(rest[:,1]<1.25)&(abs(rest[:,0])<.145)&(head<.035);candidates=np.where(keep&central[bt].all(1))[0];print('candidate faces',len(candidates),'visible',np.intersect1d(visible,candidates).tolist());print('ray15924/25 visible',np.intersect1d(visible,[15924,15925]));(W/'candidate-inspect.json').write_text(json.dumps([facefacts(f) for f in candidates],indent=2))
from collections import Counter
crop=pic[486:508,356:400];vc=Counter(np.where(keep)[0][crop[(crop>=0)&(crop<100000)]]);print('stripe ROI face counts')
for f,n in vc.most_common():
 r=facefacts(f);print(f,n,'rest',np.round(np.mean(r['rest'],0),5),'arm',np.round(r['armMass'],3))
Image.fromarray(a).crop((290,390,435,550)).resize((725,800)).save(W/'camera-replay-crop.png')
m3=json.loads((W/'BodyMask_female-current-matrix-canonical.json').read_text());k3=np.ones(len(bt),bool);k3[m3['alwaysCoveredFaceIndices']]=False;after=render(bp,tp,bt[k3]);a3=np.full((1200,900,3),218,np.uint8);a3[(after>=0)&(after<100000)]=[220,155,100];a3[after>=100000]=[162,191,73];Image.fromarray(a3).save(W/'camera-replay-mask3.png');before=Image.fromarray(a).crop((285,390,435,550)).resize((750,800));aft=Image.fromarray(a3).crop((285,390,435,550)).resize((750,800));plate=Image.new('RGB',(1500,800));plate.paste(before,(0,0));plate.paste(aft,(750,0));plate.save(W/'female_Forehand_1-mask2-mask3.png');print('new background pixels',np.count_nonzero((pic>=0)&(after<0)))
