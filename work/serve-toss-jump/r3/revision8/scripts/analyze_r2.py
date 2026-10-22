"""Measured diagnostic gates for the unchanged prompt-26 candidate. No installation."""
from pathlib import Path
import csv, hashlib, json, math
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
W = ROOT / 'work/serve-toss-jump'

def vec(row, name):
    return np.array([float(row[name+'_'+c]) for c in 'xyz'])

def quaternion(row):
    return np.array([float(row['q'+c]) for c in 'xyzw'])

def qmul(a,b):
    av,bv=a[:3],b[:3]
    return np.r_[a[3]*bv+b[3]*av+np.cross(av,bv),a[3]*b[3]-np.dot(av,bv)]

def qinv(a):
    return np.r_[-a[:3],a[3]]/np.dot(a,a)

def qangle(a,b):
    return math.degrees(2*math.acos(min(1,abs(float(np.dot(a,b)/np.linalg.norm(a)/np.linalg.norm(b))))))

def rotate(q,v):
    return qmul(qmul(q,np.r_[v,0]),qinv(q))[:3]

def foot(row, side, stage='live'):
    return min(float(row[f'{stage}_{side}heel_mm']),float(row[f'{stage}_{side}toe_mm']))

def interp(rows, field, t):
    rows=sorted(rows,key=lambda r:float(r['clipTime']))
    before=max((r for r in rows if float(r['clipTime'])<=t),key=lambda r:float(r['clipTime']))
    after=min((r for r in rows if float(r['clipTime'])>=t),key=lambda r:float(r['clipTime']))
    t0,t1=float(before['clipTime']),float(after['clipTime'])
    a=0 if t1==t0 else (t-t0)/(t1-t0)
    return float(before[field])*(1-a)+float(after[field])*a,[t0,t1]

result={}
for sex in ['male','female']:
    d=W/'r2'/sex
    rows=list(csv.DictReader((d/'trace.csv').open()))
    numeric=[k for k in rows[0] if k not in ['flow','state']]
    assert all(None not in r and len(r)==len(rows[0]) for r in rows)
    assert all(math.isfinite(float(r[k])) for r in rows for k in numeric)
    assert [int(r['frame']) for r in rows]==list(range(len(rows)))
    assert max(abs(float(rows[i]['time'])-float(rows[i-1]['time'])-1/60) for i in range(1,len(rows)))<2e-6
    serve=[r for r in rows if r['state'].startswith('Serve')]
    toss=[r for r in serve if .20<=float(r['clipTime'])<=1.55]
    predrive=[r for r in serve if float(r['clipTime'])<=1.55]
    peak=max(toss,key=lambda r:max(float(r['live_'+f+'_mm']) for f in ['Lheel','Ltoe','Rheel','Rtoe']))
    side=max('LR',key=lambda s:float(peak['live_'+s+'heel_mm']))
    diag={k:peak[k] for k in ['frame','time','clipTime','state','baseReady','baseWalk','baseServe','baseRun','upperWeight','actionLegs','legsFromRun','groundLift','sinkBeforeGround','heroRoot_y']}
    for s in 'LR':
        for k in ['stepping','stepT','locked','lockW']: diag[s+k]=peak[s+k]
        for stage in ['live','layers','base','pureServe']:
            for part in ['heel','toe']: diag[f'{stage}_{s}{part}_mm']=float(peak[f'{stage}_{s}{part}_mm'])
    diag['side']=side
    diag['procedural_heel_delta_mm']=float(peak['live_'+side+'heel_mm'])-float(peak['layers_'+side+'heel_mm'])
    diag['step_formula_mm']=65*math.sin(math.pi*min(1,max(0,float(peak[side+'stepT']))))
    diag['step_formula_residual_mm']=abs(diag['procedural_heel_delta_mm']-diag['step_formula_mm'])
    step_examples=[]
    for r in predrive:
        for s in 'LR':
            if r[s+'stepping']=='1' and 0<float(r[s+'stepT'])<1:
                delta=float(r['live_'+s+'heel_mm'])-float(r['layers_'+s+'heel_mm'])
                prediction=65*math.sin(math.pi*float(r[s+'stepT']))
                step_examples.append(dict(frame=int(r['frame']),clipTime=float(r['clipTime']),side=s,delta_mm=delta,predicted_mm=prediction,residual_mm=abs(delta-prediction),baseServe=float(r['baseServe']),upperWeight=float(r['upperWeight'])))
    exact=[x for x in step_examples if x['baseServe']>=.9999 and x['upperWeight']<=.0001]
    assert exact and min(x['residual_mm'] for x in exact)<.01
    knee=max((r for r in serve if float(r['clipTime'])<1.57),key=lambda r:max(float(r['live_Lknee_deg']),float(r['live_Rknee_deg'])))
    lowest=min((r for r in serve if float(r['clipTime'])<1.57),key=lambda r:float(r['live_pelvis_y']))
    first_left=next(r for r in serve if foot(r,'L')>3)
    first_right=next(r for r in serve if foot(r,'R')>3)
    first_both=next(r for r in serve if foot(r,'L')>3 and foot(r,'R')>3)
    first_window={s:float(next(r for r in serve if float(r['clipTime'])>=.20 and foot(r,s)>3)['clipTime']) for s in 'LR'}
    drive_both=next(r for r in serve if float(r['clipTime'])>=1.55 and foot(r,'L')>3 and foot(r,'R')>3)
    contact={}
    for k in ['Lheel_mm','Ltoe_mm','Rheel_mm','Rtoe_mm','Lknee_deg','Rknee_deg','Relbow_deg','pelvis_y']:
        contact[k],contact['bracket']=interp(serve,'live_'+k,1.70)
    apex=max((r for r in serve if 1.70<=float(r['clipTime'])<=1.95),key=lambda r:float(r['live_pelvis_y']))
    contact_frame=next(int(r['frame']) for r in serve if float(r['clipTime'])>=1.70)
    touchdown={}
    for s in 'LR':
        r=next((r for r in rows if int(r['frame'])>contact_frame and foot(r,s)<=3),None)
        touchdown[s]=None if r is None else {k:r[k] for k in ['frame','time','clipTime','state','picture']}
    steps=[]
    for a,b in zip(rows,rows[1:]):
        if not (a['state'].startswith('Serve') or b['state'].startswith('Serve')): continue
        for s in 'LR':
            steps.append(dict(frame=int(b['frame']),side=s,clipTime=float(b['clipTime']),mm=float(np.linalg.norm(vec(b,'live_'+s+'hand')-vec(a,'live_'+s+'hand'))*1000),before=float(a['ttc'])>0 and a['swinging']=='1' or not a['swinging']=='1' and float(a['clipTime'])<1.70))
    before=max((x for x in steps if x['before']),key=lambda x:x['mm'])
    strictly_before=max((x for x in steps if x['before'] and x['clipTime']<=1.70),key=lambda x:x['mm'])
    after=max((x for x in steps if not x['before']),key=lambda x:x['mm'])
    bone_rows=list(csv.DictReader((d/'bones.csv').open()))
    byframe={}
    for r in bone_rows: byframe.setdefault(int(r['frame']),{}).setdefault(r['stage'],{})[r['bone']]=r
    wrist=[]; ready_delta=[]; wrist_twist=[]
    for r in serve:
        f=int(r['frame']); table=byframe[f]
        if .15<=float(r['clipTime'])<=.20:
            for name,bone in table['pureServe'].items():
                z=table['ready'][name]
                mm=float(np.linalg.norm(np.array([float(bone[c])-float(z[c]) for c in 'xyz']))*1000)
                ready_delta.append(dict(frame=f,clipTime=float(r['clipTime']),bone=name,mm=mm))
        if f==0 or not rows[f-1]['state'].startswith('Serve'): continue
        for s,word in [('L','Left'),('R','Right')]:
            hand=word+'Hand'; forearm=word+'LowerArm'
            now=qmul(qinv(quaternion(table['live'][forearm])),quaternion(table['live'][hand]))
            prior=byframe[f-1]['live']
            prev=qmul(qinv(quaternion(prior[forearm])),quaternion(prior[hand]))
            wrist.append(dict(frame=f,side=s,clipTime=float(r['clipTime']),degrees=qangle(now,prev)))
            delta=qmul(now,qinv(prev))
            positions=lambda b:np.array([float(b[c]) for c in 'xyz'])
            axis=rotate(qinv(quaternion(table['live'][forearm])),positions(table['live'][hand])-positions(table['live'][forearm]))
            axis/=np.linalg.norm(axis)
            twist=math.degrees(2*math.atan2(float(np.dot(delta[:3],axis)),float(delta[3])))
            twist=(twist+180)%360-180
            wrist_twist.append(dict(frame=f,side=s,clipTime=float(r['clipTime']),degrees=abs(twist)))
    planted=[]
    for s in 'LR':
        anchor=None
        for r in serve:
            if foot(r,s)<=3 and r[s+'stepping']=='0':
                p=vec(r,'live_'+s+'toe')[[0,2]]
                if anchor is None: anchor=p
                planted.append(dict(frame=int(r['frame']),side=s,clipTime=float(r['clipTime']),actor_relative_drift_mm=float(np.linalg.norm(p-anchor)*1000)))
            else: anchor=None
    fields={k:len(rows) for k in ['palm','heel','toe','knee','pelvis','wrist_rotation','planted_foot_position']}
    film_count={view:len(list(d.glob(view+'_*.png'))) for view in ['game','front','side','back']}
    entry=int(serve[0]['frame']);entry_steps=[]
    for f in range(entry,min(entry+10,len(rows))):
        for name in ['head','Lhand','Rhand']:
            p=vec(rows[f],'live_'+name)+vec(rows[f],'actorRoot')
            prior=vec(rows[f-1],'live_'+name)+vec(rows[f-1],'actorRoot')
            entry_steps.append(dict(frame=f,bone=name,mm=float(np.linalg.norm(p-prior)*1000)))
    step_start=[]
    for f,r in enumerate(rows):
        for s in 'LR':
            if float(r['clipTime'])>1.3 and r[s+'stepping']=='1' and rows[f-1][s+'stepping']=='0':
                p=vec(r,'layers_'+s+'heel')+vec(r,'actorRoot');lock=vec(r,s+'lockPos')
                step_start.append(dict(frame=f,clipTime=float(r['clipTime']),side=s,drift_mm=float(np.linalg.norm((p-lock)[[0,2]])*1000)))
    result[sex]=dict(rows=len(rows),fields=fields,bone_rows=len(bone_rows),skeleton_bones=len(byframe[0]['live']),film_frame_counts=film_count,trace_end_time=float(rows[-1]['time']),serve_clip_end=float(serve[-1]['clipTime']),
        G1_max_heights_mm={f:max(float(r['live_'+f+'_mm']) for r in toss) for f in ['Lheel','Ltoe','Rheel','Rtoe']},diagnosis=diag,step_examples=exact,
        G2_knee_peak_deg=max(float(knee['live_Lknee_deg']),float(knee['live_Rknee_deg'])),G2_peak_clipTime=float(knee['clipTime']),G2_pelvis_lowest_clipTime=float(lowest['clipTime']),
        G3_first_clearance_clipTime={'L':float(first_left['clipTime']),'R':float(first_right['clipTime']),'both':float(first_both['clipTime']),'drive_both':float(drive_both['clipTime'])},G3_first_clearance_after_0p20=first_window,step_start=step_start,
        G4_contact=contact,G5_apex_clipTime=float(apex['clipTime']),G6_touchdown=touchdown,G6_landing_rows_before_1p90=sum(1 for r in serve if 1.70<float(r['clipTime'])<=1.90 and foot(r,'L')<=3),
        G7_live_ready_source_max_delta=max(ready_delta,key=lambda x:x['mm']) if ready_delta else None,G7_first_0p15_entry_hand_head_max_step=max(entry_steps,key=lambda x:x['mm']),G9_hand_step_before=before,G9_hand_step_strictly_before_contact=strictly_before,G9_hand_step_after=after,G9_local_wrist_max_step=max(wrist,key=lambda x:x['degrees']),G9_longitudinal_wrist_twist_max=max(wrist_twist,key=lambda x:x['degrees']),
        G11_actor_relative_planted_drift_max=max(planted,key=lambda x:x['actor_relative_drift_mm']),
        candidate_sha256=hashlib.sha256((W/f'export/fbx/{sex.title()}_Serve.fbx').read_bytes()).hexdigest())

(W/'r2/live_metrics.json').write_text(json.dumps(result,indent=2)+'\n')
for sex,m in result.items():
    print(sex, json.dumps({k:v for k,v in m.items() if k not in ['step_examples','fields','film_frame_counts']},indent=2))
