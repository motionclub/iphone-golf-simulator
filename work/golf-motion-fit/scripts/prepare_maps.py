from pathlib import Path
import json,math,shutil,subprocess,struct,concurrent.futures
W=Path(__file__).resolve().parents[1];N=W/'native';N.mkdir(exist_ok=True);U=W/'candidate/Unity/Assets/Resources/Golf/Maps';U.mkdir(parents=True,exist_ok=True)
stats=json.loads((W/'bake_stats.json').read_text())
for sex in ['Male','Female']:
 p=W/f'export/material_profiles_{sex}.json';profiles=json.loads(p.read_text());lookup={s['piece'][4:]:s for s in stats if s['sex']==sex}
 for b in profiles:
  s=lookup[b['atlas']];tile=.029 if b['atlas']=='Bottom' else .024 if b['atlas'].startswith(('Shoe','Glove')) else .020 if b['atlas'].startswith('Sock') else .026
  b['tileMetres']=tile;b['weaveTile']=s['size']/s['pxPerCm']/100/tile
 p.write_text(json.dumps(profiles,indent=2)+'\n')
def convert(p):
 shutil.copy2(p,U/p.name);png=N/('MatchHero_'+p.name);shutil.copy2(p,png);ktx=png.with_suffix('.ktx');fmt='ASTC4x4' if 'Atlas' in p.name else 'ASTC8x8'
 cmd=['/Applications/Xcode.app/Contents/Developer/usr/bin/TextureConverter','--compression_format='+fmt,'--compression_quality=Highest','--alpha_mode=Preserve','--channel_weighting=Linear','--gamma_in=1','--gamma_out=1','--flip_y','--wrap_mode=Clamp','--file_format=KTX','--output='+str(ktx),str(png)]
 result=subprocess.run(cmd,capture_output=True,text=True)
 if result.returncode:raise RuntimeError(result.stdout+result.stderr)
 blob=ktx.read_bytes();h=struct.unpack('<13I',blob[12:64]);width,height=h[6:8];block=4 if 'Atlas' in p.name else 8;full=sum(math.ceil(max(1,width>>i)/block)*math.ceil(max(1,height>>i)/block)*16 for i in range(int(math.log2(max(width,height)))+1))
 return dict(map=p.name,format=fmt,full_mip_bytes=full,fileBytes=len(blob),mips=h[11])
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(convert,sorted((W/'maps').glob('*.png'))))
atlas=sum(x['full_mip_bytes'] for x in rows if 'Atlas' in x['map']);totals={s:sum(x['full_mip_bytes'] for x in rows if s in x['map'])+atlas for s in ['Male','Female']}
report=dict(maps=rows,resident_bytes_per_hero=totals,status='PASS' if max(totals.values())<=6000000 else 'FAIL');(W/'data/map_budget.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(totals),flush=True)
