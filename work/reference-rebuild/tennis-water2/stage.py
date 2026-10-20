from pathlib import Path
import hashlib,json
root=Path.cwd();out=root/'work/reference-rebuild/tennis-water2'
files=['Unity/Assets/Resources/Tennis/Shaders/TennisWater.shader','Unity/Assets/Scripts/Tennis/TennisResortMaterials.cs']
baseline={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files}
p=files[0];s=(root/p).read_text()
a='_Sparkle ("Sparkle", Float) = 6'
b=a+'''
        _FragmentFog("Actual surface-depth fog",Range(0,1))=0
        _SkyMap("Existing coastal sky reflection",2D)="black"{}
        _SkyHeading("Coastal sky heading",Float)=-45
        _ReflectionWeight("Cloud reflection variation",Range(0,1))=0
        _SunSheen("Rough sun reflection",Range(0,2))=0
        _WaterDebug("Fog contribution diagnostic",Float)=0'''
assert a in s;s=s.replace(a,b)
s=s.replace('TEXTURE2D(_ShoreMap); SAMPLER(sampler_ShoreMap);','TEXTURE2D(_ShoreMap); SAMPLER(sampler_ShoreMap);\n            TEXTURE2D(_SkyMap); SAMPLER(sampler_SkyMap);')
s=s.replace('float _DeepDistance, _WaveScale, _Sparkle, _UseShoreMap;', 'float _DeepDistance, _WaveScale, _Sparkle, _UseShoreMap, _FragmentFog, _SkyHeading, _ReflectionWeight, _SunSheen, _WaterDebug;')
a='''half3 colour = lerp(water * .72 + lit * .28, _Sky.rgb, fresnel * .42) + sun.color * sparkle;
                return half4(MixFog(colour, i.fog), 1);'''
b='''half3 reflectedSky=_Sky.rgb;
                if(_ReflectionWeight>.001)
                {
                    half3 reflected=reflect(-v,n);
                    float2 skyUV=float2(frac(atan2(reflected.z,reflected.x)/6.2831853+.5+_SkyHeading/360),
                        clamp(.5+asin(clamp(reflected.y,-1,1))/3.14159265,0.001,.999));
                    // The existing sky contributes only broad reflected cloud variation;
                    // explicit LOD keeps calm-water reflections from aliasing at distance.
                    half3 panorama=SAMPLE_TEXTURE2D_LOD(_SkyMap,sampler_SkyMap,skyUV,2).rgb;
                    reflectedSky=lerp(reflectedSky,panorama*half3(.45,.72,.94),_ReflectionWeight);
                }
                half3 colour = lerp(water * .72 + lit * .28, reflectedSky, fresnel * .42) + sun.color * sparkle;
                if(_SunSheen>.001)
                {
                    // A restrained rough dielectric lobe keeps the sunlight tied to
                    // actual view/light direction. No painted or random white speckles.
                    half nl=saturate(dot(n,sun.direction)),nv=saturate(dot(n,v)),nh=saturate(dot(n,h));
                    half a2=.0105h,denom=nh*nh*(a2-1)+1;
                    half distribution=a2/(3.14159265h*denom*denom);
                    half viewFresnel=.02h+.98h*pow(1-saturate(dot(v,h)),5);
                    half k=.0512h;
                    half masking=(nl/(nl*(1-k)+k))*(nv/(nv*(1-k)+k));
                    half sheen=distribution*viewFresnel*masking/max(4*nl*nv,.02h);
                    colour+=sun.color*min(sheen,.12h)*_SunSheen;
                }
                // The source ocean is one 2400x1500m box. Corner fog factors are
                // clamped far outside the visible water and interpolate incorrectly.
                // URP's world-position fog evaluates the actual fragment's view depth.
                half fog=lerp(i.fog,InitializeInputDataFog(float4(i.positionWS,1),i.fog),_FragmentFog);
                if(_WaterDebug>.5)
                    return half4((IsFogEnabled()?1-ComputeFogIntensity(fog):0).xxx,1);
                return half4(MixFog(colour, fog), 1);'''
assert a in s;s=s.replace(a,b)
target=out/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(s)
p=files[1];s=(root/p).read_text();a='sea.SetFloat("_Sparkle",1.4f);sea.SetFloat("_WaveScale",.28f);'
b=a+'''
            sea.SetFloat("_FragmentFog",Environment.GetEnvironmentVariable("TENNIS_WATER_VERTEX_FOG")=="1"?0:1);
            sea.SetTexture("_SkyMap",Resources.Load<Texture2D>("Course/Resort/SkyCoastalSmall"));
            sea.SetFloat("_SkyHeading",-45);sea.SetFloat("_ReflectionWeight",.18f);sea.SetFloat("_SunSheen",1.6f);
            if(int.TryParse(Environment.GetEnvironmentVariable("TENNIS_WATER_DEBUG"),out int debug))sea.SetFloat("_WaterDebug",debug);'''
assert a in s;s=s.replace(a,b);target=out/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(s)
manifest={'baseline':baseline,'sourceGeometry':'original Ocean water.001:8 vertices/6faces,2400x1500m','diagnosis':'per-vertex clamped corner fog washes broad visible water; use URP fragment view-depth fog','changes':['fragment fog','existing sky broad reflection18%','bounded rough dielectric sun sheen'],'unchanged':['all court/material1 settings','all geometry/collision','HeroLighting/renderer/post'],'actualGate':'PENDING fragment-vs-vertex actual comparison'}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
old=json.loads((root/'work/reference-rebuild/capture-tennis-resort-material1.json').read_text())[0]
jobs=[]
for name,control in [('reference-tennis-water2',False),('reference-tennis-water2-vertexfog-control',True)]:
 job={'name':name,'method':old['method'],'env':dict(old['env'])}
 job['env']['HERO_VENUE_OUT']=str(root/'proof/reference-rebuild'/('tennis-water2-vertexfog-control' if control else 'tennis-water2'))
 job['env']['HERO_VENUE_ONLY']='1_gameplay,14_reference_camera' if control else '1_gameplay,14_reference_camera,16_reference_a,18_clubhouse_roof'
 if control:job['env']['TENNIS_WATER_VERTEX_FOG']='1'
 jobs.append(job)
(root/'work/reference-rebuild/capture-tennis-water2.json').write_text(json.dumps(jobs,indent=2)+'\n')
print('Water2 staged; two-file baseline and matching fragment/vertex control config saved.')
