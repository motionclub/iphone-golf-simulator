import json, sys
import make2
from make2 import render, measure, face
if __name__=="__main__" and len(sys.argv)>2: make2.T.update(json.loads(sys.argv[2]))
CAM=dict(cam=[0,0.98,5.3],look=[0,1.03,0],fov=32)
def squad(kit, cols):
    pos=[(0,0,0,"relaxed",3.0),(-1.2,-0.75,-12,"relaxed",5.2),(1.2,-0.75,12,"wave",0.9),(-2.4,-1.75,-18,"relaxed",7.5)]
    if kit=="golf": pos=[(p[0],p[1],p[2],{"relaxed":"idle","wave":"wave"}[p[3]],min(p[4],1.6)) for p in pos]
    H=[]
    for (x,z,yaw,clip,t),(fem,c) in zip(pos,cols):
        h=dict(female=fem,kit=kit,clip=clip,t=t,x=x,z=z,yaw=yaw,racketBack=(kit=="tennis")); h.update(c)
        if kit=="golf" and "skin" not in h: h["skin"]="BB9372"   # golf export default skin is far paler than tennis/bowling
        H.append(h)
    return dict(CAM,heroes=H)
COLS=[(False,{}),(True,dict(skin="E6AE7E",shirt="2F6FD6",shorts="F4F0E6")),(False,dict(skin="74432C",shirt="7BC043",shorts="23344D",shoes="FFFFFF")),(True,dict(skin="3E2317",shirt="F5C542",shorts="FFFFFF"))]
def main():
    JOBS={"v2_tennis":("tennis-resort","tennis"),"v2_golf":("golf-cliffside","golf"),"v2_bowling":("bowling-neon","bowling")}
    only=sys.argv[1].split(",") if len(sys.argv)>1 else list(JOBS)
    res={}
    for n in only:
        venue,kit=JOBS[n]; img,heroes,pts=render(n,venue,squad(kit,COLS))
        img.save(f"../img/{n}.jpg",quality=86)
        res[n]=dict(pts=pts,leader=measure(heroes,(860,390,1060,930)),darkest=measure(heroes,(240,420,400,830)),face=face(img,(930,405,980,450)))
        print(n,res[n])
    json.dump(res,open("../renders/v2_points.json","w"))
if __name__=="__main__": main()
