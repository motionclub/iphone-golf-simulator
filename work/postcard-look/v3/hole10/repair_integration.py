from pathlib import Path
lp=Path('blender/scripts/hole10_look.py');s=lp.read_text()
s=s.replace("float(texture_measure()['zone_lum_mean'])","float(texture_measure()['lum_mean'])").replace("float(texture_measure()['zone_lum_max'])","float(texture_measure()['lum_mean'])")
helper='''_UV_GLOW_CACHE = {}


def _face_glow(uv):
    """Actual decoded emission samples; intended window placement is not evidence."""
    if not _UV_GLOW_CACHE:
        import os
        path=os.path.join(os.path.dirname(__file__),'../../Unity/Assets/Resources/Course/Look/Basalt_E.png')
        im=bpy.data.images.load(os.path.abspath(path),check_existing=True)
        w,h=im.size;px=np.empty(w*h*4,np.float32);im.pixels.foreach_get(px)
        rng=np.random.default_rng(1010);r=rng.random((96,2));q=np.sqrt(r[:,0])
        _UV_GLOW_CACHE.update(G=px.reshape(h,w,4)[:,:,:3].max(2)>.2,w=w,h=h,bary=np.c_[1-q,q*(1-r[:,1]),q*r[:,1]])
    c=_UV_GLOW_CACHE;lit=total=0
    for i in range(1,len(uv)-1):
        pts=c['bary']@np.array([uv[0],uv[i],uv[i+1]])
        x=np.floor((pts[:,0]%1)*c['w']).astype(int)%c['w'];y=np.floor((pts[:,1]%1)*c['h']).astype(int)%c['h']
        lit+=int(c['G'][y,x].sum());total+=len(x)
    return lit/max(total,1)


'''
s=s.replace('def author_uv(',helper+'def author_uv(',1)
s=s.replace('            st["top_glow_free"] += 1','            st["top_glow_free"] += int(_face_glow(uv[l0:l0+n]) <= 2e-4)',1)
s=s.replace('        st["glow"] += 1 if glow else 0','        st["glow"] += int(_face_glow(uv[l0:l0+n]) > 0)',1)
lp.write_text(s)
bp=Path('blender/scripts/hole10_build.py');b=bp.read_text().replace('for st_ in list(blocked):\n    if st_.get',"for idx in sorted(blocked):\n    st_=(stacks+mesas)[idx]\n    if st_.get").replace("    idx=stacks.index(st_);old=st_['main'];old_name=old.name","    old=st_['main'];old_name=old.name")
b=b.replace("os.makedirs(os.path.join(os.path.dirname(D.out_dir),'checkpoints'),exist_ok=True)\nbpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(D.out_dir),'checkpoints','p4_unverified.blend'),relative_remap=False)","if D.out_dir:\n    os.makedirs(os.path.join(os.path.dirname(D.out_dir),'checkpoints'),exist_ok=True)\n    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(D.out_dir),'checkpoints','p4_unverified.blend'),relative_remap=False)")
bp.write_text(b)
