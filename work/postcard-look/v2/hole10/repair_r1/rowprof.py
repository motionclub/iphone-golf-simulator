import sys, numpy as np, bpy
args = sys.argv[sys.argv.index("--") + 1:]
for f in args:
    im = bpy.data.images.load(f, check_existing=False); w, h = im.size
    px = np.empty(w*h*4, np.float32); im.pixels.foreach_get(px)
    a = px.reshape(h, w, 4)[::-1, :, :3]*255
    L = 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
    st = np.abs(np.diff(L, axis=0)).mean(axis=1)
    print(f.split('/')[-2], "rows 575..605:", [round(float(st[y-1]),1) for y in range(575,606,2)])
    print("   mean 450-560:", round(float(st[449:560].mean()),2), " mean 620-740:", round(float(st[619:740].mean()),2), " row590:", round(float(st[589]),2))
