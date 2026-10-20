import sys; sys.path.insert(0,'.')
from edges import *
from leglib import *
V=np.load(sys.argv[1])
print('x-edges (+x leg): plate consensus (mean of bf,sf,bb,sb) vs mesh; y-edges: mean(left,right plate) vs mesh union')
print(' z     inner(plate/mesh/dev)      outer(plate/mesh/dev)    |  yfront(plate/mesh/dev)  yback(plate/mesh/dev)')
devs=[]
for z in np.arange(0.06,0.74,0.04):
    ins=[];outs=[]
    for v,w in (('bald_front',2),('sheet_front',1),('bald_back',2),('sheet_back',1)):
        sp=[s for s in spans(v,z) if s[0]>=0.0 and s[1]>0.05]
        if sp: ins+= [sp[0][0]]*w; outs+=[sp[0][1]]*w
    s=LEFT&(np.abs(V[:,2]-z)<0.006); s2=RIGHT&(np.abs(V[:,2]-z)<0.006)
    mi=0.5*(V[s,0].min()+(-V[s2,0].max())); mo=0.5*(V[s,0].max()+(-V[s2,0].min()))
    pi,po=np.mean(ins),np.mean(outs)
    yf=[];yb=[]
    for v in ('left','right'):
        sp=spans(v,z)
        if sp: yf.append(sp[0][0]); yb.append(sp[-1][1])
    sy=ZONE&(np.abs(V[:,2]-z)<0.006)
    myf,myb=V[sy,1].min(),V[sy,1].max()
    pf,pb=np.mean(yf),np.mean(yb)
    print('%.2f   %.3f/%.3f/%+5.1f       %.3f/%.3f/%+5.1f     |  %.3f/%.3f/%+5.1f      %.3f/%.3f/%+5.1f'%(z,pi,mi,(mi-pi)*1000,po,mo,(mo-po)*1000,pf,myf,(myf-pf)*1000,pb,myb,(myb-pb)*1000))
