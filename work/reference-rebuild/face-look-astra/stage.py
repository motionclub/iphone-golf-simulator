from pathlib import Path
import difflib,json
root=Path.cwd()
stage=root/'work/reference-rebuild/face-look-astra'
changes=[]
hlsl='Unity/Assets/Resources/Tennis/Shaders/HeroLighting.hlsl'
swift='GolfArcade/Unity/MatchHeroSurfaces.swift'
old_hlsl='''        // Satin skin: a wide soft reflection with a restrained central sheen.
        // Diffuse/pigment and geometric normals remain the accepted source.
        // The reference's broad source reflection needs a wider lobe than a
        // point-light varnish. Keep rougher lips/neck below the forehead/nose.
        half glossWeight = .5h + .5h * saturate((smoothness - .32h) / .08h);
        broad = (pow(nh, 5 + smoothness * 6) * .22h
               + pow(nh, 48 + smoothness * 60) * .018h) * glossWeight;'''
new_hlsl='''        // Softbox skin: concentrate the broad wash into a visible satin core.
        // Lower integrated reflection energy preserves the side-plane colour;
        // the soft shoulder keeps the highlight transition from becoming oily.
        // Rougher lips/neck remain below the forehead/nose response.
        half glossWeight = .5h + .5h * saturate((smoothness - .32h) / .08h);
        broad = (pow(nh, 5 + smoothness * 6) * .035h
               + pow(nh, 18 + smoothness * 18) * .40h) * glossWeight;'''
old_swift='''            float glossWeight=0.5+0.5*saturate((smoothness-0.32)/0.08);
            skinLobe=(pow(nh,5.0+smoothness*6.0)*0.22+pow(nh,48.0+smoothness*60.0)*0.018)*glossWeight;'''
new_swift='''            // Same soft shoulder / satin core as Unity's HeroSkinShade.
            float glossWeight=0.5+0.5*saturate((smoothness-0.32)/0.08);
            skinLobe=(pow(nh,5.0+smoothness*6.0)*0.035+pow(nh,18.0+smoothness*18.0)*0.40)*glossWeight;'''
for path,old,new in [(hlsl,old_hlsl,new_hlsl),(swift,old_swift,new_swift)]:
    src=(root/path).read_text()
    assert src.count(old)==1, path
    dst=src.replace(old,new)
    out=stage/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(dst)
    changes.extend(difflib.unified_diff(src.splitlines(True),dst.splitlines(True),fromfile=path,tofile=path))
(stage/'softbox.patch').write_text(''.join(changes))
queue=json.loads((root/'work/reference-rebuild/face-finish30/root-broad-queue.json').read_text())[:1]
queue[0]['name']='face-finish30-softbox'
queue[0]['env']['VISUAL_CHARACTER_OUT']=str(root/'proof/reference-rebuild/face-finish30-softbox')
queue[0]['env']['VISUAL_CHARACTER_TWO_FRONT_ONLY']='1'
queue[0]['env']['VISUAL_CHARACTER_FULL_REVIEW']='0'
queue[0]['env']['VISUAL_CHARACTER_BLINK_REVIEW']='0'
queue[0]['env']['VISUAL_CHARACTER_SKIN_POLISH']='1'
(stage/'two-front-queue.json').write_text(json.dumps(queue,indent=2)+'\n')
print(stage/'softbox.patch')
