from pathlib import Path
import shutil,subprocess,concurrent.futures,json,struct,math
from PIL import Image
W=Path(__file__).resolve().parents[1];D=W/'locker/assets';D.mkdir(parents=True,exist_ok=True)
converter='/Applications/Xcode.app/Contents/Developer/usr/bin/TextureConverter'
for p in (W/'inputs/post_cloth/GolfArcade/Unity/CharacterAssets').iterdir():
 if p.is_file() and not (D/p.name).exists():shutil.copy2(p,D/p.name)
def convert(p):
 png=D/('MatchHero_'+p.name);shutil.copy2(p,png);out=png.with_suffix('.ktx');fmt='ASTC4x4' if 'Atlas' in p.name else 'ASTC8x8'
 cmd=[converter,'--compression_format='+fmt,'--compression_quality=Highest','--alpha_mode=Preserve','--channel_weighting=Linear','--gamma_in=1','--gamma_out=1','--flip_y','--wrap_mode=Clamp','--file_format=KTX','--output='+str(out),str(png)]
 result=subprocess.run(cmd,capture_output=True,text=True)
 if result.returncode:raise RuntimeError(result.stdout+result.stderr)
 blob=out.read_bytes();assert blob[:12]==b'\xabKTX 11\xbb\r\n\x1a\n';header=struct.unpack('<13I',blob[12:64]);size=Image.open(p).size[0];block=4 if 'Atlas' in p.name else 8
 full=sum(math.ceil(max(1,size>>i)/block)**2*16 for i in range(int(math.log2(size))+1))
 return dict(map=p.name,format=fmt,file_bytes=len(blob),width=header[6],height=header[7],mip_levels=header[11],full_mip_bytes=full)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 rows=list(pool.map(convert,sorted((W/'maps').glob('*.png'))))
atlas=sum(r['full_mip_bytes'] for r in rows if 'Atlas' in r['map']);legacy=16*sum(math.ceil(max(1,256>>i)/4)**2 for i in range(9))
totals={sex:sum(r['full_mip_bytes'] for r in rows if sex in r['map'])+atlas+legacy for sex in ['Male','Female']}
out=dict(maps=rows,per_hero_full_mip_bytes=totals,legacy_weave_included_bytes=legacy,status='PASS' if max(totals.values())<=6000000 else 'FAIL')
(W/'data/golf_texture_budget.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2),flush=True)
