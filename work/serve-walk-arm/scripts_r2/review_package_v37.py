from pathlib import Path
import csv,json,subprocess,shutil,time
from PIL import Image,ImageDraw,ImageFont
W=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm')
O=W/'film_r2';O.mkdir(exist_ok=True)
FF='/Users/adnanyonathan/.cache/uv/archive-v0/FAqiNt1vNS62llSz/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1'
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
def rows(p):return {int(x['frame']):x for x in csv.DictReader((p/'trace.csv').open())}
def scope(x,role):return x['phase']=='PlayerServeHold' if role=='player' else x['phase']=='OpponentServe' and float(x['routine_time'])<2.2
def ass(path,width,height,events):
 def stamp(t):
  n=round(t*100);return f'{n//360000}:{n//6000%60:02d}:{n//100%60:02d}.{n%100:02d}'
 header=f"[Script Info]\nScriptType: v4.00+\nPlayResX: {width}\nPlayResY: {height}\nWrapStyle: 2\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,16,&H00FFFFFF,&H00FFFFFF,&H0014181E,&H0014181E,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
 path.write_text(header+''.join(f'Dialogue: 0,{stamp(a)},{stamp(b)},Default,,0,0,0,,{{\\pos({x},{y})}}{text}\n' for a,b,x,y,text in events))
manifest={'candidate':'v37; NOT INSTALLED; GATES FAIL','rate':'30 Hz pictures encoded at 15 fps = half speed','films':[],'sheets':[],'unsupported_LH':[],'raw_traces':'Unfiltered 60 Hz CSV retained; excluded reasons and phase shown.'}
for role in ['player','opponent']:
 for sex in ['male','female']:
  name=f'{role}-{sex}-rh-deuce';b=W/'before_r2_film'/name;a=W/'after_r2_film_v37'/name
  while not (a/'completed.json').exists():time.sleep(2)
  rb,ra=rows(b),rows(a)
  for view in ['game','front','left']:
   label='side' if view=='left' else view;tw,th=(640,360) if view=='game' else (480,480);width,height=tw*2,th+84
   target=O/f'{role}-{sex}-{label}-before-after-half-speed.mp4'
   subtitles=O/f'{role}-{sex}-{label}.ass'
   events=[]
   for f in sorted(set(rb)&set(ra)):
    if f%2:continue
    t=f/30
    for i,(r,tag) in enumerate(zip([rb[f],ra[f]],['BEFORE production','AFTER v37 - GATES FAIL'])):
     text=f'{tag} | {role} {sex} RH {label}\\Nf{f} depth {float(r["deepest_mm"]):.3f} mm | {r["phase"]}\\NG1 pre-scope {scope(r,role)} | in-hand {r["in_hand"]} | half speed'
     events.append((t,t+1/15,i*tw+10,6,text))
   ass(subtitles,width,height,events)
   filt=f'[0:v]scale={tw}:{th},pad={tw}:{height}:0:84:color=0x14181e[l];[1:v]scale={tw}:{th},pad={tw}:{height}:0:84:color=0x14181e[r];[l][r]hstack,ass={subtitles}[out]'
   subprocess.run([FF,'-v','error','-y','-framerate','15','-i',str(b/f'{view}_%05d.png'),'-framerate','15','-i',str(a/f'{view}_%05d.png'),'-filter_complex',filt,'-map','[out]','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-threads','2',str(target)],check=True)
   manifest['films'].append(str(target.relative_to(W)));print(target.name,flush=True)
while len(list((W/'before_r2_plant547').glob('*/completed.json'))) < 4:time.sleep(2)
for sex in ['male','female']:
 for view in ['game','front','left']:
  label='side' if view=='left' else view;tw,th=(360,202) if view=='game' else (360,360);sheet=Image.new('RGB',(tw*4,(th+50)*4),(20,24,30));d=ImageDraw.Draw(sheet)
  for role_i,role in enumerate(['player','opponent']):
   frames=[128 if sex=='male' else 142,320,547,768] if role=='player' else [128 if sex=='male' else 142,302,547,792]
   name=f'{role}-{sex}-rh-deuce'
   for version_i,stage in enumerate(['before_r2_film','after_r2_film_v37']):
    p=W/stage/name;r=rows(p)
    for col,f in enumerate(frames):
     if f==547:
      q=(W/'before_r2_plant547'/name if version_i==0 else p);src=q/('plant547-game.png' if view=='game' else 'plant547-'+label+'_00547.png')
     else:src=p/f'{view}_{f//2:05d}.png'
     assert src.exists(),src
     x,y=col*tw,(role_i*2+version_i)*(th+50);sheet.paste(Image.open(src).convert('RGB').resize((tw,th)),(x,y));v='BEFORE' if version_i==0 else 'AFTER v37 FAIL';d.text((x+5,y+th+3),f'{v} {role} f{f} depth {float(r[f]["deepest_mm"]):.3f} mm',font=small,fill='white');d.text((x+5,y+th+24),r[f]['phase'],font=small,fill='white')
  target=O/f'{sex}-{label}-contact-sheet.jpg';sheet.save(target,quality=93);manifest['sheets'].append(str(target.relative_to(W)))
# Retain run 28 LH examples with explicit unsupported labels; never include them in the RH matrix.
for a in sorted((W/'after').glob('*-lh-*')):
 b=W/'before'/a.name
 for view in ['game','front','left']:
  srca=a/f'{view}.mp4';srcb=b/f'{view}.mp4'
  if not(srca.exists() and srcb.exists()):continue
  target=O/f'UNSUPPORTED-LH-archive28-{a.name}-{view}.mp4'
  if target.exists():
   manifest['unsupported_LH'].append(str(target.relative_to(W)));continue
  filt="[0:v]setpts=2*PTS,drawtext=text='BEFORE ARCHIVE 28 - LH UNSUPPORTED':x=8:y=8:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.7[l];[1:v]setpts=2*PTS,drawtext=text='AFTER ARCHIVE 28 - LH UNSUPPORTED':x=8:y=8:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.7[r];[l][r]hstack[out]"
  subprocess.run([FF,'-v','error','-y','-i',str(srcb),'-i',str(srca),'-filter_complex',filt,'-map','[out]','-an','-c:v','libx264','-crf','23','-pix_fmt','yuv420p',str(target)],check=True)
  manifest['unsupported_LH'].append(str(target.relative_to(W)))
while len(list((W/'input_r2_v37').glob('*/completed.json'))) < 4:time.sleep(2)
manifest['real_input_films']=[]
for p in sorted((W/'input_r2_v37').glob('*')):
 assert (p/'completed.json').exists(),p
 rr=rows(p);target=O/f'real-input-{p.name}.mp4';subtitles=O/f'real-input-{p.name}.ass';events=[]
 for f,r in rr.items():
  if f%2:continue
  text=f'PLAY MODE - {p.name} - production SetLateralInput\\Nf{f} | {r["segment"]} | depth {float(r["deepest_mm"]):.3f} mm | CANDIDATE v37 NOT INSTALLED'
  events.append((f/60,f/60+1/30,10,7,text))
 ass(subtitles,960,624,events)
 subprocess.run([FF,'-v','error','-y','-framerate','30','-i',str(p/'game_%05d.png'),'-vf',f'pad=960:624:0:84:color=0x14181e,ass={subtitles}','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-threads','2',str(target)],check=True)
 manifest['real_input_films'].append(str(target.relative_to(W)));print(target.name,flush=True)
(O/'manifest.json').write_text(json.dumps(manifest,indent=2))
