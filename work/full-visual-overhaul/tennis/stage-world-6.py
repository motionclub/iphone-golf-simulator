from pathlib import Path
import shutil
ROOT=Path.cwd();W=ROOT/'work/full-visual-overhaul/tennis';S=ROOT/'Unity/Assets/Scripts/Tennis';H=ROOT/'Unity/Assets/Resources/Tennis/Shaders'
# Private staging copies; install only after the parent releases the source checkpoint.
for name in ['TennisVenueArt.cs','TennisVenueBuilder.Skyscraper.cs','TennisVenueBuilder.Volcano.cs','TennisLook.cs']:
 shutil.copyfile(S/name,W/(name+'.stage6'))
p=W/'TennisVenueArt.cs.stage6';s=p.read_text();s=s.replace('QueuePlant(parts[1] == "BUSH" ? "BUSH_BROAD" : parts[1],','QueuePlant(parts[1] == "BUSH" ? "BUSH_BROAD" : parts[1] == "SHRUB0" ? "SHRUB_0" : parts[1] == "SHRUB1" ? "SHRUB_1" : parts[1],');p.write_text(s)
p=W/'TennisLook.cs.stage6';s=p.read_text();s=s.replace('"Course/Shaders/GolfResortSky"','"Tennis/Shaders/TennisCoastalSky"').replace('"Course/Resort/SkyCoastal"','"Course/Resort/SkyCoastalSmall"').replace('sky.SetFloat("_CloudCompression",.85f)','sky.SetFloat("_CloudCompression",1.35f)');p.write_text(s)
p=W/'TennisVenueBuilder.Skyscraper.cs.stage6';s=p.read_text();s=s.replace('mat.SetTexture("_Panorama",Resources.Load<Texture2D>("Tennis/Premium/SkyRooftop"));mat.SetFloat("_Rotation",15);mat.SetFloat("_Exposure",.88f);','mat.SetTexture("_CloudTops",Resources.Load<Texture2D>("Tennis/Premium/CloudTops"));mat.SetFloat("_WorldScale",.0018f);mat.SetFloat("_Exposure",.78f);');p.write_text(s)
p=W/'TennisVenueBuilder.Volcano.cs.stage6';s=p.read_text();a=s.index('                float colF = thetaDeg / 360f * Around;',s.index('static void Fall('));b=s.index('\n            static void Falls(',a)
s=s[:a]+'''                float colF=thetaDeg/360f*Around; int a=mb.Count;
                int n=topRow-bottomRow+1; const int across=10;
                // The continuous raised ribbon has a smooth width independent of
                // terrace kind. Its inward/upward shell clears each rock overhang.
                for(int k=0;k<n;k++)
                {
                    int row=bottomRow+k;var rw=rows[row];float t=k/(float)(n-1);
                    float cf=colF+Mathf.Sin(t*5.5f+phase)*.80f+Mathf.Sin(t*11+phase*2)*.17f;
                    float width=widthRiser*(.90f+.08f*Mathf.Sin(t*6.5f+phase)+.04f*Mathf.Sin(t*13+phase));
                    float half=width*.5f/(2*Mathf.PI*Mathf.Max(rw.r,60)/Around);
                    for(int j=0;j<=across;j++)
                    {
                        float u=j/(float)across;var p=Grid(row,cf+Mathf.Lerp(-half,half,u));
                        var inward=-new Vector3(p.x,0,p.z).normalized;
                        float crown=Mathf.Sin(u*Mathf.PI);
                        p+=inward*(2.6f+crown*.85f)+Vector3.up*(1.5f+crown*.45f);
                        mb.Add(p,new Vector2(u,rw.arc/18));
                    }
                }
                for(int k=0;k<n-1;k++)for(int j=0;j<across;j++)
                {
                    int p=a+k*(across+1)+j,q=p+across+1;
                    mb.T.AddRange(new[]{p,p+1,q,p+1,q+1,q});
                }
                // Close both banks with a dark-edged thickness, instead of a
                // paper rectangle whose edges vanish into the stepped wall.
                foreach(int edge in new[]{0,across})for(int k=0;k<n-1;k++)
                {
                    var p0=mb.V[a+k*(across+1)+edge];var p1=mb.V[a+(k+1)*(across+1)+edge];
                    var out0=new Vector3(p0.x,0,p0.z).normalized;var out1=new Vector3(p1.x,0,p1.z).normalized;
                    mb.Face4(p0,p1,p1+out1*.65f-Vector3.up*.55f,p0+out0*.65f-Vector3.up*.55f,
                        Vector2.zero,Vector2.up,Vector2.one,Vector2.right);
                }
            }
''' +s[b:]
s=s.replace('fallTex,fallGlow,.30f,8,true','fallTex,fallGlow,.82f,18,true');p.write_text(s)
# The shore map is authored in Blender XY. The runtime FBX is deliberately
# rotated 180 degrees around Unity Y, thus source XY == -world XZ.
s=(H/'TennisWater.shader').read_text().replace('(i.positionWS.xz-_ShoreBounds.xy)','(-i.positionWS.xz-_ShoreBounds.xy)')
s=s.replace('float phase = dot(p, dir) * freq + sin(dot(p, float2(.13, .17))) * 1.8 + _Time.y * speed;','float phase = dot(p, dir) * freq + sin(dot(p, float2(.13, .17))) * 1.8 + sin(dot(p,float2(.047,-.063))+sin(p.x*.11)) * 3.1 + _Time.y * speed;')
s=s.replace('water=lerp(_Deep.rgb,_Shallow.rgb,shallow);','''water=lerp(_Deep.rgb,_Shallow.rgb,shallow);
                    half surf=smoothstep(.70,.92,shallow)*(1-smoothstep(.965,1,shallow));
                    surf*=.65+.35*sin(i.positionWS.x*.37+i.positionWS.z*.21+_Time.y*.32);
                    water=lerp(water,half3(.58,.77,.72),surf*.42);''')
(W/'TennisWater.shader.stage6').write_text(s)
print('world geometry staging complete')
