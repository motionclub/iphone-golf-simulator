"""Re-open the review MP4s and prove they decode: container metadata (size, fps, frame count) and real decoded frames through Blender's sequencer
(PNG stills at the first / quarter / middle / three-quarter / last frame; each must contain a picture and the frames must differ from each other).

  blender -b --factory-startup --python check_video.py -- <hero> [<hero>]       (male / female)   writes data/verify_video.json"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy

from common import *

heroes = args_after_dashes()
exp = {t: sum(json.load(open(f'{DATA}/bake_{t}.json'))['clips'][c]['frames'] for c in CLIPS) for t in heroes}
res = {}
os.makedirs(PROOF + '/_check', exist_ok=True)
for t in heroes:
    vp = f'{PROOF}/Review_{HERO[t]["label"]}.mp4'
    name = os.path.basename(vp)
    r = dict(path=vp, exists=os.path.exists(vp), bytes=os.path.getsize(vp) if os.path.exists(vp) else 0, expected_frames=exp[t])
    try:
        with open(vp, 'rb') as f:
            r['ftyp_header'] = b'ftyp' in f.read(64)
        clip = bpy.data.movieclips.load(vp)
        r['size'] = list(clip.size)
        r['fps'] = float(clip.fps) if hasattr(clip, 'fps') else None
        r['frame_duration'] = int(clip.frame_duration)
        r['duration_s'] = r['frame_duration'] / (r['fps'] or 30.0)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene
        se = sc.sequence_editor_create()
        coll = se.strips if hasattr(se, 'strips') else se.sequences
        coll.new_movie(name, vp, channel=1, frame_start=1)
        sc.render.resolution_x, sc.render.resolution_y = r['size']
        sc.render.resolution_percentage = 100
        sc.render.use_sequencer = True
        sc.render.image_settings.media_type = 'IMAGE'
        sc.render.image_settings.file_format = 'PNG'
        sc.frame_start, sc.frame_end = 1, r['frame_duration']
        D = r['frame_duration']
        picks = [1, max(2, D // 4), max(3, D // 2), max(4, (3 * D) // 4), D]
        arrs, stills = [], []
        for k in picks:
            sc.frame_set(k)
            p = f'{PROOF}/_check/{t}_{k:04d}.png'
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True)
            im = bpy.data.images.load(p)
            px = np.array(im.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
            arrs.append(px)
            stills.append(dict(frame=k, mean=float(px.mean()), std=float(px.std())))
            bpy.data.images.remove(im)
        diffs = [float(np.abs(arrs[0] - a).mean()) for a in arrs[1:]]
        r['decoded_frames'] = stills
        r['mean_abs_diff_vs_first'] = diffs
        r['frames_equal'] = r['frame_duration'] == exp[t]
        r['fps_ok'] = abs((r['fps'] or 0) - 30.0) < 1e-3
        r['decode_ok'] = bool(r['frames_equal'] and r['fps_ok'] and all(s['std'] > 0.02 for s in stills) and all(d > 0.002 for d in diffs))
    except Exception as e:                        # noqa
        r['error'] = repr(e)
        r['decode_ok'] = False
    res[t] = r
    print('VIDEO_CHECK', t, {k: v for k, v in r.items() if k in ('frame_duration', 'expected_frames', 'fps', 'size', 'decode_ok', 'error', 'mean_abs_diff_vs_first')})
json.dump(res, open(f'{DATA}/verify_video.json', 'w'), indent=1)
print('VIDEO_CHECK_DONE')
