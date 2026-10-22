import numpy as np,json,pathlib
O=pathlib.Path('work/reference-rebuild/face-finish30/forehead-check');result={}
for case in ('broad','ears','repair'):
 d=np.load(O/(case+'.npz'));p=d['p'];ns=d['n'];pick=(abs(p[:,0])<.032)&(p[:,1]<-.040)&(p[:,2]>1.585)&(p[:,2]<1.700);p=p[pick];ns=ns[pick];_,ii=np.unique(np.round(p,6),axis=0,return_index=True);p=p[ii];ns=ns[ii];rows=[]
 for z in np.arange(1.600,1.681,.005):
  x=p[:,0]/.012;v=(p[:,2]-z)/.012;w=np.exp(-(x*x+v*v)*2);A=np.c_[np.ones(len(p)),x,v,x*x,x*v,v*v,x*x*v,v*v*v];keep=w>.005;c=np.linalg.lstsq(A[keep]*np.sqrt(w[keep])[:,None],p[keep,1]*np.sqrt(w[keep]),rcond=None)[0];target=np.array([c[1]/.012,-1,c[2]/.012]);target/=np.linalg.norm(target);cn=np.sum(ns*w[:,None],axis=0);cn/=np.linalg.norm(cn);angle=np.rad2deg(np.arccos(np.clip(cn@target,-1,1)));rows.append({'z':float(z),'y':float(c[0]),'slope':float(c[2]/.012),'curvature':float(2*c[5]/.012**2/(1+(c[2]/.012)**2)**1.5),'normalErrorDeg':float(angle)})
 result[case]=rows
(O/'profiles.json').write_text(json.dumps(result,indent=2))
print('z  ears_y repair_y shift_mm ears_slope repair_slope ears_curv repair_curv normal_error_deg')
for a,b in zip(result['ears'],result['repair']):print('%.3f %.4f %.4f %+6.2f %+5.2f %+5.2f %+6.1f %+6.1f %5.1f'%(a['z'],a['y'],b['y'],(b['y']-a['y'])*1000,a['slope'],b['slope'],a['curvature'],b['curvature'],b['normalErrorDeg']))
