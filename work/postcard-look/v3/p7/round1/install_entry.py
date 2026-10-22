"""Root-owned sequential promotion and required pre/install under heavy.sh."""
from pathlib import Path
import subprocess,sys
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
V=R/'work/postcard-look/v3'
if subprocess.call([sys.executable,str(V/'p7/round1/promote_stage.py')],cwd=R):raise SystemExit(1)
raise SystemExit(subprocess.call([sys.executable,str(V/'proof/runtime/phase6_install_entry.py'),'p7_pre_install_round1'],cwd=R))
