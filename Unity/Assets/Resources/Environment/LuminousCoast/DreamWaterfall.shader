Shader "GolfArcade/DreamWaterfall" {
SubShader {
 Tags {"RenderPipeline"="UniversalPipeline" "Queue"="Transparent" "RenderType"="Transparent"}
 Blend SrcAlpha OneMinusSrcAlpha ZWrite Off Cull Off
 Pass {Tags {"LightMode"="UniversalForward"}
 HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #pragma multi_compile_fog
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 struct A{float4 p:POSITION;float2 uv:TEXCOORD0;};struct V{float4 p:SV_POSITION;float3 w:TEXCOORD0;float2 uv:TEXCOORD1;half fog:TEXCOORD2;};
 V vert(A a){V o;o.w=TransformObjectToWorld(a.p.xyz);o.p=TransformWorldToHClip(o.w);o.uv=a.uv;o.fog=ComputeFogFactor(o.p.z);return o;}
 float hash(float2 p){return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);}
 float noise(float2 p){float2 a=floor(p),f=frac(p);f=f*f*(3-2*f);return lerp(lerp(hash(a),hash(a+float2(1,0)),f.x),lerp(hash(a+float2(0,1)),hash(a+1),f.x),f.y);}
 half4 frag(V i):SV_Target {
  float flow=i.w.y*.16+_Time.y*2.1;
  half ribbon=noise(float2(i.uv.x*12,flow));
  half mist=noise(float2(i.uv.x*28,flow*2.1));
  half edge=pow(saturate(sin(i.uv.x*3.14159265)),.65);
  half3 c=lerp(half3(.12,.46,.47),half3(.75,.93,.88),ribbon*.65+mist*.25);
  return half4(MixFog(c,i.fog),edge*(.26+ribbon*.38+mist*.15)*saturate(i.w.y*.20));
 }
 ENDHLSL
 }
}
}
