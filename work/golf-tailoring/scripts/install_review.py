from pathlib import Path
import shutil
W=Path(__file__).resolve().parents[1];U=W/'Unity/Assets'
for sex in ['Male','Female']:shutil.copy2(W/'export/kit_v2'/f'Golf_{sex}_Kit.fbx',U/'Characters/GolfHeroKit'/f'{sex}_Kit.fbx')
for p in (W/'maps').glob('*.png'):shutil.copy2(p,U/'Resources/Golf/HeroDetail'/p.name)
