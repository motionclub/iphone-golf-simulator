from pathlib import Path
p=Path('Tools/HeroBase/measured_volume.py');s=p.read_text();a=s.index('    # Sculpt X coordinates');b=s.index('    base=len(g.v)',a);s=s[:a]+'    original_points=points.copy()\n'+s[b:];a=s.index('    for i,(x,dd,y) in enumerate(original_points):');b=s.index('    norm/=np.maximum',a);s=s[:a]+s[b:];p.write_text(s)
