Shader "GolfArcade/DreamSky" {
 Properties { _Panorama("Coastal panorama",2D)="white"{} _Day("Daylight",Range(0,1))=1 _Sunset("Sunset",Range(0,1))=0 _Cloud("Cloud cover",Range(0,1))=0 _Magma("Magma",Float)=0 _Ice("Aurora",Float)=0 }
 SubShader {Tags{"Queue"="Background" "RenderType"="Background" "RenderPipeline"="UniversalPipeline"} Cull Off ZWrite Off
 Pass { HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 TEXTURE2D(_Panorama);SAMPLER(sampler_Panorama);
 CBUFFER_START(UnityPerMaterial) float _Day,_Sunset,_Cloud,_Magma,_Ice;CBUFFER_END
 struct A{float4 p:POSITION;};struct V{float4 p:SV_POSITION;float3 d:TEXCOORD0;};
 V vert(A a){V o;o.p=TransformObjectToHClip(a.p.xyz);o.d=a.p.xyz;return o;}
 half4 frag(V i):SV_Target{
 float3 d=normalize(i.d);float2 uv=float2(frac(atan2(d.z,d.x)/6.2831853+.35),clamp(.5+asin(clamp(d.y,-1,1))/3.14159265*2.0,.002,.998));
 half3 coast=SAMPLE_TEXTURE2D_LOD(_Panorama,sampler_Panorama,uv,0).rgb;
 half3 night=lerp(half3(.07,.13,.24),half3(.012,.025,.08),saturate(d.y));
 night=lerp(night,coast*half3(.12,.16,.25),.6);
 half3 c=lerp(night,coast,_Day);c=lerp(c,half3(.9,.38,.2),_Sunset*pow(1-saturate(d.y),4)*.65);
 c=lerp(c,half3(.12,.07,.19),_Magma*.3);c=lerp(c,lerp(half3(.04,.06,.10),d.y<.1?half3(.24,.29,.34):half3(.14,.18,.23),_Day),_Cloud*.65);
 float2 star=floor(uv*float2(1800,900));float hash=frac(sin(dot(star,float2(127.1,311.7)))*43758.5453);
 c+=step(.9985,hash)*(1-_Day)*(1-_Cloud)*smoothstep(.05,.3,d.y)*.5;
 float ribbon=exp(-pow((d.y-(.25+.08*sin(d.x*8+_Time.y*.025)+.06*sin(d.z*13)))*18,2));
 float curtains=.55+.45*sin(atan2(d.z,d.x)*80+sin(d.x*15)*3+_Time.y*.08);
 c+=ribbon*curtains*_Ice*(1-_Day)*(1-_Cloud)*lerp(half3(.05,.5,.35),half3(.3,.15,.5),saturate(d.y*2));
 float moon=pow(saturate(dot(d,normalize(float3(-.5,.6,.3)))),1800);c+=moon*(1-_Day)*half3(.8,.9,1);
 return half4(c,1);}
 ENDHLSL }
 }
}
