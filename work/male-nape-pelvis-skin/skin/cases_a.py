OLD = [("fair",(255,224,196)),("light",(238,196,160)),("tan",(226,160,110)),("olive",(196,124,80)),("brown",(150,90,56)),("deep",(96,60,40))]
def rgb(t): return [t[0]/255.0, t[1]/255.0, t[2]/255.0, 1.0]
CASES = [dict(name="lit_old", color=[0.74,0.555,0.435,1], floats=[dict(k="_Smoothness",v=0.4),dict(k="_Metallic",v=0.0)])]
for n,t in OLD:
    CASES.append(dict(name="lit_"+n, color=rgb(t), floats=[dict(k="_Smoothness",v=0.4),dict(k="_Metallic",v=0.0)]))
for n,t in OLD:
    CASES.append(dict(name="tc_"+n, shader="GolfArcade/TennisCharacter", color=rgb(t), floats=[dict(k="_Saturation",v=1.0),dict(k="_Smoothness",v=0.2),dict(k="_Wrap",v=0.35),dict(k="_RimStrength",v=0.08)], colors=[dict(k="_Subsurface",v=[0.2,0.065,0.02,1.0])]))
