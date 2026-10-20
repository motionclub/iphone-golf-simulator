from pathlib import Path
import concurrent.futures, hashlib, json, subprocess, sys
root=Path(__file__).parent/'vendor'
tasks=[]
for ident in sys.argv[1:]:
    meta=json.loads((root/(ident+'.json')).read_text())
    asset=meta['blend']['2k']['blend']
    dest=root/ident
    tasks.append((dest/Path(asset['url']).name,asset))
    tasks.extend((dest/name,item) for name,item in asset.get('include',{}).items())
def fetch(row):
    path,item=row
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists() or hashlib.md5(path.read_bytes()).hexdigest()!=item['md5']:
        subprocess.run(['curl','-L','--fail','--silent','--show-error','--retry','2',
                        '--user-agent','CodexVisualOverhaul/1.0 (local asset evaluation)',
                        item['url'],'-o',str(path)],check=True)
    if hashlib.md5(path.read_bytes()).hexdigest()!=item['md5']:
        raise ValueError('Checksum mismatch: '+str(path))
    print(path.name+' verified '+str(path.stat().st_size),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(fetch,tasks))
