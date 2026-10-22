from pathlib import Path
import subprocess,re,json
W=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm');F='/Users/adnanyonathan/.cache/uv/archive-v0/FAqiNt1vNS62llSz/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1'
M=json.loads((W/'film_r2/manifest.json').read_text());assert 'v37' in M['candidate'] and len(M['films'])==12 and len(M['sheets'])==6 and len(M['real_input_films'])==4 and len(M['unsupported_LH'])==24
checks={}
for name in M['films']+M['real_input_films']:
 p=W/name;assert p.exists() and p.stat().st_size>10000,p
 r=subprocess.run([F,'-hide_banner','-i',str(p)],capture_output=True,text=True);s=r.stderr
 d=re.search(r'Duration: (\d+):(\d+):([\d.]+)',s);f=re.search(r'([\d.]+) fps',s);assert d and f,(p,s)
 seconds=float(d[1])*3600+float(d[2])*60+float(d[3]);fps=float(f[1]);expected=9 if p.name.startswith('real-input') else 30 if p.name.startswith('opponent') else 40;rate=30 if expected==9 else 15
 assert abs(seconds-expected)<.02 and abs(fps-rate)<.01,(p,seconds,fps)
 checks[name]={'duration_seconds':seconds,'fps':fps,'expected_duration_seconds':expected,'paired_half_speed':rate==15,'bytes':p.stat().st_size}
for name in M['sheets']+M['unsupported_LH']:assert (W/name).exists() and (W/name).stat().st_size>10000,name
(W/'report_r2/movie-readiness-v37.json').write_text(json.dumps({'pass':True,'look_approval_claimed':False,'checks':checks,'six_sheets_present':True,'24_LH_archive_films_explicitly_named_unsupported':True},indent=2));print('Verified 12 paired half-speed films and four normal-speed input films; six sheets and 24 unsupported LH archives present.')
