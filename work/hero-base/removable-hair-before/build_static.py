"""Plate-constrained static HeroBase sources. No archived character geometry, rig or outfit."""
import bpy, math, sys, json, hashlib
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from plate_profiles import MALE,FEMALE
R=Path(__file__).resolve().parents[2]; D=R/'ArtDir/hero/base_lock'; P=D/'proof'
for p in [D/'blender',D/'unity_import',P/'blender',P/'masks']:p.mkdir(parents=True,exist_ok=True)
TAU=math.tau

def interp(rows,t):
    # Shape-preserving cubic Hermite, with monotone slopes (no unconstrained subdivision).
    if t<=rows[0][0]:return rows[0][1:]
    if t>=rows[-1][0]:return rows[-1][1:]
    for i in range(len(rows)-1):
        a,b=rows[i:i+2]
        if a[0]<=t<=b[0]:break
    u=(t-a[0])/(b[0]-a[0]);out=[]
    for j in range(1,len(a)):
        d=(b[j]-a[j])/(b[0]-a[0])
        dl=(a[j]-rows[i-1][j])/(a[0]-rows[i-1][0]) if i else d
        dr=(rows[i+2][j]-b[j])/(rows[i+2][0]-b[0]) if i+2<len(rows) else d
        m0=0 if dl*d<=0 else 2*dl*d/(dl+d)
        m1=0 if dr*d<=0 else 2*dr*d/(dr+d)
        out.append((2*u**3-3*u*u+1)*a[j]+(u**3-2*u*u+u)*(b[0]-a[0])*m0+(-2*u**3+3*u*u)*b[j]+(u**3-u*u)*(b[0]-a[0])*m1)
    return out

def linrgb(c):return tuple(((v+.055)/1.055)**2.4 if v>.04045 else v/12.92 for v in c)
def material(name,c,rough=.62):
    m=bpy.data.materials.new(name);m.diffuse_color=(*linrgb(c),1);m.use_nodes=True
    n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=m.diffuse_color;n.inputs['Roughness'].default_value=rough;n.inputs['Metallic'].default_value=0
    return m

class Geo:
    def __init__(self,name,mat):self.name=name;self.v=[];self.f=[];self.mi=[];self.mat=mat
    def vert(self,p):self.v.append(tuple(p));return len(self.v)-1
    def face(self,ids,mi=0):self.f.append(ids);self.mi.append(mi)
    def bridge(self,a,b,mi=0):
        for j in range(len(a)):self.face((a[j],a[(j+1)%len(a)],b[(j+1)%len(a)],b[j]),mi)
    def cap(self,ring,mi=0):
        c=self.vert(sum((Vector(self.v[i]) for i in ring),Vector())/len(ring))
        for j in range(len(ring)):self.face((ring[j],ring[(j+1)%len(ring)],c),mi)
    def make(self):
        me=bpy.data.meshes.new(self.name);me.from_pydata(self.v,[],self.f);me.update()
        o=bpy.data.objects.new(self.name,me);bpy.context.collection.objects.link(o)
        for m in self.mat:me.materials.append(m)
        for f,i in zip(me.polygons,self.mi):f.material_index=i;f.use_smooth=True
        import bmesh
        bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
        me.update()
        if hasattr(self,'custom_normals'):
            normals=[tuple(self.custom_normals.get(i,me.vertices[i].normal)) for i in range(len(me.vertices))]
            me.normals_split_custom_set_from_vertices(normals)
        return o

def uv(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(65),island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')

def ellipsoid(g,c,r,mi=0,n=32,k=18):
    n=max(12,round(n*.70));k=max(8,round(k*.70));c=Vector(c);rings=[]
    for j in range(1,k):
        ph=math.pi*j/k;ring=[]
        for i in range(n):
            th=TAU*i/n;ring.append(g.vert(c+Vector((r[0]*math.sin(ph)*math.sin(th),-r[1]*math.sin(ph)*math.cos(th),r[2]*math.cos(ph)))))
        rings.append(ring)
    for a,b in zip(rings,rings[1:]):g.bridge(a,b,mi)
    for ri,z in [(rings[0],r[2]),(rings[-1],-r[2])]:
        ix=g.vert(c+Vector((0,0,z)))
        for i in range(n):g.face((ri[i],ri[(i+1)%n],ix),mi)

def tube(g,pts,widths,depths,mi=0,n=16,steps=36,cap_start=True):
    # Catmull-free monotone coordinates; pointed sculpted volumes, not cards.
    n=max(8,round(n*.64));steps=max(8,round(steps*.58));rows=[(i,*p,widths[i],depths[i]) for i,p in enumerate(pts)];rings=[]
    for j in range(steps+1):
        t=(len(pts)-1)*j/steps;v=interp(rows,t);c=Vector(v[:3]);lo=Vector(interp(rows,max(0,t-.01))[:3]);hi=Vector(interp(rows,min(len(pts)-1,t+.01))[:3]);axis=(hi-lo).normalized()
        side=axis.cross(Vector((0,1,0))).normalized()
        if side.length<.01:side=Vector((1,0,0))
        dep=side.cross(axis).normalized();ring=[]
        for i in range(n):
            th=TAU*i/n;ring.append(g.vert(c+side*(v[3]*math.cos(th))+dep*(v[4]*math.sin(th))))
        rings.append(ring)
    for a,b in zip(rings,rings[1:]):g.bridge(a,b,mi)
    if cap_start:g.cap(rings[0],mi)
    g.cap(rings[-1],mi)
    return rings

def build(sex,suffix,profile):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for m in list(bpy.data.materials):bpy.data.materials.remove(m)
    scale=1.7/profile['height'];sole=profile['sole'];female=sex=='female'
    pix=lambda x,y,d=0:Vector((x*scale,d*scale,(sole-y)*scale))
    mats=[material('Base_Grey',(.48,.48,.48)),material('Skin_'+suffix,tuple(v+(.035 if i!=0 else .025) for i,v in enumerate(profile['skin']))),material('Eye_White',(.88,.87,.82),.30),material('Iris_Dark',(.19,.13,.085),.31),material('Pupil',(.026,.024,.022),.22),material('Brow',(.075,.064,.053)),material('Mouth',(.20,.074,.044)),material('Teeth',(.91,.88,.80),.36),material('Lip',(.51,.26,.15))]
    g=Geo('Body_'+suffix,mats);n=48
    from measured_volume import append_volume
    append_volume(g,pix,profile,interp,female,step=5.2 if female else 6.40)
    # Flesh palm/finger/toe features are part of Body, with a material boundary at the wrist/ankle.
    if female:
        for sign in (-1,1):
            ellipsoid(g,pix(sign*85,406,-1),(10*scale,8*scale,19*scale),1,n=24,k=16)
            for fi in range(4):
                x=sign*(79+fi*4);y=416-fi*.6
                tube(g,[pix(x,y,-1),pix(x+sign*1,y+12,-2),pix(x-sign*2,y+23,-1)],[2.7*scale,2.5*scale,.9*scale],[3.1*scale,2.7*scale,1*scale],1,n=10,steps=12)
            tube(g,[pix(sign*76,403,-5),pix(sign*75,413,-8),pix(sign*77,425,-8)],[4*scale,3.2*scale,1.4*scale],[4*scale,3.2*scale,1.4*scale],1,n=12,steps=14)
            for fi in range(5):ellipsoid(g,pix(sign*(48+(fi-2)*5),670,-43+fi*1),(3.4*scale,7*scale,3.7*scale),1,n=12,k=10)
    # Neck; shared body object but material boundary follows neckline.
    neckrows=[(168,18,18),(178,20,20),(190,19,19),(201,17,18)] if female else [(150,27,26),(162,27,26),(174,28,27),(190,33,28)]
    neck=[]
    for j in range(13):
        y=neckrows[0][0]+(neckrows[-1][0]-neckrows[0][0])*j/12;w,d=interp(neckrows,y);ring=[g.vert(pix(w*math.sin(TAU*i/48),y,-d*math.cos(TAU*i/48))) for i in range(48)];neck.append(ring)
    for a,b in zip(neck,neck[1:]):g.bridge(a,b,1)
    # Head loft + analytical facial volumes. Eye/mouth openings cut into surface.
    hrows=list(reversed(profile['head']));hrows.sort();hr=[];N=72;K=34
    def frontdepth(x,y):
        w,d=interp(hrows,y);base=d*math.sqrt(max(0,1-(x/max(.01,w))**2))
        ex=profile['eye_x'];ey=profile['eye_y']
        for sx in (-1,1):base-=4*math.exp(-((x-sx*ex)/11)**2-((y-ey)/12)**2);base+=2.0*math.exp(-((x-sx*(ex+8))/13)**2-((y-(ey+19))/13)**2)
        base+=2.6*math.exp(-(x/17)**2-((y-(profile['mouth_y']-2))/11)**2)
        return base
    for j in range(K+1):
        y=hrows[0][0]+(hrows[-1][0]-hrows[0][0])*j/K;w,d=interp(hrows,y);ring=[]
        for i in range(N):
            th=TAU*i/N;x=w*math.sin(th);dep=-d*math.cos(th)
            if math.cos(th)>0:dep=-frontdepth(x,y)
            ring.append(g.vert(pix(x,y,dep)))
        hr.append(ring)
    for j,(a,b) in enumerate(zip(hr,hr[1:])):
        for i in range(N):
            ni=(i+1)%N;c=sum((Vector(g.v[k]) for k in (a[i],a[ni],b[ni],b[i])),Vector())/4;x=c.x/scale;y=sole-c.z/scale;front=c.y<-.018
            eye=any(((x-sx*profile['eye_x'])/(profile['eye_r']*.94))**2+((y-profile['eye_y'])/(profile['eye_r']*.94))**2<1 for sx in (-1,1))
            mouth=not female and (abs(x)<20 and profile['mouth_y']-7+5*(x/20)**2<y<profile['mouth_y']+4-5*(x/20)**2)
            if not (front and (eye or mouth)):g.face((a[i],a[ni],b[ni],b[i]),1)
    g.cap(hr[0],1);g.cap(hr[-1],1)
    # Ears: rounded rims and recessed inner lobe, with no disconnected sticker outline.
    ex,ey,ew,eh=profile['ear']
    for sign in (-1,1):
        ellipsoid(g,pix(sign*ex,ey,-2),(ew*scale,7*scale,eh*scale),1,n=28,k=20)
        ellipsoid(g,pix(sign*(ex+1),ey,-7),(ew*.55*scale,1.2*scale,eh*.66*scale),8,n=20,k=14)
    # Eye whites placed into the head openings; irises sit on their curved fronts.
    ex=profile['eye_x'];ey=profile['eye_y'];er=profile['eye_r']
    for sign in (-1,1):
        cx=sign*ex;cy=-frontdepth(cx,ey)+3
        ellipsoid(g,pix(cx,ey,cy),(er*scale,6.7*scale,(er+.6)*scale),2,n=32,k=22)
        ellipsoid(g,pix(cx+.25,ey+.2,cy-6.55),(5.9*scale,.9*scale,6.6*scale),3,n=28,k=18)
        ellipsoid(g,pix(cx+.25,ey+.2,cy-7.32),(3.8*scale,.6*scale,4.6*scale),4,n=24,k=16)
        ellipsoid(g,pix(cx-1.4,ey-2.2,cy-7.9),(1.25*scale,.45*scale,1.3*scale),2,n=12,k=10)
        # Eyelid margins form a soft socket, rather than giant separate floating eyes.
        for upper in (True,False):
            pts=[];ws=[];ds=[]
            for i in range(9):
                t=math.pi*i/8;x=cx+er*math.cos(t);y=ey+(-1 if upper else 1)*(er+.8)*math.sin(t);dep=cy-2.1-3*math.sin(t)
                pts.append(pix(x,y,dep));ws.append((.7 if female else 1.1)*scale);ds.append(.8*scale)
            tube(g,pts,ws,ds,5 if female and upper else 1,n=8,steps=24)
        by=profile['brow_y'];pts=[pix(cx-10,by+2,-frontdepth(cx-10,by+2)-.7),pix(cx-5,by-1,-frontdepth(cx-5,by-1)-.8),pix(cx+3,by-1.5,-frontdepth(cx+3,by-1.5)-.8),pix(cx+10,by+1,-frontdepth(cx+10,by+1)-.5)]
        tube(g,pts,[.8*scale,2.0*scale,2*scale,.7*scale],[.7*scale,1.2*scale,1.2*scale,.6*scale],5,n=10,steps=18)
    # Nose grows from bridge with small alar lobes.
    ny=ey+20 if not female else ey+16;nd=frontdepth(0,ny)
    ellipsoid(g,pix(0,ny-7,-nd-1),(4.5*scale,5*scale,10*scale),1,n=28,k=20)
    ellipsoid(g,pix(0,ny,-nd-5),(6*scale,7*scale,4.5*scale),1,n=32,k=18)
    for sign in (-1,1):
        ellipsoid(g,pix(sign*4.8,ny+1,-nd-3),(3.3*scale,4.8*scale,3*scale),1,n=20,k=14)
        ellipsoid(g,pix(sign*3.8,ny+2.9,-nd-6.5),(1.2*scale,1*scale,.7*scale),6,n=12,k=8)
    # Mouth opening/teeth/lips use the actual smile arc of the authority plate.
    my=profile['mouth_y'];mw=14 if female else 21
    if not female:
        ellipsoid(g,pix(0,my,-frontdepth(0,my)+3.3),(21*scale,2.0*scale,5.8*scale),6,n=40,k=20)
        pts=[]
        for i in range(13):
            x=-19+38*i/12;y=my-3.1-1.6*(x/19)**2;pts.append(pix(x,y,-frontdepth(x,y)-.1))
        tube(g,pts,[.5*scale]+[1.35*scale]*11+[.5*scale],[.8*scale]*13,7,n=8,steps=32)
    for upper in (True,False):
        pts=[]
        for i in range(11):
            x=-mw+2*mw*i/10;y=my+(0 if female else (4.0 if not upper else -4.8))-((4 if female else 6.3)*(x/mw)**2)
            pts.append(pix(x,y,-frontdepth(x,y)-.9))
        ws=[(.35+(.6 if female else 1.3)*math.sin(math.pi*i/10))*scale for i in range(11)]
        tube(g,pts,ws,[w*.7 for w in ws],8 if not upper else 6,n=8,steps=32)
    body=g.make()
    uv(body)
    atlas=bpy.data.images.load(str(D/'unity_import/Textures'/('Head_'+sex.title()+'_Albedo.png')))
    atlas.colorspace_settings.name='sRGB'
    node=mats[1].node_tree.nodes.new('ShaderNodeTexImage');node.image=atlas;node.extension='EXTEND';mats[1].node_tree.links.new(node.outputs['Color'],mats[1].node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    for poly in body.data.polygons:
        if poly.material_index!=1:continue
        for ix in poly.loop_indices:
            v=body.data.vertices[body.data.loops[ix].vertex_index].co;y=sole-v.z/scale
            body.data.uv_layers.active.data[ix].uv=((math.atan2(v.x,-v.y)/TAU+.5),(205-y)/155) if y<205 else (.02,.02)
    # Hair cap and opaque sculpted clumps, independent of Body.
    hm=material('Hair_'+suffix,(.085,.078,.069),.60);h=Geo('Hair_'+suffix,[hm])
    if not female:
        N=56;K=16;rings=[]
        for j in range(K+1):
            u=j/K;ring=[]
            for i in range(N):
                th=TAU*i/N;front=max(0,math.cos(th));back=max(0,-math.cos(th));yedge=104-39*front+45*back
                y=30+(yedge-30)*u
                width,depth=interp([(30,10,12),(38,36,30),(50,48,40),(66,53,46),(84,53,47),(102,49,46),(122,45,44),(138,39,36),(149,31,31)],y)
                x=width*math.sin(th);dep=-depth*math.cos(th)+1
                ring.append(h.vert(pix(x,y,dep)))
            rings.append(ring)
        for a,b in zip(rings,rings[1:]):h.bridge(a,b)
        h.cap(rings[0])
        inner=[];center=pix(0,128 if female else 91,3)
        for ring in rings:
            inner.append([h.vert(Vector(h.v[ix])+(center-Vector(h.v[ix])).normalized()*2*scale) for ix in ring])
        for a,b in zip(inner,inner[1:]):h.bridge(list(reversed(a)),list(reversed(b)))
        h.cap(list(reversed(inner[0])));h.bridge(rings[-1],inner[-1])
        # Broad swept quiff leaves follow distinct plate strokes.
        locks=[([(-51,66,-27),(-49,46,-37),(-22,31,-39),(9,43,-43)],[7,10,10,.3]),([(-46,55,-31),(-45,36,-33),(-17,28,-30),(17,48,-42)],[6,9,8,.4]),([(-33,44,-34),(-41,27,-18),(-12,29,-22),(24,55,-42)],[7,9,10,.5]),([(-17,40,-32),(-31,24,-10),(-10,25,-15),(28,51,-38)],[8,10,8,.6]),([(0,41,-28),(-10,22,2),(10,27,-8),(33,59,-35)],[8,7,7,.4]),([(18,48,-25),(15,26,10),(31,32,0),(36,62,-34)],[7,8,7,.4]),([(32,56,-22),(30,32,18),(42,45,1),(40,67,-27)],[7,6,6,.4]),([(43,65,-17),(47,49,14),(49,62,4),(49,81,-13)],[6,6,6,.4]),([(-54,80,-12),(-53,60,4),(-38,50,-19),(-8,63,-42)],[4,5,6,.4]),([(-50,98,-9),(-55,76,7),(-43,68,-14),(-24,72,-37)],[4,5,5,.5])]
        for pts,ws in locks:tube(h,[pix(*p) for p in pts],[w*scale for w in ws],[max(.4,w*.43)*scale for w in ws],0,n=12,steps=24)
        # Four layered rows of tapered opaque clumps follow measured back head mass.
        profile_h=[(30,10,12),(38,36,30),(50,48,40),(66,53,46),(84,53,47),(102,49,46),(122,45,44),(138,39,36),(149,31,31)]
        for row in range(4):
            for i in range(12):
                th=math.pi/2+math.pi*i/11;back=max(0,-math.cos(th));yend=min([69,99,129,151][row],104+45*back)
                ystart=[31,57,87,117][row]
                if yend<ystart+8:continue
                pts=[]
                for t in (0,.33,.72,1):
                    y=ystart+(yend-ystart)*t;w,d=interp(profile_h,y);ang=th+.07*(t-.5);pts.append(pix((w+1.5)*math.sin(ang),y,-(d+1.5)*math.cos(ang)+1))
                tube(h,pts,[.4*scale,5.7*scale,4.8*scale,.3*scale],[.3*scale,2.2*scale,1.7*scale,.3*scale],0,n=10,steps=18)
    else:
        N=64;K=20;rings=[]
        for j in range(K+1):
            u=j/K;ring=[]
            for i in range(N):
                th=TAU*i/N;front=max(0,math.cos(th));yedge=187
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
                ring.append(h.vert(pix(x,y,dep)))
            rings.append(ring)
        for a,b in zip(rings,rings[1:]):h.bridge(a,b)
        h.cap(rings[0])
        inner=[];center=pix(0,128 if female else 91,3)
        for ring in rings:
            inner.append([h.vert(Vector(h.v[ix])+(center-Vector(h.v[ix])).normalized()*2*scale) for ix in ring])
        for a,b in zip(inner,inner[1:]):h.bridge(list(reversed(a)),list(reversed(b)))
        h.cap(list(reversed(inner[0])));h.bridge(rings[-1],inner[-1])
        for i in range(8):
            off=i*3.8;pts=[pix(15-off*.32,84+off*.12,-17),pix(-5-off*.48,98+off*.1,-40),pix(-32-off*.37,116+off*.55,-39),pix(-48+off*.05,153+off*.5,-18),pix(-41+off*.12,178+off*.18,-8)]
            tube(h,pts,[.5*scale,6*scale,6*scale,5*scale,.4*scale],[.5*scale,2.9*scale,3*scale,2.4*scale,.4*scale],0,n=12,steps=26)
        for i in range(6):
            off=i*4;pts=[pix(17+off*.2,86+off*.13,-10),pix(35+off*.30,112,-28),pix(48+off*.17,145,-22),pix(45+off*.17,173,-10),pix(36+off*.36,184,-2)]
            tube(h,pts,[.3*scale,5.5*scale,5.7*scale,4.7*scale,.35*scale],[.3*scale,2.6*scale,2.7*scale,2.5*scale,.3*scale],0,n=12,steps=24)
        for i in range(17):
            th=math.pi/2+math.pi*i/16;pts=[]
            for y in (82,105,136,163,185+(i%3-1)*2):
                w,d=interp(profile_h,y);pts.append(pix((w+1.6)*math.sin(th),y,-(d+1.6)*math.cos(th)+3))
            tube(h,pts,[.3*scale,5.7*scale,6.3*scale,5.7*scale,.3*scale],[.3*scale,2.6*scale,2.8*scale,2.6*scale,.3*scale],0,n=12,steps=26)
    if not female:
        ymin=min(sole-v[2]/scale for v in h.v)
        h.v=[(x,d,(sole-(22+(y-ymin)*(100-22)/(100-ymin) if (y:=sole-z/scale)<100 else y))*scale) for x,d,z in h.v]
    hair=h.make();uv(hair)
    # Geometry is modeled in world metres, transforms already identity and origins at feet.
    scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    # Reference images are non-rendering locked empties in the source.
    for view,x in [('front',-1),('back',1)]:
        empty=bpy.data.objects.new('LOCKED_PLATE_'+view,None);bpy.context.collection.objects.link(empty);empty.empty_display_type='IMAGE';empty.data=bpy.data.images.load(str(D/(sex+'_body_plain.jpg')));empty.empty_display_size=1280*scale;empty.location=(0,.55,.9);empty.rotation_euler=(math.pi/2,0,0);empty.hide_render=True;empty.hide_viewport=True;empty.hide_select=True;empty['authority_sha256']=hashlib.sha256((D/(sex+'_body_plain.jpg')).read_bytes()).hexdigest()
    report={'sex':sex,'scale_m_per_pixel':scale,'source_sha256':hashlib.sha256((D/(sex+'_body_plain.jpg')).read_bytes()).hexdigest(),'parts':[]}
    for o in [body,hair]:
        o.data.calc_loop_triangles();zs=[v.co.z for v in o.data.vertices]
        report['parts'].append({'name':o.name,'vertices':len(o.data.vertices),'tris':len(o.data.loop_triangles),'scale':list(o.scale),'origin':list(o.location),'z_min':min(zs),'z_max':max(zs),'material_names':[m.name for m in o.data.materials]})
    report['height_m']=max(v.co.z for o in (body,hair) for v in o.data.vertices)-min(v.co.z for o in (body,hair) for v in o.data.vertices)
    report['tris']=sum(p['tris'] for p in report['parts']);(P/(sex+'-blender-audit.json')).write_text(json.dumps(report,indent=2))
    bpy.ops.object.select_all(action='DESELECT');body.select_set(True);hair.select_set(True);bpy.context.view_layer.objects.active=body
    bpy.ops.export_scene.fbx(filepath=str(D/'unity_import'/('HeroBase_'+sex.title()+'.fbx')),use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False)
    # Neutral studio. Consistent lighting/color settings saved in Blender source.
    scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
    scene.world.color=(.23,.23,.23);scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.23,.23,.23,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.50
    def area(name,loc,energy,size):
        data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
    area('Neutral_Key',(-2.8,-3.4,4),260,4);area('Neutral_Fill',(2.6,-1.8,2),120,3);area('Neutral_Back',(0,2.6,3),180,3)
    data=bpy.data.cameras.new('ProofCamera');cam=bpy.data.objects.new('ProofCamera',data);bpy.context.collection.objects.link(cam);scene.camera=cam;data.type='ORTHO';scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;data.ortho_scale=1280*scale
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
    data.lens=85
    for name,ang in [('front',0),('back',math.pi),('threequarter',math.pi/5)]:
        cam.location=(math.sin(ang)*5,-math.cos(ang)*5,(sole-360)*scale);cam.rotation_euler=(Vector((0,0,cam.location.z))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(P/'blender'/(suffix+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
    cam.location=(0,-5,(sole-360)*scale);cam.rotation_euler=(math.pi/2,0,0)
    bpy.ops.wm.save_as_mainfile(filepath=str(D/'blender'/('HeroBase_'+sex.title()+'.blend')))
    return report

reports=[]
for sex,suffix,profile in [('male','M',MALE),('female','F',FEMALE)]:
    if len(sys.argv)>sys.argv.index('--')+1 if '--' in sys.argv else False:
        requested=sys.argv[sys.argv.index('--')+1]
        if requested not in ('all',sex):continue
    reports.append(build(sex,suffix,profile))
print('BASE_BUILT',json.dumps(reports))
