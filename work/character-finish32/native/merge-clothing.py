"""Stage only validated garments over the current native asset; preserve other bytes and animation."""
from pathlib import Path
import json,copy,subprocess,hashlib,numpy as np,sys
repo=Path.cwd();w=repo/'work/character-finish32/native';codec=w/'cloth-codec';stem=sys.argv[1];candidate=Path(sys.argv[2]);out=Path(sys.argv[3]);roles=set(sys.argv[4:]) or {'Kit_Top'};current=repo/'GolfArcade/Unity/CharacterAssets';out.mkdir(parents=True,exist_ok=True);scratch=out/'raw';scratch.mkdir(exist_ok=True)
A=json.loads((current/(stem+'.json')).read_text());B=json.loads((candidate/(stem+'.json')).read_text());D=copy.deepcopy(A);report={'manifest':stem,'roles':sorted(roles),'sourceManifestSha256':hashlib.sha256((current/(stem+'.json')).read_bytes()).hexdigest(),'preservedNonGarmentParts':[],'animationMaxDelta':0}
def raw(root,name,label):
 dest=scratch/(label+'-'+name+'.bin');subprocess.run([str(codec),'decode',str(root/(name+'.lzfse')),str(dest)],check=True);return dest.read_bytes()
def encode(name,blob):
 dest=scratch/('merged-'+name+'.bin');dest.write_bytes(blob);subprocess.run([str(codec),'encode',str(dest),str(out/(name+'.lzfse'))],check=True)
baseA=raw(current,stem,'old');baseB=raw(candidate,stem,'candidate');base=bytearray(baseA)
def block(dest,src,offset,size):
 assert offset>=0 and offset+size<=len(src),(offset,size,len(src));new=len(dest);dest.extend(src[offset:offset+size]);return new
for part in D['parts']:
 if part['name'] not in roles:report['preservedNonGarmentParts'].append(part['name']);continue
 src=next(x for x in B['parts'] if x['name']==part['name']);part.clear();part.update(copy.deepcopy(src));n=part['vertexCount']
 for key,size in [('positionOffset',n*12),('normalOffset',n*12),('uvOffset',n*8)]:part[key]=block(base,baseB,src[key],size)
 for sub,other in zip(part['submeshes'],src['submeshes']):sub['indexOffset']=block(base,baseB,other['indexOffset'],other['indexCount']*4)
 if src.get('bindPositionOffset',-1)>=0:part['bindPositionOffset']=block(base,baseB,src['bindPositionOffset'],n*12)
assert base[:len(baseA)]==baseA;encode(stem,base)
ra,rb=A['rig'],B['rig'];assert ra['bones']==rb['bones'];assert ra['trackCount']==rb['trackCount'] and ra['floatsPerTrack']==rb['floatsPerTrack'];rigA=raw(current,ra['file'],'old');rigB=raw(candidate,rb['file'],'candidate');rig=bytearray(rigA)
for part in D['rig']['parts']:
 if part['part'] not in roles:continue
 src=next(x for x in rb['parts'] if x['part']==part['part']);part.clear();part.update(copy.deepcopy(src));n=src['vertexCount']
 for key,size in [('bindPositionOffset',n*12),('bindNormalOffset',n*12),('weightOffset',n*16),('indexOffset',n*4),('inverseBindOffset',len(src['bones'])*64)]:part[key]=block(rig,rigB,src[key],size)
 for morph,other in zip(part.get('morphs',[]),src.get('morphs',[])):
  for key in ['positionOffset','normalOffset']:morph[key]=block(rig,rigB,other[key],n*12)
for clip in D['rig']['clips']:
 src=next(x for x in rb['clips'] if x['id']==clip['id'])
 for key in ['name','loop','length','fps','contact','frames','times','equipment']:assert clip.get(key)==src.get(key),(stem,clip['id'],key)
 count=clip['frames']*ra['trackCount']*ra['floatsPerTrack'];aa=np.frombuffer(rigA,dtype='<f4',count=count,offset=clip['offset']);bb=np.frombuffer(rigB,dtype='<f4',count=count,offset=src['offset']);aa=aa.reshape(clip['frames'],ra['trackCount'],ra['floatsPerTrack'])[:,:len(ra['bones'])];bb=bb.reshape(clip['frames'],rb['trackCount'],rb['floatsPerTrack'])[:,:len(rb['bones'])];delta=float(abs(aa-bb).max());assert delta<1e-6,(clip['id'],delta);report['animationMaxDelta']=max(report['animationMaxDelta'],delta)
 clip['morphWeights']=[x for x in clip.get('morphWeights',[]) if x['part'] not in roles]
 for mw in src.get('morphWeights',[]):
  if mw['part'] in roles:
   item=copy.deepcopy(mw);item['offset']=block(rig,rigB,mw['offset'],clip['frames']*mw['count']*4);clip['morphWeights'].append(item)
assert rig[:len(rigA)]==rigA;encode(ra['file'],rig)
assert A['swingTimes']==B['swingTimes'] and A['swingFrames']==B['swingFrames']
for frame in A['swingFrames']:
 old=raw(current,frame,'old');new=raw(candidate,frame,'candidate');merged=bytearray(old)
 for part in D['parts']:
  if part['name'] not in roles:continue
  src=next(x for x in B['parts'] if x['name']==part['name']);n=src['vertexCount']
  for key in ['swingPositionOffset','swingNormalOffset']:
   offset=block(merged,new,src[key],n*12)
   if frame==A['swingFrames'][0]:part[key]=offset
   else:assert part[key]==offset
 assert merged[:len(old)]==old;encode(frame,merged)
# Existing palette roles and every non-garment material are retained.
known={x['name'] for x in D['materials']}
for m in B['materials']:
 if m['name'] not in known:D['materials'].append(copy.deepcopy(m));known.add(m['name'])
for pa,pd in zip(A['parts'],D['parts']):
 if pa['name'] not in roles:assert pa==pd
for pa,pd in zip(ra['parts'],D['rig']['parts']):
 if pa['part'] not in roles:assert pa==pd
(out/(stem+'.json')).write_text(json.dumps(D,indent=2));report.update(status='PASS',baseOriginalBytesPreserved=len(baseA),rigOriginalBytesPreserved=len(rigA),bonesUnchanged=len(ra['bones']),swingFramesUnchanged=len(A['swingFrames']));(out/(stem+'-merge-proof.json')).write_text(json.dumps(report,indent=2));print(report,flush=True)
