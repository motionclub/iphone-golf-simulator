from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import csv,json,shutil,subprocess
from PIL import Image,ImageDraw,ImageFont

W=Path(__file__).resolve().parents[1]
D=W/'r2'
(D/'film').mkdir(exist_ok=True);(D/'proof').mkdir(exist_ok=True)
jobs=[]
for sex in ['male','female']:
    for view in ['front','side','back','game']:
        frames=sorted((D/sex).glob(view+'_*.png'))
        assert len(frames)==269
        for half,fps in [(False,30),(True,15)]:
            name=f'serve_r2_{sex}_{view}'+('_half_speed' if half else '')+'.mp4'
            size=['960','540'] if view=='game' else ['640','640']
            jobs.append([str(W/'scripts/enc'),str(D/'film'/name),str(fps),*size,*map(str,frames)])
def encode(cmd):
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: raise RuntimeError(f'Encoder {Path(cmd[1]).name}: exit {r.returncode}; {r.stderr[:2000]}')
    return r.stdout.strip()
with ThreadPoolExecutor(max_workers=2) as pool:
    for result in pool.map(encode,jobs): print(result,flush=True)

try: font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',15)
except OSError: font=ImageFont.load_default()
sheet=Image.new('RGB',(2560,768),(17,22,30));draw=ImageDraw.Draw(sheet)
metrics=json.loads((D/'live_metrics.json').read_text())
for si,sex in enumerate(['male','female']):
    rows=list(csv.DictReader((D/sex/'trace.csv').open()))
    serving=[r for r in rows if r['state'].startswith('Serve') and int(r['picture'])>=0]
    targets=[('release',.70),('trophy',1.278853),('procedural lift',1.510118),('contact',1.70),('apex',1.778333),('still airborne',1.90),('last Serve pose',1.978333)]
    chosen=[(label,min(serving,key=lambda r:abs(float(r['clipTime'])-t))) for label,t in targets]
    landing=rows[int(metrics[sex]['G6_touchdown']['L']['frame'])]
    chosen.append(('blend into Run: touch',landing))
    for col,(label,r) in enumerate(chosen):
        n=int(r['picture']);im=Image.open(D/sex/f'side_{n:05d}.png').convert('RGB');im.thumbnail((320,320))
        x,y=col*320,si*384+30;sheet.paste(im,(x,y))
        draw.text((x+6,y+323),sex+' | '+label,font=font,fill=(245,245,245))
        draw.text((x+6,y+342),'frame '+r['frame']+' clip '+r['clipTime'],font=font,fill=(215,220,230))
    n=int(landing['picture'])
    for view in ['side','game']:
        shutil.copy2(D/sex/f'{view}_{n:05d}.png',D/'proof'/f'{sex}_actual_blend_touch_{view}.png')
draw.text((8,5),'UNCHANGED CANDIDATE — FAIL. Live Unity poses; touchdown occurs after Serve has exited.',font=font,fill=(255,200,145))
sheet.save(D/'proof/live_serve_keys.jpg',quality=93)

# The procedural rise is shown next to its measured graph-stage trace, not labelled an authored jump.
for sex in ['male','female']:
    rows=list(csv.DictReader((D/sex/'trace.csv').open()));diag=metrics[sex]['diagnosis'];target=int(diag['frame'])
    r=min((r for r in rows if int(r['picture'])>=0),key=lambda r:abs(int(r['frame'])-target))
    im=Image.open(D/sex/f"side_{int(r['picture']):05d}.png").convert('RGB')
    canvas=Image.new('RGB',(960,760),(17,22,30));canvas.paste(im,(0,75));paint=ImageDraw.Draw(canvas)
    paint.text((12,10),sex+' — PROCEDURAL FOOT STEP DURING SERVE',font=font,fill=(255,220,170))
    paint.text((12,35),'pictured frame '+r['frame']+' / measured peak frame '+diag['frame'],font=font,fill='white')
    s=diag['side'];lines=[f"Peak clip time: {float(diag['clipTime']):.6f} s",f"Base Serve weight: {float(diag['baseServe']):.6f}",f"Ready / Walk / Run: 0 / 0 / 0",f"Upper layer: {float(diag['upperWeight']):.6f}",f"{s} heel in layers: {diag['layers_'+s+'heel_mm']:.3f} mm",f"{s} heel live: {diag['live_'+s+'heel_mm']:.3f} mm",f"Added rise: {diag['procedural_heel_delta_mm']:.3f} mm",f"sin(pi * stepT) * 65: {diag['step_formula_mm']:.3f} mm",'Source: LockFeet, line 708',f"stepping = 1; stepT = {float(diag[s+'stepT']):.6f}"]
    for i,line in enumerate(lines): paint.text((654,105+i*28),line,font=font,fill=(235,240,248))
    canvas.save(D/'proof'/f'{sex}_procedural_step.jpg',quality=93)
