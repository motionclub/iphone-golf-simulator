import bpy, os, sys
sc = bpy.context.scene
print('engines', [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items])
r = sc.render
try:
    r.image_settings.media_type = 'VIDEO'
    print('media_type ok')
except Exception as e:
    print('media_type err', e)
try:
    r.image_settings.file_format = 'FFMPEG'
    r.ffmpeg.format = 'MPEG4'
    r.ffmpeg.codec = 'H264'
    r.ffmpeg.constant_rate_factor = 'HIGH'
    r.ffmpeg.ffmpeg_preset = 'GOOD'
    r.ffmpeg.audio_codec = 'NONE'
    print('ffmpeg settings ok', r.image_settings.file_format, r.ffmpeg.format, r.ffmpeg.codec)
except Exception as e:
    print('ffmpeg err', e)
print([i.identifier for i in r.ffmpeg.bl_rna.properties['codec'].enum_items])
print([i.identifier for i in r.ffmpeg.bl_rna.properties['format'].enum_items])
