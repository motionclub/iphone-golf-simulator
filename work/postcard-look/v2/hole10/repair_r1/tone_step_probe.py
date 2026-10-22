import sys, numpy as np, bpy
args = sys.argv[sys.argv.index("--") + 1:]
for f in args:
    im = bpy.data.images.load(f, check_existing=False); w, h = im.size
    px = np.empty(w*h*4, np.float32); im.pixels.foreach_get(px)
    a = px.reshape(h, w, 4)[::-1, :, :3]*255
    L = 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
    rm = L.mean(axis=1)
    # local tone step across a row: mean over 5 rows below minus mean over 5 rows above, with a 2-row guard
    ys = np.arange(300, 1400)
    D = np.array([rm[y+3:y+8].mean() - rm[y-8:y-3].mean() for y in ys])
    # texture energy step: ratio of mean |gx| 
    gx = np.abs(np.diff(L, axis=1)).mean(axis=1)
    G = np.array([np.log(gx[y+3:y+13].mean() / gx[y-13:y-3].mean()) for y in ys])
    k = 590 - 300
    print(f.split('/')[-2], "tone step at 590: %.2f (|D| median %.2f, p95 %.2f, rank %d/%d)" % (D[k], np.median(np.abs(D)), np.percentile(np.abs(D), 95), int((np.abs(D) > abs(D[k])).sum()), len(D)),
          "| log texture-energy step at 590: %.3f (|G| median %.3f p95 %.3f)" % (G[k], np.median(np.abs(G)), np.percentile(np.abs(G), 95)))
