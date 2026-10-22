from pathlib import Path
p=Path('Tools/HeroBase/build_static.py');s=p.read_text()
a=s.index('    # torso is built directly');b=s.index('    # Neck;',a)
s=s[:a]+'''    from measured_volume import append_volume
    append_volume(g,pix,profile,interp,female,step=4.7)
    # Flesh palm/finger/toe features are part of Body, with a material boundary at the wrist/ankle.
    if female:
        for sign in (-1,1):
            ellipsoid(g,pix(sign*85,406,-1),(10*scale,8*scale,19*scale),1,n=24,k=16)
            for fi in range(4):
                x=sign*(79+fi*4);y=416-fi*.6
                tube(g,[pix(x,y,-1),pix(x+sign*1,y+12,-2),pix(x-sign*2,y+23,-1)],[2.7*scale,2.5*scale,.9*scale],[3.1*scale,2.7*scale,1*scale],1,n=10,steps=12)
            tube(g,[pix(sign*76,403,-5),pix(sign*75,413,-8),pix(sign*77,425,-8)],[4*scale,3.2*scale,1.4*scale],[4*scale,3.2*scale,1.4*scale],1,n=12,steps=14)
            for fi in range(5):ellipsoid(g,pix(sign*(48+(fi-2)*5),670,-43+fi*1),(3.4*scale,7*scale,3.7*scale),1,n=12,k=10)
'''+s[b:]
a=s.index('    import bmesh\n    bm=bmesh.new();bm.from_mesh(body.data)');b=s.index('    # Hair cap',a)
s=s[:a]+'    uv(body)\n'+s[b:]
# Rebuild back locks on the current cap, where they can be seen in both Blender and Unity.
a=s.index('        # Short side and back locks');b=s.index('    else:\n        N=64;K=20',a)
s=s[:a]+'''        # Four layered rows of tapered opaque clumps follow measured back head mass.
        profile_h=[(30,10,12),(38,36,30),(50,48,40),(66,53,46),(84,53,47),(102,49,46),(122,45,44),(138,39,36),(149,31,31)]
        for row in range(4):
            for i in range(12):
                th=math.pi/2+math.pi*i/11;back=max(0,-math.cos(th));yend=min([69,99,129,151][row],104+45*back)
                ystart=[31,57,87,117][row]
                if yend<ystart+8:continue
                pts=[]
                for t in (0,.33,.72,1):
                    y=ystart+(yend-ystart)*t;w,d=interp(profile_h,y);ang=th+.07*(t-.5);pts.append(pix((w+1.5)*math.sin(ang),y,-(d+1.5)*math.cos(ang)+1))
                tube(h,pts,[.4*scale,5.7*scale,4.8*scale,.3*scale],[.3*scale,2.2*scale,1.7*scale,.3*scale],0,n=10,steps=18)
'''+s[b:]
a=s.index('        for i in range(16):\n            th=math.pi/2');b=s.index('    if not female:\n        ymin=',a)
s=s[:a]+'''        for i in range(17):
            th=math.pi/2+math.pi*i/16;pts=[]
            for y in (82,105,136,163,185+(i%3-1)*2):
                w,d=interp(profile_h,y);pts.append(pix((w+1.6)*math.sin(th),y,-(d+1.6)*math.cos(th)+3))
            tube(h,pts,[.3*scale,5.7*scale,6.3*scale,5.7*scale,.3*scale],[.3*scale,2.6*scale,2.8*scale,2.6*scale,.3*scale],0,n=12,steps=26)
'''+s[b:]
p.write_text(s)
p=Path('Unity/Assets/Editor/HeroBaseStaticImport.cs');s=p.read_text().replace('Mathf.Cos(a)*5','-Mathf.Cos(a)*5').replace('new Vector3(0,.85f,5)','new Vector3(0,.85f,-5)');s=s.replace('new Vector3(-2.8f,3.4f,4f)','new Vector3(-2.8f,3.4f,-4f)').replace('new Vector3(2.6f,1.8f,2f)','new Vector3(2.6f,1.8f,-2f)').replace('new Vector3(0,2.6f,-3f)','new Vector3(0,2.6f,3f)');s=s.replace('AssetDatabase.SaveAssets();SessionState.SetBool(Key,true)', 'File.WriteAllLines(Proof+"/unity-mesh-material-audit.txt",audit);AssetDatabase.SaveAssets();SessionState.SetBool(Key,true)');p.write_text(s)
