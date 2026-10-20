from pathlib import Path
W=Path('work/full-visual-overhaul/tennis');S=Path('Unity/Assets/Scripts/Tennis');H=Path('Unity/Assets/Resources/Tennis/Shaders')
p=W/'TennisVenueBuilder.Volcano.cs.stage7';s=p.read_text();a=s.index('                float colF=thetaDeg/360f*Around;',s.index('static void Fall('));b=s.index('\n            static void Falls(',a)
s=s[:a]+'''                float colF=thetaDeg/360f*Around;var bottom=Grid(bottomRow,colF);var top=Grid(topRow,colF);
                float bottomR=new Vector2(bottom.x,bottom.z).magnitude-5,topR=new Vector2(top.x,top.z).magnitude-4;
                const int along=104,around=16;int start=mb.Count;
                Vector3 Centre(float t)
                {
                    // One broad continuous flow clears the terraced overhangs. The
                    // inward bow joins the same source lip and lake landing envelope.
                    float radius=Mathf.Lerp(bottomR,topR,t)-48*Mathf.Sin(t*Mathf.PI);
                    float theta=(thetaDeg+Mathf.Sin(t*5.2f+phase)*1.4f)*Mathf.Deg2Rad;
                    return new Vector3(Mathf.Cos(theta)*radius,Mathf.Lerp(LakeY,top.y+1.2f,t),Mathf.Sin(theta)*radius);
                }
                for(int row=0;row<=along;row++)
                {
                    float t=row/(float)along;var c=Centre(t);
                    var tangent=(Centre(Mathf.Min(1,t+.005f))-Centre(Mathf.Max(0,t-.005f))).normalized;
                    var across=new Vector3(-c.z,0,c.x).normalized;
                    var front=Vector3.Cross(across,tangent).normalized;
                    float width=widthRiser*(.84f+.07f*Mathf.Sin(t*7+phase)+.045f*Mathf.Sin(t*15+phase*1.6f));
                    for(int ring=0;ring<=around;ring++)
                    {
                        float angle=ring/(float)around*Mathf.PI*2;
                        var p=c+across*(Mathf.Cos(angle)*width*.5f)+front*(Mathf.Sin(angle)*(1.15f+.18f*Mathf.Sin(t*13+phase)));
                        mb.Add(p,new Vector2(ring/(float)around,(c.y-LakeY)/18));
                    }
                }
                for(int row=0;row<along;row++)for(int ring=0;ring<around;ring++)
                {
                    int p=start+row*(around+1)+ring,q=p+around+1;
                    // Closed stream ring, outward normals all along the flow.
                    mb.T.AddRange(new[]{p,q,p+1,p+1,q,q+1});
                }
            }
''' +s[b:];s=s.replace('"Course/Shaders/GolfLava"','"Tennis/Shaders/TennisLava"').replace('m.SetFloat("_WorldUV",1);','m.SetFloat("_WorldUV",vertical?0:1);m.SetFloat("_Stream",vertical?1:0);').replace('fallTex,fallGlow,.82f,18,true','fallTex,fallGlow,.93f,18,true');p.write_text(s)
s=Path('Unity/Assets/Resources/Course/Shaders/GolfLava.shader').read_text().replace('GolfArcade/GolfLava','GolfArcade/TennisLava').replace('_SlopeFlow ("Consistent vertical flow projection",Range(0,1))=0','_SlopeFlow ("Consistent vertical flow projection",Range(0,1))=0\n        _Stream("Stream-aligned plate field",Range(0,1))=0').replace('half _Cooling,_SlopeFlow;','half _Cooling,_SlopeFlow,_Stream;').replace('float2 field=pw/max(_PlateScale,1);','float2 field=lerp(pw/max(_PlateScale,1),i.uv*float2(1.8,.8),_Stream);');(W/'TennisLava.shader.stage7').write_text(s)
s=(H/'TennisCoastalSky.shader').read_text().replace('half3 sky=SAMPLE_TEXTURE2D(_Panorama,sampler_Panorama,uv).rgb;','float edge=min(uv.x,1-uv.x);\n    uv.x=lerp(.008,.992,uv.x);\n    half3 sky=SAMPLE_TEXTURE2D(_Panorama,sampler_Panorama,uv).rgb;').replace('float edge=min(uv.x,1-uv.x);float blend=','float blend=');(W/'TennisCoastalSky.shader.stage7').write_text(s)
s=(H/'TennisWater.shader').read_text().replace('surf*=.65+.35*sin(i.positionWS.x*.37+i.positionWS.z*.21+_Time.y*.32);','surf*=.85+.15*sin(i.positionWS.x*.09+i.positionWS.z*.13+_Time.y*.32);').replace('surf*.42','surf*.22');(W/'TennisWater.shader.stage7').write_text(s)
s=(S/'TennisVenueFx.cs').read_text().replace('if (Material) glow = Material.GetColor("_EmissionColor");','if (Material && Material.HasProperty("_EmissionColor")) glow = Material.GetColor("_EmissionColor");').replace('Material.SetColor("_EmissionColor", glow *','if(Material.HasProperty("_EmissionColor")) Material.SetColor("_EmissionColor", glow *');(W/'TennisVenueFx.cs.stage7').write_text(s)
print('continuous closed lava stream and measured shore shading staged')
