from pathlib import Path
p=Path('Tools/HeroBase/build_static.py');s=p.read_text()
s=s.replace('def ellipsoid(g,c,r,mi=0,n=32,k=18):\n    c=Vector(c);rings=[]','def ellipsoid(g,c,r,mi=0,n=32,k=18):\n    n=max(12,round(n*.78));k=max(8,round(k*.78));c=Vector(c);rings=[]')
s=s.replace('def tube(g,pts,widths,depths,mi=0,n=16,steps=36):','def tube(g,pts,widths,depths,mi=0,n=16,steps=36,cap_start=True):')
s=s.replace('rows=[(i,*p,widths[i],depths[i]) for i,p in enumerate(pts)];rings=[]','n=max(8,round(n*.70));steps=max(8,round(steps*.64));rows=[(i,*p,widths[i],depths[i]) for i,p in enumerate(pts)];rings=[]')
s=s.replace('g.cap(rings[0],mi);g.cap(rings[-1],mi)','if cap_start:g.cap(rings[0],mi)\n    g.cap(rings[-1],mi)')
s=s.replace("g=Geo('Body_'+suffix,mats);n=64","g=Geo('Body_'+suffix,mats);n=48")
s=s.replace("rows=profile['torso'];tor=[]\n    samples=40","rows=profile['torso'][:-1];tor=[]\n    samples=28")
s=s.replace('for a,b in zip(tor,tor[1:]):g.bridge(a,b)','''holes=[]
    j0=4 if not female else 3;j1=12 if not female else 11
    for side in (1,-1):
        c0,c1=(8,16) if side==1 else (32,40)
        boundary=tor[j0][c0:c1+1]+[tor[j][c1] for j in range(j0+1,j1+1)]+list(reversed(tor[j1][c0:c1]))+[tor[j][c0] for j in range(j1-1,j0,-1)]
        holes.append(boundary)
    for j,(a,b) in enumerate(zip(tor,tor[1:])):
        for i in range(n):
            if j0<=j<j1 and (8<=i<16 or 32<=i<40):continue
            g.face((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))''')
s=s.replace("rings=[];rows=profile['leg'];ns=58","rings=[];rows=profile['leg'];ns=42")
s=s.replace("ring.append(g.vert(pix(x,y,dep)))\n            rings.append(ring)","yy=y+max(0,-sign*math.sin(th))**2*18*max(0,1-j/6)\n                ring.append(g.vert(pix(x,yy,dep)))\n            rings.append(ring)",1)
s=s.replace("tube(g,pts,[r[2]*scale for r in rows],[r[3]*scale for r in rows],0,n=32,steps=36)","""ar=tube(g,pts,[r[2]*scale for r in rows],[r[3]*scale for r in rows],0,n=46,steps=44,cap_start=False)
        boundary=holes[0 if sign==1 else 1];first=ar[0]
        # resample boundary perimeter to tube circumference, preserving the authored shoulder opening.
        nA=len(first);nB=len(boundary)
        if nA!=nB:
            # zipper triangulation joins loops without Boolean/remesh or duplicated shoulder caps.
            best=min(range(nB),key=lambda k:(Vector(g.v[boundary[k]])-Vector(g.v[first[0]])).length)
            candidates=[]
            for rev in (1,-1):
                bb=[boundary[(best+rev*i)%nB] for i in range(nB)]
                score=sum((Vector(g.v[first[i]])-Vector(g.v[bb[round(i*nB/nA)%nB]])).length_squared for i in range(nA));candidates.append((score,bb))
            bb=min(candidates,key=lambda q:q[0])[1];ia=ib=0
            while ia<nA or ib<nB:
                if (ia+1)/nA<=(ib+1)/nB and ia<nA:
                    g.face((first[ia%nA],first[(ia+1)%nA],bb[ib%nB]));ia+=1
                else:g.face((first[ia%nA],bb[(ib+1)%nB],bb[ib%nB]));ib+=1
        else:
            bb=min(([boundary[(k+rev*i)%nB] for i in range(nB)] for k in range(nB) for rev in (1,-1)),key=lambda bb:sum((Vector(g.v[a])-Vector(g.v[b])).length_squared for a,b in zip(first,bb)))
            g.bridge(first,bb)""")
s=s.replace('N=96;K=46','N=80;K=38')
# Use direct surface smile geometry, eliminate dark disconnected overlapping opening.
s=s.replace("ellipsoid(g,pix(0,my,-frontdepth(0,my)+1),(21*scale,2.2*scale,7.3*scale),6,n=40,k=20)","ellipsoid(g,pix(0,my,-frontdepth(0,my)+3.3),(21*scale,2.0*scale,5.8*scale),6,n=40,k=20)")
s=s.replace("y=my-3.1+1.4*(x/19)**2","y=my-3.1-1.6*(x/19)**2")
s=s.replace("(2.8 if not upper else -4.8)","(4.0 if not upper else -4.8)")
s=s.replace("mw=16 if female else 21","mw=14 if female else 21")
# Hair caps must close via an inner shell, never a fan drawn across the face opening.
s=s.replace("h.cap(rings[0]);h.cap(rings[-1])","""h.cap(rings[0])
        inner=[];center=pix(0,128 if female else 91,3)
        for ring in rings:
            inner.append([h.vert(Vector(h.v[ix])+(center-Vector(h.v[ix])).normalized()*2*scale) for ix in ring])
        for a,b in zip(inner,inner[1:]):h.bridge(list(reversed(a)),list(reversed(b)))
        h.cap(list(reversed(inner[0])));h.bridge(rings[-1],inner[-1])""")
s=s.replace('N=72;K=18','N=56;K=16');s=s.replace('N=80;K=24;rings=[]','N=64;K=20;rings=[]')
s=s.replace("th=TAU*i/N;front=max(0,math.cos(th));phmax=2.85-1.58*front**4","""th=TAU*i/N;front=max(0,math.cos(th));phmax=2.55
                if front>.15:
                    bangs=[(-57,180),(-43,153),(-30,127),(-15,118),(0,111),(14,106),(26,117),(37,146),(57,180)]
                    def diff(ph):
                        x=56*math.sin(ph)*math.sin(th);yy=128-49*math.cos(ph)+max(0,ph-1.6)*12/1.25
                        return yy-interp(bangs,x)[0]
                    lo,hi=.01,2.55
                    for _ in range(24):
                        mid=(lo+hi)/2
                        if diff(mid)>0:hi=mid
                        else:lo=mid
                    phmax=(lo+hi)/2""")
# Constrain quiff height to the plate top while leaving its lower fit unchanged.
s=s.replace("hair=h.make();uv(hair)","""if not female:
        ymin=min(sole-v[2]/scale for v in h.v)
        h.v=[(x,d,(sole-(22+(y-ymin)*(100-22)/(100-ymin) if (y:=sole-z/scale)<100 else y))*scale) for x,d,z in h.v]
    hair=h.make();uv(hair)""")
p.write_text(s)
