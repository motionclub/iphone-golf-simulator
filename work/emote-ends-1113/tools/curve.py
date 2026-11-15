import json, sys, numpy as np
S=sys.argv[1]
for name in ["MatchHero_Male","MatchHero_Female"]:
    m=json.load(open(name+".json")); r=m["rig"]; tc=r["trackCount"]; bones=r["bones"]
    blob=np.memmap(f"{S}/{name}_Rig.bin",dtype=np.float32,mode="r"); idx={b:i for i,b in enumerate(bones)}
    H=[idx[b] for b in ["LeftHand","RightHand","LeftLowerArm","RightLowerArm"]]
    clips={c["id"]:c for c in r["clips"]}
    print("==",name)
    for e in ["jumpJoy","fistPump","stomp","slump","shock","victory","defeat","wave","bringIt","pushups","scuba","thrust","spike"]:
        c=clips[e]; n=c["frames"]; a=np.asarray(blob[c["offset"]//4:c["offset"]//4+n*tc*10]).reshape(n,tc,10)
        times=np.array(c.get("times") or np.linspace(0,c["length"],n))
        d=np.max(np.linalg.norm(a[:,H,0:3]-a[0][H,0:3],axis=2),axis=1)*100
        ts=np.arange(0,c["length"]+1e-6,.1); dd=[d[np.argmin(abs(times-t))] for t in ts]
        print(f"{e:9s}", " ".join(f"{x:3.0f}" for x in dd))
