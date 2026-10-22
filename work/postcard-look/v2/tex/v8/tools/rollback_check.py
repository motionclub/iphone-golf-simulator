"""rollback_check.py <outdir>: applies every documented v8 rollback and regenerates Lava / Fairway / Green / Smoke into <outdir> (Blender python); compare with v8/before/*.png (= v7)."""
import sys, os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
g.LAVA_P.update(g.LAVA_P_V7); g.LAVA_ENC['quantile'] = 0
g.FAIRWAY_P['micro'] = 0.0; g.FAIRWAY_P['micro_h'] = 0.0; g.GREEN_P['micro'] = 0.0; g.GREEN_P['micro_h'] = 0.0
g.SMOKE_P.update(g.SMOKE_P_V7)
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
g.main(['--out', out, '--only', 'Lava,Fairway,Green,Smoke'])
