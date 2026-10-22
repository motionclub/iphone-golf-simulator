def rgb(t): return [t[0]/255.0, t[1]/255.0, t[2]/255.0, 1.0]
V = {"A_current":(244,206,172),"B":(243,201,166),"C":(241,196,160),"D":(246,203,166),"E":(242,199,164)}
CASES = [dict(name="fair_"+k, asset="Assets/Characters/HeroBase/Materials/Male_Form_Skin.mat", color=rgb(t), setColor=True) for k,t in V.items()]
CASES[0]["tone"]=-1
VIEWS = ["head_front","head_q"]
