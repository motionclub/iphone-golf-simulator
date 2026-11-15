import json, sys, numpy as np
S=sys.argv[1]; out={}
for sex,name in [("Male","MatchHero_Male"),("Female","MatchHero_Female")]:
    m=json.load(open(name+".json")); r=m["rig"]; tc=r["trackCount"]; bones=r["bones"]
    blob=np.memmap(f"{S}/{name}_Rig.bin",dtype=np.float32,mode="r"); idx={b:i for i,b in enumerate(bones)}
    H=[idx[b] for b in ["LeftHand","RightHand","LeftLowerArm","RightLowerArm"]]
    clips={c["id"]:c for c in r["clips"]}
    for e in ["jumpJoy","fistPump","stomp","slump","shock","victory","defeat","wave","bringIt","pushups","scuba","thrust","spike"]:
        c=clips[e]; n=c["frames"]; a=np.asarray(blob[c["offset"]//4:c["offset"]//4+n*tc*10]).reshape(n,tc,10)
        t=np.array(c.get("times") or np.linspace(0,c["length"],n)); o=np.argsort(t); t=t[o]; a=a[o]
        d=np.max(np.linalg.norm(a[:,H,0:3]-a[0][H,0:3],axis=2),axis=1)*100
        t0=t[np.argmax(d>=15)]
        last=t[np.where(d>=6)[0][-1]]
        win=(t>=last-1.0)&(t<=last); Pl=d[win].max()
        thr=20; tb=t[np.where(d>=thr)[0][-1]]
        out.setdefault(e,{})[sex]=(round(float(t0),3),round(float(tb),3),round(float(c["length"]),3))
for e,v in out.items(): print(e, v)
json.dump(out,open(f"{S}/table.json","w"))
