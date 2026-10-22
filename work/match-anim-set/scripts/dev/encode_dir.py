"""Blender: encode a directory of numbered PNGs to an H.264 mp4 (30 fps):  blender -b --factory-startup --python encode_dir.py -- <frames_dir> <out.mp4> <w> <h>
Used for the progress previews that live OUTSIDE the repo."""
import os, sys
import bpy
a = sys.argv[sys.argv.index('--') + 1:]
d, out, w, h = a[0], a[1], int(a[2]), int(a[3])
seq = sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith('.png'))
scn = bpy.context.scene
se = scn.sequence_editor_create() if scn.sequence_editor is None else scn.sequence_editor
coll = se.strips if hasattr(se, 'strips') else se.sequences
strip = coll.new_image('p', seq[0], channel=1, frame_start=1, fit_method='STRETCH')
for p in seq[1:]:
    strip.elements.append(os.path.basename(p))
r = scn.render
r.resolution_x, r.resolution_y = w - (w % 2), h - (h % 2)
r.resolution_percentage = 100
r.fps, r.fps_base = 30, 1.0
scn.frame_start, scn.frame_end = 1, len(seq)
r.use_sequencer = True
r.image_settings.media_type = 'VIDEO'
r.image_settings.file_format = 'FFMPEG'
r.ffmpeg.format = 'MPEG4'
r.ffmpeg.codec = 'H264'
r.ffmpeg.constant_rate_factor = 'HIGH'
r.ffmpeg.ffmpeg_preset = 'GOOD'
r.ffmpeg.audio_codec = 'NONE'
r.filepath = out
bpy.ops.render.render(animation=True)
print('ENCODE_DIR_DONE', out, len(seq))
