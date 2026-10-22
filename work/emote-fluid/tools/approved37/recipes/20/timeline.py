"""Approved endpoint-preserving READY retiming; contacts outside these edges retain time."""
import numpy as np
def source_times(n,clip,dest):
 dest=np.asarray(dest,dtype=float);times=dest.copy()
 if clip in ['Emote_Spike','Intro_Pushups']:
  early_source=1.0 if clip=='Intro_Pushups' else 2.1
  times=np.interp(dest,[0,4.5,9,n-1],[0,early_source,9,n-1])
 a=n-17 if clip=='Intro_Pushups' else n-13;b=n-1 if clip=='Intro_Pushups' else n-6;duration=b-a
 u=np.clip((dest-a)/duration,0,1);edge=(2*u**3-3*u*u+1)*a+(u**3-2*u*u+u)*duration+(-2*u**3+3*u*u)*(n-1)
 return np.where(dest>=a,edge,times)
def destination_time(n,clip,src):
 d=np.linspace(0,n-1,(n-1)*100+1);s=source_times(n,clip,d);unique,idx=np.unique(s,return_index=True)
 return float(np.interp(src,unique,d[idx]))
