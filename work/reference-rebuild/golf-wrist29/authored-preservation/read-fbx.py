import struct,zlib,json
from pathlib import Path
class Fbx:
 def __init__(self,p):
  self.b=Path(p).read_bytes();self.v=struct.unpack_from('<I',self.b,23)[0];self.wide=self.v>=7500;self.roots=[];o=27
  while True:
   n,o=self.node(o)
   if n is None:break
   self.roots.append(n)
 def node(self,o):
  end,nprops,nbytes,sz=struct.unpack_from('<QQQB' if self.wide else '<IIIB',self.b,o);o+=25 if self.wide else 13
  if end==0:return None,o
  name=self.b[o:o+sz].decode();o+=sz;props=[]
  for _ in range(nprops):
   t=chr(self.b[o]);o+=1
   if t in 'YCFDIL':
    fmt={'Y':'h','C':'?','F':'f','D':'d','I':'i','L':'q'}[t];v=struct.unpack_from('<'+fmt,self.b,o)[0];o+=struct.calcsize(fmt)
   elif t in 'SR':
    sz=struct.unpack_from('<I',self.b,o)[0];o+=4;v=self.b[o:o+sz];o+=sz
    if t=='S':v=v.decode(errors='replace')
   else:
    count,enc,sz=struct.unpack_from('<III',self.b,o);o+=12;b=self.b[o:o+sz];o+=sz;b=zlib.decompress(b) if enc else b;fmt={'f':'f','d':'d','l':'q','i':'i','b':'?','c':'b'}[t];v=list(struct.unpack('<'+fmt*count,b))
   props.append(v)
  kids=[]
  while o<end-(25 if self.wide else 13):
   n,o=self.node(o)
   if n is None:break
   kids.append(n)
  return {'n':name,'p':props,'c':kids},end
 def root(self,n):return next(x for x in self.roots if x['n']==n)
if __name__=='__main__':
 R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist29/authored-preservation'
 for sex in ('Male','Female'):
  f=Fbx(R/f'Unity/Assets/Resources/Hero/golfer_{"m" if sex=="Male" else "f"}.fbx');objects=f.root('Objects')['c'];subset=[]
  for n in objects:
   if n['n'] in ('AnimationStack','AnimationLayer'):subset.append({'type':n['n'],'p':n['p']})
   if n['n']=='Model' and 'RightLittleProximal' in n['p'][1]:subset.append(n)
  (W/f'{sex}-fbx-inventory.json').write_text(json.dumps(subset,indent=2));print(sex,f.v,[(x['type'],x['p']) for x in subset if 'type' in x]);print([x for x in subset if x.get('n')=='Model'])
