"""Before | after side-by-side clips from two filmed matches, aligned on the same event (the player's serve contact, or a player stroke contact
of the same kind), cut from film_game_1080p60.mp4 (1920x1080, 60 fps) and from the review composite (side + hand views).
usage: python3 make_compare.py <before run> <after run> <out dir> <label>
Writes <label>_serve.mp4, <label>_stroke.mp4 (1920x540 each: before left, after right, halves of the 1080p frames) and *_review.mp4."""
import csv, os, subprocess, sys

FF = '/Users/adnanyonathan/tai-films/ffmpeg'


def contacts(run, role='player'):
    """Real hits only (strings within 10 cm of the incoming ball at the contact, analyze.py swings)."""
    import json
    an = json.load(open(os.path.join(run, 'analysis.json')))
    key = next(k for k in an if k.endswith('_' + role))
    return [(s['tick'], s['kind'], s['clip']) for s in an[key]['swings'] if s['gap'] <= .10]


def pick(cs, kinds):
    for t, k, c in cs:
        if k in kinds and t > 120: return t, c
    return None, None


def cut(src, t, pre, post, out, crop=None):
    vf = f"crop={crop}," if crop else ''
    subprocess.run([FF, '-v', 'error', '-y', '-ss', f'{max(0, (t / 60) - pre):.3f}', '-t', f'{pre + post:.3f}', '-i', src,
                    '-vf', vf + 'scale=960:-2', '-an', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', out], check=True)


def pair(a, b, out, label_a, label_b):
    fc = (f"[0:v]drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='{label_a}':x=12:y=12:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.6[l];"
          f"[1:v]drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='{label_b}':x=12:y=12:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.6[r];[l][r]hstack=2")
    subprocess.run([FF, '-v', 'error', '-y', '-i', a, '-i', b, '-filter_complex', fc, '-an', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', out], check=True)


if __name__ == '__main__':
    before, after, outdir, label = sys.argv[1:5]
    os.makedirs(outdir, exist_ok=True); tmp = os.path.join(outdir, '_tmp'); os.makedirs(tmp, exist_ok=True)
    cb, ca = contacts(before), contacts(after)
    log = []
    for name, kinds, pre, post in (('serve', {'Serve'}, 2.2, 1.4), ('stroke', {'Drive', 'Running', 'LowPickup', 'Slice', 'Volley'}, 1.3, 1.2)):
        tb, clb = pick(cb, kinds); ta, cla = pick(ca, kinds)
        if tb is None or ta is None: log.append(f'{name}: not found (before {tb}, after {ta})'); continue
        for src, crop, suffix in (('film_game_1080p60.mp4', None, ''), ('film.mp4', '640:720:1280:0', '_side'), ('film.mp4', '960:360:0:720', '_hands')):
            pb, pa = os.path.join(tmp, f'b{suffix}.mp4'), os.path.join(tmp, f'a{suffix}.mp4')
            cut(os.path.join(before, src), tb, pre, post, pb, crop); cut(os.path.join(after, src), ta, pre, post, pa, crop)
            pair(pb, pa, os.path.join(outdir, f'{label}_{name}{suffix}.mp4'), f'BEFORE t{tb} {clb}', f'AFTER t{ta} {cla}')
        log.append(f'{name}: before tick {tb} ({clb}), after tick {ta} ({cla}), {pre}s before to {post}s after contact')
    open(os.path.join(outdir, f'{label}_compare.txt'), 'w').write('\n'.join(log) + '\n')
    print('\n'.join(log))
