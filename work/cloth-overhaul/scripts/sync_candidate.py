from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[3];W=R/'work/cloth-overhaul';C=W/'isolation/Unity'
assert len(list((W/'maps').glob('Kit_*_N.png')))==12
for rel in ['Assets/Scripts/Tennis/MatchHeroLook.cs','Assets/Resources/Tennis/Shaders/TennisCloth.shader','Assets/Editor/HeroDetailTextures.cs','Assets/Editor/ClothProofRig.cs','Assets/Editor/ClothCompileProbe.cs','Assets/Editor/ClothProofMask.shader']:
 shutil.copy2(R/'Unity'/rel,C/rel)
for sex in ['Male','Female']:shutil.copy2(W/f'export/{sex}_Kit.fbx',C/f'Assets/Characters/MatchHeroKit/{sex}_Kit.fbx')
for p in (W/'maps').glob('*.png'):shutil.copy2(p,C/'Assets/Resources/Tennis/HeroDetail'/p.name)
print('Synced candidate into isolated Unity only')
