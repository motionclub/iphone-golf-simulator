NAMES = ["fair","light","tan","olive","brown","deep"]
OLD = {"fair":(255,224,196),"light":(238,196,160),"tan":(226,160,110),"olive":(196,124,80),"brown":(150,90,56),"deep":(96,60,40)}
def rgb(t): return [t[0]/255.0, t[1]/255.0, t[2]/255.0, 1.0]
CASES = [dict(name="before_default", color=[0.74,0.555,0.435,1], floats=[dict(k="_Smoothness",v=0.4),dict(k="_Metallic",v=0.0)])]
for n in NAMES: CASES.append(dict(name="before_"+n, color=rgb(OLD[n]), floats=[dict(k="_Smoothness",v=0.4),dict(k="_Metallic",v=0.0)]))
CASES.append(dict(name="after_default", asset="Assets/Characters/HeroBase/Materials/Male_Form_Skin.mat"))
for i,n in enumerate(NAMES): CASES.append(dict(name="after_"+n, asset="Assets/Characters/HeroBase/Materials/Male_Form_Skin.mat", tone=i))
VIEWS = ["head_front","head_side","head_q","head_back","body_front","torso_q"]
