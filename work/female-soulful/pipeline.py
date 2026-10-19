"""Route the existing garment tools to this pass's isolated inputs and outputs.

Blender -b source/<file>.blend --python pipeline.py -- export|render|maps|cover|correctives <tool args...>
"""
from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'clothing-v2/py'
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(ROOT))

import cv2io
cv2io.ROOT = str(ROOT)
cv2io.DUMP = str(ROOT/('dump-current' if all((ROOT/'dump-current'/h/'hero.json').exists() for h in ['MatchHero_Female','GolfKitHero_Female']) else 'dump'))
args = sys.argv[sys.argv.index('--')+1:]
mode, args = args[0], args[1:]
if args and args[0]=="GolfKitHero_Female" and (ROOT/"dump-polo/GolfKitHero_Female/hero.json").exists():cv2io.DUMP=str(ROOT/"dump-polo")
tool = {'export':'export2','polo_export':'polo2_export','render':'look',
        'maps':'maps','cover':'cover','correctives':'correctives','poke':'poke','posed':'posed'}[mode]
sys.argv = ['pipeline.py','--'] + args
path = SOURCE/(tool+'.py')
code = path.read_text()
if mode in ('export','polo_export'):
    import bpy
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector
    from polo2 import apply_modifier
    piece = args[1] if mode == 'export' else 'Kit_Top'
    ob = bpy.data.objects[piece]
    mesh = ob.data
    mesh.calc_loop_triangles()
    original = BVHTree.FromPolygons([v.co.copy() for v in mesh.vertices],
                                  [list(t.vertices) for t in mesh.loop_triangles],all_triangles=True)
    if mode=='polo_export':
        maximum=max((mesh.vertices[e.vertices[0]].co-mesh.vertices[e.vertices[1]].co).length for e in mesh.edges)
        print('POLO source maximum edge metres',maximum,flush=True)
        if maximum>.10:raise RuntimeError('Polo thickness or seam produced a stretched face')
    count = len(mesh.loop_triangles)
    if count > 20000:
        dec = ob.modifiers.new('Mobile garment budget','DECIMATE')
        dec.ratio = 19800/count
        dec.use_collapse_triangulate = True
        apply_modifier(ob,dec)
    mesh.calc_loop_triangles()
    deviations = [original.find_nearest(v.co)[3] for v in mesh.vertices]
    report = dict(piece=piece,sourceTriangles=count,triangles=len(mesh.loop_triangles),
                  maxVertexDeviationMeters=max(deviations),construction='independent pattern cage')
    (ROOT/'proof/geometry').mkdir(parents=True,exist_ok=True)
    (ROOT/'proof/geometry'/(args[0]+'_'+piece+'.json')).write_text(json.dumps(report,indent=2))
    print('BUDGET',report)
if mode=='export' and args[0]=='MatchHero_Female' and args[1]=='Kit_Top':
    needle="    W = finalize.restricted_weights(body, pos, piece)"
    replacement=needle+'''
    # Sleeveless cloth belongs to the torso; the skin's ArmBlend palette would
    # stretch the armhole across a lifted arm. This is the existing tank's
    # torso-binding policy, applied offline before fitting garment correctives.
    oldW=W.copy();W[:]=0
    chest=body.bones.index('Chest');upper=body.bones.index('UpperChest')
    t=G.smoothstep(1.14,1.32,pos[:,2]) if hasattr(G,'smoothstep') else np.clip((pos[:,2]-1.14)/.18,0,1)
    t=t*t*(3-2*t)
    def real(index,weights):
        name=body.bones[index]
        if name.endswith(('UpperArm','LowerArm','Hand')):
            W[:,chest]+=weights*(1-t);W[:,upper]+=weights*t
        else:W[:,index]+=weights
    for index,name in enumerate(body.bones):
        weights=oldW[:,index]
        if name.startswith('ArmBlend_'):
            a=name.split('_');blend=int(a[3])/8
            real(int(a[1]),weights*(1-blend));real(int(a[2]),weights*blend)
        else:real(index,weights)
'''
    assert code.count(needle)==1
    code=code.replace(needle,replacement)
if mode=='export' and args[1]=='Kit_Bottom':
    needle='    W = finalize.restricted_weights(body, pos, piece)'
    assert code.count(needle)==1
    code=code.replace(needle,needle+'\n    liner_weights=W.copy()')
    needle="    W = finalize.smooth_weights(W, tri, int(kv.get('wsmooth', os.environ.get('CV2_WSMOOTH', '6'))))"
    assert code.count(needle)==1
    code=code.replace(needle,needle+'''
    # A fitted liner follows skin accurately; smoothing is for loose cloth.
    liner=np.zeros(len(pos),bool);liner[tri[kind0==18].ravel()]=True
    W[liner]=liner_weights[liner]''')
if mode=='polo_export':
    needle='bi, bw = G.prune(W, 4)'
    replacement='''# The loose lower torso can be closer to a hanging arm than to the ribcage.
# Transfer that region from torso skin only; proximity must not bind the waist to an arm.
old_names,old_blends=finalize.TOP_BONES,finalize.TOP_BLENDS
finalize.TOP_BONES=['Hips','Spine','Chest','UpperChest','Neck']
finalize.TOP_BLENDS=[]
torsoW=finalize.restricted_weights(body,pos,'Kit_Top')
finalize.TOP_BONES,finalize.TOP_BLENDS=old_names,old_blends
# Stable inverse skinning for the body-driven garment pose shapes: each sleeve
# uses its upper arm; the sewn root uses the torso. The morph reconstructs the
# continuous cloth surface without singular half-turn matrix blends.
W=torsoW.copy()
is_torso=np.zeros(len(pos),bool);is_torso[tri[np.isin(panel,[FRONT,BACK])].ravel()]=True
for side in (-1,1):
    mask=np.isin(vpan,[SLEEVE_L,SLEEVE_R,CUFF])&(pos[:,0]*side>0)&~is_torso
    W[mask]=0;W[mask,body.bones.index('LeftUpperArm' if side<0 else 'RightUpperArm')]=1
bi, bw = G.prune(W, 4)'''
    assert code.count(needle)==1
    code=code.replace(needle,replacement)
if mode=='correctives':
    if args[0]=='GolfKitHero_Female':raise RuntimeError('Use wrap_correctives.py for the posed sleeve sewing surface')
    # Full joint frames retain sleeve twist that segment-direction dots omit.
    old='    return np.array(f)'
    new='    from pose_features import features as full_features\n    return full_features(hero,bones_world)'
    assert code.count(old)==1
    code=code.replace(old,new)
    code=code.replace("prof = {'anchors':", "prof = {'featureMode':'female-joint-frames', 'anchors':")
    needle='        return dbind, moved'
    replacement='''        # The same point on two UV islands must carry the same corrective.
        _, inverse, counts=np.unique(np.round(gpos,5),axis=0,return_inverse=True,return_counts=True)
        summed=np.zeros((len(counts),3));np.add.at(summed,inverse,dbind)
        dbind=summed[inverse]/counts[inverse,None]
        # Correctives are local fit changes; bound inverse-skinning amplification.
        size=np.linalg.norm(dbind,axis=1)
        dbind*=np.minimum(1,.018/np.maximum(size,1e-12))[:,None]
        return dbind, moved'''
    assert code.count(needle)==1
    code=code.replace(needle,replacement)
if mode in ('export','polo_export'):
    needle='bi, bw = G.prune(W, 4)'
    replacement='''# Pattern / UV seams must remain closed under skinning.
_, seam_inverse, seam_counts = np.unique(np.round(pos,5),axis=0,return_inverse=True,return_counts=True)
seam_sum=np.zeros((len(seam_counts),W.shape[1]))
np.add.at(seam_sum,seam_inverse,W)
W=seam_sum[seam_inverse]/seam_counts[seam_inverse,None]
bi, bw = G.prune(W, 4)'''
    assert code.count(needle)==1
    code=code.replace(needle,replacement)
if mode=='polo_export':
    code=code.replace('res = 2048','res = 1024')
if tool == 'maps':
    code = code.replace("os.path.join(ROOT, 'c', 'libraster.dylib')",repr(str(SOURCE.parent/'c/libraster.dylib')))
if tool == 'look':
    code = code.replace("if not o.data.materials: o.data.materials.append(cloth)",
                        "if not o.data.materials: o.data.materials.append(cloth)\n    for slot in range(len(o.data.materials)): o.data.materials[slot] = cloth")
if mode=='cover':
    # Scope coverage/contact authoring to the requested garment; carry other
    # accepted masks through byte-for-byte in the archive.
    code=code.replace('masks = {}', "_only=set(os.environ.get('CV2_PIECES','').split(','))-{''}\n_old=os.path.join(udir,'cover.npz')\nmasks=dict(np.load(_old)) if _only and os.path.exists(_old) else {}")
    code=code.replace("    name = os.path.basename(f)[:-10]\n    g = np.load(f)","    name = os.path.basename(f)[:-10]\n    if _only and name not in _only: continue\n    g = np.load(f)")
    code=code.replace("for k, v in masks.items():\n    if not k.startswith('Kit_Shoe'):","for k, v in masks.items():\n    if _only and k not in _only: continue\n    if not k.startswith('Kit_Shoe'):")
    code=code.replace("for name in list(masks):\n    if name.startswith('Kit_Shoe'):","for name in list(masks):\n    if _only and name not in _only: continue\n    if name.startswith('Kit_Shoe'):")
if mode=='cover':
    # Exposure test: a normal ray that misses the garment means either the
    # skin is genuinely uncovered (hem/armhole lifted away) or the skin has
    # pushed THROUGH the garment. Only the first must stay drawable; the
    # second is exactly the skin that would show as poke-through. Garment
    # surface up to 6 cm behind the skin point (inside the body) = penetration;
    # skin pushed 25-30 mm through a raised-arm tank was misread as uncovered at 2.5 cm.
    _old_line="            if r[0] is None: exposed[v] = True"
    if code.count(_old_line)!=1: raise RuntimeError('cover.py exposure test changed; re-check penetration patch')
    # Oblique pokes miss both normal rays: when the nearest cloth (<= 35 mm) is an
    # interior face of an outer shell (>= 8 mm from every opening), the skin went
    # through the cloth; skin beside an armhole/neck/hem opening stays exposed.
    code=code.replace(_old_line,"            if r[0] is None and tree.ray_cast(Vector(bp[v] - bn[v] * 1e-4), Vector(-bn[v]), .06)[0] is None:\n                _nr = tree.find_nearest(Vector(bp[v]), .035)\n                if _nr[0] is None or not _FI[_nr[2]]: exposed[v] = True")
    _fi_code=("_FI = []\n"
        "for _gg in pieces.values():\n"
        "    _outer = _gg['part'] == 0; _ot = _gg['tri'][_outer]; _loops = G.boundary_loops(_ot)\n"
        "    _de = G.edge_distance(_gg['pos'], _ot, _loops) if _loops else np.full(len(_gg['pos']), 1.0)\n"
        "    _FI.append(_outer & (_de[_gg['tri']].mean(1) > .008))\n"
        "_FI = np.concatenate(_FI)\n"
        "for c in hero.clips:")
    if code.count("\nfor c in hero.clips:")!=1: raise RuntimeError('cover.py clip loop changed')
    code=code.replace("\nfor c in hero.clips:","\n"+_fi_code,1)
if mode=='cover' and __import__('os').environ.get('COVER_DEBUG_VERTS'):
    # Diagnostic: why given body vertices stay drawn (rest visibility / margin / pose exposure).
    code=code.replace("print('skin a garment uncovers in some pose:'","_dbg=[int(x) for x in os.environ['COVER_DEBUG_VERTS'].split(',')]\nfor _v in _dbg: print('DEBUG v',_v,'hiddenPre',{k:bool(m[_v]) for k,m in masks.items()},'cov',bool(cov[_v]),'vis',bool(vis[_v]),'candidate',bool(cand[_v]),'exposed',bool(exposed[_v]))\nprint('skin a garment uncovers in some pose:'")
if mode=='cover' and args[0] in ('GolfKitHero_Female','MatchHero_Female'):
    # With the penetration-aware pose test, a narrow 18 mm drawn band at the
    # openings suffices; a wide band leaves skin that pokes through the cloth.
    code=code.replace("MARGIN = {'Kit_Top': .045","MARGIN = {'Kit_Top': .018")
if mode in ('cover','poke','posed') and (ROOT/'dump-arm-final'/args[0]/'hero.json').exists():
    # Garment bindposes stay authored on their original (A25 for golf) rig.
    # Collision/coverage follows the repaired live body at the same clip times.
    import numpy as np
    _clip=cv2io.Hero.clip
    _meta=json.loads((ROOT/'dump-arm-final'/args[0]/'hero.json').read_text())
    def repaired_body_clip(self,name):
        _,bones=_clip(self,name)
        entry=next(c for c in _meta['clips']if c['name']==name)
        body=np.fromfile(ROOT/'dump-arm-final'/args[0]/('clip_'+entry['file']+'_body.f32'),np.float32).reshape(entry['frames'],-1,3)
        if len(body)!=len(bones):raise ValueError('Repair clip sampling mismatch')
        return body,bones
    cv2io.Hero.clip=repaired_body_clip
if mode in ('cover','poke','posed'):
    import correctives_rt
    from pose_features import features
    correctives_rt.features=features
    def blend_female(hero,bones,C):
        w=correctives_rt.weights(hero,bones,C['feats'])
        if 'nearest' in C.files:
            count=min(int(C['nearest']),len(w));keep=np.argpartition(w,-count)[-count:];cutoff=np.max(np.delete(w,keep))if len(keep)<len(w)else 0;selected=np.zeros_like(w);selected[keep]=np.maximum(0,w[keep]-cutoff);w=selected/selected.sum()if selected.sum()>0 else np.isin(np.arange(len(w)),keep)/len(keep)
        k=len(C['shapes']);return np.einsum('k,kvc->vc',w[1:1+k],C['shapes'])if k else 0
    import numpy as np
    correctives_rt.blend=blend_female
exec(compile(code,str(path),'exec'),{'__name__':'__main__','__file__':str(path)})
if mode=='polo_export':
    from clean_polo_export import clean
    print('Zero-area button pole faces removed:',clean(ROOT/'out'/args[0]/'unity',args[0]))
if mode=='cover':
    import numpy as np
    hero=cv2io.Hero(args[0])
    folder=ROOT/'out'/args[0]/'unity'
    archive=np.load(folder/'cover.npz')
    masks={key:archive[key].copy() for key in archive.files}
    # A raised arm can expose axilla skin that a rest-pose ray marks covered.
    # Those complete body triangles must remain available in every pose.
    if 'Kit_Top' in masks and args[0]=='MatchHero_Female':

        p=hero.body.pos
        # Superseded 2026-10-16: the blanket axilla un-hide (|x|>.065, z>1.09) kept the
        # whole upper chest side drawn, which pokes through the tank whenever the arm
        # rises. Exposure is now decided per clip frame by the penetration-aware test.
        if __import__('os').environ.get('TANK_AXILLA_BLANKET')=='1':
            axilla=(np.abs(p[:,0])>.065)&(p[:,2]>1.09)
            masks['Kit_Top'][axilla]=False
        tri=hero.body.tri[masks['Kit_Top'][hero.body.tri].all(1)]
        tri.astype(np.int32).tofile(folder/'Kit_Top_hide.bin')
    if 'Kit_Top' in masks and args[0]=='GolfKitHero_Female':
        p=hero.body.pos
        # These panels are closed in the independent pattern in every pose.
        # Preserve skin at the collar and open cuff, but omit the complete body
        # surface underneath the sewn torso/proximal sleeve (standard kit coverage).
        covered=(p[:,2]>.995)&(p[:,2]<1.30)&(np.abs(p[:,0])<.15)
        for side in ['Left','Right']:
            a=np.linalg.inv(hero.body.bind[hero.body.bones.index(side+'UpperArm')])[:3,3]
            b=np.linalg.inv(hero.body.bind[hero.body.bones.index(side+'LowerArm')])[:3,3]
            axis=(b-a)/np.linalg.norm(b-a);along=(p-a)@axis
            radius=np.linalg.norm(p-a-along[:,None]*axis,axis=1)
            covered|=(along>-.075)&(along<.10)&(radius<.095)&((np.abs(p[:,0])>.085)|(p[:,2]<1.27))
        masks['Kit_Top']|=covered
        tri=hero.body.tri[masks['Kit_Top'][hero.body.tri].all(1)]
        tri.astype(np.int32).tofile(folder/'Kit_Top_hide.bin')
        print('Polo closed-panel coverage:',int(masks['Kit_Top'].sum()),'vertices',flush=True)
    np.savez(folder/'cover.npz',**masks)
