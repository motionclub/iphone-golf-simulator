from pathlib import Path
p=Path('work/full-visual-overhaul/tennis/build-premium-coast.py');s=p.read_text()
s=s.replace('return -3.85+min(d*(.42+.26*k),5.6+3.6*k)+wave(x,y)*min(1,d/16)', '''hill=7*math.exp(-((x+62)**2+(y-45)**2)/(2*48**2))+9*math.exp(-((x-57)**2+(y-72)**2)/(2*48**2))+6*math.exp(-((x+13)**2+(y-153)**2)/(2*62**2))
    return -3.85+min(d*(.50+.30*k),8.5+5*k)+(wave(x,y)*1.65+hill)*min(1,d/25)''')
s=s.replace("templates=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('CLIFF_BLOCK_')]", "templates=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('BLUFF_')]")
s=s.replace('if len(selected)>=16:break','if len(selected)>=13:break')
s=s.replace('for member in range(rng.randint(3,5)):', 'for member in range(rng.randint(2,4)):')
s=s.replace('rng.uniform(9,15),rng.uniform(7,12),rng.uniform(3.3,5.7)', 'rng.uniform(6.0,10.5),rng.uniform(5.5,9.5),rng.uniform(2.2,4.0)')
s=s.replace('z=elevation(px,py)-1.9', 'z=elevation(px,py)-1.6')
s=s.replace('if len(seeds)>=22:break','if len(seeds)>=36:break').replace('math.hypot(x-a,y-b)<36','math.hypot(x-a,y-b)<26')
s=s.replace('range(rng.randint(9,15))', 'range(rng.randint(17,27))').replace('rng.gauss(0,13)','rng.gauss(0,15)').replace('math.hypot(x-a,y-b)<5.0','math.hypot(x-a,y-b)<3.8')
s=s.replace("typ='PALM' if rng.random()<.22 else 'CANOPY'", "typ='PALM' if rng.random()<.13 else 'CANOPY'")
s=s.replace('rng.uniform(6.0,9.5)', 'rng.uniform(5.8,9.2)')
s=s.replace('if n%3==0:', 'if n%2==0:').replace("marker('BUSH',x+dx,y+dy,rng.uniform(1.2,2.4),rng.uniform(1.5,2.6))", "marker('SHRUB0' if n%4==0 else 'SHRUB1',x+dx,y+dy,rng.uniform(2.0,3.4),rng.uniform(2.8,4.4))")
# A continuous irregular shoreline scrub belt joins the tree pockets at multiple heights.
s=s.replace("bpy.ops.object.select_all(action='SELECT')\nasset=", '''for ring in inner:
    for n,point in enumerate(ring):
        if n%2:continue
        x=point.x+rng.uniform(-1,1);y=point.y+rng.uniform(-1,1)
        if sample(distance,x,y)<2.4 or abs(x)<39 and abs(y)<40:continue
        marker('SHRUB0' if n%4==0 else 'SHRUB1',x,y,rng.uniform(1.6,3.0),rng.uniform(2.8,4.5));understory+=1

bpy.ops.object.select_all(action='SELECT')
asset=''')
s=s.replace("ROOT/'Unity/Assets/Resources/Tennis/Premium/TennisCoast.fbx'", "WORK/'TennisCoast-v3.fbx'").replace("ROOT/'Unity/Assets/Resources/Tennis/Premium/CoastShallows.png'", "WORK/'CoastShallows-v3.png'").replace("WORK/'TennisCoast.blend'", "WORK/'TennisCoast-v3.blend'").replace("PROOF/'coast-manifest.json'", "PROOF/'coast-manifest-v3.json'")
Path('work/full-visual-overhaul/tennis/build-premium-coast-v3.py').write_text(s)
# Filled irregular foliage beneath outlined broad leaves; preserves semantic mesh roles.
s=Path('work/full-visual-overhaul/tennis/build-premium-botany.py').read_text()
s=s.replace('tube((0,0,0),(0,0,.52),.06,.017,0,9)', 'tube((0,0,0),(0,0,.36),.075,.022,0,9)')
s=s.replace('for k in range(9):','for k in range(11):').replace('.60+.10*math.sin(k)', '.49+.13*math.sin(k*1.8)')
s=s.replace('tube((0,0,.40),c,.02,.008,0,7)', '''tube((0,0,.30),c,.026,.009,0,7)
 bulb(c+Vector((0,0,.02)),(.34+.04*math.sin(k),.28+.05*math.cos(k),.18+.04*math.sin(k*1.7)),1+k%3,4,9)''')
s=s.replace("str(asset/'TennisBotanicalKit.fbx')", "str(OUT/'TennisBotanicalKit-v2.fbx')").replace("OUT/'TennisBotanicalKit.blend'", "OUT/'TennisBotanicalKit-v2.blend'").replace("PROOF/'tennis-botanical-kit-manifest.json'", "PROOF/'tennis-botanical-kit-manifest-v2.json'")
Path('work/full-visual-overhaul/tennis/build-premium-botany-v2.py').write_text(s)
