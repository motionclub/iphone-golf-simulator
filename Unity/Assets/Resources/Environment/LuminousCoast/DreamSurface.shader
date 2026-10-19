Shader "GolfArcade/DreamCoastSurface" {
Properties {
 _Metallic("Metal",Range(0,1))=0
 _Smoothness("Smoothness",Range(0,1))=.2
 _Detail("Rock detail",Range(0,1))=0
 _Leaf("Leaf transmission",Range(0,1))=0
 _Cull("Cull",Float)=2
 _RockMap("Rock color",2D)="white"{}
 _RockNormal("Rock normal",2D)="bump"{}
}
SubShader {
 Tags {"RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry"}
 Cull [_Cull]
 HLSLINCLUDE
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
 CBUFFER_START(UnityPerMaterial)
 half _Metallic,_Smoothness,_Detail,_Leaf,_Cull;
 CBUFFER_END
 TEXTURE2D(_RockMap);SAMPLER(sampler_RockMap);
 TEXTURE2D(_RockNormal);SAMPLER(sampler_RockNormal);
 struct A {float4 p:POSITION;float3 n:NORMAL;half4 c:COLOR;UNITY_VERTEX_INPUT_INSTANCE_ID};
 struct V {float4 p:SV_POSITION;float3 w:TEXCOORD0;half3 n:TEXCOORD1;half4 c:TEXCOORD2;half fog:TEXCOORD3;};
 V vert(A a){UNITY_SETUP_INSTANCE_ID(a);V o;o.w=TransformObjectToWorld(a.p.xyz);o.p=TransformWorldToHClip(o.w);o.n=TransformObjectToWorldNormal(a.n);o.c=a.c;o.fog=ComputeFogFactor(o.p.z);return o;}
 ENDHLSL
 Pass {Name "ForwardLit" Tags {"LightMode"="UniversalForward"}
 HLSLPROGRAM
 #pragma target 3.0
 #pragma vertex vert
 #pragma fragment frag
 #pragma multi_compile_instancing
 #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
 #pragma multi_compile _ _ADDITIONAL_LIGHTS
 #pragma multi_compile_fragment _ _SHADOWS_SOFT
 #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
 #pragma multi_compile_fog
 half4 frag(V i, FRONT_FACE_TYPE face:FRONT_FACE_SEMANTIC):SV_Target {
  half3 n=normalize(i.n)*IS_FRONT_VFACE(face,1,-1);
  half3 color=SRGBToLinear(i.c.rgb);
  if(_Detail>.1h) {
   half3 weights=pow(abs(n),4);weights/=max(dot(weights,1),.001);
   float3 p=i.w*.18;
   half3 detail=SAMPLE_TEXTURE2D(_RockMap,sampler_RockMap,p.zy).rgb*weights.x+SAMPLE_TEXTURE2D(_RockMap,sampler_RockMap,p.xz).rgb*weights.y+SAMPLE_TEXTURE2D(_RockMap,sampler_RockMap,p.xy).rgb*weights.z;
   half value=dot(detail,half3(.2126,.7152,.0722));color*=lerp(1,clamp(.72+value*2.4,.60,1.25),_Detail);
   half3 nx=UnpackNormal(SAMPLE_TEXTURE2D(_RockNormal,sampler_RockNormal,p.zy));
   half3 ny=UnpackNormal(SAMPLE_TEXTURE2D(_RockNormal,sampler_RockNormal,p.xz));
   half3 nz=UnpackNormal(SAMPLE_TEXTURE2D(_RockNormal,sampler_RockNormal,p.xy));
   n=normalize(n+half3(ny.x*weights.y+nz.x*weights.z,nx.y*weights.x+nz.y*weights.z,nx.x*weights.x+ny.y*weights.y)*_Detail*.25);
  }
  InputData input=(InputData)0;input.positionWS=i.w;input.normalWS=n;input.viewDirectionWS=GetWorldSpaceNormalizeViewDir(i.w);
  input.shadowCoord=TransformWorldToShadowCoord(i.w);input.fogCoord=i.fog;input.bakedGI=SampleSH(n);input.normalizedScreenSpaceUV=GetNormalizedScreenSpaceUV(i.p);input.shadowMask=half4(1,1,1,1);
  SurfaceData surface=(SurfaceData)0;surface.albedo=color;surface.metallic=_Metallic;surface.specular=half3(.04,.04,.04);surface.smoothness=_Smoothness;surface.normalTS=half3(0,0,1);surface.occlusion=1;surface.alpha=1;
  Light sun=GetMainLight(input.shadowCoord);
  surface.emission=color*_Leaf*.12*saturate(dot(-n,sun.direction))*sun.color*sun.shadowAttenuation;
  return half4(MixFog(UniversalFragmentPBR(input,surface).rgb,i.fog),1);
 }
 ENDHLSL
 }
 Pass {Name "ShadowCaster" Tags {"LightMode"="ShadowCaster"} ColorMask 0
 HLSLPROGRAM
 #pragma vertex shadow
 #pragma fragment zero
 #pragma multi_compile_instancing
 float3 _LightDirection;
 V shadow(A a){V o=vert(a);o.p=TransformWorldToHClip(ApplyShadowBias(o.w,o.n,_LightDirection));
 #if UNITY_REVERSED_Z
 o.p.z=min(o.p.z,UNITY_NEAR_CLIP_VALUE*o.p.w);
 #else
 o.p.z=max(o.p.z,UNITY_NEAR_CLIP_VALUE*o.p.w);
 #endif
 return o;}
 half4 zero(V i):SV_Target{return 0;}
 ENDHLSL
 }
 Pass {Name "DepthOnly" Tags {"LightMode"="DepthOnly"} ColorMask R
 HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment zero
 #pragma multi_compile_instancing
 half4 zero(V i):SV_Target{return 0;}
 ENDHLSL
 }
 Pass {Name "DepthNormals" Tags {"LightMode"="DepthNormals"}
 HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment normal
 #pragma multi_compile_instancing
 half4 normal(V i):SV_Target{return half4(normalize(i.n),0);}
 ENDHLSL
 }
}
}
