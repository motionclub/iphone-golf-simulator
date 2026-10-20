from pathlib import Path
p=Path('Tools/HeroBase/measured_volume.py');s=p.read_text();s=s.replace('    def path(points,widths,depths,k=3.0):\n        for i in range(len(points)-1):','''    def path(points,widths,depths,k=3.0):
        rows=[(i,*point,widths[i],depths[i]) for i,point in enumerate(points)]
        sampled=[interp(rows,t) for t in np.linspace(0,len(rows)-1,36)]
        points=[r[:3] for r in sampled];widths=[r[3] for r in sampled];depths=[r[4] for r in sampled]
        pathfield=np.full(shape,1e4,dtype=np.float32)
        for i in range(len(points)-1):''');s=s.replace('            add(val,k)\n    for sign', '            pathfield=np.minimum(pathfield,val)\n        add(pathfield,k)\n    for sign')
s=s.replace('    def warp(x,y):\n        j=', '    def warp(x,y):\n        return x,1\n        j=')
p.write_text(s)
