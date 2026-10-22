from pathlib import Path
import subprocess
W=Path(__file__).resolve().parents[1]
for sex in ['male','female']:
    files=sorted((W/f'film_game_{sex}').glob('f*.png'),key=lambda p:int(p.stem[1:]))
    assert files
    subprocess.run([str(W/'scripts/enc'),str(W/'film'/f'serve_toss_jump_{sex}_game_full.mp4'),'30','1280','720']+[str(p) for p in files],check=True)
