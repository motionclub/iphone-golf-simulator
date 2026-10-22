"""smoke_validation.py: writes v2/tex/v4/smoke_model_validation.txt  (model vs the three real GolfLookSmoke runs, then v3 / v4 Smoke_C under the live LK_SMOKE spec and variants)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, smoke_model as sm
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
import importlib.util
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); gl = importlib.util.module_from_spec(spec); spec.loader.exec_module(gl)
L = []
rgba = sm.load_before()
L.append('MODEL vs REAL GolfLookSmoke runs (card over the Crater sky; real = v2/runtime/smoke_<run>.txt / logs; model = tools/smoke_model.py with the per-run fitted light)')
for name, r in sm.RUNS.items():
    G, A = sm.fit_run(name, rgba); sky = sm.load_rgb(name + '_smoke_card_without.rgb').astype(float)
    fr, al = sm.render(rgba, sky, r['tint'], r['gain'], r['selflight'], r['lit'], G=G, A=A); st = sm.stats(fr, sky); w = r['want']
    L.append('  %-4s tint %s gain %.2f selflight %.2f lit %.1f | model N %d median %.2f p99 %.1f step %.2f | real N %d median %.1f p99 %.1f step %.2f' % (
        name, r['tint'][:3], r['gain'], r['selflight'], r['lit'], st['N'], st['med'], st['p99'], st['grad'], w['N'], w['med'], w['p99'], w['grad']))
f, fS, res = sm.light_fit()
L.append('light model G_c = f_c (1 - Lit + Lit e) + fS_c Lit : f %s fS %s, max |residual of G| over the 3 runs %.4f (so settings that were never run can be predicted)' % (np.round(f, 3), np.round(fS, 3), abs(res).max()))
sky = sm.load_rgb('t4e_smoke_card_without.rgb').astype(float)
new = sm.read_png_np(os.path.join(ROOT, 'Unity/Assets/Resources/Course/Look/Smoke_C.png'))
sp = gl.smoke_spec()
L.append('')
L.append('LIVE LK_SMOKE (%s): tint %s AlphaGain %.2f Lit %.2f SelfLight %.2f EdgeFade %.2f' % (sp['src'], sp['tint'], sp['gain'], sp['lit'], sp['selflight'], sp['fade']))
L.append('%-34s | %-28s | %s' % ('setting', 'v3 (thin S curl)', 'v4 (installed)'))
rows = [('LIVE', sp['tint'], sp['gain'], sp['selflight'], sp['lit']), ('AlphaGain 1.10', sp['tint'], 1.10, sp['selflight'], sp['lit']), ('AlphaGain 1.20', sp['tint'], 1.20, sp['selflight'], sp['lit']),
        ('AlphaGain 1.30', sp['tint'], 1.30, sp['selflight'], sp['lit']), ('AlphaGain 1.40', sp['tint'], 1.40, sp['selflight'], sp['lit']),
        ('SelfLight 0.25', sp['tint'], sp['gain'], .25, sp['lit']), ('SelfLight 0.35', sp['tint'], sp['gain'], .35, sp['lit']), ('Lit 0.6', sp['tint'], sp['gain'], sp['selflight'], .6),
        ('tint white', (1, 1, 1, 1), sp['gain'], sp['selflight'], sp['lit']), ('tint (.62,.56,.56) gain 1.0 (10:50)', (.62, .56, .56, 1), 1.0, .05, .6)]
for lbl, tint, gain, e, lit in rows:
    cell = []
    for S in (rgba, new):
        G = sm.G_for(lit, e, f, fS)
        fr, al = sm.render(S, sky, tint, gain, e, lit, G=G, A=np.zeros(3), fade=sp['fade']); st = sm.stats(fr, sky)
        ok = .55 <= al.max() <= .72 and st['med'] >= 8 and 28 <= st['p99'] <= 90 and st['grad'] <= 6
        cell.append('a %.2f med %4.1f p99 %4.1f st %.1f %s' % (al.max(), st['med'], st['p99'], st['grad'], 'PASS' if ok else 'FAIL'))
    L.append('%-34s | %-28s | %s' % (lbl, cell[0], cell[1]))
L.append('(PASS/FAIL here = the runtime SMOKE_SOFT thresholds: effective alpha .55..0.72, median >= 8, p99 28..90, edge step <= 6; border alpha is 0 on both)')
open(os.path.join(HERE, '..', 'tex', 'v4', 'smoke_model_validation.txt'), 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
