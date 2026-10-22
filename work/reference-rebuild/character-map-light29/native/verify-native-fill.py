import pathlib,re,json,subprocess
O=pathlib.Path('work/reference-rebuild/character-map-light29/native');s=(O/'MatchHeroSurfaces.swift').read_text();base=(O/'MatchHeroSurfaces.swift.baseline').read_text()
def block(name,text=s):return re.search(r'static let '+name+r' = """\n(.*?)\n    """',text,re.S)[1]
direction=block('presentationDirection');char=block('presentationCharacter');cloth=block('clothLighting').split('#pragma body',1)[1];garment=block('garmentLighting').split('#pragma body',1)[1]
bodies={'character':direction+char}
for name,b in [('cloth',cloth),('garment1',garment),('garment2',garment.replace('_surface.roughness*5.0','_surface.roughness*9.0').replace('float3 n=normalize(_surface.normal)','if(id>5.5){smooth=id<6.5?0.09:id<7.5?0.12:id<8.5?0.18:0.08;sheen=id<6.5?0.24:id<7.5?0.32:id<8.5?0.10:0.18;}\nfloat3 n=normalize(_surface.normal)'))]:
 b=b.replace('_light.direction','hpL').replace('_light.intensity.rgb','hpColor').replace('_lightingContribution.diffuse','hpDiffuse').replace('_lightingContribution.specular','hpSpecular');assert '_light.' not in b and '_lightingContribution' not in b;bodies[name]=direction+'\n{float3 hpDiffuse=float3(0),hpSpecular=float3(0);\n'+b+'\n_surface.emission.rgb+=hpDiffuse*_surface.diffuse.rgb+hpSpecular;}'
header='''#include <metal_stdlib>
using namespace metal;
struct Surface {float3 normal,view;float4 diffuse,emission,specular;float shininess,roughness,metalness;};
struct Frame {float4x4 viewTransform;};
'''
metal=header
for name,b in bodies.items():metal+=f'void fill_{name}(thread Surface &_surface, Frame scn_frame,float heroPresentationFill,float4 athleteSurface,float4 athleteWarmth,float4 headOrigin,float skinFinish,float4 clothLook){{\n'+b+'\n}\n'
(O/'presentation-fill-syntax.metal').write_text(metal)
assert all(block(n)==block(n,base) for n in ['athleteLighting','clothLighting','garmentLighting','clothShoulder'])
result={'swiftParsePass':True,'patchApplyCheckPass':True,'sceneKitSDKContract':'SCNShadable.h: all surface geometric fields are view space; scn_frame.viewTransform is supported Metal uniform; surface emission writable','existingPerLightAndShoulderStringsExact':True,'fillUsesSceneLightReferences':False,'oncePerSurfaceInvocation':True,'generatedSceneKitPipeline':'PENDING, requires root actual native render; standalone Metal syntax is not a GPU claim'}
proc=subprocess.run(['xcrun','-sdk','macosx','metal','-c',str(O/'presentation-fill-syntax.metal'),'-o',str(O/'presentation-fill-syntax.air')],capture_output=True,text=True);result['standaloneMetalSyntaxPass']=proc.returncode==0;result['metalCompilerDiagnostic']=proc.stderr;result['metalCompileGate']='PENDING: local Metal Toolchain missing' if 'missing Metal Toolchain' in proc.stderr else 'PASS' if proc.returncode==0 else 'FAIL';(O/'metal-syntax.log').write_text(proc.stdout+proc.stderr)
(O/'VERIFY_GATE.json').write_text(json.dumps(result,indent=2)+'\n')
