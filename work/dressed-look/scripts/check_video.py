"""Re-open the turntable MP4s and prove they decode: container metadata (size, fps, frame count) + real decoded frames through Blender's
video sequencer, written to PNG; the frames must contain a picture and must differ from each other (the character turns).

  blender -b --factory-startup --python check_video.py -- <out.json> <video1.mp4> [video2.mp4 ...]"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_common import *

a_ = args_after_dashes()
out_json, videos = a_[0], a_[1:]
res = {}
for vp in videos:
    name = os.path.basename(vp)
    r = dict(path=vp, exists=os.path.exists(vp), bytes=os.path.getsize(vp) if os.path.exists(vp) else 0)
    try:
        with open(vp, 'rb') as f:
            head = f.read(64)
        r['ftyp_header'] = b'ftyp' in head
        clip = bpy.data.movieclips.load(vp)
        r['size'] = list(clip.size)
        r['fps'] = float(clip.fps) if hasattr(clip, 'fps') else None
        r['frame_duration'] = int(clip.frame_duration)
        fps = r['fps'] or 24.0
        r['duration_s'] = r['frame_duration'] / fps
        # decode real frames through the sequencer
        sc = bpy.data.scenes.new('vcheck_' + name)
        bpy.context.window.scene = sc if bpy.context.window else bpy.context.scene
        seq_owner = sc
        if seq_owner.sequence_editor is None:
            seq_owner.sequence_editor_create()
        se = seq_owner.sequence_editor
        coll = se.strips if hasattr(se, 'strips') else se.sequences
        new_movie = coll.new_movie
        strip = new_movie(name, vp, channel=1, frame_start=1)
        sc.render.resolution_x, sc.render.resolution_y = r['size']
        sc.render.resolution_percentage = 100
        sc.render.use_sequencer = True
        sc.render.image_settings.media_type = 'IMAGE'
        sc.render.image_settings.file_format = 'PNG'
        sc.frame_start, sc.frame_end = 1, r['frame_duration']
        stills = []
        picks = [1, max(2, r['frame_duration'] // 4), max(3, r['frame_duration'] // 2), max(4, (3 * r['frame_duration']) // 4), r['frame_duration']]
        arrs = []
        for k in picks:
            sc.frame_set(k)
            p = f'{RAW}/video_check_{name}_{k:04d}.png'
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True, scene=sc.name)
            im = bpy.data.images.load(p)
            px = np.array(im.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
            arrs.append(px)
            stills.append(dict(frame=k, path=p, mean=float(px.mean()), std=float(px.std())))
            bpy.data.images.remove(im)
        diffs = [float(np.abs(arrs[0] - a).mean()) for a in arrs[1:]]       # frames at 1/4, 1/2, 3/4 and the last one against the first
        r['decoded_frames'] = stills
        r['mean_abs_diff_vs_first'] = diffs
        r['moves_at_quarter_points'] = bool(all(d > 0.004 for d in diffs[:3]))                 # the figure is turning
        r['loop_closes'] = bool(diffs[3] < 0.5 * min(diffs[:3]))                                # a 360 degree loop: the last frame is back near the first
        r['decode_ok'] = bool(all(s['std'] > 0.02 for s in stills) and r['moves_at_quarter_points'] and r['loop_closes'])
    except Exception as e:                        # noqa
        r['error'] = repr(e)
        r['decode_ok'] = False
    res[name] = r
json.dump(res, open(out_json, 'w'), indent=1)
print('VIDEO_CHECK_DONE', {k: (v.get('frame_duration'), v.get('size'), round(v.get('duration_s', 0), 2), v.get('decode_ok')) for k, v in res.items()})
