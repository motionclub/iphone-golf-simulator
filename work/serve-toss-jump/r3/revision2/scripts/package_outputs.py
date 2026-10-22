"""Copy reviewable failed candidates and proof into the invoking chat's outputs folder."""
from pathlib import Path
import json,hashlib,os,shutil
W=Path(__file__).resolve().parents[1]
OUT=Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/find-x20/outputs/serve-toss-jump')
OUT.mkdir(parents=True,exist_ok=True)
def cp(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
for n in ['GATE_REPORT.md','NOT_INSTALLED.md','WATCH_SERVE.md','CANDIDATE_SHA256SUMS.txt']:
    cp(W/n,OUT/n)
for p in (W/'film').glob('serve_toss_jump_*.mp4'):
    assert p.stat().st_size>1000;cp(p,OUT/'film'/p.name)
for n in ['serve_keys.jpg','serve_reference_comparison.jpg','male_game_sheet.jpg','female_game_sheet.jpg']:
    cp(W/'proof'/n,OUT/'proof'/n)
for p in (W/'proof/movie_decode').glob('*'):cp(p,OUT/'proof/movie_decode'/p.name)
for p in (W/'proof/raw_keys').glob('*.png'):cp(p,OUT/'proof/raw_keys'/p.name)
for tag in ['alcaraz','federer','djokovic']:
    for phase in ['release','trophy','contact','landing']:
        n=f'{tag}_{phase}.jpg';cp(W/'refs'/n,OUT/'refs'/n)
for H in ['Male','Female']:
    cp(W/'export/fbx'/f'{H}_Serve.fbx',OUT/'candidates'/f'{H}_Serve.fbx')
    for suffix in ['fbx','fbx.meta']:
        n=f'{H}_Serve.{suffix}';cp(W/'rollback'/n,OUT/'rollback'/n)
cp(W/'rollback/SHA256SUMS.txt',OUT/'rollback/SHA256SUMS.txt')
for p in (W/'data').glob('*.json'):
    if p.name.startswith('right_hand_path'):continue
    cp(p,OUT/'data'/p.name)
for sex in ['male','female']:
    cp(W/'data'/f'gen_serve_{sex}.npz',OUT/'data'/f'gen_serve_{sex}.npz')
    cp(W/f'film_{sex}/trace.csv',OUT/'traces'/f'serve_toss_film_{sex}.csv')
cp(W/'proof/unity_feet/trace.csv',OUT/'traces/runtime_feet.csv')
cp(W/'proof/unity_feet/audit.txt',OUT/'traces/runtime_contacts.txt')
for p in (W/'work/hero-mainstay/data').glob('unity_bones_*_Serve.json'):cp(p,OUT/'traces'/p.name)
script_names=['serve_dj.py','run_dj.py','clipkit_dj.py','loco.py','smooth_right.py','bake_loco.py','rebuild_dj.sh','build_candidate.sh','export_fbx.py','penetrate_dj.py','trace_fbx.py','contact_scale_audit.py','check_gates.py','audit_and_report.py','render_sheet.py','read_trace.py','make_proof_dj.py','package_visuals.py','unity_run.sh','enc.swift','encode_full_game.py','reencode_all.sh','inspect_movies.swift','package_outputs.py']
for n in script_names:cp(W/'scripts'/n,OUT/'scripts'/n)
for p in (W/'logs').glob('*.log'):cp(p,OUT/'logs'/p.name)
prompt=W.parents[1]/'ArtDir/hero/base_lock/parallel_prompts/26_SERVE_TOSS_THEN_JUMP.txt'
cp(prompt,OUT/'26_SERVE_TOSS_THEN_JUMP.txt')
(OUT/'candidates/README.md').write_text('FAIL — NOT FOR INSTALLATION. Both FBXs are review candidates. The original installed assets remain in place. Read GATE_REPORT.md before using these files.\n')
rollback=f'''# Rollback backups

No rollback is needed: this candidate was not installed. Both installed FBXs and metas still match these backups.

Canonical backup folder: `{W/'rollback'}`.

For a later restoration, replace only the following four files in the original project, then check the SHA256 manifest. Preserve all unrelated project changes.

```zsh
serve_project="{W.parents[1]}"
serve_backup="{OUT/'rollback'}"
cp "$serve_backup/Male_Serve.fbx" "$serve_project/Unity/Assets/Characters/MatchHeroes/Male/Male_Serve.fbx"
cp "$serve_backup/Male_Serve.fbx.meta" "$serve_project/Unity/Assets/Characters/MatchHeroes/Male/Male_Serve.fbx.meta"
cp "$serve_backup/Female_Serve.fbx" "$serve_project/Unity/Assets/Characters/MatchHeroes/Female/Female_Serve.fbx"
cp "$serve_backup/Female_Serve.fbx.meta" "$serve_project/Unity/Assets/Characters/MatchHeroes/Female/Female_Serve.fbx.meta"
```
'''
(OUT/'rollback/README.md').write_text(rollback)
written=[]
for base,dirs,files in os.walk(W):
    if Path(base)==W:dirs[:]=[d for d in dirs if d!='UnityClone']
    dirs[:]=[d for d in dirs if d!='__pycache__']
    for n in files:written.append(str((Path(base)/n).relative_to(W)))
(OUT/'FILES_WRITTEN.txt').write_text(f'All project working files below are under {W}.\nUnityClone is excluded from this listing: it is an APFS clone with only the two candidate Serve FBXs explicitly staged by this task.\nNo production Serve FBX/meta changes.\n\n'+'\n'.join(sorted(written))+'\n')
link=lambda text,path:f'[{text}]({OUT/path})'
index=f'''# Serve toss + jump — FAIL

Original FBXs and metas remain installed. No commit. The two candidates fail the required gates; runtime proof omissions also count as FAIL.

{link('Full binary gate report','GATE_REPORT.md')} · {link('Reference observations','WATCH_SERVE.md')} · {link('Written working files','FILES_WRITTEN.txt')} · {link('Rollback backups and instructions','rollback/README.md')}

{link('Side-view key sheet','proof/serve_keys.jpg')} · {link('Reference comparison','proof/serve_reference_comparison.jpg')}

| Hero | Back + side | Half-speed side | Full game |
|---|---|---|---|
| Male | {link('Film','film/serve_toss_jump_male_views.mp4')} | {link('Film','film/serve_toss_jump_male_side_half_speed.mp4')} | {link('Film','film/serve_toss_jump_male_game_full.mp4')} |
| Female | {link('Film','film/serve_toss_jump_female_views.mp4')} | {link('Film','film/serve_toss_jump_female_side_half_speed.mp4')} | {link('Film','film/serve_toss_jump_female_game_full.mp4')} |

Front-view Unity films: 0/2, FAIL. Adnan eye reviews: 0, FAIL. Side/back films: 3.0 seconds; half-speed: 6.0 seconds; full game: 10.70/10.667 seconds. Six representative files each decoded successfully at three times.

`candidates/` holds the two failed FBXs; `rollback/` holds the four original assets. `data/`, `traces/`, and `logs/` preserve measurements and execution evidence. `scripts/` contains review copies: run the canonical project scripts under `{W/'scripts'}` where their input blends and Unity clone exist.
'''
(OUT/'INDEX.md').write_text(index)
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
(OUT/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(OUT)) for p in files)+'\n')
print('OUTPUT',OUT,'files',len(files),'bytes',sum(p.stat().st_size for p in files))
