from pathlib import Path
import difflib
root=Path.cwd(); stage=root/'work/reference-rebuild/face-look-astra/regional'; changes=[]
for path,old,new in [
('Unity/Assets/Resources/Tennis/Shaders/HeroLighting.hlsl','half glossWeight = .5h + .5h * saturate((smoothness - .32h) / .08h);','half glossWeight = .16h + .84h * saturate((smoothness - .32h) / .06h);'),
('GolfArcade/Unity/MatchHeroSurfaces.swift','float glossWeight=0.5+0.5*saturate((smoothness-0.32)/0.08);','float glossWeight=0.16+0.84*saturate((smoothness-0.32)/0.06);')]:
    source=(root/path).read_text(); assert source.count(old)==1,path
    candidate=source.replace(old,new);out=stage/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(candidate)
    changes.extend(difflib.unified_diff(source.splitlines(True),candidate.splitlines(True),fromfile=path,tofile=path))
(stage/'regional.patch').write_text(''.join(changes))
