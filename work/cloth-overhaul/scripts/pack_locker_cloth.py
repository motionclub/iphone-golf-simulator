from pathlib import Path
import json,subprocess,hashlib,numpy as np
W=Path(__file__).resolve().parents[1];D=W/'locker/assets';O=W/'locker/packed';O.mkdir(exist_ok=True)
rows=[]
for sex in ['Male','Female']:
 j=json.loads((D/f'MatchHero_{sex}.json').read_text())
 for name in [f'MatchHero_{sex}',*j['swingFrames']]:
  inp=D/(name+'.lzfse');raw=O/(name+'.bin');out=O/(name+'.lzfse')
  subprocess.run(['/usr/bin/compression_tool','-decode','-a','lzfse','-i',str(inp),'-o',str(raw)],check=True,capture_output=True)
  original=raw.read_bytes();data=bytearray(original);mask=np.zeros(len(data),dtype=bool);maxpos=0;maxnormal=0
  for p in j['parts']:
   if p['kind']!='kit':continue
   for kind,shift in [('Position',10),('Normal',12)]:
    field=('swing'+kind+'Offset') if 'Swing' in name else kind.lower()+'Offset'
    offset=p[field];length=p['vertexCount']*12;a=np.frombuffer(data,dtype='<u4',count=length//4,offset=offset)
    old=a.view('<f4').copy();a[:]=(a+(1<<(shift-1)))&np.uint32(0xffffffff^((1<<shift)-1));new=a.view('<f4')
    error=float(np.linalg.norm((new-old).reshape(-1,3),axis=1).max())
    if kind=='Position':maxpos=max(maxpos,error)
    else:maxnormal=max(maxnormal,error)
    mask[offset:offset+length]=True
  assert np.array_equal(np.frombuffer(original,dtype=np.uint8)[~mask],np.frombuffer(data,dtype=np.uint8)[~mask])
  assert maxpos<.00015 and maxnormal<.0005,(name,maxpos,maxnormal)
  raw.write_bytes(data);subprocess.run(['/usr/bin/compression_tool','-encode','-a','lzfse','-i',str(raw),'-o',str(out)],check=True,capture_output=True)
  rows.append({'file':name+'.lzfse','before_bytes':inp.stat().st_size,'after_bytes':out.stat().st_size,'position_max_mm':maxpos*1000,'normal_max_vector_error':maxnormal,'noncloth_bytes_exact':True,'decompressed_bytes':len(data)})
  print(name,inp.stat().st_size,'->',out.stat().st_size,flush=True)
report={'method':'Round only kit pose positions to 10 cleared float mantissa bits and kit normals to 12; body, face, racket, UVs, indices, skeleton, weights and all rig/clip tracks remain byte-exact. Existing float32 layout and LZFSE reader are unchanged.','files':rows,'before_bytes':sum(r['before_bytes'] for r in rows),'after_bytes':sum(r['after_bytes'] for r in rows)}
(O/'packing_report.json').write_text(json.dumps(report,indent=2));print(report['before_bytes'],report['after_bytes'])
