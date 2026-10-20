from pathlib import Path
import json,subprocess,hashlib,importlib.util
W=Path(__file__).resolve().parents[1];R=W.parents[1]
def index():
 out=subprocess.check_output(['git','ls-files','--stage','-z'],cwd=R)
 return {row.split(b'\t',1)[1].decode():row.split(b'\t',1)[0].decode() for row in out.split(b'\0') if row}
rows=json.loads((W/'changed_files.json').read_text());projects=['GolfArcade.xcodeproj/project.pbxproj','GolfArcadeUnity.xcodeproj/project.pbxproj']
paths={r['path'] for r in rows if r['path'] not in projects}
paths.update(str(p.relative_to(R)) for p in (R/'ArtDir/screenshots/cloth_overhaul').rglob('*') if p.is_file())
paths.update(str(p.relative_to(R)) for p in (R/'ArtDir/hero/kit/refs').rglob('*') if p.is_file());paths.add('ArtDir/hero/kit/GARMENT_SPEC.md')
for folder in ['maps','rollback','sheets','compile_final','locker/src','locker/proof']:
 paths.update(str(p.relative_to(R)) for p in (W/folder).rglob('*') if p.is_file())
for p in (W/'scripts').iterdir():
 if p.is_file() and p.name not in ['add_pockets.py','write_shader.py','debug_skin.py']:paths.add(str(p.relative_to(R)))
for p in (W/'export').iterdir():
 if p.suffix in ['.blend','.fbx','.npz','.json']:paths.add(str(p.relative_to(R)))
for p in W.iterdir():
 if p.is_file() and p.suffix in ['.md','.json','.txt'] and p.name not in ['pocket_geometry.json','signing_identities.txt','signing_certificate_subject.txt','git_status_before.txt','candidate_proof_manifest.json','final_proof_manifest.json','bake_stats.json','bake_stats_before_stitches.json','bake_stats_full_previous.json','protected_external_changes.json'] and not p.name.startswith(('air_tt','binary_perf','metal_','texturetool','texture_converter')):paths.add(str(p.relative_to(R)))
for n in ['main.swift','DUMMY_POLO.json','spec_reuse_proof.json','compressed_maps.json','installed_files.json','packing_export_verification.json','budget.json']:
 paths.add(str((W/'locker'/n).relative_to(R)))
paths.add(str((W/'locker/packed/packing_report.json').relative_to(R)))
for p in (W/'logs').glob('*'):
 if p.is_file() and any(v in p.name for v in ['exact_final','packed','final','shimmer_before2','locker_export.txt','check_fbx','prefab','rig','shoes_before_clear']):paths.add(str(p.relative_to(R)))
for variant in ['before_verified','after_final']:
 for n in ['audit.json','srp_batcher.txt','palette_uniforms.json']:
  p=W/variant/n
  if p.exists():paths.add(str(p.relative_to(R)))
for variant in ['ios_before','ios_after']:
 for n in ['build_summary.txt','compiled_metal.txt']:
  p=W/variant/n
  if p.exists():paths.add(str(p.relative_to(R)))
paths.update(str((W/n).relative_to(R)) for n in ['staged_paths.txt','index_preservation.json','production_manifest.json','rollback/README.md'])
allpaths=sorted(paths|set(projects));(W/'staged_paths.txt').write_text('\n'.join(allpaths)+'\n')
(W/'rollback/README.md').write_text('Restore only cloth-owned paths listed in ../changed_files.json after checking subsequent edits. First snapshot preserves original files; p5_after_lobby preserves completed lobby work. p5_unpacked preserves the intermediate cloth-only export. NEW files have no prior counterpart. Do not bulk reset the repository.\n')
manifest={r['path']:hashlib.sha256((R/r['path']).read_bytes()).hexdigest() for r in rows};(W/'production_manifest.json').write_text(json.dumps(manifest,indent=2))
before=index();(W/'index_before_stage.json').write_text(json.dumps(before,indent=2))
(W/'index_preservation.json').write_text('{}')
subprocess.run(['git','add','--pathspec-from-file=-','--pathspec-file-nul'],input=b'\0'.join(x.encode() for x in sorted(paths))+b'\0',cwd=R,check=True)
spec=importlib.util.spec_from_file_location('locker_install',W/'scripts/install_locker.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
for rel in projects:
 current=subprocess.check_output(['git','show',':'+rel],cwd=R,text=True)
 if not all(n in current for n in mod.names):current=mod.patch_project(current)
 target=W/'locker'/(Path(rel).parent.name+'.index.pbxproj');target.write_text(current)
 blob=subprocess.check_output(['git','hash-object','-w',str(target)],cwd=R,text=True).strip()
 subprocess.run(['git','update-index','--cacheinfo','100644,'+blob+','+rel],cwd=R,check=True)
after=index();unexpected=[p for p,v in before.items() if p not in allpaths and after.get(p)!=v]+[p for p in after if p not in before and p not in allpaths]
assert not unexpected,unexpected
summary={'other_index_entries_unchanged':True,'other_entries_checked':len([p for p in before if p not in allpaths]),'owned_staged_paths':len(allpaths),'owned_stage_bytes':sum((R/p).stat().st_size for p in allpaths),'projects':'25 KTX resource additions applied to each existing index version; unrelated working-tree hunks excluded','no_commit':True}
(W/'index_preservation.json').write_text(json.dumps(summary,indent=2));subprocess.run(['git','add','work/cloth-overhaul/index_preservation.json'],cwd=R,check=True)
print(json.dumps(summary,indent=2))
