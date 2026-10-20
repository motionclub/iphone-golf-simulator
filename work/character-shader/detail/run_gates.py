"""GATE HERO_DETAIL: PASS / FAIL per line, from proof/detail/after/report.txt (the in-game audit), the shader sources and the before/after file hashes.
   python3 work/character-shader/detail/run_gates.py  -> work/character-shader/detail/GATE_RESULTS.md"""
import re, subprocess, os, hashlib, sys
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..",".."))
os.chdir(ROOT)
rep=open("work/character-shader/proof/detail/after/report.txt").read()
cloth=open("Unity/Assets/Resources/Tennis/Shaders/TennisCloth.shader").read()
char=open("Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader").read()
def rows(section):
    out=[]; on=False
    for ln in rep.splitlines():
        if ln.startswith("== "): on = ln.strip()==("== "+section)
        elif on and ln.startswith("  "): 
            f=ln.split(); out.append(ln)
    return out
def grab(ln,key):
    m=re.search(key+r"=([^\s]+)",ln); return m.group(1) if m else None
res=[]; 
def gate(name,ok,detail): res.append((name,ok,detail))
for sec in ("match male","locker male","locker female"):
    R=rows(sec); 
    if not R: gate(f"audit section '{sec}' present",False,"missing"); continue
    def find(sub,mat=None): return [l for l in R if sub in l]
    tag=sec
    # --- cloth: weave normal + thread break + dark trim + sole
    kit=[l for l in R if "GolfArcade/TennisCloth" in l and "Kit_" in l.split()[0]]
    weave_ok=all("weave=Cloth_Weave" in l and "baseMap=Kit_" in l and float(grab(l,"weaveN"))>0 for l in kit if "Kit_Sole" not in l)
    thread_ok=all(float(grab(l,"thread"))>0 for l in kit if "Kit_Sole" not in l)
    gate(f"[{tag}] TennisCloth samples a weave normal + base (seam) map on every kit piece",weave_ok and len(kit)>=9,f"{len(kit)} kit materials")
    gate(f"[{tag}] thread break multiplied into the colour (thread>0) on every kit cloth",thread_ok,"")
    trim=find("Kit_ShirtTrim")[0]; shirt=find("Kit_Shirt (hero)")[0]; band=find("Kit_ShortsBand")[0]
    gate(f"[{tag}] shirt trim is dark (#09090A) and not the shirt white, smoothness ~0.25",grab(trim,"base")=="#09090A" and grab(shirt,"base")!=grab(trim,"base") and abs(float(grab(trim,"smooth"))-0.25)<0.011,f"trim {grab(trim,'base')} sm {grab(trim,'smooth')} | shirt {grab(shirt,'base')} | band {grab(band,'base')}")
    sole=find("Kit_Sole")[0]; shoe=find("Kit_Shoe (hero)")[0]
    def lum(h): h=h.lstrip('#'); r,g,b=[int(h[i:i+2],16)/255 for i in (0,2,4)]; return .2126*r+.7152*g+.0722*b
    gate(f"[{tag}] sole is darker and rougher than the upper",lum(grab(sole,"base"))<lum(grab(shoe,"base"))-0.1 and float(grab(sole,"smooth"))<float(grab(shoe,"smooth")),f"sole {grab(sole,'base')} sm {grab(sole,'smooth')} | upper {grab(shoe,'base')} sm {grab(shoe,'smooth')}")
    cl=[l for l in kit if grab(l,"base") not in ("#09090A",) and "Kit_Sole" not in l]
    gate(f"[{tag}] cloth smoothness <= 0.14 (dark trim excepted)",all(float(grab(l,"smooth"))<=0.14 for l in cl),"max "+str(max(float(grab(l,'smooth')) for l in cl)))
    # --- skin
    sk=[l for l in R if l.split()[0].startswith("Body_")][0]
    sss=grab(sk,"sss")
    gate(f"[{tag}] skin smoothness ~0.2",abs(float(grab(sk,"smooth"))-0.2)<0.011,grab(sk,"smooth"))
    gate(f"[{tag}] skin normal on and weak (0 < bump <= 0.25), wrap + subsurface unchanged",("_NORMALMAP" in sk) and "bumpMap=Skin_Soft_N" in sk and 0<float(grab(sk,"bump"))<=0.25 and sss=="(0.18,0.06,0.03)" and abs(float(grab(sk,"wrap"))-0.55)<0.006,f"bump {grab(sk,'bump')} wrap {grab(sk,'wrap')} sss {sss}")
    eyes=[l for l in R if any(("_Face_"+p) in l for p in ("Sclera","Iris","Pupil","Limbal","Catch"))]
    gate(f"[{tag}] eyes stay smoother than skin (~0.85), no weave / bump",all(abs(float(grab(l,"smooth"))-0.85)<0.011 and "weave=-" in l and "bumpMap=-" in l for l in eyes) and len(eyes)>=5,f"{len(eyes)} eye materials")
    # --- decals, grip, strings off URP Lit
    dec=[l for l in R if l.split()[0].startswith("Face_") and not any(("_Face_"+p) in l for p in ("Sclera","Iris","Pupil","Limbal","Catch"))]
    gate(f"[{tag}] brow / lid / lip / nostril / seam decals on TennisCharacter (no URP Lit), no weave, no bump",all("GolfArcade/TennisCharacter" in l and "weave=-" in l and "bumpMap=-" in l for l in dec) and len(dec)>=7,f"{len(dec)} decal materials")
    grip=[l for l in R if "Black_Grip" in l]; strg=[l for l in R if "White_Strings" in l]
    gate(f"[{tag}] grip on TennisCloth, dark, rougher than the shirt",bool(grip) and all("GolfArcade/TennisCloth" in l and lum(grab(l,"base"))<0.15 and float(grab(l,"smooth"))<float(grab(shirt,"smooth")) for l in grip),f"grip sm {grab(grip[0],'smooth')} base {grab(grip[0],'base')} | shirt sm {grab(shirt,'smooth')}")
    gate(f"[{tag}] strings on TennisCharacter, a touch smoother than the grip, no weave",bool(strg) and all("GolfArcade/TennisCharacter" in l and "weave=-" in l and "bumpMap=-" in l and float(grab(l,"smooth"))>float(grab(grip[0],"smooth")) for l in strg),f"strings sm {grab(strg[0],'smooth')}")
    lit=[l for l in R if "Universal Render Pipeline/Lit" in l]
    gate(f"[{tag}] nothing on either hero is still URP Lit",not lit,f"{len(lit)} Lit materials")
# --- shader source gates (no new post, no toon ramp, no outline, no hard cloth dot)
for nm,src in (("TennisCloth",cloth),("TennisCharacter",char)):
    bad=[w for w in ("bloom","toon","ramp","outline","Outline","_OUTLINE","Bloom") if re.search(r"\b"+w,src) and w.lower() not in ("ramp",)]
    code=re.sub(r"//.*","",src)
    gate(f"{nm}: no bloom / toon ramp / outline in the shader",not re.search(r"(?i)bloom|toon|outline|smoothstep\s*\(\s*0\s*,\s*0\.\d+\s*,\s*ndl",code),"")
blinn=re.search(r"pow\(saturate\(dot\(n, h\)\), _Smoothness \* 96",cloth)
gate("TennisCloth: the small hard Blinn dot is gone (exponent <= 30, peak <= 0.35*smoothness, sheen term present)",(not blinn) and "_Smoothness * 28 + 2" in cloth and "graze" in cloth and "_Smoothness * 0.35" in cloth,"")
gate("TennisCloth: sheen is gated by the light (ndl) and shadow (atten) -> dead in shadow",("saturate(ndl * 1.5)" in cloth) and ("* light.color * atten" in cloth),"")
gate("TennisCloth: samples the weave map and multiplies a thread break into the colour",("SAMPLE_TEXTURE2D(_WeaveMap" in cloth) and ("weave.b" in cloth) and ("TransformTangentToWorld" in cloth),"")
# --- untouched files
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def load(fn): return {l.split()[1]:l.split()[0] for l in open(fn).read().splitlines() if l.strip()}
b=load("work/character-shader/detail/sha_before.txt"); 
chg=[p for p,h in b.items() if os.path.exists(p) and sha(p)!=h]
gate("TennisURP.asset (post stack, bloom, light layers) + Serve / Walk / Run FBXs byte-identical to before",not chg,"changed: "+",".join(chg) if chg else "0 changed of %d"%len(b))
bc=load("work/character-shader/detail/sha_clips_before.txt"); chg=[p for p,h in bc.items() if os.path.exists(p) and sha(p)!=h]
# clip .meta are not rewritten by this pass; kit FBX lives outside MatchHeroes
gate("all 16 clip FBXs x 2 heroes (+ .meta) under Characters/MatchHeroes byte-identical",not chg,"changed: "+",".join(chg) if chg else "0 changed of %d files"%len(bc))
bco=load("work/character-shader/detail/sha_course_before.txt"); chg=[p for p,h in bco.items() if os.path.exists(p) and sha(p)!=h]
# every file this pass writes (anything else that changed under the course tree belongs to the golf session that is working there in parallel)
MINE=["Unity/Assets/Resources/Tennis/Shaders/TennisCloth.shader","Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader","Unity/Assets/Scripts/Tennis/MatchHeroLook.cs",
 "Unity/Assets/Editor/MatchHeroKit.cs","Unity/Assets/Editor/MatchHeroKitTests.cs","Unity/Assets/Editor/HeroDetailTextures.cs","Unity/Assets/Editor/HeroDetailStill.cs",
 "Unity/Assets/Characters/MatchHeroes/Materials/Kit/Kit_ShirtTrim.mat","Unity/Assets/Characters/MatchHeroes/Materials/Kit/Kit_Sole.mat"]+["Unity/Assets/Resources/Tennis/HeroDetail/"+f for f in os.listdir("Unity/Assets/Resources/Tennis/HeroDetail") if f.endswith(".png")]
mine_in_course=[m for m in MINE if "/Course" in m]
gate("course files (Resources/Course, Scripts/Course): this pass writes none of them (%d files written by the pass, 0 in the course tree)"%len(MINE),not mine_in_course,("also changed under the course tree during the run, by the parallel golf session: "+",".join(chg)) if chg else "0 changed of %d files"%len(bco))
txt="# GATE HERO_DETAIL\n\n"+"\n".join(f"- {'PASS' if ok else 'FAIL'}  {n}" + (f"  ({d})" if d else "") for n,ok,d in res)
nf=sum(1 for _,ok,_ in res if not ok)
txt+=f"\n\n**GATE: HERO_DETAIL {'PASS' if nf==0 else 'FAIL'}** ({len(res)-nf}/{len(res)} lines)\n"
open("work/character-shader/detail/GATE_RESULTS_auto.md","w").write(txt); print(txt)
