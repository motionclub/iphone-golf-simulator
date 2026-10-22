"""Live trace measurements; failures are data, never silently relaxed gates."""
from pathlib import Path
import csv, json, sys, math
import numpy as np

def vec(r, n): return np.array([float(r[n+'_'+c]) for c in 'xyz'])
def foot(r,s,stage='live'): return min(float(r[f'{stage}_{s}heel_mm']),float(r[f'{stage}_{s}toe_mm']))
def qm(a,b): return np.r_[a[3]*b[:3]+b[3]*a[:3]+np.cross(a[:3],b[:3]),a[3]*b[3]-a[:3]@b[:3]]
def qi(a): return np.r_[-a[:3],a[3]]/(a@a)
def quat(r): return np.array([float(r['q'+c]) for c in 'xyzw'])
def point(r): return np.array([float(r[c]) for c in 'xyz'])
def rotate(q,v): return qm(qm(q,np.r_[v,0]),qi(q))[:3]
def measure(d):
    rows=list(csv.DictReader((d/'trace.csv').open()))
    entry=next(i for i,r in enumerate(rows) if r['state'].startswith('Serve'))
    end=next((i for i in range(entry+1,len(rows)) if not rows[i]['state'].startswith('Serve')),len(rows))
    serve=rows[entry:end]
    toss=[r for r in serve if .2<=float(r['clipTime'])<=1.55]
    load=max((r for r in serve if .2<=float(r['clipTime'])<1.57),key=lambda r:max(float(r['live_Lknee_deg']),float(r['live_Rknee_deg'])))
    heights={n:max(float(r[f'live_{n}_mm']) for r in toss) for n in ['Lheel','Ltoe','Rheel','Rtoe']}
    first={s:next((float(r['clipTime']) for r in serve if float(r['clipTime'])>.2 and foot(r,s)>3),None) for s in 'LR'}
    drift={}
    for stage in ['live','pureServe']:
        worst={'mm':0}
        for s in 'LR':
            anchor=None
            for r in serve:
                if foot(r,s,stage)<=3 and r[s+'stepping']=='0':
                    points=[vec(r,('world'+s+n) if stage=='live' else (stage+'_'+s+n))[[0,2]] for n in ['heel','toe']]
                    if anchor is None: anchor=points
                    for part,p,a in zip(['heel','toe'],points,anchor):
                        mm=float(np.linalg.norm(p-a)*1000)
                        if mm>worst['mm']: worst=dict(mm=mm,side=s,part=part,frame=int(r['frame']),clipTime=float(r['clipTime']))
                else: anchor=None
        drift[stage]=worst
    entry_steps=[]
    for i in range(entry,min(entry+10,end)):
        for bone in ['head','Lhand','Rhand']:
            mm=float(np.linalg.norm(vec(rows[i],'live_'+bone)-vec(rows[i-1],'live_'+bone))*1000)
            entry_steps.append(dict(mm=mm,bone=bone,frame=i,clipTime=float(rows[i]['clipTime'])))
    hands={}
    for s in 'LR':
        for name,lo,hi in [('all',-1,10),('before',-1,1.65),('contact',1.65,1.75),('after',1.75,10)]:
            pairs=[dict(mm=float(np.linalg.norm(vec(b,'live_'+s+'hand')-vec(a,'live_'+s+'hand'))*1000),frame=int(b['frame']),clipTime=float(b['clipTime'])) for a,b in zip(serve,serve[1:]) if lo<=float(b['clipTime'])<hi]
            hands[s+'_'+name]=max(pairs,key=lambda x:x['mm']) if pairs else None
    follow_rows=[r for r in serve if float(r['clipTime'])>1.75]
    follow={}
    for mode in ['actorLocal','world']:
        points=np.array([vec(r,'live_Rhand')+(vec(r,'actorRoot') if mode=='world' else 0) for r in follow_rows])
        velocities=np.diff(points,axis=0);turns=[]
        for i,(a,b) in enumerate(zip(velocities,velocities[1:])):
            if min(np.linalg.norm(a),np.linalg.norm(b))<.005: continue
            deg=float(np.degrees(np.arccos(np.clip(a@b/np.linalg.norm(a)/np.linalg.norm(b),-1,1))))
            turns.append(dict(degrees=deg,frame=int(follow_rows[i+2]['frame']),clipTime=float(follow_rows[i+2]['clipTime'])))
        follow[mode]=dict(maxTurn=max(turns,key=lambda x:x['degrees']) if turns else None,reversals=[r for r in turns if r['degrees']>90])
    nsteps=sum(max(0,int(b['stepsTaken'])-int(a['stepsTaken'])) for a,b in zip(rows,rows[1:]) if not b['state'].startswith('Serve'))
    apex=max((r for r in serve if 1.70<=float(r['clipTime'])<=1.95),key=lambda r:float(r['live_pelvis_y']))
    touch=next((r for r in serve if float(r['clipTime'])>1.75 and foot(r,'L')<=3),None)
    settled=next((r for i,r in enumerate(serve[1:],1) if float(r['clipTime'])>1.85 and max(foot(r,s) for s in 'LR')<=3 and max(np.linalg.norm(vec(r,'world'+s+'heel')-vec(serve[i-1],'world'+s+'heel'))*1000 for s in 'LR')<=5 and abs(float(r['live_pelvis_y'])-float(serve[i-1]['live_pelvis_y']))*1000<=10),None)
    ct=list(csv.DictReader((d/'contact.csv').open())) if (d/'contact.csv').exists() else []
    ct=[r for r in ct if int(r['frame'])<end]
    # Interpolate the actual physics poses bracketing the specified clip time 1.70 s.
    contact=None
    if ct:
        before=max((r for r in ct if float(r['clipTime'])<=1.7),key=lambda r:float(r['clipTime']))
        after=min((r for r in ct if float(r['clipTime'])>=1.7),key=lambda r:float(r['clipTime']))
        t0,t1=float(before['ttc']),float(after['ttc']);u=(1.7-float(before['clipTime']))/(float(after['clipTime'])-float(before['clipTime']))
        contact={k:float(before[k])*(1-u)+float(after[k])*u for k in before if k not in ['frame','time','ttc']}
        contact['bracket_ttc']=[t0,t1]
    rendered=min((r for r in serve if float(r['clipTime'])>1.65),key=lambda r:abs(float(r['clipTime'])-1.7))
    rendered_contact=dict(frame=int(rendered['frame']),clipTime=float(rendered['clipTime']),strings=list(vec(rendered,'live_strings')),elbow=float(rendered['live_Relbow_deg']),frontKnee=float(rendered['live_Lknee_deg']),footHeights={s:[float(rendered['live_'+s+n+'_mm']) for n in ['heel','toe']] for s in 'LR'})
    bone_rows=csv.DictReader((d/'bones.csv').open());byframe={}
    for r in bone_rows:
        f=int(r['frame'])
        if entry-1<=f<end and r['stage']=='live':byframe.setdefault(f,{})[r['bone']]=r
    wrists=[]
    for a,b in zip(serve,serve[1:]):
        f0,f1=int(a['frame']),int(b['frame']);prev,now=byframe[f0],byframe[f1]
        for s,word in [('L','Left'),('R','Right')]:
            fore,hand=word+'LowerArm',word+'Hand'
            q0=qm(qi(quat(prev[fore])),quat(prev[hand]));q1=qm(qi(quat(now[fore])),quat(now[hand]));delta=qm(q1,qi(q0))
            axis=rotate(qi(quat(now[fore])),point(now[hand])-point(now[fore]));axis/=np.linalg.norm(axis)
            deg=math.degrees(2*math.atan2(delta[:3]@axis,delta[3]));deg=abs((deg+180)%360-180)
            wrists.append(dict(degrees=deg,side=s,frame=f1,clipTime=float(b['clipTime'])))
    return dict(rows=len(rows),entryFrame=entry,entryTime=float(rows[entry]['time']),serveEnd=float(serve[-1]['clipTime']),G1_heights_mm=heights,G2_knee_deg=max(float(load['live_Lknee_deg']),float(load['live_Rknee_deg'])),G2_time=float(load['clipTime']),tossKneeThroughRelease=max(max(float(r['live_Lknee_deg']),float(r['live_Rknee_deg'])) for r in serve if float(r['clipTime'])<=.7),G3_first_clearance=first,G4_G8_contact=contact,G4_G8_rendered_contact=rendered_contact,G5_apex=float(apex['clipTime']),G6_touch=None if touch is None else dict(frame=int(touch['frame']),clipTime=float(touch['clipTime'])),G6_settled=None if settled is None else dict(frame=int(settled['frame']),clipTime=float(settled['clipTime'])),G7_entry_max_step=max(entry_steps,key=lambda x:x['mm']),G9_hands=hands,G9_followthrough=follow,G9_wrist=max(wrists,key=lambda x:x['degrees']),G11_drift=drift,nonServeSteps=nsteps,totalSteps=int(rows[-1]['stepsTaken']))

if __name__=='__main__':
    d=Path(sys.argv[1]); result=measure(d)
    (d/'metrics.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
