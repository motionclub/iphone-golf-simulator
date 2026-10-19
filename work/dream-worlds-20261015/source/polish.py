from pathlib import Path
# World materials must follow the clock, including authored wrap-light shaders.
p=Path('Unity/Assets/Resources/Environment/Shaders/EnvironmentSurface.hlsl');s=p.read_text().replace('half _EnvironmentWetness,','half _DreamNight;\nhalf _EnvironmentWetness,');s=s.replace('    if(_EnvironmentDepthEnabled<.5h)return MixFog(color,fogFactor);','    color*=lerp(half3(1,1,1),half3(.22,.30,.48),_DreamNight);\n    if(_EnvironmentDepthEnabled<.5h)return MixFog(color,fogFactor);');p.write_text(s)
for name in ['GolfCoastalTurf.shader','GolfRock.shader','GolfBotanical.shader','GolfIce.shader','GolfBasaltColumns.shader']:
 p=Path('Unity/Assets/Resources/Course/Shaders')/name;s=p.read_text();first='#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"';
 if first in s:s=s.replace(first,first+'\n   half _DreamNight;',1)
 else:
  first='#include "GolfSurface.hlsl"';s=s.replace(first,first+'\n half _DreamNight;',1)
 for variable in ['colour','c']:
  s=s.replace(f'MixFog({variable},',f'MixFog({variable}*lerp(half3(1,1,1),half3(.22,.30,.48),_DreamNight),')
 p.write_text(s)
p=Path('Unity/Assets/Scripts/Environment/DreamEnvironment.cs');s=p.read_text().replace('            if(Current)Current.Release();','            if(Current){var previous=Current;previous.Release();Destroy(previous.gameObject);}')
s=s.replace('            Shader.SetGlobalFloat("_DreamNight",1-day);','            Shader.SetGlobalFloat("_DreamNight",1-day);\n            Shader.SetGlobalFloat("_EnvironmentWeatherEnabled",1);');p.write_text(s)
p=Path('Unity/Assets/Scripts/Environment/WeatherDirector.cs');s=p.read_text().replace('bool active=EnvironmentLook.Stage>=5 && EnvironmentLook.Active;','bool active=DreamEnvironment.Current || EnvironmentLook.Stage>=5 && EnvironmentLook.Active;');p.write_text(s)
# Natural stone surfaces retain the analytic sphere envelope, with <=4% inset visual relief.
p=Path('Unity/Assets/Scripts/Game/MoverView.cs');s=p.read_text().replace('                        stone.GetComponent<Renderer>().sharedMaterial.SetFloat("_Smoothness",.18f);','''                        if(m.Kind==MoverKind.RockGate){
                            var mesh=Instantiate(stone.GetComponent<MeshFilter>().sharedMesh);var vertices=mesh.vertices;
                            for(int k=0;k<vertices.Length;k++){var v=vertices[k];vertices[k]*=.96f+.04f*Mathf.Sin(v.x*13+v.y*17+v.z*9);}
                            mesh.vertices=vertices;mesh.RecalculateNormals();stone.GetComponent<MeshFilter>().sharedMesh=mesh;
                            var mat=new Material(Shader.Find("Universal Render Pipeline/Lit"));mat.SetColor("_BaseColor",new Color(.63f,.68f,.67f));
                            mat.SetTexture("_BaseMap",Resources.Load<Texture2D>("Course/Resort/CoastalCliffScan_C"));mat.SetTexture("_BumpMap",Resources.Load<Texture2D>("Course/Resort/CoastalCliffScan_N"));mat.EnableKeyword("_NORMALMAP");mat.SetFloat("_Smoothness",.15f);stone.GetComponent<Renderer>().sharedMaterial=mat;
                        }''');p.write_text(s)
p=Path('Unity/Assets/Scripts/Course/DreamCourseLayout.cs');s=p.read_text().replace('                    list.Add(Mover.Dream(new CoursePoint(h.Centre.X,h.Centre.D),h.Height+21,h.Period,h.Phase/h.Period,h.Radius, -h.Motion));','''                    list.Add(Mover.Dream(new CoursePoint(h.Centre.X,h.Centre.D),h.Height+21,h.Period,h.Phase/h.Period,h.Radius, -h.Motion));
                    list.Add(Mover.Dream(h.Centre,h.Height+14.5,h.Period,h.Phase/h.Period,2.2,0,true));''');s=s.replace('                } else if(h.Kind==DreamHazardKind.WindLift)', '                } else if(h.Kind==DreamHazardKind.LavaVent)list.Add(Mover.Dream(h.Centre,h.Height+12,h.Period,h.Phase/h.Period,3,0,true));\n                else if(h.Kind==DreamHazardKind.WindLift)');p.write_text(s)
p=Path('Unity/Assets/Scripts/Course/CourseMovers.cs');s=p.read_text().replace('hit.Vx*1.12,Math.Max(8,hit.Vy+8),hit.Vd*1.12','hit.Vx*1.28,Math.Max(12,hit.Vy+10),hit.Vd*1.28');p.write_text(s)
p=Path('Unity/Assets/Scripts/Environment/DreamWorldArt.cs');s=p.read_text().replace('m.SetFloat("_Smoothness",smooth);materials.Add(m);','''m.SetFloat("_Smoothness",smooth);
            if(name!="Luminous mineral"){m.SetTexture("_BaseMap",Resources.Load<Texture2D>("Course/Resort/CoastalCliffScan_C"));m.SetTexture("_BumpMap",Resources.Load<Texture2D>("Course/Resort/CoastalCliffScan_N"));m.EnableKeyword("_NORMALMAP");m.SetTextureScale("_BaseMap",Vector2.one*.3f);}
            materials.Add(m);''')
s=s.replace('const int sides=10,rings=7','const int sides=20,rings=14').replace('float r=(1-y*.8f)*(1+.13f*Mathf.Sin(seed+i*2.3f+j*.7f));','float r=(1-y*.35f)*(1+.14f*Mathf.Sin(seed+i*2.3f+j*.7f)+.10f*Mathf.Sin(y*19));')
s=s.replace('            Make("Layered landform",vertices,triangles,stone);','''            int cap=vertices.Count;vertices.Add(p+Vector3.up*scale.y);
            for(int i=0;i<sides;i++)triangles.AddRange(new[]{cap,(rings-1)*sides+i,(rings-1)*sides+(i+1)%sides});
            Make("Layered landform",vertices,triangles,stone);''')
s=s.replace('mesh.SetVertices(vertices);mesh.SetTriangles(tris,0);','mesh.SetVertices(vertices);mesh.SetTriangles(tris,0);var uv=new List<Vector2>();foreach(var v in vertices)uv.Add(new Vector2(v.x+v.z*.3f,v.y+v.z*.2f));mesh.SetUVs(0,uv);')
p.write_text(s)
