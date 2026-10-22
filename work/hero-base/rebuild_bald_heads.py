from pathlib import Path
p=Path('Tools/HeroBase/measured_volume.py');s=p.read_text()
s=s.replace("ys=np.arange(163 if not female else 190,690,step,dtype=np.float32)","ys=np.arange(pr['torso'][0][0]-10,pr['sole']+12,step,dtype=np.float32)")
s=s.replace("tr=[((166 if not female else 193),1,1)]+tr+([(396,72,44),(412,35,26),(421,1,1)] if not female else [(387,60,42),(399,34,24),(407,1,1)])", "tr=[(pr['torso'][0][0]-3,1,1)]+tr+([(374,65,42),(384,20,24),(388,1,1)] if not female else [(359,58,40),(366,16,24),(369,1,1)])")
s=s.replace("w,d=curve(tr);a=(np.sqrt((X/np.maximum(w,1))**2+(Z/np.maximum(d,1))**2)-1)*np.minimum(w,d)",'''w,d=curve(tr)
    # Continuous chest and abdomen shaping lives on the body surface, with no glued-on muscle pieces.
    detail=np.zeros(shape,dtype=np.float32)
    if not female:
        detail=4.5*np.exp(-((np.abs(X)-31)/26)**2-((Y-225)/24)**2)-2*np.exp(-(X/5)**2-((Y-230)/34)**2)+1.4*np.exp(-((np.abs(X)-18)/14)**2-((Y-288)/32)**2)
    else:detail=2.6*np.exp(-((np.abs(X)-23)/20)**2-((Y-211)/27)**2)
    depth=d+np.where(Z<0,detail,0)
    a=(np.sqrt((X/np.maximum(w,1))**2+(Z/np.maximum(depth,1))**2)-1)*np.minimum(w,depth)''')
s=s.replace("lr=list(pr['leg']);lr=[(367 if not female else 351,lr[0][1],1,1),(379 if not female else 366,lr[0][1],25,25)]+lr", "lr=list(pr['leg']);lr=[(lr[0][0]-30,lr[0][1],1,1),(lr[0][0]-15,lr[0][1],lr[0][2]*.62,25)]+lr")
a=s.index('    for sign in (-1,1):\n        rows=pr[\'arm\']');b=s.index('    # exact ground plane',a)
s=s[:a]+'''    for sign in (-1,1):
        rows=pr['arm_sections'];cx,w,d=curve(rows)
        a=(np.sqrt(((X-sign*cx)/np.maximum(w,1))**2+(Z/np.maximum(d,1))**2)-1)*np.minimum(w,d)
        a=np.maximum(a,np.maximum(rows[0][0]-Y,Y-rows[-1][0]));add(a,2.5)
''' +s[b:]
s=s.replace('y>=622','y>=620')
p.write_text(s)
p=Path('Tools/HeroBase/build_static.py');s=p.read_text()
s=s.replace("material('Base_Grey',(.48,.48,.48))", "material('Base_Grey_'+suffix,profile['grey'])")
s=s.replace("material('Skin_'+suffix,tuple(v+(.035 if i!=0 else .025) for i,v in enumerate(profile['skin'])))", "material('Skin_'+suffix,profile['skin'])")
s=s.replace("material('Lip',(.51,.26,.15))", "material('Lip_'+suffix,tuple(v*f for v,f in zip(profile['skin'],(.97,.85,.79)))),material('Ear_Shadow_'+suffix,tuple(v*.88 for v in profile['skin']))")
s=s.replace("step=5.35 if female else 6.55", "step=5.2 if female else 6.0")
a=s.index('    # Flesh palm/finger/toe features');b=s.index('    # Head loft',a)
s=s[:a]+'''    # Hands remain part of the grey mannequin. Female feet retain the skin boundary of the supplied plate.
    for sign in (-1,1):
        if female:
            ellipsoid(g,pix(sign*91,383,-1),(11*scale,8*scale,21*scale),0,n=24,k=16)
            for fi in range(4):
                x=sign*(86+fi*3.8);y=391+fi*.3
                tube(g,[pix(x,y,-1),pix(sign*(85+fi*3.2),402-fi*.5,-3),pix(sign*(87+fi*1.8),411-fi*1.1,-1)],[2.5*scale,2.2*scale,.8*scale],[2.7*scale,2.4*scale,.9*scale],0,n=10,steps=12)
            tube(g,[pix(sign*83,378,-5),pix(sign*82,391,-8),pix(sign*85,400,-8)],[3.5*scale,3*scale,1.2*scale],[3.6*scale,3*scale,1.3*scale],0,n=12,steps=14)
            for fi in range(5):ellipsoid(g,pix(sign*(48+(fi-2)*5),sole-6,-43+fi),(3.3*scale,7*scale,3.5*scale),1,n=12,k=10)
        else:
            tube(g,[pix(sign*204,340,-6),pix(sign*201,350,-8),pix(sign*200,363,-7)],[5.8*scale,5.4*scale,1.5*scale],[5.5*scale,5*scale,1.8*scale],0,n=12,steps=16)
    # Neck under the complete jaw, shaped independently of optional hair.
    neckrows=profile['neck'];neck=[]
    for j in range(13):
        y=neckrows[0][0]+(neckrows[-1][0]-neckrows[0][0])*j/12;w,d=interp(neckrows,y);ring=[]
        for i in range(48):
            th=TAU*i/48;back=max(0,-math.cos(th));yy=y-(18 if female else 15)*back*(j/12)**3
            ring.append(g.vert(pix(w*math.sin(th),yy,-d*math.cos(th))))
        neck.append(ring)
    for a,b in zip(neck,neck[1:]):g.bridge(a,b,1)
''' +s[b:]
s=s.replace('N=72;K=39','N=96;K=54')
a=s.index('    def frontdepth(x,y):');b=s.index('    for j in range(K+1):',a)
s=s[:a]+'''    def frontdepth(x,y):
        w,d=interp(hrows,y);base=d*math.sqrt(max(0,1-(x/max(.01,w))**2))
        ex=profile['eye_x'];ey=profile['eye_y'];ny=profile['nose_y']
        for sx in (-1,1):
            base-=(1.6 if female else 1.1)*math.exp(-((x-sx*ex)/(profile['eye_r']+3))**2-((y-ey)/9)**2)
            base+=1.2*math.exp(-((x-sx*(ex+5))/11)**2-((y-(ey+14))/12)**2)
        # Nose, bridge, philtrum and chin grow from a single head surface.
        base+=profile['nose_depth']*.52*math.exp(-(x/3.5)**2-((y-(ny-7))/8)**2)
        base+=profile['nose_depth']*math.exp(-(x/profile['nose_w'])**2-((y-ny)/4.2)**2)
        base+=.75*math.exp(-(x/13)**2-((y-(profile['mouth_y']+10))/6)**2)
        base-=.35*math.exp(-(x/1.7)**2-((y-(profile['mouth_y']-4))/3)**2)
        return base
''' +s[b:]
a=s.index('            eye=any(');b=s.index('    g.cap(hr[0]',a)
s=s[:a]+'''            g.face((a[i],a[ni],b[ni],b[i]),1)
''' +s[b:]
s=s.replace('),8,n=20,k=14)', '),9,n=20,k=14)')
a=s.index('    # Eye whites placed');b=s.index('    body=g.make()',a)
s=s[:a]+'''    # Shallow eye surfaces conform to the skull, instead of protruding eyeball spheres.
    ex=profile['eye_x'];ey=profile['eye_y'];er=profile['eye_r'];ery=profile['eye_ry']
    def eye_depth(cx,x,y):
        r=((x-cx)/er)**2+((y-ey)/ery)**2
        return -frontdepth(x,y)-2.0*math.sqrt(max(0,1-r))
    def patch(cx,cy,rx,ry,depth_fn,mi,n=32,k=7):
        # Closed relief volume: front surface and skin-embedded backing share the outer edge.
        center=g.vert(pix(cx,cy,depth_fn(cx,cy)));rings=[]
        for j in range(1,k+1):
            rho=j/k;ring=[]
            for i in range(n):
                th=TAU*i/n;x=cx+rho*rx*math.cos(th);y=cy+rho*ry*math.sin(th)
                ring.append(g.vert(pix(x,y,depth_fn(x,y))))
            rings.append(ring)
        for i in range(n):g.face((center,rings[0][i],rings[0][(i+1)%n]),mi)
        for a,b in zip(rings,rings[1:]):g.bridge(a,b,mi)
        rear=g.vert(pix(cx,cy,-frontdepth(cx,cy)+1.0))
        for i in range(n):g.face((rings[-1][(i+1)%n],rings[-1][i],rear),mi)
    for sign in (-1,1):
        cx=sign*ex
        patch(cx,ey,er,ery,lambda x,y:eye_depth(cx,x,y)-.16,2)
        patch(cx,ey-.2,profile['iris_x'],profile['iris_y'],lambda x,y:eye_depth(cx,x,y)-.34,3,n=28,k=5)
        patch(cx,ey-.2,profile['pupil_x'],profile['pupil_y'],lambda x,y:eye_depth(cx,x,y)-.46,4,n=24,k=4)
        sx=cx-1.1;sy=ey-1.7;ellipsoid(g,pix(sx,sy,eye_depth(cx,sx,sy)-.62),(.6*scale,.15*scale,.7*scale),2,n=12,k=10)
        for upper in (True,False):
            pts=[];ws=[]
            for i in range(13):
                t=math.pi*i/12;x=cx+er*math.cos(t);y=ey+(-1 if upper else 1)*ery*math.sin(t)
                pts.append(pix(x,y,eye_depth(cx,x,y)-.2));ws.append((.38 if upper else .30)*scale)
            tube(g,pts,ws,[w*.8 for w in ws],5 if female and upper else 1,n=8,steps=28)
        by=profile['brow_y'];bw=11 if female else 9
        pts=[pix(cx-bw,by+1.7,-frontdepth(cx-bw,by+1.7)-.4),pix(cx-bw*.5,by-1.3,-frontdepth(cx-bw*.5,by-1.3)-.5),pix(cx+bw*.4,by-1.2,-frontdepth(cx+bw*.4,by-1.2)-.5),pix(cx+bw,by+1,-frontdepth(cx+bw,by+1)-.35)]
        tube(g,pts,[.35*scale,1.8*scale,1.6*scale,.25*scale],[.25*scale,.6*scale,.6*scale,.2*scale],5,n=12,steps=22)
    ny=profile['nose_y']
    for sign in (-1,1):
        x=sign*(3.2 if not female else 2.8);y=ny+2.1
        ellipsoid(g,pix(x,y,-frontdepth(x,y)-.15),(.65*scale,.25*scale,.4*scale),6,n=12,k=8)
    # Both new plates have a gentle closed smile, without a large mouth cavity or teeth bar.
    my=profile['mouth_y'];mw=profile['mouth_w']
    for upper in (True,False):
        pts=[];ws=[]
        for i in range(13):
            t=i/12;x=-mw+2*mw*t;y=my+(0 if upper else 1.6)-2.7*(x/mw)**2
            pts.append(pix(x,y,-frontdepth(x,y)-(.25 if upper else .35)))
            ws.append((.16+(.16 if upper else .42)*math.sin(math.pi*t))*scale)
        tube(g,pts,ws,[w*.7 for w in ws],6 if upper else 8,n=8,steps=32)
''' +s[b:]
s=s.replace("(205-y)/155", "(profile.get('atlas_y1',182)-y)/(profile.get('atlas_y1',182)-profile.get('atlas_y0',24))")
s=s.replace('if y<205 else (.02,.02)', "if y<profile.get('atlas_y1',182) else (.02,.02)")
s=s.replace("hm=material('Hair_'+suffix,(.085,.078,.069),.60)", "hm=material('Hair_'+suffix,(.045,.038,.032),.64);hm.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.20")
s=s.replace('N=56;K=16;rings=[]','N=48;K=12;rings=[]').replace('N=64;K=20;rings=[]','N=52;K=16;rings=[]')
s=s.replace('for row in range(4):','for row in range(3):').replace('for i in range(12):\n                th=math.pi/2+math.pi*i/11','for i in range(10):\n                th=math.pi/2+math.pi*i/9')
s=s.replace('yend=min([69,99,129,151][row]', 'yend=min([81,117,151][row]').replace('ystart=[31,57,87,117][row]','ystart=[32,65,101][row]')
s=s.replace('for i in range(17):\n            th=math.pi/2+math.pi*i/16','for i in range(15):\n            th=math.pi/2+math.pi*i/14')
s=s.replace('    hair=h.make();uv(hair)', '''    # Optional hairstyles are fitted to the new complete skull and kept out of the base proofs.
    old_eye=profile['hair_reference_eye_y'];new_eye=profile['eye_y']
    h.v=[(x*profile['hair_fit_x'],d*profile['hair_fit_depth'],(sole-(new_eye+(sole-z/scale-old_eye)*profile['hair_fit_y']))*scale) for x,d,z in h.v]
    hair=h.make();uv(hair)''')
s=s.replace("report['height_m']=max(v.co.z for o in (body,hair) for v in o.data.vertices)-min(v.co.z for o in (body,hair) for v in o.data.vertices)", "report['height_m']=max(v.co.z for v in body.data.vertices)-min(v.co.z for v in body.data.vertices);report['optional_hair_preview_height_m']=max(v.co.z for o in (body,hair) for v in o.data.vertices)-min(v.co.z for v in body.data.vertices)")
a=s.index('    for bald in (False,True):');b=s.index('    cam.location=(0,-5',a)
s=s[:a]+'''    for mode in ('base','bald','withhair'):
        hair.hide_render=mode!='withhair'
        for name,ang in [('front',0),('back',math.pi),('threequarter',math.pi/5)]:
            cam.location=(math.sin(ang)*5,-math.cos(ang)*5,(sole-360)*scale);cam.rotation_euler=(Vector((0,0,cam.location.z))-cam.location).to_track_quat('-Z','Y').to_euler()
            tag='' if mode=='base' else '_'+mode
            scene.render.filepath=str(P/'blender'/(suffix+tag+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
    hair.hide_render=True;hair.hide_viewport=True
''' +s[b:]
p.write_text(s)
# New texture range and pigment positions correspond to the new smaller faces, not the archived face layout.
p=Path('Tools/HeroBase/plate_profiles.py');s=p.read_text()+"\nMALE['atlas_y0']=24;MALE['atlas_y1']=182\nFEMALE['atlas_y0']=24;FEMALE['atlas_y1']=182\n";p.write_text(s)
p=Path('Tools/HeroBase/build_albedo.py');s=p.read_text().replace('y=50+v*155','y=24+v*158').replace("('Male',(.705,.465,.305)),('Female',(.735,.515,.355))", "('Male',(.77,.565,.425)),('Female',(.87,.68,.53))")
s=s.replace('(Y-130)/20','(Y-121)/15').replace('(175-Y)/9','(156-Y)/6').replace('((Y-141)/9)', '((Y-131)/5)').replace('((Y-158)/11)', '((Y-96)/9)')
p.write_text(s)
