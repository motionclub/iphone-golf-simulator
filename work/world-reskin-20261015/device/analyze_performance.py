"""Evaluate real collected phone evidence. This never generates benchmark samples."""
import argparse,csv,json,math
from pathlib import Path

def stats(values):
    if not values or any(not math.isfinite(x) or x<=0 for x in values):
        raise ValueError('Positive finite measured frame intervals required')
    ordered=sorted(values)
    def percentile(p):return ordered[math.ceil((len(ordered)-1)*p)]
    return dict(frames=len(values),seconds=sum(values)/1000,meanFps=len(values)*1000/sum(values),p50Ms=percentile(.5),p95Ms=percentile(.95),p99Ms=percentile(.99),worstMs=max(values),over25msPercent=100*sum(x>25 for x in values)/len(values))

def pacing_failures(s):
    failures=[]
    for name,okay in [('mean FPS >=59.0',s['meanFps']>=59),('p95 <=18ms',s['p95Ms']<=18),('p99 <=20ms',s['p99Ms']<=20),('frames over25ms <=0.5%',s['over25msPercent']<=.5)]:
        if not okay:failures.append(name)
    return failures

def analyze(directory):
    summary_path=directory/'summary.json'
    if not summary_path.exists():return {'status':'FAIL','failures':['No completed evidence summary; successful build/install is not FPS evidence.']}
    source=json.loads(summary_path.read_text());failures=list(source.get('failures',[]));runs=[]
    if source.get('status')!='EVIDENCE_COLLECTED':failures.append('Collection was incomplete')
    if len(source.get('runtime',[]))!=1:failures.append('Exactly one fresh runtime report required')
    for run in source.get('runtime',[]):
        report=run['report'];path=Path(run['path']).parent/'frames.csv'
        with path.open() as handle:rows=list(csv.DictReader(handle))
        values=[float(r['elapsed_frame_ms']) for r in rows];measured=stats(values)
        if measured['seconds']<119.99:failures.append('Less than120seconds of active gameplay')
        if any(int(r['target_fps'])!=60 for r in rows):failures.append('Frame target changed away from60')
        failures.extend(pacing_failures(measured))
        if any(int(r['quality_reductions'])>0 for r in rows):failures.append('Quality governor reduced the reviewed preset')
        runs.append({'device':report['device'],'sport':report['sport'],'venue':report['venue'],'displayPixels':[report['screenWidth'],report['screenHeight']],'allFramesIncludingScreenshotIO':measured})
    thermal=[]
    for item in source.get('thermal',[]):
        samples=item['report'].get('samples',[])
        states=sorted(set(str(r.get('thermalState','missing')) for r in samples))
        if not states or any(state.lower() not in ['nominal','fair'] for state in states):failures.append('Thermal state did not stay nominal/fair')
        if any(r.get('seconds',0)>=10 and r.get('applicationState')!=0 for r in samples):failures.append('App was not continuously foreground during the thermal span')
        thermal.append({'states':states,'maximumProcessFootprintBytes':max((r['processFootprintBytes'] for r in samples),default=0)})
    timing_reports=[]
    for p in (directory/'timings').rglob('*.json'):
        d=json.loads(p.read_text())
        # Only the requested run's freshly collected timing file is evidence.
        from datetime import datetime,timedelta
        if datetime.fromisoformat(d['startedUtc'].replace('Z','+00:00')) < datetime.fromisoformat(source['startedUtc'])-timedelta(seconds=3):continue
        active=[r for r in d.get('samples',[]) if r.get('scene') in ['Golf','Tennis'] and 10<=r['elapsed']<=140]
        if not active:continue
        if any('renderScale' not in r for r in active):failures.append('Actual render scale missing from hardware report');continue
        settings=sorted(set((r['width'],r['height'],r['renderScale'],r['msaa'],r['shadowResolution'],r['shadowCascades'],r['qualityReductions']) for r in active))
        if any(r['qualityReductions']>0 or r['renderScale']<.999 for r in active):failures.append('Measured rendering reduced the reviewed full-resolution preset')
        gpu={r['timestamp']:r['gpuMs'] for r in active if r['timestamp']>0 and r['gpuMs']>0}
        timing_reports.append({'path':str(p),'device':d['device'],'settingsColumns':['width','height','renderScale','msaa','shadowResolution','shadowCascades','qualityReductions'],'actualSettings':settings,'uniquePositiveGpuSamples':len(gpu),'gpuTiming':{k:v for k,v in stats(list(gpu.values())).items() if k in ['p50Ms','p95Ms','p99Ms','worstMs']} if gpu else 'Unavailable; do not interpret zero as GPU headroom.'})
    if len(timing_reports)!=1:failures.append('Exactly one fresh hardware/settings report required')
    return {'status':'PASS' if not failures else 'FAIL','scope':'60fps target on the named physical device, measured120second active-play run including capture I/O; no all-device guarantee. Thresholds declared before measurement.','thresholds':{'meanFpsMin':59,'p95MsMax':18,'p99MsMax':20,'over25msPercentMax':.5,'renderScaleMin':1,'qualityReductionsMax':0},'failures':failures,'runs':runs,'hardware':timing_reports,'thermal':thermal}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);args=parser.parse_args()
    try:report=analyze(args.directory)
    except (OSError,ValueError,KeyError) as error:report={'status':'FAIL','failures':['Invalid or incomplete measured evidence: '+str(error)]}
    path=args.directory/'performance-gate.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));raise SystemExit(0 if report['status']=='PASS' else 1)
