from pathlib import Path
import json,shutil
root=Path(__file__).resolve().parents[2]
work=Path(__file__).resolve().parent
for relative in json.loads((work/'owned-files.json').read_text()):
    for suffix in ('','.meta'):
        source=root/'Unity/Assets'/(relative+suffix)
        if source.exists():shutil.copy2(source,work/'AfterUnity/Assets'/(relative+suffix))
shutil.copytree(root/'Unity/Assets/Resources/Course/Standard',work/'AfterUnity/Assets/Resources/Course/Standard',dirs_exist_ok=True)
