import struct,zlib,json
from pathlib import Path
p=Path('Unity/Assets/Resources/Tennis/TropicalV3/TropicalTennisResort.fbx')
b=p.read_bytes();ver=struct.unpack_from('<I',b,23)[0];wide=ver>=7500;head=25 if wide else 13

def prop(o):
 t=chr(b[o]);o+=1
 size={'Y':2,'C':1,'I':4,'F':4,'D':8,'L':8}
 fmt={'Y':'h','C':'?','I':'i','F':'f','D':'d','L':'q'}
 if t in size:return struct.unpack_from('<'+fmt[t],b,o)[0],o+size[t]
 if t in 'SR':
  n=struct.unpack_from('<I',b,o)[0];v=b[o+4:o+4+n];return v,o+4+n
 if t in 'fdlibc':
  n,enc,sz=struct.unpack_from('<III',b,o);o+=12;raw=b[o:o+sz];raw=zlib.decompress(raw) if enc else raw
  code={'f':'f','d':'d','l':'q','i':'i','b':'?','c':'b'}[t]
  return struct.unpack('<'+str(n)+code,raw),o+sz
 raise ValueError(t)
def node(o):
 if wide:e,n,z,l=struct.unpack_from('<QQQB',b,o)
 else:e,n,z,l=struct.unpack_from('<IIIB',b,o)
 if e==0:return None,o+head
 name=b[o+head:o+head+l].decode();o+=head+l;props=[]
 for _ in range(n):v,o=prop(o);props.append(v)
 children=[]
 while o<e-head:
  c,o=node(o)
  if c:children.append(c)
 return (name,props,children),e
nodes=[];o=27
while o<len(b)-head:
 n,o=node(o)
 if not n:break
 nodes.append(n)
objects=next(n[2] for n in nodes if n[0]=='Objects');connections=next(n[2] for n in nodes if n[0]=='Connections')
ids={n[1][0]:n for n in objects};links={}
for c in connections:
 if c[0]=='C':links.setdefault(c[1][2],[]).append(c[1][1])
rows=[]
for ob in objects:
 if ob[0]!='Model':continue
 children=[ids[x] for x in links.get(ob[1][0],[]) if x in ids]
 mats=[x for x in children if x[0]=='Material'];geos=[x for x in children if x[0]=='Geometry']
 if not any(b'TropicalV3_001' in x[1][1] for x in mats):continue
 for geo in geos:
  v=next((x[1][0] for x in geo[2] if x[0]=='Vertices'),[])
  pts=list(zip(v[0::3],v[1::3],v[2::3]));pol=next((x[1][0] for x in geo[2] if x[0]=='PolygonVertexIndex'),[])
  ps=next((x[2] for x in ob[2] if x[0]=='Properties70'),[])
  props={x[1][0].decode():x[1][4:] for x in ps if x[0]=='P' and x[1][0] in (b'Lcl Translation',b'Lcl Rotation',b'Lcl Scaling')}
  rows.append({'model':ob[1][1].decode(errors='replace'),'vertices':len(pts),'faces':sum(x<0 for x in pol),'boundsMin':[min(p[i] for p in pts) for i in range(3)],'boundsMax':[max(p[i] for p in pts) for i in range(3)],'modelTRS':props,'sampleVertices':pts[:8]})
print(json.dumps({'fbxVersion':ver,'water':rows},indent=2));Path('work/reference-rebuild/tennis-water2/source-water-assay.json').write_text(json.dumps(rows,indent=2))
