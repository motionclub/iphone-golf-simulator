NEW = [("fair",(255,216,181)),("light",(238,187,143)),("tan",(226,160,110)),("olive",(196,122,76)),("brown",(150,88,53)),("deep",(96,57,36))]
def rgb(t): return [t[0]/255.0, t[1]/255.0, t[2]/255.0, 1.0]
CASES = []
for n,t in NEW:
    CASES.append(dict(name="new_"+n, color=rgb(t), floats=[dict(k="_Smoothness",v=0.4),dict(k="_Metallic",v=0.0)]))
for n,t in NEW:
    CASES.append(dict(name="new38_"+n, color=rgb(t), floats=[dict(k="_Smoothness",v=0.38),dict(k="_Metallic",v=0.0)]))
