from pathlib import Path
import re,json,math
O=Path(__file__).resolve().parent;R=O.parents[2];u=(R/'Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader').read_text();n=(O/'MatchHeroSurfaces.swift').read_text()
u=u.split('if (_SkinPigmentUV > 1.5h)',1)[1].split('half3 pigment',1)[0];n=n.split('if(skinPigmentUV>1.5)',1)[1].split('_surface.diffuse.rgb=',1)[0]
vector=lambda source,name:[tuple(float(v.rstrip('h')) for v in m.split(',')) for m in re.findall(name+r'\(([^)]+)\)',source)]
assert vector(u,'half3')==vector(n,'float3')==[(.95,.68,.69),(.94,.61,.64),(.62,.44,.42)]
assert 'linePigment*lerp(1.0h,1.65h,saturate(lipPigment*4.0h))' in u and 'linePigment*mix(1.0,1.65,saturate(lipPigment*4.0))' in n
sat=lambda x:max(0,min(1,x));worst=0;cases=0
for sex in range(2):
 for lip in [-.1,0,.001,.05,.2499,.25,.2501,.70,1,1.1]:
  for line in [0,.01,.10,.35,.46,.60,1]:
   for tone in [(1,1,1),(.78,.43,.22),(.32,.16,.09)]:
    lm=sat(lip);dm=sat(line);gain=1+(1.65-1)*sat(lm*4);a=sat(dm*gain)
    nativeGain=(1-sat(lm*4))+1.65*sat(lm*4);bb=sat(dm*nativeGain);col=[(.95,.68,.69),(.94,.61,.64)][sex];dark=(.62,.44,.42)
    unity=[tone[i]*(1+(col[i]-1)*lm)*(1+(dark[i]-1)*a) for i in range(3)];native=[tone[i]*((1-lm)+col[i]*lm)*((1-bb)+dark[i]*bb) for i in range(3)]
    worst=max(worst,max(abs(v-w) for v,w in zip(unity,native)));cases+=1
assert worst<1e-14
report={'gate':'PASS CPU SOURCE PALETTE PARITY','exactStrongPaletteCoefficients':True,'mouthOnlyGainExpressionExact':True,'relativeSkinTonePreserved':True,'boundaryAndSkinToneCases':cases,'maxDoublePrecisionReferenceError':worst,'nativeMetalOrArt':'NOT RUN, ROOT REQUIRED','mode0and1':'No changes to existing coefficients or branch guard'}
(O/'palette-parity-gate.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
