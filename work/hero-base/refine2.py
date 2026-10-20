from pathlib import Path
p=Path('Tools/HeroBase/plate_profiles.py');s=p.read_text();s+='''
# Corrected centerlines after independent silhouette measurement; source masks stay unchanged.
MALE['arm']=[(84,222,27,32),(100,246,30,32),(123,280,28,29),(150,307,26,26),(174,328,24,24),(195,346,21,20),(215,370,16,16),(222,380,14,14)]
MALE['leg']=[(397,42,42,39),(416,44,42,42),(447,49,36,38),(477,54,31,33),(500,56,25,29),(518,59,23,31),(541,62,27,37),(569,63,25,34),(600,65,21,27),(625,65,20,24),(642,69,26,29),(657,76,32,44),(674,77,34,47),(680,77,27,42)]
FEMALE['arm']=[(57,230,13,16),(60,250,14,16),(62,278,14,15),(65,304,14,14),(70,330,14,14),(78,357,11,12),(85,385,9,10)]
FEMALE['leg']=[(382,33,30,33),(402,34,30,34),(429,35,29,31),(454,35,27,29),(479,37,22,24),(501,38,21,24),(520,38,22,29),(546,38,22,32),(575,39,21,28),(601,40,15,22),(622,40,13,17),(635,41,13,17),(649,44,17,27),(661,47,22,34),(670,49,22,36),(676,49,13,28)]
''';p.write_text(s)
p=Path('Tools/HeroBase/build_static.py');s=p.read_text();s=s.replace("(.50,.50,.50)","(.48,.48,.48)")
s=s.replace("profile['skin']),material", "tuple(v+(.035 if i!=0 else .025) for i,v in enumerate(profile['skin']))),material")
s=s.replace('cy=-frontdepth(cx,ey)+2','cy=-frontdepth(cx,ey)+3')
s=s.replace("pc=(sign*85,403)","pc=(sign*85,410)")
s=s.replace('y=412-fi*.6','y=418-fi*.6')
s=s.replace("pix(sign*76,398,-5),pix(sign*75,407,-8),pix(sign*77,419,-8)","pix(sign*76,403,-5),pix(sign*75,413,-8),pix(sign*77,425,-8)")
# Depth-only fairing at authored branch joins preserves the measured XY silhouette.
s=s.replace('body=g.make();uv(body)', '''body=g.make()
    import bmesh
    bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table()
    joins=[v for v in bm.verts if ((370 if female else 372)<sole-v.co.z/scale<(416 if female else 433))]
    for _ in range(5):
        vals={v: .55*v.co.y+.45*sum(e.other_vert(v).co.y for e in v.link_edges)/max(1,len(v.link_edges)) for v in joins}
        for v,y in vals.items():v.co.y=y
    bm.to_mesh(body.data);bm.free();uv(body)''')
# Replace ellipsoid cap with a measured full-volume bob/quiff profile.
a=s.index('                th=TAU*i/N;front=max(0,math.cos(th));phmax=1.94-.96*front')
b=s.index('                ring.append(h.vert(pix(x,y,dep)))',a)
s=s[:a]+'''                th=TAU*i/N;front=max(0,math.cos(th));back=max(0,-math.cos(th));yedge=104-39*front+45*back
                y=30+(yedge-30)*u
                width,depth=interp([(30,10,12),(38,36,30),(50,48,40),(66,53,46),(84,53,47),(102,49,46),(122,45,44),(138,39,36),(149,31,31)],y)
                x=width*math.sin(th);dep=-depth*math.cos(th)+1
'''+s[b:]
s=s.replace('ph0=.55+ring*.33;ph1=ph0+.42','ph0=.55+ring*.55;ph1=ph0+.60')
s=s.replace('91-58*math.cos(ph)','100-55*math.cos(ph)')
a=s.index('                th=TAU*i/N;front=max(0,math.cos(th));phmax=2.55')
b=s.index('                ring.append(h.vert(pix(x,y,dep)))',a)
s=s[:a]+'''                th=TAU*i/N;front=max(0,math.cos(th));yedge=187
                profile_h=[(79,4,6),(88,27,24),(101,42,34),(120,52,42),(141,58,46),(162,56,44),(179,47,39),(188,31,31)]
                if front>.15:
                    bangs=[(-57,181),(-43,153),(-30,127),(-15,118),(0,111),(14,106),(26,117),(37,146),(57,181)]
                    lo,hi=79,187
                    for _ in range(24):
                        mid=(lo+hi)/2;ww,dd=interp(profile_h,mid);xx=ww*math.sin(th)
                        if mid>interp(bangs,xx)[0]:hi=mid
                        else:lo=mid
                    yedge=(lo+hi)/2
                y=79+(yedge-79)*u;width,depth=interp(profile_h,y);x=width*math.sin(th)-4*max(0,1-(y-79)/55);dep=-depth*math.cos(th)+3
'''+s[b:]
# Trim quiff leaves that rise through the skull profile; width retains individual opaque clumps.
s=s.replace("(ph1-ph0)*t;ang", "(ph1-ph0)*t;ang")
# Normals preserved, source material contains no directional light in albedo.
p.write_text(s)
