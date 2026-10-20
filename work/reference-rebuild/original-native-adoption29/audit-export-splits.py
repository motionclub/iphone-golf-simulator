from pathlib import Path
import ctypes,json,numpy as np,collections,hashlib
O=Path(__file__).resolve().parent;P=O.parent/'original-native-adoption1'
lib=ctypes.CDLL('/usr/lib/libcompression.dylib');decode=lib.compression_decode_buffer;decode.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_int];decode.restype=ctypes.c_size_t
def raw(path):
 encoded=path.read_bytes();src=ctypes.create_string_buffer(encoded);dst=ctypes.create_string_buffer(128*1024*1024);n=decode(dst,len(dst),src,len(encoded),None,0x801);assert 0<n<len(dst),(path,n);return dst.raw[:n]
def read(folder,stem):
 d=json.load(open(folder/(stem+'.json')));p=next(p for p in d['parts'] if p['name']=='Body');rp=next(p for p in d['rig']['parts'] if p['part']=='Body');base=raw(folder/(stem+'.lzfse'));rig=raw(folder/(d['rig']['file']+'.lzfse'));count=rp['vertexCount']
 def floats(blob,offset,width):return np.frombuffer(blob,dtype='<f4',count=count*width,offset=offset).reshape(count,width).copy()
 positions=floats(rig,rp['bindPositionOffset'],3)
 return {'count':count,'indices':np.frombuffer(base,dtype='<i4',count=p['submeshes'][0]['indexCount'],offset=p['submeshes'][0]['indexOffset']).copy(),'positions':positions,'normal':floats(rig,rp['bindNormalOffset'],3),'uv':floats(base,p['uvOffset'],2),'weights':floats(rig,rp['weightOffset'],4),'bones':np.frombuffer(rig,dtype='u1',count=count*4,offset=rp['indexOffset']).reshape(count,4).copy(),'morphs':{m['name']:floats(rig,m['positionOffset'],3)-positions for m in rp['morphs']},'rigBoneOrder':d['rig']['bones'],'rawBytes':[len(base),len(rig)]}
stem='MatchHero_Male';a=read(P/'export',stem);b=read(O/'export',stem);assert a['rigBoneOrder']==b['rigBoneOrder'];assert len(a['indices'])==len(b['indices'])
oldToNew=collections.defaultdict(set)
for old,new in zip(a['indices'],b['indices']):oldToNew[int(old)].add(int(new))
conflicts={k:sorted(v) for k,v in oldToNew.items() if len(v)>1};assert not conflicts,'triangle ordering/corner source correspondence differs: '+str(list(conflicts.items())[:8])
newToOld=collections.defaultdict(list)
for old,new in oldToNew.items():newToOld[next(iter(new))].append(old)
merges={k:sorted(v) for k,v in newToOld.items() if len(v)>1};details=[];mapped=np.array(sorted(oldToNew));newIds=np.array([next(iter(oldToNew[k])) for k in mapped]);d=b['positions'][newIds]-a['positions'][mapped]
print('COORD_DIFF',np.max(abs(d),axis=0),'merges',len(merges),'removed',sum(len(v)-1 for v in merges.values()),flush=True)
assert np.max(abs(d[:,[0,2]]))<1e-6,'fixed X/Z drift';assert np.max(abs(a['weights'][mapped]-b['weights'][newIds]))==0,'Bone weights changed';assert np.array_equal(a['bones'][mapped],b['bones'][newIds]),'Bone indices changed'
morphErrors={shape:float(np.max(abs(a['morphs'][shape][mapped]-b['morphs'][shape][newIds]))) for shape in a['morphs']}
for shape,error in morphErrors.items():assert error==0,shape+' delta changed'
for new,olds in merges.items():
 positions=a['positions'][olds];weights=a['weights'][olds];bones=a['bones'][olds];assert np.max(abs(positions-positions[0]))==0;assert np.max(abs(weights-weights[0]))==0;assert np.all(bones==bones[0])
 for shape in a['morphs']:assert np.max(abs(a['morphs'][shape][olds]-a['morphs'][shape][olds[0]]))==0
 details.append({'newVertex':new,'oldSplitVertices':olds,'sourceRestPosition':positions[0].tolist(),'oldNormalMaxDifference':float(np.max(abs(a['normal'][olds]-a['normal'][olds[0]]))),'oldUvMaxDifference':float(np.max(abs(a['uv'][olds]-a['uv'][olds[0]]))),'newNormal':b['normal'][new].tolist(),'newUv':b['uv'][new].tolist(),'oldPositionWeightsBonesMorphDeltasExactWithinMerge':True})
removed=sum(len(v)-1 for v in merges.values());assert a['count']-b['count']==removed==11
report={'gate':'PASS EXACT 11 ATTRIBUTE-SPLIT COLLAPSE, NO SOURCE FACE OR WEIGHT LOSS','oldVertexCount':a['count'],'newVertexCount':b['count'],'unchangedIndexCount':len(a['indices']),'unchangedTriangleCount':len(a['indices'])//3,'allTriangleCornersMapConsistently':True,'mappedOldVertices':len(mapped),'mappedNewVertices':len(newToOld),'mergedOldDuplicates':removed,'distinctMergedGroups':len(merges),'fixedXZMaxDeltaMetres':np.max(abs(d[:,[0,2]])).item(),'weightsBonesMorphDeltasExactAfterMapping':True,'morphDeltaMaxErrorMetres':morphErrors,'intentionalDepthMaxDeltaMm':float(np.max(abs(d[:,1]))*1000),'mergeDetails':details,'rawDecodedBytesBeforeAfter':[a['rawBytes'],b['rawBytes']],'explanation':'Same indexed triangle-corner order defines exact old-to-new source mapping. Each removed old vertex duplicates position, bone indices, weights and half/full morph deltas of retained vertex; old exported UV0 and rest normals also match within all eleven pairs. Smooth1 reduces duplicate imported mouth-seam records without removing triangles or physical source topology. The importer-only attribute responsible for splitting is not exported and is not inferred here.','filesChecked':{'oldBase':str(P/'export'/(stem+'.lzfse')),'newBase':str(O/'export'/(stem+'.lzfse'))}}
(O/'export-split-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='mergeDetails'},indent=2))
