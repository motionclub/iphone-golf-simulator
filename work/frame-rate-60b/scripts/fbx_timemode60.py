"""FRAME_RATE_60B: mark an FBX whose keys are already on a 1/60 s grid as a 60 fps file.

The approved rev-37 emotes (work/emote-fluid) carry 60 Hz keys but a 30 fps header (GlobalSettings TimeMode 6),
and Unity's Resample Curves re-samples a take at the file's frame rate, so the game played them at 30 Hz.
This rewrites only TimeMode (-> 3, eFrames60) and CustomFrameRate (-> 60); every key, curve, mesh and ID is
written back as read (the same binary FBX round trip emote-fluid's fluid_pass.py uses).

    Blender -b --factory-startup --python fbx_timemode60.py -- <in.fbx> <out.fbx> [...pairs]
"""
import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fbx_curves as FB
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
for src, dst in zip(args[::2], args[1::2]):
    root, version, models, channels = FB.read(src)
    gs = next(e for e in root.elems if e.id == b'GlobalSettings')
    props = next(e for e in gs.elems if e.id == b'Properties70')
    seen = {}
    for p in props.elems:
        if p.props and p.props[0] == b'TimeMode': seen['TimeMode'] = p.props[4]; p.props[4] = 3
        if p.props and p.props[0] == b'CustomFrameRate': seen['CustomFrameRate'] = p.props[4]; p.props[4] = 60.0
    assert seen.get('TimeMode') in (6, 3), (src, seen)
    # every key is on the 1/60 s grid (else a 60 fps header would not make it play at 60)
    off = 0
    for k, c in channels.items():
        t = np.array(FB.data(c, b'KeyTime'), np.int64)
        r = t % 769769300
        off += int(np.count_nonzero((r > 4) & (r < 769769300 - 4)))      # (1-tick rounding is on the grid)
    assert off == 0, (src, off, "keys off the 60 Hz grid")
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    FB.write(dst, root, version)
    # read back: the same curves, key for key
    root2, _v, _m, ch2 = FB.read(dst)
    for k, c in channels.items():
        assert list(FB.data(c, b'KeyTime')) == list(FB.data(ch2[k], b'KeyTime')) and list(FB.data(c, b'KeyValueFloat')) == list(FB.data(ch2[k], b'KeyValueFloat')), k
    print(f"TIMEMODE60 {os.path.basename(src)} {seen} -> TimeMode 3 / 60.0; {len(channels)} curves identical; sha {hashlib.sha256(open(dst,'rb').read()).hexdigest()[:12]}")
