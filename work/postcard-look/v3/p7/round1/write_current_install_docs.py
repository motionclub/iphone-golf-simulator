"""Record exact current staging provenance for the unchanged required installer."""
from pathlib import Path
import hashlib,json
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');V=R/'work/postcard-look/v3';O=V/'p7/round1/install_doc_provenance'
assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for n in ('08','09','10'):
 folder=V/f'hole{n}';stage=folder/'stage';doc=folder/'INSTALL.md'
 old=doc.read_bytes();(O/f'INSTALL_hole{n}_before.md').write_bytes(old)
 text=f'# Hole{n}: current P7 round1 stage\n\nActual current stage files and build input lists. Original builder/verifier/native thresholds remain unchanged. Scoring is compared with the frozen baseline at exactly0m. Native installed proof is pending; this manifest is not an all-gates PASS. Older phase manifests are archived under p7/round1/install_doc_provenance.\n\n'
 for ext in ('blend','fbx'):
  p=stage/f'hole_{n}.{ext}';assert p.is_file();text+=f'{sha(p)}  {p.relative_to(R)}\n'
 text+='\nCurrent source/lib provenance: lib_sha_final.txt; all31 current Look PNGs: look_png_sha_final.txt. Stage file hashes: stage_sha256.txt. Only use actual v2/proof/install_holes.py pre then install through the unchanged heavy.sh. Copy blend and FBX only; installed FBX.meta must stay byte-identical.\n'
 doc.write_text(text);records.append(dict(hole=n,old_sha=hashlib.sha256(old).hexdigest(),new_sha=sha(doc),blend_sha=sha(stage/f'hole_{n}.blend'),fbx_sha=sha(stage/f'hole_{n}.fbx')))
(O/'receipt.json').write_text(json.dumps(records,indent=2)+'\n');print('six actual stage SHA lines written; older docs archived; no installer predicate change')
