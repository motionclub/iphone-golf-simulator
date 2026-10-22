from pathlib import Path
import subprocess,concurrent.futures,json
W=Path(__file__).resolve().parents[1];D=W/'locker/assets';converter='/Applications/Xcode.app/Contents/Developer/usr/bin/TextureConverter';paths=list(D.glob('MatchHero_Kit_*_[NM].png'))+[D/'MatchHero_Cloth_FabricAtlas.png']
assert len(paths)==25
rows=[]
def convert(p):
 out=p.with_suffix('.ktx');fmt='ASTC4x4' if 'Atlas' in p.name else 'ASTC8x8'
 result=subprocess.run([converter,'--compression_format='+fmt,'--compression_quality=Highest','--alpha_mode=Preserve','--channel_weighting=Linear','--gamma_in=1','--gamma_out=1','--flip_y','--wrap_mode=Clamp','--file_format=KTX','--output='+str(out),str(p)],capture_output=True,text=True)
 if result.returncode:raise RuntimeError(result.stdout+result.stderr)
 return {'source':str(p),'compressed':str(out),'format':fmt,'file_bytes':out.stat().st_size}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for r in pool.map(convert,paths):rows.append(r);print(r['compressed'],flush=True)
(W/'locker/compressed_maps.json').write_text(json.dumps(rows,indent=2))
