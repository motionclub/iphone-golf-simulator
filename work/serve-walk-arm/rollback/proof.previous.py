import argparse, csv, json, math, subprocess
from pathlib import Path
from PIL import Image, ImageDraw

FFMPEG='/Users/adnanyonathan/.cache/uv/archive-v0/FAqiNt1vNS62llSz/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1'
p=argparse.ArgumentParser(); p.add_argument('run', type=Path); p.add_argument('--film', action='store_true'); args=p.parse_args()
run=args.run
rows=list(csv.DictReader((run/'trace.csv').open()))
f=lambda x,k:float(x[k])
walk=[r for r in rows if abs(f(r,'speed'))>.2 and f(r,'prepare')<=.001 and r['phase']=='PlayerServeHold']
left=[r for r in walk if f(r,'speed')<0]
turn=[r for r in rows if not r['segment'].startswith('control') and (r['segment'].startswith(('walk','plant','tap')))]
summary={}
for name,a in [('all',rows),('walk',walk),('left',left),('walk_turn_plant',turn)]:
 if not a: continue
 worst=max(a,key=lambda r:f(r,'deepest_mm'))
 summary[name]={'frames':len(a),'deepest_mm':f(worst,'deepest_mm'),'worst_frame':int(worst['frame']), 'worst_bone':worst['worst_bone'],'inside_pct_at_worst':f(worst,'inside_pct'), 'inside_pct_max':max(f(r,'inside_pct') for r in a), 'game_visibility_pct':100*sum(int(r['game_visible']) for r in a)/len(a), 'front_visibility_pct':100*sum(int(r['front_visible']) for r in a)/len(a),'ball_palm_max_cm':100*max(f(r,'ball_palm_m') for r in a),'elbow_range_deg':[min(f(r,'elbow_flexion') for r in a),max(f(r,'elbow_flexion') for r in a)],'length_delta_mm':max(f(r,'length_delta_mm') for r in a),'hand_step_max_cm':100*max(f(r,'hand_step_m') for r in a),'hand_speed_change_max':max(f(r,'hand_speed_change') for r in a),'hip_lateral_min_cm':100*min(f(r,'hip_lateral_m') for r in a)}
(run/'summary.json').write_text(json.dumps(summary,indent=2))
worst=max(left or rows,key=lambda r:f(r,'deepest_mm')); frame=int(worst['frame']); centre=frame//2
for view in ['front','left','game','top']:
 paths=[run/f'{view}_{max(0,centre-6+i):05d}.png' for i in range(12)]
 tilew=320; tileh=320 if view!='game' else 180
 sheet=Image.new('RGB',(4*tilew,3*(tileh+36)),(22,25,31)); draw=ImageDraw.Draw(sheet)
 for i,path in enumerate(paths):
  if not path.exists(): continue
  img=Image.open(path).convert('RGB'); img.thumbnail((tilew,tileh)); x=(i%4)*tilew;y=(i//4)*(tileh+36);sheet.paste(img,(x,y)); n=int(path.stem.split('_')[-1])*2
  row=next((r for r in rows if int(r['frame'])==n),None)
  label=f'frame {n} | {f(row,"deepest_mm"):.1f} mm' if row else f'frame {n}'
  draw.text((x+6,y+tileh+6),label, fill='white')
 sheet.save(run/f'worst-{view}-sheet.jpg',quality=94)
 if args.film:
  subprocess.run([FFMPEG,'-v','error','-y','-framerate','30','-i',str(run/f'{view}_%05d.png'),'-c:v','libx264','-crf','19','-pix_fmt','yuv420p',str(run/f'{view}.mp4')],check=True)
print(json.dumps(summary,indent=2))
