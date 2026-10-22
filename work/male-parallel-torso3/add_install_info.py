import json, hashlib
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso3'); OUT = W / 'proof/male-torso-form3-checks.json'
d = json.load(open(OUT)); sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
ART = W.parent.parent / 'ArtDir/hero/base_lock'
inst = dict(
    brief_start_blend_sha256='1fe4d53b3bcb9cfaef885d64350150e323a1d726cc4d54cc305ea71e323119bb',
    artdir_moves_during_task=[dict(sha256='4287ba523218e89ae5a822483c322dc4cfa163c7af143ebcac11abbacea2db21', by='hands FORM2', time='06:52'), dict(sha256='b51cbb05d5135325b083462efc1b6e05d444a8a514c6c3b58547dad9564431ee', by='hands FORM3', time='07:53'), dict(sha256='2e8f973b892b1e1bfba541341fa5d21b07565ddcf1aa23c7f4e09d93596bee3f', by='legs+feet FORM2', time='08:00')],
    method='guarded vertex-index patch (work/male-parallel-torso3/install_form3.sh -> apply_form3.py -> verify_merge3.py -> export_fbx.py -> normals3.py), lock dir, backup, last-moment SHA recheck, atomic move; no whole-file overwrite',
    installed_over_blend_sha256=(W / 'export/installed_over_blend_sha.txt').read_text().strip(), installed_over_fbx_sha256=(W / 'export/installed_over_fbx_sha.txt').read_text().strip(),
    installed_blend_sha256=(W / 'export/installed_blend_sha.txt').read_text().strip(), installed_fbx_sha256=(W / 'export/installed_fbx_sha.txt').read_text().strip(),
    artdir_blend_sha256_now=sha(ART / 'blender/HeroBase_Male_Silhouette.blend'), artdir_fbx_sha256_now=sha(ART / 'unity_import/HeroBase_Male_Body.fbx'),
    staged_blend_sha256=sha(W / 'export/HeroBase_Male_Silhouette_form3.blend'), staged_fbx_sha256=sha(W / 'export/HeroBase_Male_Body_form3.fbx'),
    merge_verify=json.load(open(W / 'proof/male-torso-form3-install-verify.json')), normals_installed=json.load(open(W / 'proof/normals_form3_installed.json')), normals_staged=json.load(open(W / 'proof/normals_form3.json')),
    silhouette_whole_figure_installed_vs_preinstall=json.load(open(W / 'proof/installed_silhouette.json')),
    rollback=dict(blend='work/male-parallel-torso3/baseline/pre_install_form3_2e8f973b.blend', fbx='work/male-parallel-torso3/baseline/pre_install_form3_d40e9b55.fbx'),
    reapply='blender -b --factory-startup --python work/male-parallel-torso3/apply_form3.py -- <current.blend> <out.blend>',
    unity_project_copy_refreshed=False, unity_note='Unity/Assets/Characters/HeroBase/Models copy NOT refreshed (other chats still installing); HeroBaseMaleFormProof.cs ExpectedTriangles must be 66158 when it is')
d['install'] = inst
import sys, numpy as np
sys.path.insert(0, str(W)); import os; os.chdir(W)
from pmo_val import *
_V0 = np.load('data/V_base.npy'); _T = Torso(_V0); _T.make_basis(0.012, 0.009); _VL = Val(_T)
d['heldout_back_3q_panels']['RBF_asset_only'] = {k: round(v, 3) for k, v in _VL.score(np.load('data/V_K0.npy')).items()}
ho = d['heldout_back_3q_panels']
ka = ho['RBF_asset_only']
F1 = d['form_correlation_vs_plate']['dog_1.2_5.0']
d['validation_disclosure'] = dict(heldout_back_3q_FORM2=ho['FORM2'], heldout_back_3q_RBF_asset_only=ka, heldout_back_3q_FORM3=ho['FORM3'],
    statement=(f"The two held-out back 3/4 panels (validation only, never fitted; the AI plates are not fully 3D-consistent) correlate slightly LESS with FORM3 than with FORM2: left {ho['FORM2']['q3BL']:.3f} -> {ho['FORM3']['q3BL']:.3f}, right {ho['FORM2']['q3BR']:.3f} -> {ho['FORM3']['q3BR']:.3f}; "
               f"glute band {ho['FORM2']['q3BL_glute']:.2f}/{ho['FORM2']['q3BR_glute']:.2f} -> {ho['FORM3']['q3BL_glute']:.2f}/{ho['FORM3']['q3BR_glute']:.2f}, lumbar {ho['FORM2']['q3BL_lumbar']:.2f}/{ho['FORM2']['q3BR_lumbar']:.2f} -> {ho['FORM3']['q3BL_lumbar']:.2f}/{ho['FORM3']['q3BR_lumbar']:.2f}, upper back {ho['FORM2']['q3BL_upper']:.2f}/{ho['FORM2']['q3BR_upper']:.2f} -> {ho['FORM3']['q3BL_upper']:.2f}/{ho['FORM3']['q3BR_upper']:.2f}. "
               f"Decomposition: the frozen photometric fit alone gives {ka['q3BL']:.3f} (left) / {ka['q3BR']:.3f} (right); the requested buttock lobes + V-cleft take the glute band from {ka['q3BL_glute']:.2f}/{ka['q3BR_glute']:.2f} to {ho['FORM3']['q3BL_glute']:.2f}/{ho['FORM3']['q3BR_glute']:.2f}. "
               f"The plain front/back plates (primary authority) improve in all six regions (gate mean {F1['mean_FORM2']:.3f} -> {F1['mean_FORM3']:.3f}). Back-coefficient scaling 0.0/0.5/0.75/1.0 traded gate vs held-out almost linearly (held-out left 0.597/0.595/0.592/0.588), so the validated 1.0 asset was kept."))
json.dump(d, open(OUT, 'w'), indent=1); print('install block written; ArtDir now == installed:', inst['artdir_blend_sha256_now'] == inst['installed_blend_sha256'], inst['artdir_fbx_sha256_now'] == inst['installed_fbx_sha256'])
print('heldout FORM2', {k: ho['FORM2'][k] for k in ('q3BL', 'q3BR')}, 'FORM3', {k: ho['FORM3'][k] for k in ('q3BL', 'q3BR')})
