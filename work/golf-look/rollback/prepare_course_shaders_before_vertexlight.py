"""P3 candidate only. Shared core; no course vertex or scoring changes."""
from pathlib import Path
import json
W=Path(__file__).resolve().parents[1];C=W/'candidate/Unity'
D=C/'Assets/Resources/Course/Shaders';D.mkdir(parents=True,exist_ok=True)
core=r'''#ifndef GOLF_SURFACE_INCLUDED
#define GOLF_SURFACE_INCLUDED
#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
CBUFFER_START(UnityPerMaterial)
float4 _BaseColor,_BaseMap_ST,_EmissionColor,_StripeDirection;
half _Smoothness,_BumpScale,_Surface,_Bands,_StripeWidth,_SheenFromAlpha;
half _Wrap,_Rock,_Basalt,_Cap,_NormalEnabled,_EmissionEnabled;
CBUFFER_END
TEXTURE2D(_BaseMap);SAMPLER(sampler_BaseMap);
TEXTURE2D(_BumpMap);SAMPLER(sampler_BumpMap);
TEXTURE2D(_EmissionMap);SAMPLER(sampler_EmissionMap);
TEXTURE2D(_GolfEdgeMap);SAMPLER(sampler_GolfEdgeMap);
float4 _GolfEdgeBounds;
struct A {float4 p:POSITION;float3 n:NORMAL;float4 t:TANGENT;float2 uv:TEXCOORD0;UNITY_VERTEX_INPUT_INSTANCE_ID};
struct V {float4 p:SV_POSITION;float3 w:TEXCOORD0;half3 n:TEXCOORD1;half4 t:TEXCOORD2;float2 uv:TEXCOORD3;half fog:TEXCOORD4;UNITY_VERTEX_INPUT_INSTANCE_ID};
V GolfVertex(A a) {
 V o=(V)0;UNITY_SETUP_INSTANCE_ID(a);UNITY_TRANSFER_INSTANCE_ID(a,o);
 VertexPositionInputs p=GetVertexPositionInputs(a.p.xyz);VertexNormalInputs n=GetVertexNormalInputs(a.n,a.t);
 o.p=p.positionCS;o.w=p.positionWS;o.n=n.normalWS;o.t=half4(n.tangentWS,a.t.w*GetOddNegativeScale());
 o.uv=a.uv*_BaseMap_ST.xy+_BaseMap_ST.zw;o.fog=ComputeFogFactor(p.positionCS.z);return o;
}
float4 GolfShadow(A a):SV_POSITION {
 UNITY_SETUP_INSTANCE_ID(a);
 float3 p=TransformObjectToWorld(a.p.xyz),n=TransformObjectToWorldNormal(a.n);
 float4 clip=TransformWorldToHClip(ApplyShadowBias(p,n,_LightDirection));
 #if UNITY_REVERSED_Z
 clip.z=min(clip.z,UNITY_NEAR_CLIP_VALUE*clip.w);
 #else
 clip.z=max(clip.z,UNITY_NEAR_CLIP_VALUE*clip.w);
 #endif
 return clip;
}
float4 GolfDepth(A a):SV_POSITION {UNITY_SETUP_INSTANCE_ID(a);return TransformObjectToHClip(a.p.xyz);}
half4 GolfZero():SV_Target {return 0;}
#endif
'''
# Shadow helpers need the same declarations in every shader/pass.
core=core.replace('float4 GolfShadow(A a)', '#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"\nfloat3 _LightDirection;\nfloat4 GolfShadow(A a)')
(D/'GolfSurface.hlsl').write_text(core)
shadow_receiver='half GolfShadowAttenuation(float3 world)\n            {\n                #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)\n                return MainLightRealtimeShadow(ComputeScreenPos(TransformWorldToHClip(world)));\n                #elif defined(MAIN_LIGHT_CALCULATE_SHADOWS)\n                float4 sc = TransformWorldToShadowCoord(world);\n                ShadowSamplingData data = GetMainLightShadowSamplingData();\n                float2 stepUV = data.shadowmapSize.xy * .45;\n                half a = SAMPLE_TEXTURE2D_SHADOW(_MainLightShadowmapTexture, sampler_LinearClampCompare, sc.xyz + float3(stepUV,0));\n                half b = SAMPLE_TEXTURE2D_SHADOW(_MainLightShadowmapTexture, sampler_LinearClampCompare, sc.xyz - float3(stepUV,0));\n                half attenuation = LerpWhiteTo((a+b)*.5h, GetMainLightShadowParams().x);\n                if (BEYOND_SHADOW_FAR(sc)) attenuation=1;\n                return lerp(attenuation, 1, GetMainLightShadowFade(world));\n                #else\n                return 1;\n                #endif\n            }\n'
fragment=r'''
#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
#include "../../Tennis/Shaders/HeroLighting.hlsl"
half GolfBand(float phase) {
 // Integrate away bands smaller than one pixel. No frame-dependent inputs.
 half fade=saturate(1-fwidth(phase)*2);
 return sin(phase*6.2831853)*fade;
}
half3 GolfLight(Light l,half3 n,half3 v,half3 albedo,half gloss) {
 half nl=saturate(dot(n,l.direction));
 half wrapped=HeroWrapped(n,l.direction,_Wrap);
 half grazing=pow(1-saturate(dot(n,v)),4)*gloss*.10h;
 half spec=pow(saturate(dot(n,SafeNormalize(l.direction+v))),12+gloss*20)*gloss*.08h*nl;
 return (albedo*(wrapped+grazing*nl)+spec)*l.color*l.distanceAttenuation*l.shadowAttenuation;
}
half4 GolfFragment(V i):SV_Target {
 UNITY_SETUP_INSTANCE_ID(i);
 half3 n=normalize(i.n),v=SafeNormalize(GetWorldSpaceViewDir(i.w));
 half4 base;
 #if defined(GOLF_ROCK)
  // Metric world coordinates: cliff UV aspect never stretches a stratum.
  half3 weight=abs(n);weight*=weight;weight/=max(dot(weight,half3(1,1,1)),.001h);
  float3 p=i.w*.09;
  base=SAMPLE_TEXTURE2D(_BaseMap,sampler_BaseMap,p.zy)*weight.x;
  base+=SAMPLE_TEXTURE2D(_BaseMap,sampler_BaseMap,p.xz)*weight.y;
  base+=SAMPLE_TEXTURE2D(_BaseMap,sampler_BaseMap,p.xy)*weight.z;
  half strata=GolfBand(i.w.y*.22+sin(i.w.x*.025)*.10);
  base.rgb*=1+strata*.075h;
  half cap=smoothstep(.65h,.94h,n.y)*_Cap;
  base.rgb=lerp(base.rgb,base.rgb*half3(.70h,1.10h,.55h),cap);
  // Basalt is a broad static column rhythm, filtered before a phone can alias it.
  half columns=GolfBand(i.w.x*.16+i.w.z*.12);
  base.rgb*=1+columns*_Basalt*.07h;
 #else
  base=SAMPLE_TEXTURE2D(_BaseMap,sampler_BaseMap,i.uv);
  if (_NormalEnabled>.5h) {
   half3 ts=UnpackNormal(SAMPLE_TEXTURE2D(_BumpMap,sampler_BumpMap,i.uv));
   half fade=1-smoothstep(.12h,.6h,max(length(ddx(i.uv)),length(ddy(i.uv)))*64);
   ts.xy*=_BumpScale*fade;
   half3 t=SafeNormalize(i.t.xyz),b=cross(n,t)*i.t.w;
   n=SafeNormalize(t*ts.x+b*ts.y+n*ts.z);
  }
  half4 edges=SAMPLE_TEXTURE2D(_GolfEdgeMap,sampler_GolfEdgeMap,(i.w.xz-_GolfEdgeBounds.xy)*_GolfEdgeBounds.zw)*32;
  half phase=dot(i.w.xz,_StripeDirection.xz)/max(_StripeWidth,.5h);
  half bands=GolfBand(phase)*_Bands;
  if (_Surface>1.5h&&_Surface<2.5h) bands+=GolfBand(dot(i.w.xz,_StripeDirection.zx*float2(-1,1))/max(_StripeWidth,.5h))*.018h;
  base.rgb*=1+bands;
  // Distances come from the original playable top-surface boundaries.
  if (_Surface<4.5h) {
   half fringe=(1-smoothstep(.6h,2.4h,edges.r))*step(1.5h,_Surface)*step(_Surface,3.5h);
   base.rgb=lerp(base.rgb,base.rgb*half3(.82h,.93h,.79h),fringe*.45h);
   half apron=1-smoothstep(.3h,1.8h,edges.g);
   base.rgb*=1-apron*.045h;
  } else if (_Surface<5.5h) {
   half lip=1-smoothstep(.3h,1.8h,edges.b);
   half damp=1-smoothstep(.5h,5h,edges.a);
   base.rgb*=1+lip*.10h-damp*.12h;
   half ripple=GolfBand(dot(i.w.xz,float2(.8,.6))*1.4);
   n=SafeNormalize(n+half3(.025h*ripple,0,.018h*ripple));
  }
 #endif
 half3 albedo=base.rgb*_BaseColor.rgb;
 half gloss=_Smoothness*lerp(1,base.a,_SheenFromAlpha);
 Light main=HeroMain(GetMainLight());
 main.shadowAttenuation=GolfShadowAttenuation(i.w);
 half3 colour=GolfLight(main,n,v,albedo,gloss)+HeroAmbient(n)*albedo;
 #if defined(_ADDITIONAL_LIGHTS)
 uint count=GetAdditionalLightsCount();
 for(uint li=0;li<count;li++)colour+=GolfLight(GetAdditionalLight(li,i.w),n,v,albedo,gloss);
 #endif
 #if defined(GOLF_ROCK)
 if(_EmissionEnabled>.5h)colour+=base.aaa*_EmissionColor.rgb;
 #endif
 return half4(MixFog(colour,i.fog),1);
}
'''
props=r'''
 [MainTexture] _BaseMap("Albedo / band sheen",2D)="white"{}
 [MainColor] _BaseColor("Tint",Color)=(1,1,1,1)
 _BumpMap("Blade / ripple normal",2D)="bump"{}
 _EmissionMap("Rock fissures",2D)="black"{}
 _EmissionColor("Emission",Color)=(0,0,0,1)
 _Smoothness("Sheen",Float)=.12
 _BumpScale("Normal strength",Float)=.6
 _Surface("0 rough 1 fairway 2 green 3 tee 4 fringe 5 sand",Float)=0
 _Bands("Band amplitude",Float)=.05
 _StripeWidth("Band period (yards)",Float)=5
 _StripeDirection("Mowing direction",Vector)=(1,0,0,0)
 _SheenFromAlpha("Albedo alpha sheen",Float)=0
 _Wrap("Shared wrap",Float)=.5
 _Rock("Triplanar rock",Float)=0
 _Basalt("Column rhythm",Float)=0
 _Cap("Grass cap",Float)=0
 _NormalEnabled("Normal map present",Float)=0
 _EmissionEnabled("Emission map present",Float)=0
'''
import re
core=re.sub(r'(?<![.\w])(\d+)h\b',r'\1.0h',core)
(D/'GolfSurface.hlsl').write_text(core)
fragment=re.sub(r'(?<![.\w])(\d+)h\b',r'\1.0h',fragment)
fragment=fragment.replace('half GolfBand',shadow_receiver+'\nhalf GolfBand')
for name in ['GolfGround','GolfRock']:
 shader='Shader "GolfArcade/'+name+'" {\nProperties {\n'+props+'\n}\nSubShader {\nTags {"RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry"}\nHLSLINCLUDE\n#include "GolfSurface.hlsl"\nENDHLSL\n'
 rock_define='#define GOLF_ROCK 1\n' if name=='GolfRock' else ''
 shader+='Pass { Name "ForwardLit" Tags {"LightMode"="UniversalForward"}\nHLSLPROGRAM\n#pragma target 3.0\n#pragma vertex GolfVertex\n#pragma fragment GolfFragment\n#pragma multi_compile_instancing\n#pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN\n#pragma multi_compile _ _ADDITIONAL_LIGHTS\n#pragma multi_compile_fragment _ _SHADOWS_SOFT\n#pragma multi_compile_fog\n'+rock_define+fragment+'\nENDHLSL\n}\n'
 for pname,lightmode,vertex,frag,state in [('ShadowCaster','ShadowCaster','GolfShadow','GolfZero','ZWrite On ZTest LEqual ColorMask 0'),('DepthOnly','DepthOnly','GolfDepth','GolfZero','ZWrite On ColorMask R'),('DepthNormals','DepthNormals','GolfVertex','GolfNormals','ZWrite On')]:
  shader+=f'Pass {{Name "{pname}" Tags {{"LightMode"="{lightmode}"}} {state}\nHLSLPROGRAM\n#pragma target 3.0\n#pragma vertex {vertex}\n#pragma fragment {frag}\n#pragma multi_compile_instancing\n'
  if pname=='DepthNormals':shader+='half4 GolfNormals(V i):SV_Target {return half4(normalize(i.n),0);}\n'
  shader+='ENDHLSL\n}\n'
 shader+='}\nFallBack Off\n}\n';(D/(name+'.shader')).write_text(shader)
(W/'data/course_shader_candidate.json').write_text(json.dumps(dict(installed=False,shaders=['GolfArcade/GolfGround','GolfArcade/GolfRock'],variants=dict(forward_before_stripping=4*2*2*4*2,other_passes=2),fetches=dict(ground_base=1,ground_normal=1,ground_edges=1,rock_triplanar=3,rock_emission=1,shadow='URP selected variant; compile stats pending'),G11='FAIL until compiled Metal stats/device timing'),indent=2)+'\n')
print('Course shaders prepared; not installed, compiled or certified')
