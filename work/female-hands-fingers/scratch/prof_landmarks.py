import numpy as np
from PIL import Image
B = '../../ArtDir/hero/base_lock/'
im = np.array(Image.open(B+'female_multiangle_body.jpg').convert('L')).astype(float)
S2 = 1.7039/288.5
np.set_printoptions(precision=1, suppress=True, linewidth=200)
for nm, anchor, flip, x0, x1 in (('left', 791.5, False, 758, 812), ('right', 1095.5, True, 1070, 1130)):
    print(nm)
    for z in (0.76, 0.75, 0.74, 0.73, 0.72, 0.71, 0.70, 0.69):
        r = int(round(338.5 - z/S2)); 
        row = im[r, x0:x1]
        # y (cm) of each column
        ys = ((np.arange(x0, x1) - anchor) * S2 * 100) * (-1 if flip else 1)
        # report dark local minima (slits) below row mean-12
        loc = []
        for i in range(2, len(row)-2):
            if row[i] < row[i-1] and row[i] <= row[i+1] and row[i] < np.median(row) - 14: loc.append((round(ys[i], 1), int(row[i])))
        print('  z %.2f row %d' % (z, r), 'dark minima (y_cm, val):', loc)
