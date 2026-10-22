import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, lab
C = lab.load(os.path.join(lab.ROOT, 'Unity/Assets/Resources/Course/Look/Lava_C.png')); E = lab.load(os.path.join(lab.ROOT, 'Unity/Assets/Resources/Course/Look/Lava_E.png'))
for m in [(0, 0, 0), (1.0, 1.0, 1.0), (1.1, 1.1, 1.1), (1.2, 1.2, 1.2), (1.3, 1.3, 1.3), (1.3, 0.85, 0.55), (1.2, 1.0, 0.8)]:
    st = lab.lava_stats(lab.lava_game(C, E, m))
    print(m, {k: (tuple(int(x) for x in v) if isinstance(v, tuple) else round(v, 3)) for k, v in st.items()})
