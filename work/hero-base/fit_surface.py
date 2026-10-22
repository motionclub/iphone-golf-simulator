from pathlib import Path
p=Path('Tools/HeroBase/measured_volume.py');s=p.read_text();needle='    base=len(g.v)\n'
insert='''    # Sculpt X coordinates to independent front/back plate boundaries, in the mesh itself.
    # This is a geometric fit at fixed Y/depth, never a resized/warped proof image.
    def intervals(poly,y,cx,reverse=False):
        cross=[]
        for (x0,y0),(x1,y1) in zip(poly,poly[1:]+poly[:1]):
            if min(y0,y1)<=y<max(y0,y1):cross.append(x0+(x1-x0)*(y-y0)/(y1-y0)-cx)
        cross.sort();pairs=[(cross[i],cross[i+1]) for i in range(0,len(cross)-1,2)]
        return list(reversed([(-b,-a) for a,b in pairs])) if reverse else pairs
    projection=field.min(axis=1);fits=[]
    for j,y in enumerate(ys):
        vals2=projection[:,j];inside=vals2<0;changes=np.flatnonzero(inside[:-1]!=inside[1:]);edges2=[]
        for i in changes:edges2.append(float(xs[i]+step*vals2[i]/(vals2[i]-vals2[i+1])))
        current=[(edges2[i],edges2[i+1]) for i in range(0,len(edges2)-1,2)]
        front=intervals(pr['front_outline'],float(y),pr['cx']);back=intervals(pr['back_outline'],float(y),pr['back_cx'],True);row=[]
        for a,b in current:
            center=(a+b)/2
            if not front:row.append((a,b,a,b));continue
            f=min(front,key=lambda q:abs((q[0]+q[1])/2-center))
            if back:
                bb=min(back,key=lambda q:abs((q[0]+q[1])/2-center))
                target=((f[0]+bb[0])/2,(f[1]+bb[1])/2) if abs((f[0]+f[1]-bb[0]-bb[1])/2)<12 else f
            else:target=f
            row.append((a,b,*target))
        fits.append(row)
    def warp(x,y):
        j=int(np.clip(round((y-ys[0])/step),0,len(ys)-1));row=fits[j]
        if not row or y<(211 if female else 195):return x,1
        a,b,c,d=min(row,key=lambda q:abs((q[0]+q[1])/2-x));r=(d-c)/max(1e-4,b-a)
        return (c+d)/2+(x-(a+b)/2)*r,r
    original_points=points.copy()
    # Interpolate between row fits so contours remain smooth at authored sampling boundaries.
    def smoothwarp(x,y):
        jf=np.clip((y-ys[0])/step,0,len(ys)-1);j=int(jf);u=jf-j
        q0,r0=warp(x,float(ys[j]));q1,r1=warp(x,float(ys[min(j+1,len(ys)-1)]));return q0*(1-u)+q1*u,r0*(1-u)+r1*u
    for i,pnt in enumerate(points):points[i,0]=smoothwarp(float(pnt[0]),float(pnt[2]))[0]
'''
s=s.replace(needle,insert+needle)
s=s.replace('gridcoords=(points-np.array([xs[0],ds[0],ys[0]]))/step','gridcoords=(original_points-np.array([xs[0],ds[0],ys[0]]))/step')
s=s.replace('norm/=np.maximum(np.linalg.norm(norm,axis=1),1e-9)[:,None]', '''for i,(x,dd,y) in enumerate(original_points):
        _,ratio=smoothwarp(float(x),float(y));xp,_=smoothwarp(float(x),float(y+.5));xm,_=smoothwarp(float(x),float(y-.5));deriv=xp-xm
        norm[i,2]-=deriv*norm[i,0]/ratio;norm[i,0]/=ratio
    norm/=np.maximum(np.linalg.norm(norm,axis=1),1e-9)[:,None]''')
p.write_text(s)
