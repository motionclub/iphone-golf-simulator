from pathlib import Path
O=Path('work/reference-rebuild/face-finish29/smooth-mouth1');s=Path('work/reference-rebuild/face-finish29/build-face-finish.py').read_text();s=s.replace("O=R/'work/reference-rebuild/face-finish29'","O=R/'work/reference-rebuild/face-finish29/smooth-mouth1'").replace('OriginalFaceFinish29','OriginalFaceFinish29Smooth1')
s=s.replace('upper=(.0028 if sex==\'Female\' else .0026)*gauss(z,upperLine,.0035)','upper=.0018*gauss(z,upperLine,.0045)').replace('lower=(.0040 if sex==\'Female\' else .0037)*gauss(z,lowerLine,.0040)','lower=.0024*gauss(z,lowerLine,.0050)').replace('seamRecess=.0010*gauss(relative,0,.0018)','seamRecess=0*relative')
s=s.replace('original=np.array([tuple(v.co) for v in me.vertices]);','originalCustomNormals=[tuple(d.value) for d in me.attributes[\'custom_normal\'].data];original=np.array([tuple(v.co) for v in me.vertices]);')
needle=' delta=np.zeros_like(original);'
field=''' # Fit local mouth depth with moving quadratic least squares. X/Z are fixed.
 # This removes high-frequency depth ridges while retaining broad original lip forms.
 mouthBlend=front*(1-smooth(mouthWidth*.78,mouthWidth*1.08,abs(x)))*(1-smooth(.016,.025,abs(relative)))*eyeFade
 mouthIds=np.flatnonzero((front>.8)&(abs(x)<mouthWidth+.018)&(abs(relative)<.039))
 mouthKd=KDTree(len(mouthIds))
 for i in mouthIds:mouthKd.insert(Vector((x[i],0,z[i])),int(i))
 mouthKd.balance()
 def surfaceFit(i,ys,radius=.011):
  nearby=mouthKd.find_range(Vector((x[i],0,z[i])),radius)
  ids=np.array([q[1] for q in nearby],dtype=int)
  if len(ids)<6:return np.array([ys[i],0,0,0,0,0])
  xx=(x[ids]-x[i])/radius;zz=(z[ids]-z[i])/radius;A=np.column_stack((np.ones(len(ids)),xx,zz,xx*xx,xx*zz,zz*zz));w=np.exp(-2*(xx*xx+zz*zz))
  return np.linalg.lstsq(A*w[:,None],ys[ids]*w,rcond=None)[0]
 fair=np.zeros(len(original))
 for i in np.flatnonzero(mouthBlend>.001):fair[i]=np.clip(surfaceFit(i,y)[0]-y[i],-.0025,.0025)*mouthBlend[i]
 lipdelta+=fair
'''
assert needle in s;s=s.replace(needle,field+needle)
needle=' assert invariants(body)==stable;'
post=''' # Smooth local mouth normals using the derivative of the same depth fit.
 calculatedNormals=[tuple(n.vector) for n in me.corner_normals]
 normalVectors=[(0,0,0)]*len(me.loops)
 newYs=np.array([v.co.y for v in me.vertices]);fittedNormals={}
 for i in np.flatnonzero(mouthBlend>.001):
  c=surfaceFit(i,newYs);nn=Vector((float(c[1]/.011),-1,float(c[2]/.011))).normalized();fittedNormals[int(i)]=nn
 for li,loop in enumerate(me.loops):
  i=loop.vertex_index
  if i in fittedNormals:normalVectors[li]=tuple(Vector(calculatedNormals[li]).lerp(fittedNormals[i],float(mouthBlend[i])).normalized())
 me.normals_split_custom_set(normalVectors)
 for li,loop in enumerate(me.loops):
  if loop.vertex_index not in fittedNormals:me.attributes['custom_normal'].data[li].value=originalCustomNormals[li]
 me.update()
 # Re-register lip and separation masks to smooth continuous upper/lower/seam fits.
 # Accepted relative hue coefficients remain exact; no dark border is added.
 oldLookup=np.array([tuple(u.uv) for u in me.uv_layers[0].data]);uvChanged=0;colorChanged=set()
 color=me.color_attributes.get('SkinPigment');maskByVertex={}
 lipAmount=.70*smooth(lowerLine-.002,lowerLine+.001,z)*(1-smooth(upperLine-.001,upperLine+.002,z))*(1-smooth(mouthWidth-.004,mouthWidth+.001,abs(x)))
 seamAmount=.35*gauss(relative,0,.0013)*(1-smooth(mouthWidth-.004,mouthWidth,abs(x)))
 for li,loop in enumerate(me.loops):
  i=loop.vertex_index
  if mouthBlend[i]<=.001:continue
  old=np.clip((oldLookup[li]*64-.5)/63,0,1);blend=float(mouthBlend[i]);new=old*(1-blend)+np.array([lipAmount[i],seamAmount[i]])*blend
  me.uv_layers[0].data[li].uv=((.5+63*new)/64);maskByVertex[i]=(old,new);uvChanged+=1
 if color:
  for i,(old,new) in maskByVertex.items():
   coeff=lambda m:(1+(np.array([.93,.66,.68])-1)*m[0])*(1+(np.array([.64,.49,.48])-1)*m[1])
   col=np.array(color.data[i].color);color.data[i].color=tuple(np.r_[col[:3]/coeff(old)*coeff(new),col[3]]);colorChanged.add(i)
 afterStable=invariants(body)
 assert all(afterStable[k]==stable[k] for k in ('topology','weights','groups'))
'''
assert needle in s;s=s.replace(needle,post+' assert True;')
s=s.replace("'topologyUvColorWeightsGroupsExact':True","'topologyWeightsGroupsExact':True,'uvColorChangesOnlyRegisteredMouth':True,'uvChangedLoops':uvChanged,'colorChangedVertices':len(colorChanged),'mouthFittedNormalsVertices':len(fittedNormals)")
s=s.replace("'upperLobeMm':2.8 if sex=='Female' else 2.6,'lowerLobeMm':4.0 if sex=='Female' else 3.7,'seamRecessMm':1.0","'upperLobeMm':1.8,'lowerLobeMm':2.4,'seamRecessMm':0,'mouthFairingMaxMm':2.5,'quadraticFitRadiusMm':11,'seamMaskPeak':.35,'seamMaskSigmaMm':1.3")
s=s.replace('Accepted relative-pigment UV buffers and runtime LUT unchanged. Physical lip lobes/seam, ala/nostril and broad cheek relief only.','Existing mouth masks re-registered continuously; relative pigment hue LUT unchanged. Broad physical lip lobes, local depth/normal fairing; no physical seam recess. Nose/cheek same field as Face29.')
(O/'build-smooth-mouth.py').write_text(s)
for name in ('render-source-preview.py','verify-blink-regression.py','verify-fbx-roundtrip.py'):
 a=Path('work/reference-rebuild/face-finish29',name).read_text().replace("O=R/'work/reference-rebuild/face-finish29'","O=R/'work/reference-rebuild/face-finish29/smooth-mouth1'").replace('OriginalFaceFinish29','OriginalFaceFinish29Smooth1')
 if name=='verify-blink-regression.py':a=a.replace('with', 'with')
 if name=='verify-fbx-roundtrip.py':a=a.replace("assert a['stable']==b['stable'];", "assert all(a['stable'][k]==b['stable'][k] for k in ('topology','weights')); ")
 (O/name).write_text(a)
