"""Female reference-pack garments, using the existing independent pattern pipeline.

Run in Blender: --python build_garments.py -- tennis_top|golf_top|tennis_skirt|golf_skirt
Body data is a clearance / weight source, never the garment's source surface.
Source builders stay unchanged; the small fold changes below are asserted exactly.
"""
from pathlib import Path
import sys, types, json

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'clothing-v2' / 'py'
sys.path.insert(0, str(SOURCE))
sys.path.insert(0,str(ROOT))
import cv2io
cv2io.ROOT = str(ROOT)
cv2io.DUMP = str(ROOT / 'dump-current')


def source_module(name, replacements=()):
    path = SOURCE / (name + '.py')
    code = path.read_text()
    # Start an empty work file without resetting the user's preferences.
    code = code.replace('bpy.ops.wm.read_factory_settings(use_empty=True)',
                        'clear_work_scene()')
    for old, new in replacements:
        assert code.count(old) == 1, 'Source changed: ' + old
        code = code.replace(old, new)
    if name=='tank2':
        needle='    # ---- fields'
        assert code.count(needle)==1
        code=code.replace(needle,"    from drape import settle\n    settle(shell,hero)\n    pos,faces=polys(shell)\n    loops=boundary_loops_poly(faces);hem=min(loops,key=lambda l:pos[l,2].mean())\n"+needle)
    if name=='polo2':
        a=code.index('        flat = R.reshape(-1, 3); keep =',code.index('def make_sleeves_lofted'))
        b=code.index('        F = []; corners = []',a)
        code=code[:a]+"        from stitch import fair_sleeve\n        R=fair_sleeve(R,D,side)\n"+code[b:]
        needle="    panel = np.zeros(len(faces), np.int32); shirt.data.attributes['panel'].data.foreach_get('value', panel)"
        assert code.count(needle)==1
        code=code.replace(needle,"    from drape import settle\n    settle(shirt,hero,True)\n    pos,faces=polys(shirt)\n"+needle)
        needle="    parts = [shirt, col, pk, cuffs_ob] + bts + ((make_sleeves_lofted(D, fit, body, shirt) if D.get('lofted_sleeves') else make_sleeves(D, fit, body)) if D.get('tube_sleeves') else [])"
        assert code.count(needle)==1
        code=code.replace(needle,"    from stitch import sleeves_into_shell\n    sleeves=make_sleeves_lofted(D,fit,body,shirt)\n    sleeves_into_shell(shirt,sleeves,cuffs_ob,D['cuff']['w'])\n    parts=[shirt,col,pk,cuffs_ob]+bts")
        needle="        if o.name.startswith('Sleeve'): sm.use_even_offset = False; sm.nonmanifold_thickness_mode = 'CONSTRAINTS'"
        assert code.count(needle)==1
        code=code.replace(needle,needle+"\n        if o is shirt: sm.use_even_offset=False")
    module = types.ModuleType('soulful_' + name)
    module.__file__ = str(path)
    module.clear_work_scene = clear_work_scene
    exec(compile(code, str(path), 'exec'), module.__dict__)
    return module


def clear_work_scene():
    import bpy
    # The connected editor was explicitly moved to a fresh work file first.
    # Batch processes start with --factory-startup. Never reset user preferences.
    for obj in list(bpy.context.scene.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def tennis_top():
    m = source_module('tank2', [('body = G.Body(hero)', 'body = G.body_no_arms(G.Body(hero),.65)'),(
        '.0006 * np.sin(thv * 9 + z * 40) * smoothstep(1.2, 1.05, z)',
        '(.0080 * np.sin(thv * 4 + (z-1.05)*25) + .0045 * np.cos(thv * 3 - (z-1.05)*34)) * smoothstep(1.24, 1.09, z) * smoothstep(.985, 1.035, z)'
    ),(
        "    x, d = fit.push_clear_multi(body, pos, tri, gap=D['fit_gap'])\n    mv = np.linalg.norm(x - pos, axis=1)\n    print('FIT moved %d verts, max %.1f mm, min clearance %.1f mm' % (int((mv > 1e-4).sum()), mv.max() * 1000, d.min() * 1000))\n    pos = x\n",
        "    # Cut the openings before clearance fitting: removed arm panels must not inflate the surviving torso.\n"
    ),(
        "    pos, faces = polys(shell)\n    loops = boundary_loops_poly(faces)\n    hem = min(loops, key=lambda l: pos[l, 2].mean())\n    # Newton snap",
        "    pos, faces = polys(shell)\n    tri=np.array([t for f in faces for t in ([f[0],f[1],f[2]],[f[0],f[2],f[3]])])\n    x,d=fit.push_clear_multi(body,pos,tri,gap=D['fit_gap'],cap=.008)\n    mv=np.linalg.norm(x-pos,axis=1);j=int(mv.argmax());print('AFTER-CUT FIT max mm',float(mv.max()*1000),'from',pos[j],'to',x[j])\n    delta=x-pos;length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.012/np.maximum(length,1e-9))[:,None]\n    edge_free=1-smoothstep(1.205,1.255,pos[:,2])*(1-smoothstep(.045,.085,np.abs(pos[:,1])))\n    pos=pos+delta*edge_free[:,None]\n    loops = boundary_loops_poly(faces)\n    hem = min(loops, key=lambda l: pos[l, 2].mean())\n    # Newton snap"
    )])
    original = m.design_female_tank
    def design():
        d = original()
        d.update(rings=[(.975,.155,-.151,.112),(1.025,.154,-.157,.115),
                         (1.075,.149,-.158,.114),(1.130,.150,-.166,.112),
                         (1.190,.160,-.164,.111),(1.230,.157,-.156,.106),
                         (1.270,.148,-.141,.104),(1.310,.157,-.112,.102),
                         (1.345,.153,-.090,.096),(1.372,.119,-.075,.082),
                         (1.395,.074,-.060,.068)],
                 v_tip=1.267,v_slope=1.15,back_z=1.342,back_k=4.8,
                 arm_front=dict(c=(.187,-.048,1.338),s=(.080,.120,.125)),
                 arm_back=dict(c=(.187,.060,1.340),s=(.086,.122,.125)),
                 trim_w=.012,bind_w=.012,bind_lift=.0015,thick=.0028,
                 hem_band=.018,band_thick=.0028,fit_gap=.005,
                 strap_x=(.055,.127),strap_nz=.35,strap_blend=.004)
        return d
    m.DESIGNS['soulful'] = design
    m.build('MatchHero_Female', 'soulful', str(ROOT/'source/tennis_top.blend'))


def golf_top():
    cv2io.DUMP=str(ROOT/'dump-polo')
    m = source_module('polo2', [(
        '.0007 * drape * np.sin(thv * 7 + 1.3)',
        'drape * (.0055*np.sin(thv*5+(z-1.04)*19)+.0035*np.cos(thv*3-(z-1.04)*27))'
    ),('    pos = x\n    # a degenerate polygon',
        '    delta=x-pos;length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.012/np.maximum(length,1e-9))[:,None]\n'
        '    edge_free=1-smoothstep(1.19,1.25,pos[:,2])*(1-smoothstep(.045,.085,np.abs(pos[:,1])))\n'
        '    pos=pos+delta*edge_free[:,None]\n    # a degenerate polygon')])
    original = m.design_golf_female
    def design():
        d = original()
        d.update(rings=[('H',.974,.972,.150,.128),('L',1.040,1.040,.154,.135),
                         ('W',1.115,1.115,.151,.137),('A',1.190,1.190,.156,.128)],
                 M=dict(z=1.272,a=.155,b=.134),
                 S=dict(z_front=1.318,z_side=1.352,z_back=1.338,a=.169,b_front=.118,b_back=.130),
                 placket=dict(len=.087,w=.027,buttons=2),cuff=dict(w=.022),
                 collar=dict(stand=.015,fall=.060,point=.052,gap=.010,thick=.0028,splay=.45),
                 hem=dict(w=.025),armhole=dict(c=(.174,.004,1.317),s=(.067,.072,.064)),sleeve_len=.123,sleeve_r=(.064,.058),
                 arm_dir=(.422618,0,-.906308),sleeve_off=(.006,.004,0),
                 sleeve=dict(t=(.034,.080,.125),r=(.065,.060,.055)))
        return d
    m.DESIGNS['soulful'] = design
    sys.argv = ['build_garments.py','--','GolfKitHero_Female',str(ROOT/'source/golf_top.blend'),'soulful']
    m.main()


def skirt(golf):
    m = source_module('skirt2')
    original = m.design_female_tennis_skirt
    def design():
        d = original()
        d.update(pleats=18 if not golf else 20,depth=.022 if not golf else .021,
                 thick=.0026,wb_t=.0035,z_stitch=.921,z_free=.812,rows=16,
                 pleat_u=[0.0,.72,.79,.91,.97],under_role=0,band_role=0)
        if golf:
            d.update(name='soulful_golf',z_wb=(.952,.990),band_fabric=7,
                     band_role=0,under_role=0)
        return d
    m.DESIGNS['soulful'] = design
    hero = 'GolfKitHero_Female' if golf else 'MatchHero_Female'
    out = ROOT/'source'/('golf_skirt.blend' if golf else 'tennis_skirt.blend')
    m.build(hero,'soulful',str(ROOT.parent/'clothing-v2/shorts/female_undershorts.blend'),str(out))


if __name__ == '__main__':
    (ROOT/'source').mkdir(exist_ok=True)
    job = sys.argv[sys.argv.index('--')+1]
    {'tennis_top':tennis_top,'golf_top':golf_top,
     'tennis_skirt':lambda:skirt(False),'golf_skirt':lambda:skirt(True)}[job]()
