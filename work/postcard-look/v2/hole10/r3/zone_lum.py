import bpy, numpy as np
img = bpy.data.images.load("/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/Basalt_C.png")
w,h=img.size; px=np.empty(w*h*4,np.float32); img.pixels.foreach_get(px); C=px.reshape(h,w,4)[:,:,:3]
L=(0.2126*C[:,:,0]+0.7152*C[:,:,1]+0.0722*C[:,:,2])
ZONES = ((0.141, 0.211), (0.225, 0.350), (0.364, 0.435), (0.460, 0.525), (0.547, 0.705), (0.730, 0.795), (0.820, 0.920), (0.940, 1.110))
print("global mean lum", L.mean())
for a,b in ZONES:
    idx=[int(round(u*w))%w for u in np.linspace(a,b,max(2,int((b-a)*w)))]
    print(f"zone {a:.3f}-{b:.3f}: mean lum {L[:,idx].mean():.3f}")
