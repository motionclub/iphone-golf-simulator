"""Measure the actual re-imported FBX, including subframes. No animation edits.
blender -b --factory-startup --python fluid_audit.py -- before|after [male|female|both]
Writes portable traces plus JSON/Markdown, and saves unmodified imported baseline scenes.
"""
import os,sys,json,math,hashlib
from pathlib import Path
import numpy as np
import bpy
from mathutils import Matrix,Quaternion
sys.path.insert(0,str(Path(__file__).parent))
from fluid_spec import *
import native_curves as NC
REPO=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
W=Path(os.environ.get('FLUID_WORK',str(REPO/'work/emote-fluid')))
def curves(act):
    return [f for l in act.layers for s in l.strips for cb in s.channelbags for f in cb.fcurves]
def qlog(q):
    q=np.array(q,float);q=q/np.maximum(np.linalg.norm(q,axis=-1,keepdims=True),1e-12)
    q=np.where(q[...,0,None]<0,-q,q)
    angle=2*np.arctan2(np.linalg.norm(q[...,1:],axis=-1),q[...,0])
    return q[...,1:]*np.divide(angle,np.linalg.norm(q[...,1:],axis=-1),out=np.zeros_like(angle),where=np.linalg.norm(q[...,1:],axis=-1)>1e-12)[...,None]*180/math.pi
def increments(q):
    out=[]
    for a,b in zip(q[:-1],q[1:]):
        out.append(qlog(np.array(Quaternion(tuple(b))@Quaternion(tuple(a)).inverted())))
    return np.array(out)
def rotation_progress(q,a,b):
    base=Quaternion(tuple(q[a]));delta=np.array([qlog(np.array(Quaternion(tuple(v))@base.inverted())) for v in q])
    axis=delta[b];norm=np.linalg.norm(axis)
    return delta@(axis/max(norm,1e-12)),norm
def result(ok,**numbers):return dict(ok=bool(ok),**numbers)
def longest(mask):
    best=cur=0
    for a in mask:
        cur=cur+1 if a else 0;best=max(best,cur)
    return best

def measure(z,curve_info,clip):
    names=json.loads(str(z['meta']))['bones'];ix={n:i for i,n in enumerate(names)}
    n=len(z['M']);spec=dict(SPEC[clip]);meta=json.loads(str(z['meta']));pp=W/'proof'/f"plan_{meta['hero']}_{clip}.json"
    if 'candidate/fbx' in meta['path'] and pp.exists():spec['moves']=json.load(open(pp))
    Q=z['Q']; P=z['M'][...,:3,3];g={};body=[b for b in BODY if b in ix]
    inc={b:increments(Q[:,ix[b]]) for b in body};speed={b:np.linalg.norm(v,axis=1) for b,v in inc.items()}
    # Signed angular velocity in each joint's dominant motion direction at each beat.
    # A zero plateau counts its arrival once; frozen joints are counted by F3, not as crossings.
    crossing_rows=[]
    for beat in spec['beats']:
        lo=max(0,beat-5);hi=min(n-2,beat+5); counts={f:[] for f in range(lo+1,hi+1)}
        for b,v in inc.items():
            sample=v[lo:hi+1]
            if np.linalg.norm(sample)<.001:continue
            axis=np.linalg.svd(sample,full_matrices=False)[2][0]; s=v@axis
            for f in counts:
                before,after=s[f-1],s[f]
                if before*after<0 or (abs(before)>.001 and abs(after)<=.001):counts[f].append(b)
        if counts:
            frame=max(counts,key=lambda f:len(counts[f]));crossing_rows.append(dict(beat=beat,frame=frame,count=len(counts[frame]),bones=counts[frame]))
    worst=max(crossing_rows,key=lambda x:x['count']) if crossing_rows else dict(beat=0,frame=0,count=0,bones=[])
    g['F1']=result(worst['count']<=2,limit=2,**worst,beats=crossing_rows)
    chains=[];overs=[];antis=[];stretch=[]
    for m in spec['moves']:
        a,b=m['start'],min(n-1,m['pose']);lo=max(0,a);hi=min(n-2,b+m['settle']-1)
        shared_peaks=[lo+int(np.argmax(speed[j][lo:hi+1]))+1 for j in m['chain']]
        windows=m.get('link_windows',{j:[a,b] for j in m['chain']});peaks=[]
        for j in m['chain']:
            aa,bb=windows[j];l=max(0,int(math.floor(aa)));h=min(n-2,max(l,int(math.ceil(bb))-1));peaks.append(l+int(np.argmax(speed[j][l:h+1]))+1)
        gaps=np.diff(peaks); chains.append(dict(move=m['name'],chain=m['chain'],peaks=peaks,action_windows=windows,previous_shared_window_peaks=shared_peaks,gaps=gaps.tolist(),ok=bool(np.all((gaps>=1)&(gaps<=4)))))
        pr,mag=rotation_progress(Q[:,ix[m['bone']]],max(0,a),min(n-1,b+m['settle']))
        settle_value=float(pr[min(n-1,b+m['settle'])]);peak=float(np.max(pr[max(0,b-1):min(n,b+m['settle']+1)]));pct=100*(peak-settle_value)/max(abs(settle_value),1e-9)
        # The overshoot must happen at the pose beat, with actual return to the settle value.
        peakf=max(0,b-1)+int(np.argmax(pr[max(0,b-1):min(n,b+m['settle']+1)]));settlef=min(n-1,b+m['settle']);sf=settlef-peakf
        overs.append(dict(move=m['name'],bone=m['bone'],move_deg=float(mag),overshoot_pct=float(pct),peak_frame=peakf,settle_frame=settlef,settle_frames=sf,ok=bool(mag>.001 and pct>=5 and 3<=sf<=6)))
        anti_a=max(0,m['anticipation'][0]);anti_b=min(n-1,a)
        main,_=rotation_progress(Q[:,ix[m['bone']]],anti_b,b)
        dif=np.diff(main[anti_a:anti_b+1]);counter=longest(dif<-.001)
        # Pelvis translation may supply anticipation even when torso is contact constrained.
        pv=P[:,ix['Hips']];d=pv[b]-pv[anti_b];d/=max(np.linalg.norm(d),1e-9);pd=np.diff(pv[anti_a:anti_b+1]@d)
        counter=max(counter,longest(pd<-.000001))
        hip_progress,_=rotation_progress(Q[:,ix['Hips']],anti_b,b)
        counter=max(counter,longest(np.diff(hip_progress[anti_a:anti_b+1])<-.001))
        antis.append(dict(move=m['name'],start=a,counter_frames=int(counter),ok=counter>=3))
        if m['stretch']:
            f=slice(max(0,b-2),min(n,b+3));ratio=z['CHAIN_RATIO'][f];dev=float(np.max(abs(ratio-1)))
            stretch.append(dict(move=m['name'],frames=[max(0,b-2),min(n-1,b+2)],ratio_min=float(ratio.min()),ratio_max=float(ratio.max()),deviation=dev,ok=bool(dev>=.005 and ratio.min()>=.88 and ratio.max()<=1.12)))
    g['F2']=result(all(x['ok'] for x in chains),passing=sum(x['ok'] for x in chains),required=len(chains),moves=chains)
    g['F3']=result(curve_info['linear_rotation_keys']==0 and curve_info['flat_runs']==0,**curve_info)
    holds=[]
    for a,b in spec['holds']:
        if (b-a)/30<=.5:continue
        best=None
        for nm in ['Chest','Hips']:
            pr,mag=rotation_progress(Q[:,ix[nm]],a,b);momentum=0.
            for k in range(a-1,-1,-1):
                v=pr[k+1]-pr[k]
                if abs(v)>.001:momentum=v;break
            drift=pr[b]-pr[a]
            item=dict(bone=nm,drift_deg=float(abs(drift)),direction_dot=float(momentum*drift),ok=bool(abs(drift)>=1.5 and momentum*drift>0))
            if best is None or (item['ok'],item['drift_deg'])>(best['ok'],best['drift_deg']):best=item
        holds.append(dict(frames=[a,b],**best))
    g['F4']=result(all(x['ok'] for x in holds),passing=sum(x['ok'] for x in holds),required=len(holds),holds=holds)
    g['F5']=result(all(x['ok'] for x in overs),passing=sum(x['ok'] for x in overs),required=len(overs),poses=overs)
    g['F6']=result(all(x['ok'] for x in antis),passing=sum(x['ok'] for x in antis),required=len(antis),moves=antis)
    trails={nm:P[:,ix[nm]] for nm in ['LeftHand','RightHand']};trails['HeadTop']=z['HEADTOP']
    kinkrows=[]
    for nm,p in trails.items():
        v=np.diff(p,axis=0);den=np.linalg.norm(v[:-1],axis=1)*np.linalg.norm(v[1:],axis=1)
        angle=np.degrees(np.arccos(np.clip(np.divide(np.sum(v[:-1]*v[1:],axis=1),den,out=np.ones_like(den),where=den>1e-10),-1,1)))
        for f in spec['impacts']:
            angle[max(0,f-2):min(len(angle),f+1)]=0
        f=int(np.argmax(angle))+1;kinkrows.append(dict(bone=nm,frame=f,kink_deg=float(angle[f-1])))
    worstk=max(kinkrows,key=lambda x:x['kink_deg']);g['F7']=result(worstk['kink_deg']<=60,limit_deg=60,**worstk,paths=kinkrows)
    socket=[i for i,nm in enumerate(names) if nm.endswith(('Hand','LowerArm','Head','Foot','Toes'))]+[ix[nm] for nm in z['socket_bones'].tolist() if nm in ix]
    socket_delta=float(np.max(abs(z['SCALE'][:,socket]-1)))
    g['F8']=result(all(x['ok'] for x in stretch) and socket_delta==0,passing=sum(x['ok'] for x in stretch),required=len(stretch),socket_scale_delta=socket_delta,ratio_min=float(z['CHAIN_RATIO'].min()),ratio_max=float(z['CHAIN_RATIO'].max()),moves=stretch)
    cr=[]
    for nm in ['LeftShoulder','RightShoulder']:
        qq=Q[:,ix[nm]];aa=[]
        for q in qq:aa.append(qlog(np.array(Quaternion(tuple(q))@Quaternion(tuple(qq[0])).inverted())))
        aa=np.array(aa);cr.append(float(max(np.linalg.norm(x-y) for x in aa[::2] for y in aa[::2])))
    g['F9']=result(min(cr)>=6,left_deg=cr[0],right_deg=cr[1],limit_deg=6)
    # Separate proof files populate these after genuine clearance and Unity runs.
    for num,required in [('F10',96),('F12',1),('F14',4),('F15',24)]:g[num]=result(False,passing=0,required=required)
    step_rows=[]
    for nm in ['LeftHand','RightHand','HeadTop']:
        p=z['HEADTOP60'] if nm=='HeadTop' else z['M60'][:,ix[nm],:3,3]
        d=np.linalg.norm(np.diff(p,axis=0),axis=1)*1000
        for a,b in spec['fast']:d[max(0,a*2-1):min(len(d),b*2+1)]=0
        f=int(np.argmax(d));step_rows.append(dict(bone=nm,frame60=f+1,step_mm=float(d[f])))
    twist=[]
    for nm in ['LeftHand','RightHand']:
        qq=z['Q60'][:,ix[nm]];vals=[];total=[]
        for aa,bb in zip(qq[:-1],qq[1:]):
            rel=Quaternion(tuple(bb))@Quaternion(tuple(aa)).inverted();angle=2*math.atan2(rel.y,rel.w);angle=(angle+math.pi)%(2*math.pi)-math.pi;vals.append(abs(angle)*180/math.pi);total.append(rel.angle*180/math.pi)
        a=np.array(vals);f=int(np.argmax(a));twist.append(dict(bone=nm,frame60=f+1,twist_deg=float(a[f]),full_joint_rotation_deg=float(max(total)),measurement='Swing/twist decomposition about local hand +Y (finger/forearm axis).'))
    maxstep=max(step_rows,key=lambda x:x['step_mm']);maxtwist=max(twist,key=lambda x:x['twist_deg'])
    g['F11']=result(maxstep['step_mm']<=150 and maxtwist['twist_deg']<=15,step=maxstep,twist=maxtwist,limit_mm=150,limit_deg=15)
    g['F13']=result(False,passing=0,required=15)
    return g

def main():
    args=sys.argv[sys.argv.index('--')+1:];phase=args[0];tags=[args[1]] if len(args)>1 and args[1]!='both' else ['male','female']
    out=W/'data'/phase;out.mkdir(parents=True,exist_ok=True);allresults={}
    for tag in tags:
      names=[x['name'] for x in json.load(open(REPO/f'work/match-anim-set/data/rig_{tag}.json'))['bones']]
      for clip in (args[2:] or CLIPS):
        label=tag.title();path=(W/'rollback/fbx' if phase=='before' else W/'candidate/fbx')/f'{label}_{clip}.fbx'
        bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(path),axis_forward='-Z',axis_up='Y')
        if phase=='after':
            for obj in bpy.context.scene.objects:
                if obj.type=='MESH':
                    for modifier in obj.modifiers:modifier.show_viewport=False
        sc=bpy.context.scene;sc.render.fps=30;sc.render.fps_base=1;arm=next(o for o in sc.objects if o.type=='ARMATURE');act=arm.animation_data.action
        f0,f1=map(lambda x:int(round(x)),act.frame_range);n=f1-f0+1;pbs=[arm.pose.bones[nm] for nm in names]
        def sample(rate):
            nf=(n-1)*rate+1;M=np.zeros((nf,len(names),4,4));Q=np.zeros((nf,len(names),4));LOC=np.zeros((nf,len(names),3));SC=np.zeros_like(LOC);HEAD=np.zeros((nf,3));HR=np.zeros((nf,4,4));RC=np.zeros_like(HR);ARM=np.zeros_like(HR);ROOT=np.zeros((nf,7));RATIO=np.ones(nf)
            chain=['Spine','Chest','Neck','Head'];rest=sum((arm.data.bones[b].head_local-arm.data.bones[b].parent.head_local).length for b in chain)
            for k in range(nf):
                t=f0+k/rate;sc.frame_set(int(t),subframe=t-int(t));bpy.context.view_layer.update();mw=arm.matrix_world
                for j,pb in enumerate(pbs):M[k,j]=np.array(mw@pb.matrix);Q[k,j]=np.array(pb.rotation_quaternion);LOC[k,j]=np.array(pb.location);SC[k,j]=np.array(pb.scale)
                HEAD[k]=np.array(mw@arm.pose.bones['Head'].tail);ARM[k]=np.array(mw)
                for nm,arr in [('Hand_Racket',HR),('Racket_Classic',RC)]:
                    obj=bpy.data.objects.get(nm);arr[k]=np.array(obj.matrix_world) if obj else np.eye(4)
                rb=arm.pose.bones['Root'];ROOT[k,:3]=np.array(rb.location);ROOT[k,3:]=np.array(rb.rotation_quaternion)
                RATIO[k]=sum((arm.pose.bones[b].head-arm.pose.bones[b].parent.head).length for b in chain)/rest
            return dict(M=M,Q=Q,LOC=LOC,SCALE=SC,HEADTOP=HEAD,HR=HR,RC=RC,ARM=ARM,ROOT=ROOT,CHAIN_RATIO=RATIO)
        z=sample(1);z60=sample(2)
        native,channels=NC.read_pose(path,names,n,rate=2)
        z['BLENDER_M']=z['M'].copy()
        qnative=np.zeros((len(native['M']),len(names),4))
        for j,nm in enumerate(names):
            pb=pbs[j];rest=pb.parent.bone.matrix_local.inverted()@pb.bone.matrix_local if pb.parent else pb.bone.matrix_local
            rq=rest.to_quaternion().inverted()
            for f in range(len(native['M'])):qnative[f,j]=np.array(rq@Matrix(native['LOCAL'][f,j].tolist()).to_quaternion())
        for key in ['M','HR','RC','ARM','SCALE']:z[key]=native[key][::2]
        z['Q']=qnative[::2];z['M60']=native['M'];z['Q60']=qnative
        hi=names.index('Head');length=arm.data.bones['Head'].length
        z['HEADTOP60']=native['M'][:,hi,:3,3]+native['M'][:,hi,:3,1]*length;z['HEADTOP']=z['HEADTOP60'][::2]
        chain=['Spine','Chest','Neck','Head'];rest=sum((arm.data.bones[b].head_local-arm.data.bones[b].parent.head_local).length for b in chain)
        z['CHAIN_RATIO']=sum(np.linalg.norm(z['M'][:,names.index(b),:3,3]-z['M'][:,names.index(arm.pose.bones[b].parent.name),:3,3],axis=1) for b in chain)/rest
        flatrows=[];linear=0;total=0
        for fc in curves(act):
            if '.rotation_' not in fc.data_path:continue
            if not any(f'"{nm}"' in fc.data_path for nm in BODY):continue
            keys=fc.keyframe_points;total+=len(keys);linear+=sum(k.interpolation=='LINEAR' for k in keys)
            vals=np.array([k.co.y for k in keys]);frames=np.array([k.co.x-f0 for k in keys]);runs=[];start=0
            for j in range(1,len(vals)+1):
                if j<len(vals) and vals[j]==vals[j-1]:continue
                if j-start>=3:
                    aa,bb=frames[start],frames[j-1];intended=bb<=7.5 or aa>=(n-1)-7.5 or any(aa>=a and bb<=b for a,b in SPEC[clip]['holds']) or aa>=SPEC[clip]['money'][0] and bb<=SPEC[clip]['money'][1]
                    if not intended:runs.append([float(aa),float(bb)])
                start=j
            if runs:flatrows.append(dict(path=fc.data_path,component=fc.array_index,runs=runs))
        native_linear=0;native_total=0;native_flat=[]
        for (nm,prop,axis),curve in channels.items():
            if nm not in BODY or prop!='Lcl Rotation':continue
            vals=np.array(NC.FB.data(curve,b'KeyValueFloat'));times=np.array(NC.FB.data(curve,b'KeyTime'),float)/NC.TIME*30;flags=NC.expand(curve,b'KeyAttrFlags');native_linear+=int(np.sum((flags&14)==4));native_total+=len(vals)
            start=0
            for j in range(1,len(vals)+1):
                if j<len(vals) and vals[j]==vals[j-1]:continue
                if j-start>=3:
                    aa,bb=times[start],times[j-1];intended=bb<=7.5 or aa>=(n-1)-7.5 or any(aa>=a and bb<=b for a,b in SPEC[clip]['holds']) or aa>=SPEC[clip]['money'][0] and bb<=SPEC[clip]['money'][1]
                    outside=~((times[start:j]<=7.5)|(times[start:j]>=(n-1)-7.5))
                    for a,b in SPEC[clip]['holds']+[SPEC[clip]['money']]:outside&=~((times[start:j]>=a)&(times[start:j]<=b))
                    if longest(outside)>=3:native_flat.append(dict(bone=nm,axis=axis,frames=[float(aa),float(bb)]))
                start=j
        ci=dict(linear_rotation_keys=native_linear,total_rotation_keys=native_total,flat_runs=len(native_flat),flat_details=native_flat,blender_derived_linear_keys=linear,measurement='Actual FBX interpolation flags; native cubic tangents evaluated at 60 Hz. Stock Blender importer generates linear approximation curves regardless of file flags.')
        hr=bpy.data.objects.get('Hand_Racket');parents=[(b.name,b.parent.name if b.parent else None) for b in arm.data.bones]
        meta=dict(clip=clip,hero=tag,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bones=names,parents=parents,objects=sorted(o.name for o in sc.objects),meshes=sorted(o.name for o in sc.objects if o.type=='MESH'),empties=sorted(o.name for o in sc.objects if o.type=='EMPTY'),armatures=1,rc_parent=bpy.data.objects['Racket_Classic'].parent.name,hr_parent=[hr.parent.name,hr.parent_type,hr.parent_bone],frame_range=[f0,f1])
        z['frames']=n;z['meta']=json.dumps(meta);z['socket_bones']=np.array([o.parent_bone for o in sc.objects if o.parent==arm and o.parent_type=='BONE']);z['curve_info']=json.dumps(ci)
        np.savez_compressed(out/f'trace_{tag}_{clip}.npz',**z)
        if phase=='before':
            sc.frame_set(f0);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{label}_{clip}.blend'))
        gate=measure(z,ci,clip);allresults[f'{tag}/{clip}']=gate
        print('AUDIT',phase,tag,clip,'frames',n,' '.join(f'{k}:{"PASS" if v["ok"] else "FAIL"}' for k,v in gate.items()),flush=True)
    jp=out/'audit.json';prior=json.load(open(jp)) if jp.exists() else {};prior.update(allresults);jp.write_text(json.dumps(prior,indent=2))
    lines=[f'# {phase.upper()} fluidity audit','', '| Hero / clip | '+ ' | '.join(f'F{i}' for i in range(1,16))+' |','|---|'+ '|'.join(['---']*15)+'|']
    for k,g in prior.items():lines.append('| '+k+' | '+' | '.join('PASS' if g[f'F{i}']['ok'] else 'FAIL' for i in range(1,16))+' |')
    (out/'SCORECARD.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
