"""posed.py [key=value ...]: the hero with the arms hanging (armio.swing, 32 deg, the game's own skin weights), measured the way
the tier 1 turnaround is read: width across both shoulders, and the arm's width seen from the front and from the side at
heights down the arm. Base, 11-11 build, the first muscle model (v3) and the current one. `rows()` is used by board.py."""
import sys, numpy as np, armio, armfield as af
B = armio.bones("export/male_torso/bones.json"); sk = {n: armio.read_skin(f"export/male_skin/{n}.skin") for n in ("Body", "Kit_Top")}
mL = armio.membership(sk['Body'], sk['Body'], "Left"); mR = armio.membership(sk['Body'], sk['Body'], "Right")
TARGET = dict(name="tier 1 target", polo=58.5, up=11.3, el=11.3, fo=11.6, wr=7.0, upd=12.8, fod=11.5)   # read off the turnaround at 3.27 px per cm; upper arm = at the cuff
def load(tag): return {n: armio.read(f"export/{tag}/{n}.bin") for n in ("Body", "Kit_Top")}
def down(parts):
    out = {}
    for n, m in parts.items():
        if n not in sk: continue
        p = armio.swing(m['pos'], sk[n], sk['Body'], B["LeftUpperArm"], "Left", 32); out[n] = armio.swing(p, sk[n], sk['Body'], B["RightUpperArm"], "Right", -32)
    return out
def fitted(parts, P=None):
    """Arms + chest with the tops refitted (fit.dress)."""
    import fit
    return fit.dress(parts, B, mL, mR, P)

def muscles(parts, P, chest=None):
    body = dict(parts['Body'], armLeft=mL, armRight=mR)
    TL = af.field_tables(body, B, 'Left', P)
    mb = dict(body, pos=body['pos'] * [-1, 1, 1], armLeft=mR, armRight=mL, w=np.concatenate([body['w'][:, 4:], body['w'][:, :4]], 1))
    Bm = {k.replace("Left", "#").replace("Right", "Left").replace("#", "Right"): v * [-1, 1, 1] for k, v in B.items()}
    TR = af.field_tables(mb, Bm, 'Left', P)
    out = {n: dict(m, pos=af.apply(af.apply(m['pos'], B, TL, 'Left', cloth=n != 'Body'), B, TR, 'Right', cloth=n != 'Body')) for n, m in parts.items()}
    if chest is not None:
        import torsofield as tf
        TT = tf.tables(body, chest if isinstance(chest, dict) else tf.P)
        for n, m in parts.items(): out[n]['pos'] = out[n]['pos'] + tf.apply(m['pos'], TT, cloth=n != 'Body', arms=(B, TL, TR)) - m['pos']
    return out
def joint(name):
    one = dict(names=[name], parents=["LeftUpperArm"], idx=np.zeros((1, 4), int), w=np.array([[1., 0, 0, 0]]))
    return armio.swing(B[name][None], one, sk['Body'], B["LeftUpperArm"], "Left", 32)[0]
def measure(name, parts):
    d = down(parts); b, t = d['Body'], d['Kit_Top']
    sh = lambda p: np.ptp(p[(p[:, 1] > 1.10) & (p[:, 1] < 1.40)][:, 0]) * 100
    arm = b[mL > .6]; S, E, W = B["LeftUpperArm"], joint("LeftLowerArm"), joint("LeftHand")
    def ext(a, c, f, ax):
        y1, y0 = a[1] + (c[1] - a[1]) * f, a[1] + (c[1] - a[1]) * (f + .1); s = arm[(arm[:, 1] >= y0) & (arm[:, 1] < y1)]
        return np.ptp(s[:, ax]) * 100 if len(s) > 20 else float('nan')
    g = {(n, round(u, 2)): gg for n, u, gg, fb, ac in af.girths(parts['Body']['pos'], parts['Body']['w'], B)}
    return dict(name=name, bare=sh(b), polo=sh(t), head=np.ptp(b[b[:, 1] > b[:, 1].max() - .12][:, 0]) * 100,
                up=max(ext(S, E, f, 0) for f in (.45, .55, .65)), upd=max(ext(S, E, f, 2) for f in (.45, .55, .65)),
                el=min(ext(S, E, .9, 0), ext(E, W, 0, 0)), fo=max(ext(E, W, f, 0) for f in (.1, .2, .3)), fod=max(ext(E, W, f, 2) for f in (.1, .2, .3)),
                wr=min(ext(E, W, f, 0) for f in (.8, .9)),
                gup=max(v for (n, u), v in g.items() if n == 'upper' and .4 <= u <= .7) * 100, gfo=max(v for (n, u), v in g.items() if n == 'fore' and .1 <= u <= .5) * 100)
def rows(P=None, every=True):
    out = []
    if every: out += [measure("base", load("male_build0")), measure("11-11 build", load("male_build1")), measure("first muscle model", muscles(load("male_torso"), af.V3))]
    return out + [measure("muscle model", muscles(load("male_torso"), P or af.P))]
if __name__ == "__main__":
    P = dict(af.P); over = [a for a in sys.argv[1:] if "=" in a]
    for a in over: k, v = a.split("="); P[k] = float(v)
    for r in rows(P, every=not over):
        print(f"{r['name']:18} shoulders bare {r['bare']:5.1f}, in the polo {r['polo']:5.1f} cm ({r['polo']/r['head']:.2f} heads)  front: upper {r['up']:4.1f} elbow {r['el']:4.1f} forearm {r['fo']:4.1f} wrist {r['wr']:4.1f}  side: upper {r['upd']:4.1f} forearm {r['fod']:4.1f}  girth: upper {r['gup']:4.1f} forearm {r['gfo']:4.1f}  upper/forearm front {r['up']/r['fo']:.2f} girth {r['gup']/r['gfo']:.2f}")
    t = TARGET; print(f"{t['name']:18} shoulders in the polo 58-59 cm (2.82 heads)  front: upper {t['up']} (at the cuff) elbow {t['el']} forearm {t['fo']} wrist {t['wr']}  side: upper {t['upd']} (above the elbow) forearm {t['fod']}")
