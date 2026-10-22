import numpy as np, zlib, struct, sys, math
YD=0.9144
def png(path, arr):
    h,w,_=arr.shape
    raw=b''.join(b'\x00'+arr[y].tobytes() for y in range(h))
    def ch(t,d): 
        c=struct.pack('>I',len(d))+t+d
        return c+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+ch(b'IDAT',zlib.compress(raw,6))+ch(b'IEND',b''))
d=np.load(sys.argv[1], allow_pickle=True)
S=float(sys.argv[3]) if len(sys.argv)>3 else 2.0   # px per metre
x0,x1,y0,y1=-40,60,-20,340   # metres Blender (x right, y down the hole)
W=int((x1-x0)*S); H=int((y1-y0)*S)
img=np.full((H,W,3),(40,60,120),np.uint8)
col={'TERRAIN_NEEDLE':(90,110,40),'FAIRWAY':(120,200,60),'FAIRWAY_FIRSTCUT':(90,160,50),'GREEN':(80,255,120),'GREEN_APRON':(150,210,90),'TEE_BOX':(230,230,120),'BUNKER_01':(240,220,150),'BUNKER_01_LIP':(70,120,40),'DRESS_PATH_01':(200,200,200),'DRESS_PATH_02':(200,200,200)}
order=['TERRAIN_NEEDLE','FAIRWAY_FIRSTCUT','GREEN_APRON','FAIRWAY','TEE_BOX','GREEN','BUNKER_01_LIP','BUNKER_01','DRESS_PATH_01','DRESS_PATH_02']
def fill(tri, c):
    xs=(tri[:,0]-x0)*S; ys=(tri[:,1]-y0)*S
    mnx,mxx=int(max(0,math.floor(xs.min()))),int(min(W-1,math.ceil(xs.max())))
    mny,mxy=int(max(0,math.floor(ys.min()))),int(min(H-1,math.ceil(ys.max())))
    if mxx<mnx or mxy<mny: return
    X,Y=np.meshgrid(np.arange(mnx,mxx+1)+0.5,np.arange(mny,mxy+1)+0.5)
    ax,ay,bx,by,cx,cy=xs[0],ys[0],xs[1],ys[1],xs[2],ys[2]
    den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
    if abs(den)<1e-9: return
    l1=((by-cy)*(X-cx)+(cx-bx)*(Y-cy))/den; l2=((cy-ay)*(X-cx)+(ax-cx)*(Y-cy))/den; l3=1-l1-l2
    m=(l1>=0)&(l2>=0)&(l3>=0)
    img[mny:mxy+1,mnx:mxx+1][m]=c
for nm in order:
    if nm+'|V' not in d: continue
    V=d[nm+'|V']; T=d[nm+'|T']; M=d[nm+'|M']
    for t,mm in zip(T,M):
        c=col[nm]
        if nm=='FAIRWAY_FIRSTCUT' and 'ROUGH' in str(mm): c=(60,110,30)
        fill(V[t][:,:2],c)
# camera frusta
def cam(ball,aim,col_=(255,0,0)):
    b=np.array(ball)*YD; a=np.array(aim)*YD
    dv=(a-b)/np.linalg.norm(a-b)
    c=b-dv*4.5*YD
    for ang in (-18.4,0,18.4):
        r=math.radians(ang); dd=np.array([dv[0]*math.cos(r)-dv[1]*math.sin(r), dv[0]*math.sin(r)+dv[1]*math.cos(r)])
        for t in np.linspace(0,120,600):
            p=c+dd*t; px=int((p[0]-x0)*S); py=int((p[1]-y0)*S)
            if 0<=px<W and 0<=py<H: img[py,px]=col_
cam((0,0),(19,178)); cam((19,178),(-6,340),(255,160,0))
png(sys.argv[2],img)
print("ok",W,H)
