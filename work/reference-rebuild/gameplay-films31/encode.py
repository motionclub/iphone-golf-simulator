from pathlib import Path
import json,subprocess,hashlib,shutil,wave,sys
r=Path.cwd();w=r/'work/reference-rebuild/gameplay-films31'
o=Path('/Users/adnanyonathan/Documents/Codex/2026-10-06/open-4/outputs/reference-check/gameplay-films');o.mkdir(exist_ok=True)
ff='/Users/adnanyonathan/.cache/uv/archive-v0/FAqiNt1vNS62llSz/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1'
name=sys.argv[1];d=w/'frames'/name;golf=name.startswith('golf-')
f=sorted(d.glob('f_*.jpg')) if golf else sorted((d/'frames').glob('game_*.jpg'))
assert f,'No captured frames';pattern=str(d/'f_%05d.jpg') if golf else str(d/'frames/game_%05d.jpg')
a=d/('sound.wav' if golf else 'audio.wav');audio=False
if a.exists():
 with wave.open(str(a),'rb') as wav:audio=wav.getnframes()>0
p=o/(name+'.mp4');cmd=[ff,'-hide_banner','-loglevel','error','-y','-framerate','30','-i',pattern]
if audio:cmd+=['-i',str(a)]
cmd+=['-c:v','libx264','-preset','fast','-crf','18','-threads','2','-pix_fmt','yuv420p','-t',str(len(f)/30)]
cmd+=['-c:a','aac','-b:a','160k'] if audio else ['-an']
cmd+=['-movflags','+faststart',str(p)];subprocess.run(cmd,check=True)
subprocess.run([ff,'-hide_banner','-loglevel','error','-i',str(p),'-f','null','-'],check=True)
# Preserve exact current game frames as posters, no painted modifications.
poster=o/(name+'.jpg');shutil.copy2(f[min(len(f)-1,25)],poster)
row={'id':name,'file':str(p),'poster':str(poster),'frames':len(f),'fps':30,'duration':len(f)/30,'width':1280,'height':720,'audio':audio,'mp4Sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'decode':'PASS all frames','firstFrame':str(f[0]),'lastFrame':str(f[-1]),'sourceReport':str(d/('film.json' if golf else 'audit.txt'))}
(w/(name+'-encoded.json')).write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row))
