"""foldtab5.py: fold-line table vs x for a pelvis variant: python3 tools/foldtab5.py NAME '{overrides of PP5_final}'   (prints zmin / onset / depth for x .02-.135 vs the plate + envelope dev)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, foldx5 as fx
XS = (0.02, 0.03, 0.045, 0.06, 0.075, 0.09, 0.105, 0.12, 0.135)
def table(co, tag):
    img, _ = fx.render(co)
    pl = [fx.fold_stats(fx.profile_plate(x)) for x in XS]; md = [fx.fold_stats(fx.profile_model(img, x)) for x in XS]
    print(f'[{tag}] zmin  ' + ' '.join(f"{m['zmin']:.3f}" for m in md) + '   plate ' + ' '.join(f"{p['zmin']:.3f}" for p in pl))
    print(f'[{tag}] onset ' + ' '.join(f"{m['onset']:.3f}" for m in md) + '   plate ' + ' '.join(f"{p['onset']:.3f}" for p in pl))
    print(f'[{tag}] depth ' + ' '.join(f"{m['depth']:5.0f}" for m in md) + '   plate ' + ' '.join(f"{p['depth']:5.0f}" for p in pl))
    err = np.sqrt(np.mean([(m['zmin'] - p['zmin']) ** 2 for m, p in zip(md, pl)])) * 100
    print(f'[{tag}] zmin rms err vs plate {err:.2f} cm; smile rise (x.045->.12) model {100*(md[7]["zmin"]-md[2]["zmin"]):+.1f} cm plate {100*(pl[7]["zmin"]-pl[2]["zmin"]):+.1f} cm')
if __name__ == '__main__':
    name = sys.argv[1]; over = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    co, PP = fx.build(over)
    np.save(f'{fx.HERE}/data/_variants/co5p_{name}.npy', co); json.dump(PP, open(f'{fx.HERE}/data/PP5_{name}.json', 'w'), indent=1)
    table(co, name); fx.report(name, co)
