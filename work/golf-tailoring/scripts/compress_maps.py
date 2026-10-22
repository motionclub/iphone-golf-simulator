from pathlib import Path
import subprocess,concurrent.futures,json
W=Path(__file__).resolve().parents[1];D=W/'native';D.mkdir(exist_ok=True)
def convert(p):
 out=D/p.name.replace('Golf_','MatchHero_GolfKit_').replace('.png','.ktx')
 fmt='ASTC4x4' if 'Atlas' in p.name else 'ASTC8x8'
 result=subprocess.run(['/Applications/Xcode.app/Contents/Developer/usr/bin/TextureConverter','--compression_format='+fmt,'--compression_quality=Highest','--alpha_mode=Preserve','--channel_weighting=Linear','--gamma_in=1','--gamma_out=1','--flip_y','--wrap_mode=Clamp','--file_format=KTX','--output='+str(out),str(p)],capture_output=True,text=True)
 if result.returncode:raise RuntimeError(result.stderr+result.stdout)
 return dict(name=out.name,bytes=out.stat().st_size)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(convert,sorted((W/'maps').glob('*.png'))))
(W/'data/native_maps.json').write_text(json.dumps(rows,indent=2));print('COMPRESSED',len(rows))
