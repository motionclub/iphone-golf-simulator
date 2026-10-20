from pathlib import Path
p=Path('Tools/HeroBase/measured_volume.py');s=p.read_text()
s=s.replace('return (c+d)/2+(x-(a+b)/2)*r,r','''offset=(c+d-a-b)/2
        if not .78<r<1.22 or abs(offset)>5:return x,1
        corrected=(c+d)/2+(x-(a+b)/2)*r
        corrected=x+max(-2.5,min(2.5,corrected-x))
        return corrected,r''')
s=s.replace('_,ratio=smoothwarp(float(x),float(y));xp,_=smoothwarp(float(x),float(y+.5));xm,_=smoothwarp(float(x),float(y-.5));deriv=xp-xm','''xright,_=smoothwarp(float(x+.1),float(y));xleft,_=smoothwarp(float(x-.1),float(y));ratio=max(.70,min(1.3,(xright-xleft)/.2))
        xp,_=smoothwarp(float(x),float(y+.5));xm,_=smoothwarp(float(x),float(y-.5));deriv=max(-.8,min(.8,xp-xm))''')
p.write_text(s)
p=Path('Tools/HeroBase/build_static.py');s=p.read_text().replace('step=5.2 if female else 6.35','step=5.2 if female else 6.40');p.write_text(s)
