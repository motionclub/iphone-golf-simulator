"""Root-owned finite P7 texture/library checks; run inside actual heavy.sh."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
V=R/'work/postcard-look/v3'; O=V/'p7/round1/shared_checks'
assert not O.exists(), 'fresh output required'
O.mkdir(); B='/Applications/Blender.app/Contents/MacOS/Blender'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
look=R/'Unity/Assets/Resources/Course/Look'
before={p.name:sha(p) for p in sorted(look.glob('*.png'))}; assert len(before)==31
results=[]
jobs=[('basalt_generate',[sys.executable,str(R/'blender/scripts/golf_look_textures.py'),'--out',str(look),'--only','Basalt','--periodicity']),
      ('all_original_texture_gates',[sys.executable,str(R/'blender/scripts/golf_look_textures.py'),'--out',str(look),'--gates-only']),
      ('postcard_look_smoke',[B,'-b','--factory-startup','--python',str(R/'blender/scripts/postcard_look_smoke.py'),'--','--out',str(O/'ground'),'--no-render']),
      ('postcard_props_smoke',[B,'-b','--factory-startup','--python',str(R/'blender/scripts/postcard_props_smoke.py'),'--','--out-root',str(O/'props'),'--no-render','--no-holes'])]
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
for label,argv in jobs:
    with (O/(label+'.log')).open('xb') as f:rc=subprocess.call(argv,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT)
    results.append(dict(label=label,exit=rc,log=str(O/(label+'.log')),argv=argv))
    print(label,'exit',rc,flush=True)
after={p.name:sha(p) for p in sorted(look.glob('*.png'))}
changed=[n for n in before if before[n]!=after.get(n)]
allowed={'Basalt_C.png','Basalt_N.png','Basalt_E.png'}
assert set(after)==set(before) and set(changed)<=allowed, 'unexpected PNG mutation'
payload=dict(results=results,png_before=before,png_after=after,changed_png=changed,other28_identical=all(before[n]==after[n] for n in before if n not in allowed))
(O/'result.json').write_text(json.dumps(payload,indent=2)+'\n')
print('changed PNGs',changed,'other28 identical',payload['other28_identical'])
sys.exit(0 if all(j['exit']==0 for j in results) else 1)
