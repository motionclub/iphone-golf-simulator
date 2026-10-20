"""Coordinate descent on hand parameters against the hand-ROI silhouette XOR (8 ROIs: bald front/back, sheet front/back, L+R)."""
import sys, json, time
import numpy as np
import run, handobj
base=dict(thumb_morph=3.0,thumb_anchor=1,thumb_first=0.008,pol_thumb=[0.040,25])
# parameter spec: name -> (index or None, step, lo, hi)
SPEC=[('r_a',None,0.0006,0.0112,0.0140),('r_n',None,0.0008,0.0155,0.0195),('gap',None,0.0006,0.0008,0.0040),
      ('f_tip',0,0.004,0.136,0.172),('f_tip',1,0.004,0.146,0.182),('f_tip',2,0.004,0.138,0.174),('f_tip',3,0.004,0.118,0.150),
      ('taper',None,0.02,0.02,0.16),('splay_deg',0,1.5,-2.0,9.0),('splay_deg',3,1.5,-9.0,2.0),
      ('thumb_r',0,0.0012,0.0150,0.0240),('thumb_r',1,0.0012,0.0140,0.0230),('thumb_r',2,0.0010,0.0120,0.0200),('thumb_r',3,0.0010,0.0100,0.0170),
      ('tp1_a',None,0.003,0.040,0.070),('tp1_n',None,0.003,-0.002,0.040),('tp1_w',None,0.004,0.040,0.080),
      ('tp2_a',None,0.003,0.040,0.075),('tp2_n',None,0.004,0.005,0.050),('tp2_w',None,0.005,0.060,0.100),
      ('tp3_a',None,0.003,0.040,0.075),('tp3_n',None,0.004,0.010,0.060),('tp3_w',None,0.005,0.080,0.125)]
def params_from(cur):
    p={}
    for k,v in cur.items(): p[k]=v
    tp=[list(x) for x in run.BASEP['thumb_pts']]
    for i in (1,2,3):
        for j,a in enumerate('anw'):
            key=f'tp{i}_{a}'
            if key in cur: tp[i][j]=cur[key]
    p['thumb_pts']=tp
    out={k:v for k,v in p.items() if not k.startswith('tp')}
    return out
def init_state():
    st={}
    for name,idx,step,lo,hi in SPEC:
        if name.startswith('tp'):
            i=int(name[2]); j='anw'.index(name[4]); st[name]=run.BASEP['thumb_pts'][i][j]
        elif idx is None: st[name]=run.BASEP[name]
        else:
            st.setdefault(name,list(run.BASEP[name]))
    return st
def build_params(st):
    over=dict(base)
    for name,idx,step,lo,hi in SPEC:
        if name.startswith('tp'): continue
        over[name]=st[name] if idx is None else list(st[name])
    tp=[list(x) for x in run.BASEP['thumb_pts']]
    for i in (1,2,3):
        for j,a in enumerate('anw'): tp[i][j]=st[f'tp{i}_{a}']
    over['thumb_pts']=tp
    return over
def turn_penalty(over):
    import hand_sdf  # noqa
    sys.path.insert(0,str(run.W.parent/'male-micro1e'))
    pts=np.array(over['thumb_pts'],float)
    seg=np.diff(pts,axis=0); seg/=np.linalg.norm(seg,axis=1,keepdims=True)
    pen=0.0
    for i in range(len(seg)-1):
        ang=np.degrees(np.arccos(np.clip(seg[i]@seg[i+1],-1,1)))
        if ang>55: return None
        pen+=6.0*max(0.0,ang-32.0)
    # thumb must keep going down the hand: tip w above mid w by >= 1.5 cm
    if pts[3,2]-pts[2,2]<0.015: return None
    return pen
def objective(st):
    over=build_params(st)
    pen=turn_penalty(over)
    if pen is None: return 1e9
    mf=run.build(over); V=run.patch(mf)
    tot,res=handobj.xor_report(V,run.T0,run.SEL,False)
    return tot+pen
if __name__=='__main__':
    st=init_state(); t0=time.time()
    best=objective(st); print('start',best,flush=True)
    rounds=int(sys.argv[1]) if len(sys.argv)>1 else 2
    for rd in range(rounds):
        for name,idx,step,lo,hi in SPEC:
            cur=st[name] if idx is None else st[name][idx]
            for sgn in (+1,-1):
                trial=min(hi,max(lo,cur+sgn*step))
                if abs(trial-cur)<1e-12: continue
                st2=json.loads(json.dumps(st))
                if idx is None: st2[name]=trial
                else: st2[name][idx]=trial
                try: v=objective(st2)
                except Exception as e: print('fail',name,idx,trial,e); continue
                if v<best:
                    best=v; st=st2; cur=trial; print(f'rd{rd} {name}[{idx}] -> {trial:.5f}  xor={best}  t={time.time()-t0:.0f}s',flush=True)
                    break
        json.dump(st,open(f'data/opt_state_rd{rd}.json','w'),indent=1)
        print('round',rd,'best',best,flush=True)
    json.dump(build_params(st),open('data/opt_best_params.json','w'),indent=1)
