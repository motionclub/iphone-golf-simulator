"""Route the existing garment tools to this pass's isolated inputs and outputs.

Blender -b source/<file>.blend --python pipeline.py -- export|render|maps|cover|correctives <tool args...>
"""
from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'clothing-v2/py'
sys.path.insert(0, str(SOURCE))
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
release=np.clip((pos[:,2]-1.15)/.095,0,1);release=release*release*(3-2*release)
release[np.isin(vpan,[SLEEVE_L,SLEEVE_R,CUFF])]=1
W=torsoW*(1-release[:,None])+W*release[:,None]
# Smooth the stitched sleeve/torso transition across coincident pattern edges.
_,weld_inverse,weld_counts=np.unique(np.round(pos,4),axis=0,return_inverse=True,return_counts=True)
weldW=np.zeros((len(weld_counts),W.shape[1]));np.add.at(weldW,weld_inverse,W);weldW/=weld_counts[:,None]
weldW=finalize.smooth_weights(weldW,weld_inverse[tri],12)
W=weldW[weld_inverse]
# Keep the lower panels entirely on the torso after seam diffusion.
keep_torso=1-np.clip((pos[:,2]-1.13)/.07,0,1)
keep_torso[np.isin(vpan,[SLEEVE_L,SLEEVE_R,CUFF])]=0
W=torsoW*keep_torso[:,None]+W*(1-keep_torso[:,None])
bi, bw = G.prune(W, 4)'''
    assert code.count(needle)==1
    code=code.replace(needle,replacement)
if mode=='correctives':
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
if tool == 'maps':
    code = code.replace("os.path.join(ROOT, 'c', 'libraster.dylib')",repr(str(SOURCE.parent/'c/libraster.dylib')))
if tool == 'look':
    code = code.replace("if not o.data.materials: o.data.materials.append(cloth)",
                        "if not o.data.materials: o.data.materials.append(cloth)\n    for slot in range(len(o.data.materials)): o.data.materials[slot] = cloth")
exec(compile(code,str(path),'exec'),{'__name__':'__main__','__file__':str(path)})
if mode=='cover':
    import numpy as np
    hero=cv2io.Hero(args[0])
    folder=ROOT/'out'/args[0]/'unity'
    archive=np.load(folder/'cover.npz')
    masks={key:archive[key].copy() for key in archive.files}
    # A raised arm can expose axilla skin that a rest-pose ray marks covered.
    # Those complete body triangles must remain available in every pose.
    if 'Kit_Top' in masks:
        p=hero.body.pos
        axilla=(np.abs(p[:,0])>.065)&(p[:,2]>1.09)
        masks['Kit_Top'][axilla]=False
        tri=hero.body.tri[masks['Kit_Top'][hero.body.tri].all(1)]
        tri.astype(np.int32).tofile(folder/'Kit_Top_hide.bin')
    np.savez(folder/'cover.npz',**masks)
