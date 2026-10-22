import sys; sys.path.insert(0,'.')
from common import *
from PIL import Image, ImageDraw
N = vnormals(V0); X,Y,Z = V0[:,0],V0[:,1],V0[:,2]
sel = (np.abs(X)<0.13)&(Z>0.735)&(Z<0.83)&(N[:,2]<-0.25)
print('floor-facing verts', sel.sum())
# floor height map: print z of floor verts on a coarse (x,y) grid (mean per cell)
xs = np.arange(-0.12,0.1201,0.01); ys = np.arange(-0.16,0.1201,0.02)
print('rows y (mm), cols x (mm): mean z (mm) of down-facing verts')
print('       '+' '.join(f'{x*1000:5.0f}' for x in xs))
for y in ys[::-1]:
    row=[]
    for x in xs:
        m = sel & (np.abs(X-x)<0.005) & (np.abs(Y-y)<0.01)
        row.append(f'{Z[m].mean()*1000:5.0f}' if m.any() else '    .')
    print(f'y{y*1000:5.0f} '+' '.join(row))
# draw
S=3000; im=Image.new('RGB',(int(0.26*S),int(0.30*S)),(20,20,24)); d=ImageDraw.Draw(im)
for i in np.where(sel)[0]:
    px=(X[i]+0.13)*S; py=(0.12-Y[i])*S; t=np.clip((Z[i]-0.74)/0.08,0,1); c=(int(255*t),int(120+100*(1-t)),int(255*(1-t)))
    d.ellipse([px-2,py-2,px+2,py+2],fill=c)
im.save('tmp/floor_scatter.png'); print(im.size)
