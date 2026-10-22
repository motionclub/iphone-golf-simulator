import sys, math
import numpy as np
YD=0.9144
def cam_tee(bz_ground=6.24, ball=(0,0), aim=(19,178)):
    bx,by=ball[0]*YD,ball[1]*YD; ax,ay=aim[0]*YD,aim[1]*YD
    d=np.array([ax-bx,ay-by,0.]); d/=np.linalg.norm(d)
    b=np.array([bx,by,bz_ground+0.055])
    cam=b-d*4.5*YD+np.array([0,0,2.4*YD]); look=b+d*1.5*YD
    return cam,look,b
def project(P,cam,look,W=900,H=1600,fov=60):
    f=(look-cam); f/=np.linalg.norm(f); r=np.cross(f,[0,0,1.]); r/=np.linalg.norm(r); u=np.cross(r,f)
    v=P-cam; z=v@f; x=v@r; y=v@u
    th=math.tan(math.radians(fov/2))
    px=(x/z/(th*W/H)+1)/2*W; py=(1-y/z/th)/2*H
    return px,py
cam,look,b=cam_tee()
print("cam",cam,"ball",b)
for name,P in [("ball",b),("tee edge x0 y3.52 z6.24",np.array([0,3.52,6.24])),("tee edge x-2.81 y3.82",np.array([-2.81,3.82,6.24])),("tee edge x2.54 y3.21",np.array([2.54,3.21,6.24]))]:
    print(name, [round(v,1) for v in project(P,cam,look)])
