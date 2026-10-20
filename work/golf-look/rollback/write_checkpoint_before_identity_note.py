"""Write an honest G0 WAITING checkpoint and portable review deliverables."""
from pathlib import Path
import hashlib, json, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont

R = Path(__file__).resolve().parents[3]
W = R / 'work/golf-look'
OUT = Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/find-4/outputs/golf-look')
OUT.mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 15)
for sex in ['Male', 'Female']:
    sheet=Image.new('RGB',(2400,1480),(22,26,30));draw=ImageDraw.Draw(sheet)
    draw.text((20,10),f'{sex} golf draft — isolated Blender geometry, G6/G7 FAIL; not Unity lighting / identity proof',font=font,fill='white')
    for j,name in enumerate(['front','quarter','side','back','polo','headwear','shoes','glove']):
        im=Image.open(W/f'proof/{sex}_{name}.png').convert('RGB');im.thumbnail((600,680))
        x=j%4*600;y=45+j//4*715;sheet.paste(im,(x+(600-im.width)//2,y))
        draw.text((x+12,y+680),name+' / DRAFT',font=font,fill=(225,228,231))
    sheet.save(W/f'proof/{sex}_DRAFT_SHEET.png')
    swing=Image.new('RGB',(2400,1700),(22,26,30));sd=ImageDraw.Draw(swing)
    sd.text((15,10),f'{sex} / proof-only retarget; G7 FAIL. V4 has no finger animation. Not Unity gameplay.',font=font,fill='white')
    for i,hand in enumerate(['RH','LH']):
        for j,state in enumerate(['ReadyIdle','Top','Impact','Finish']):
            im=Image.open(W/f'proof/{sex}_{hand}_{state}.png').convert('RGB')
            swing.paste(im,(j*600,50+i*820));sd.text((j*600+15,835+i*820),f'{hand} {state} / DRAFT',font=font,fill='white')
    swing.save(W/f'proof/{sex}_SWING_DRAFT_SHEET.png')

builds = [json.loads((W/f'data/build_{s}.json').read_text()) for s in ['Male','Female']]
courses = json.loads((W/'data/course_mesh_audit.json').read_text())
fabric = json.loads((W/'data/fabric_prototypes.json').read_text())
shaders = json.loads((W/'data/shader_inventory.json').read_text())
deform = [json.loads((W/f'data/deform_draft_{s}.json').read_text()) for s in ['Male','Female']]
dm=[]
for d in deform:
    for n in sorted({n for r in d['poses'] for n in r['pieces']}):
        rows=[(r,r['pieces'][n]) for r in d['poses'] if n in r['pieces']]
        pose,measure=max(rows,key=lambda x:x[1].get('candidate_poke_max_mm') or 0)
        dm.append(f'| {d["sex"]} | {n} | {measure["covered_body_samples"]:,} | {measure.get("candidate_poke_max_mm",0):.3f} | {pose["handedness"]} {pose["state"]} | {max(m.get("lost_home_correspondences",0) for _,m in rows)} |')
drift=max(m['rigid_head_drift_max_mm'] for d in deform for r in d['poses'] for m in r['headwear'].values())
gate_rows=[
    ('G0 PRECONDITIONS','WAITING','HEAD 2225264c; v3/PHASE_STATUS.md says P8 NOT RUN; 29 active, draft GARMENT_SPEC exists but no completion report. No dependency-owned file edited.'),
    ('G1 GOLFER_LIT','FAIL','No semantic-masked Unity skin clip %, polo L* or trim L* on holes 7–10. Historical V4 numbers in AUDIT are not new evidence.'),
    ('G2 ONE_LIGHT','FAIL','Shared hero profile not installed; no measured shadow-angle comparison or tee contact-shadow proof.'),
    ('G3 GROUND_READS','FAIL','No new Ground/Rock shader installed or per-hole masked phone measures/worst-cliff sheets. v3 thresholds .12 fairway / .08 green upper bounds are recorded.'),
    ('G4 NO_SHIMMER','FAIL','No BEFORE/AFTER 3-second 1170×2532 camera films; temporal residuals unmeasured.'),
    ('G5 COURSE_FROZEN','FAIL','Seven guards PASS in logs/guards_before.txt and guards_after.txt; final 15 freeze and complete top-surface/collision proof still pending. This task changed no course geometry.'),
    ('G6 GOLF_KIT_READS','FAIL','Male_DRAFT_SHEET.png / Female_DRAFT_SHEET.png show drafts. Shoe saddle boundaries are cut geometry. Collar/vent/cuff/pockets, sole/welt crops, skort inner shorts/pleats and perforation detail need completion; required labelled G6 crops have not all passed.'),
    ('G7 DEFORM','FAIL',f'Both heroes: 8 proof poses each, RH/LH ReadyIdle and V4 top/impact/finish, in *_SWING_DRAFT_SHEET.png. Body and 53-bone rig unchanged, max 4 weights. Sampled candidates/lost correspondences are listed below; full collision and grip verification incomplete. Rigid headwear drift max {drift:.6f} mm. No gameplay motion installed.'),
    ('G8 RECOLOUR + LOCKER','FAIL','No Unity colour grid or locker payload/sport-swap/parity capture. Catalog/preview currently owned by concurrent work.'),
    ('G9 ONE_SYSTEM','FAIL','No shader fork introduced. Shared lighting/fabric includes and registered golf IDs not implemented; active GARMENT_SPEC not edited.'),
    ('G10 TENNIS_UNCHANGED','FAIL','No post-29 tennis BEFORE/AFTER hero-region diff. Shader/kit files continue changing in the owner chat.'),
    ('G11 BUDGET','FAIL',f'Draft kit tris {builds[0]["visible_kit_tris"]:,} male / {builds[1]["visible_kit_tris"]:,} female, within pre-29 allowances; final N/M plan {fabric["planned_per_hero"]["MB"]:.3f} MB/hero before shared atlas. Actual GPU draws, UV density, resident ASTC budget, iPhone timing and Metal stats/log all unmeasured.'),
    ('G12 EYE','FAIL','Two Blender review sheets and fabric prototype sheet exist; required Unity BEFORE/AFTER sheets, films, locker views and Adnan eye approval are pending.')]
gate_json=[dict(gate=g,status=s,evidence=e) for g,s,e in gate_rows]
(W/'data/gates_checkpoint.json').write_text(json.dumps(gate_json,indent=2)+'\n')
proofs=[]
for p in sorted((W/'proof').glob('*.png')):
    with Image.open(p) as im:size=list(im.size)
    proofs.append(dict(path=str(p),pixels=size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),kind='isolated Blender draft; not Unity evidence'))
(W/'data/proof_manifest.json').write_text(json.dumps(proofs,indent=2)+'\n')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
gates='\n'.join(f'- **GATE: {g} {s}** — {e}' for g,s,e in gate_rows)
ct='\n'.join(f'| {c["hole"]} | {c["source_mesh_triangles"]:,} | {c["renderer_material_slots_upper_bound"]:,} | Stable during read | UNMEASURED |' for c in courses)
st='\n'.join(f'- `{s["shader"]}` — `{R/s["file"]}`' for s in shaders)
pp='\n'.join('- `'+p['path']+'` ('+'×'.join(map(str,p['pixels']))+')' for p in proofs)
text=f'''# Golf shaders and kit — G0 WAITING checkpoint

Project: `{R}`. Full supplied prompt read and executed within its section 0 precondition boundary. Goal Mode remains incomplete. No commit. HEAD observed: `{head}`.

The prompt requires: “If 15 or 29 is still running: do ONLY the phases that touch none of their files ... Then stop at GATE PRECONDITIONS: WAITING.” This checkpoint follows that instruction. It does not claim all gates pass.

## Gate results

{gates}

## Ready and remaining work

P0: protected input snapshots; read-only course Blender/material/texture/shader audit; guards 7/7; proof-tool source prepared. Exact Unity BEFORE captures and runtime metrics are pending. The proof rig at `{W/'proof-tools/GolfLookProofRig.cs'}` is UNCOMPILED and uninstalled; it supports 1170×2532 static specimens but its aerial is provisional and must use 15's delivered camera matrix. No Unity/xcodebuild process was launched.

P1: construction references and garment/surface design ready in `{R/'ArtDir/hero/kit/golf/GOLF_KIT_DESIGN.md'}`. Source product/pattern notes have links; no branding copied.

P4: isolated separate golf shells and accessories built over frozen copies of the existing rigs. Male: {builds[0]['visible_kit_tris']:,} visible-kit tris; female: {builds[1]['visible_kit_tris']:,}. These include the active lead-hand glove; the alternate glove switches in the LH proof. Both use 53 existing bones with no new socket; body/rig fingerprints pass. Copies retain existing garment weights, gloves and trousers retain source body-vertex weight lineage including pelvis/Spine blends. Source tops were verified as closed shells (`source_shell_topology.json`); extra solidification was removed and ease moves both walls outward together. Skort clearance was increased. Shoe saddle panels are cut overlay geometry. V4 top/impact/finish are retargeted in separate proof-only blends; both handednesses and mirrored ReadyIdle are rendered. V4 has no fingers, so finger poses are ReadyIdle-derived and cannot certify grip. Final construction and swing deformation gates still FAIL.

P5: seven deterministic fabric normal/relief prototypes in `{W/'maps/fabric_prototypes'}`. These are not garment AO/N/M bakes. Numeric IDs, M packing, density and residency are not installed. 29's in-progress spec was read and snapshotted; its A=ID/5 encoding and 2048² tennis tops must be reconciled with golf additions without changing tennis bytes/arithmetic.

P2/P3/P6/P7: blocked by the dependency release. Shared profiles, GolfGround/GolfRock, runtime golf kit, locker, iPhone/Metal budgets and final proof/eye loop remain required. GolferView's V4 gameplay swing remains installed. Two-paragraph handoff: `{W/'NEXT_SWING.md'}`.

## Budgets before and draft after

| Hole | BEFORE source mesh triangles | BEFORE material-slot upper bound | AFTER course | Actual draws / timing |
|---|---:|---:|---|---|
{ct}

Slot counts are not GPU draw-call measurements; source mesh totals are not visible triangles. They do not certify G11. `v3/THRESHOLDS.md` keeps the tighter 250k source cap as well as the 300k visible-hole/250 tee-draw requirements. Course source files were not changed by this task.

| Hero | Frozen pre-29 tennis kit | Golf draft | Allowance (tennis+4,000) |
|---|---:|---:|---:|
| Male | 91,226 | {builds[0]['visible_kit_tris']:,} | 95,226 |
| Female | 81,038 | {builds[1]['visible_kit_tris']:,} | 85,038 |

The planned final ten N/M maps at ASTC 6×6 including mips allocate {fabric['planned_per_hero']['bytes']:,} bytes = {fabric['planned_per_hero']['MB']:.3f} MB per hero **before shared atlas**, with 1024² polo/bottom/shared shoes and 512² glove/headwear. This is a reservation, not measured residency or approved density. Re-audit budgets against 29's delivered kit and spec. Shader ALU/fetches, stripped variants, iPhone-class frame time and Metal compile log: UNMEASURED.

## Shader list

New: none installed. Changed: none by this task. Removed: none. Existing names (exact pragma/include inventory is `{W/'data/shader_inventory.json'}`):

{st}

GolfGround, GolfRock, HeroLighting and HeroCloth remain planned. No copied character/cloth shader is shipping from this preparation.

## Isolated deformation diagnostics

| Hero | Garment | Covered bind samples | Max candidate poke mm | Worst sampled pose | Lost home correspondences (max) |
|---|---|---:|---:|---|---:|
{chr(10).join(dm)}

These are bind-ray/body-vertex/home-triangle diagnostics, not exhaustive surface collision. Coverage requires a two-wall shell within 35 mm at bind; outer loose regions, already invalid bind fit, edges and triangle interiors can be missed. Candidate values are warnings to investigate, not a certified maximum penetration. Lost correspondences fail the diagnostic instead of being converted to zero. Glove edge ratios and exact pose rows are in `{W/'data/deform_draft_Male.json'}` and `{W/'data/deform_draft_Female.json'}`. Headwear drift from the initial rigid Head attachment is <= {drift:.6f} mm, but bind clearance and hair collision remain unverified. G7 stays FAIL.

## Review evidence paths

{pp}

Films: none. Required gameplay/aerial/tee Unity BEFORE/AFTER sheets: none. Locker golf tab: none. Tennis diff images: none. Those gaps are failed gates, not omitted evidence.

## Files, rollback and staging

All task-owned additions are under `{W}` plus the new golf design path. No existing course, character, shader, Swift or pipeline source was replaced. Original live assets were read only. Frozen source copies and hashes live in inputs/. Rollback scope is `{W/'rollback/README.md'}`; draft iteration backups are in rollback/. Do not undo concurrently changed TennisCloth, MatchHeroLook or CharacterModelPreview.

Explicit stage list: `{W/'data/staged_paths.txt'}`. Preparatory scripts, metadata, maps, draft models, review images, proof-tool source and design are staged; frozen input binaries, scratch caches and unrelated files are excluded. No commit, no runtime installation, no shared asset ownership taken.

## Improve next

Finish garment construction, per-garment high/low bakes and swing retarget proof; measure penetrations instead of assuming skin transfer passes. Use fresh tennis baselines after 29 finishes. Capture actual semantic masks under each hole's sun; preserve exact tennis math while adding a golf shoulder/profile. Measure Metal cost and phone temporal shimmer before claiming a ground-shader performance win. Exact dependency and resume state: `{W/'RESUME.md'}`.
'''
(W/'REPORT.md').write_text(text)
for rel in ['REPORT.md','AUDIT.md','design/GOLF_KIT_DESIGN.md','NEXT_SWING.md','proof/Male_DRAFT_SHEET.png','proof/Female_DRAFT_SHEET.png','proof/FABRIC_PROTOTYPES.png','proof/Male_SWING_DRAFT_SHEET.png','proof/Female_SWING_DRAFT_SHEET.png','export/Golf_Male_Draft.blend','export/Golf_Female_Draft.blend','export/Golf_Male_SwingProof.blend','export/Golf_Female_SwingProof.blend']:
    source=W/rel;shutil.copy2(source,OUT/source.name)
print('WAITING checkpoint:',OUT/'REPORT.md')
