import sys
def load(path):
    out=[]
    for ln in open(path).read().splitlines()[1:]:
        f=ln.split(',')
        v=lambda i:[float(x) for x in f[i:i+3]]
        out.append(dict(frame=int(f[0]),t=float(f[1]),flow=f[2],state=f[3],clip=float(f[4]),prep=float(f[5]),sw=f[6],ttc=float(f[7]),ball=v(8),Lh=v(11),Ls=v(14),Rh=v(17),Rs=v(20),head=v(23),strings=v(26),root=v(29),yaw=float(f[32]),Lel=(v(33) if len(f)>=36 else None),Rel=(v(36) if len(f)>=39 else None)))
    return out
if __name__=='__main__':
    rows=load(sys.argv[1]); step=int(sys.argv[2]) if len(sys.argv)>2 else 3
    sel=[r for r in rows if r['prep']>0.0005 and r['flow']!='Rally']
    f=lambda v:' '.join('%6.2f'%x for x in v)
    print('frame flow  clip  prep | ball(x,y,z) | Lhand-Lshoulder | Rhand-Rshoulder | head')
    for r in sel[::step]:
        d=lambda a,b:[x-y for x,y in zip(a,b)]
        print(r['frame'],r['flow'][-5:],'%.3f %.3f'%(r['clip'],r['prep']),'|',f(r['ball']),'|',f(d(r['Lh'],r['Ls'])),'|',f(d(r['Rh'],r['Rs'])),'|',f(r['head']), r['sw'][:1])
