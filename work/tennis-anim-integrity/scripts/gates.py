"""Chat 4 binary gates from a clip dump (clipcheck.json) and match telemetry (analysis.json of telemetry / filmed runs).
usage: python3 gates.py --dump <dump dir> --runs <run dir> [<run dir> ...] [--out gates.json]
Thresholds are the brief's (work/delegation-2026-10-17/04_tennis_animation_integrity.md); the hand-shape thresholds are stated below."""
import json, sys, os
import numpy as np

STROKES = ['Forehand', 'ForehandOpen', 'ForehandWide', 'ForehandShort', 'Backhand', 'BackhandWide', 'SliceApproach', 'Return',
           'VolleyForehand', 'VolleyBackhand', 'Overhead', 'SplitToForehand', 'SplitToBackhand', 'RecoverCenter']
GRIP_MIN = 100.0        # racket-hand MCP+PIP flexion (deg, mean of index..little) while the hand is on the racket: wrapped round the handle
FREE_MIN, FREE_MAX = 35.0, 140.0   # off hand, off the racket: below = flat paddle, above = clenched (allowed only as a fist in emotes)


def arg(name, many=False):
    if name not in sys.argv: return [] if many else None
    i = sys.argv.index(name) + 1
    if not many: return sys.argv[i]
    out = []
    while i < len(sys.argv) and not sys.argv[i].startswith('--'): out.append(sys.argv[i]); i += 1
    return out


def clip_gates(cc):
    rows = []
    for sex, clips in cc.items():
        live = {k.split(':', 1)[1]: e for k, e in clips.items() if k.startswith('live:')}
        for name, e in sorted(live.items()):
            base = name.split('_', 1)[1]
            r = dict(sex=sex, clip=name)
            r['RATE'] = e['frameRate'] >= 59.9 and 0 < e['minKeyDt'] <= 1 / 60 + 1e-4 and e['maxKeyDt'] <= 1 / 60 + 1e-4
            r['rate'] = f"{e['frameRate']:.0f} fps, keys {e['minKeyDt']*1000:.1f}-{e['maxKeyDt']*1000:.1f} ms"
            am = e.get('approvedMax')
            if am is not None and base.replace('ArmCorrected', '') in STROKES:
                worst = max(am['RightHand'], am['LeftHand'], am['tip'])
                r['APPROVED'] = worst <= .015; r['approved'] = f"max {worst*100:.1f} cm (R {am['RightHand']*100:.1f} L {am['LeftHand']*100:.1f} tip {am['tip']*100:.1f})"
            r['GRIP_clip'] = e['rightCurlPolished'][0] >= GRIP_MIN; r['grip'] = f"polished curl min {e['rightCurlPolished'][0]:.0f} deg"
            rows.append(r)
    return rows


def run_gates(an):
    out = {}
    for key, v in an.items():
        if key == 'events': continue
        sw = [s for s in v['swings'] if s['gap'] < .7]
        con = [s for s in sw if s['kind'] != 'Serve']
        c_ok = [s for s in sw if s['gap'] <= .03 and s['speedAtContact'] >= .7 * s['peak'] and abs(s['peakOffsetFrames']) <= 2]
        serves = v['serves']
        sv = [s.get('activeRate') if s.get('activeRate') is not None else s['visibleRate'] for s in serves]
        plants = v['feet']
        slide_bad = [f for f in plants if f['slide'] > .015]
        out[key] = dict(
            CONTACT=len(sw) > 0 and len(c_ok) == len(sw), contact=f"{len(c_ok)}/{len(sw)} hits: strings <= 3 cm, speed >= 70% of peak, peak within 2 frames",
            SERVE_LIVE=len(sv) > 0 and all(.9 <= x <= 1.1 for x in sv), serve=f"serve swing rate (trophy hold release -> contact) {', '.join(f'{x:.2f}' for x in sv)}",
            FEET_SLIDE=len(slide_bad) == 0, feet=f"{len(slide_bad)}/{len(plants)} plants slide > 1.5 cm",
            FEET_DIP=(v.get('soleMax') if v.get('soleMax') is not None else v['sinkMax']) <= .005, dip=f"max sole dip {(v.get('soleMax') if v.get('soleMax') is not None else v['sinkMax'])*1000:.1f} mm ({'shoe sole points' if v.get('soleMax') is not None else 'joint sink only'})",
            NO_POP=len([p for p in v['pops'] if p['transition']]) == 0, pops=f"{len([p for p in v['pops'] if p['transition']])} transition spikes > 2x clip peak",
        )
    return out


if __name__ == '__main__':
    res = {}
    d = arg('--dump')
    if d: res['clips'] = clip_gates(json.load(open(os.path.join(d, 'clipcheck.json'))))
    for r in arg('--runs', True): res[os.path.basename(r.rstrip('/'))] = run_gates(json.load(open(os.path.join(r, 'analysis.json'))))
    json.dump(res, open(arg('--out') or 'gates.json', 'w'), indent=1)
    print(json.dumps(res, indent=1)[:6000])
