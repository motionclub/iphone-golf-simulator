from pathlib import Path
R=Path.cwd();W=R/'work/full-visual-overhaul/tennis';S=R/'Unity/Assets/Scripts/Tennis';H=R/'Unity/Assets/Resources/Tennis/Shaders'
# Explicit longitude texture gradients prevent implicit derivatives spanning the panorama wrap.
sky=(R/'Unity/Assets/Resources/Course/Shaders/GolfResortSky.shader').read_text().replace('GolfArcade/GolfResortSky','GolfArcade/TennisCoastalSky');(W/'TennisCoastalSky.shader.stage8').write_text(sky)
# Same data convention is measured from the loaded FBX, not guessed from its screenshot.
s=(S/'TennisStandsCrowd.cs').read_text().replace('''                foreach(var r in selected.GetComponentsInChildren<MeshRenderer>(true))''','''                if(i==0)
                {
                    var head=Part(selected,"HEAD");var mf=head?head.GetComponent<MeshFilter>():null;
                    if(mf&&mf.sharedMesh)
                    {
                        var expected=new Color(.76f,.44f,.27f);var gamma=expected.gamma;float linearDistance=10,gammaDistance=10;Color found=Color.white;
                        foreach(var c in mf.sharedMesh.colors)
                        {
                            float dl=Mathf.Pow(c.r-expected.r,2)+Mathf.Pow(c.g-expected.g,2)+Mathf.Pow(c.b-expected.b,2);
                            float dg=Mathf.Pow(c.r-gamma.r,2)+Mathf.Pow(c.g-gamma.g,2)+Mathf.Pow(c.b-gamma.b,2);
                            linearDistance=Mathf.Min(linearDistance,dl);if(dg<gammaDistance){gammaDistance=dg;found=c;}
                        }
                        material.SetFloat("_ColorsAreSRGB",gammaDistance<linearDistance?1:0);
                        Debug.Log($"[CrowdColours] vertex skin {found} linearDistance={linearDistance:F6} gammaDistance={gammaDistance:F6} decodeSRGB={gammaDistance<linearDistance}");
                    }
                }
                foreach(var r in selected.GetComponentsInChildren<MeshRenderer>(true))''',1)
(W/'TennisStandsCrowd.cs.stage8').write_text(s)
s=(H/'TennisSpectator.shader').read_text().replace('Properties { _Smoothness("Sport fabric polish",Range(0,1))=.17 }','Properties { _Smoothness("Sport fabric polish",Range(0,1))=.17 _ColorsAreSRGB("FBX color convention",Range(0,1))=0 }').replace('half _Smoothness;','half _Smoothness,_ColorsAreSRGB;').replace('s.albedo=i.c.rgb;','s.albedo=lerp(i.c.rgb,SRGBToLinear(i.c.rgb),_ColorsAreSRGB);').replace('c.rgb=MixFog(c.rgb,i.fog);','c.rgb+=s.albedo*half3(.18,.16,.13);c.rgb=MixFog(c.rgb,i.fog);')
(W/'TennisSpectator.shader.stage8').write_text(s)
# A continuous but shallower stream shell; bright long flow cores, dark side banks.
s=(S/'TennisVenueBuilder.Volcano.cs').read_text().replace('-48*Mathf.Sin(t*Mathf.PI)','-18*Mathf.Sin(t*Mathf.PI)').replace('(1.15f+.18f*Mathf.Sin(t*13+phase))','(.65f+.10f*Mathf.Sin(t*13+phase))')
(W/'TennisVenueBuilder.Volcano.cs.stage8').write_text(s)
s=(H/'TennisLava.shader').read_text();at=s.index('                half fog = InitializeInputDataFog');s=s[:at]+'''                if(_Stream>.5h)
                {
                    // Mesh U wraps once around the shallow closed stream. Cosine
                    // maps it to a consistent width coordinate, with hot fronts
                    // and restrained cool side banks rather than transverse bars.
                    float across=cos(i.uv.x*6.2831853);
                    float along=i.uv.y;
                    float bend=(LavaNoise(float2(along*.36,17))-.5)*.27;
                    half core=1-smoothstep(.21,.90,abs(across-bend));
                    half strand=LavaNoise(float2(across*5.5,along*.30-_Time.y*.28));
                    half scab=smoothstep(.50,.77,LavaNoise(float2(across*2.7+9,along*.48-_Time.y*.14)));
                    half motion=core*(.72h+strand*.28h)*(1-scab*.55h);
                    half3 dark=half3(.015h,.013h,.012h)+half3(.045h,.008h,.001h)*core;
                    half3 hotCore=lerp(_Flow.rgb*.72h,_Hot.rgb,saturate(core*.60h+strand*.28h));
                    colour=lerp(dark,hotCore,motion);
                }
''' + s[at:];(W/'TennisLava.shader.stage8').write_text(s)
# Measured crowd bounds avoid cropping, isolated variants explicitly remove foreground foliage.
p=R/'Unity/Assets/Editor/TennisCrowdProof.cs';s=p.read_text();old='''{var fan=GameObject.Find("Seated sporting fan "+i);if(!fan)continue;var at=fan.transform.position+Vector3.up*.62f;Shot(cam,Path.Combine(dir,"seated_variant_"+i+".png"),at+new Vector3(3,1,.8f),at,640,640);}''';new='''{
    var fan=GameObject.Find("Seated sporting fan "+i);if(!fan)continue;
    var rs=fan.GetComponentsInChildren<Renderer>();var bounds=rs[0].bounds;foreach(var r in rs)bounds.Encapsulate(r.bounds);
    var foliage=Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None);var hidden=new System.Collections.Generic.List<Renderer>();
    foreach(var r in foliage)if(r.enabled&&r.name.StartsWith("Tennis foliage pocket")){r.enabled=false;hidden.Add(r);}
    float distance=bounds.size.y/(2*Mathf.Tan(17.5f*Mathf.Deg2Rad))*1.24f;
    var at=bounds.center;Shot(cam,Path.Combine(dir,"seated_variant_"+i+".png"),at+new Vector3(distance,.25f,.38f),at,640,640);
    foreach(var r in hidden)r.enabled=true;
   }''';assert old in s;s=s.replace(old,new)
s=s.replace('   crowd.Cheer(1);','''   // Diagnostic only: a sky-only image distinguishes a panorama derivative seam
   // from a floating legacy mesh. Restore exact original enabled states afterwards.
   var renderers=Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None);var enabled=new bool[renderers.Length];
   for(int i=0;i<renderers.Length;i++){enabled[i]=renderers[i].enabled;renderers[i].enabled=false;}
   Shot(cam,Path.Combine(dir,"sky_only.png"),cam.transform.position,cam.transform.position+cam.transform.forward,1920,1080);
   for(int i=0;i<renderers.Length;i++)renderers[i].enabled=enabled[i];
   crowd.Cheer(1);''')
s=s.replace('Actual visual review required.','Actual visual review required. Variant close-ups isolate foreground foliage only; group and cheer retain the complete actual scene.')
(W/'TennisCrowdProof.cs.stage8').write_text(s)
print('World8 staged: analytic sky gradients, measured sRGB crowd decoder + warm bounce, bound-framed portraits, shallow continuous stream with hot longitudinal core.')
