from pathlib import Path
import re,uuid
p=Path('Unity/Assets/Scripts/Tennis/TennisVenueBuilder.Skyscraper.cs');s=p.read_text()
s=s.replace('                Wisps(root);','                // The authored atmosphere provides cloud volume; no opaque pebble wisps.')
s=s.replace('return SeaY + (dome * (.25f + .75f * crease) * 23f + puff * 6f) + swell * 9f;', 'return SeaY + dome * crease * 3f + puff * .8f + swell * 1.4f;')
s=s.replace('var mat = Matte(Color.white, CloudRamp("Cloud ramp"));','''var shader=Resources.Load<Shader>("Tennis/Shaders/TennisCloudAtmosphere");
                var mat=shader ? new Material(shader) {name="Authored cloud-top atmosphere"} : Matte(Color.white,CloudRamp("Cloud ramp"));
                if(shader){mat.SetTexture("_Panorama",Resources.Load<Texture2D>("Tennis/Premium/SkyRooftop"));mat.SetFloat("_Rotation",15);mat.SetFloat("_Exposure",.88f);}''')
a=s.index('                // banks of cumulus standing on the sea');b=s.index('                return SeaHeight;',a)
s=s[:a]+'                // The panorama carries richly shaped distant cloud banks, continuously into the horizon.\n'+s[b:]
a=s.index('                    // a collar of cloud where the shaft enters the sea');b=s.index('\n                }',a)
s=s[:a]+s[b:]
s=s.replace('                MeshObject(group, "Tower collars", collars.ToMesh("Tower collars"), Matte(Color.white, CloudRamp("Collar ramp")), false);','')
a=s.index('                var sun = SunDir; float sunAz',s.index('static void Sky(Transform root)'));b=s.index('\n            static Texture2D SunRings()',a)
s=s[:a]+'''                // Real distant cloud shape and an uninterrupted dusk gradient come from the
                // production latitude-longitude atmosphere, shared with the cloud surface below.
                // The painted sun supplies the warm horizon; old giant ring sprites are removed.
            }
''' +s[b:]
s=s.replace('                RenderSettings.skybox = null;\n                camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = haze;', '''                var skyShader=Resources.Load<Shader>("Tennis/Shaders/TennisRooftopSky");
                var panorama=Resources.Load<Texture2D>("Tennis/Premium/SkyRooftop");
                if(skyShader && panorama)
                {
                    var sky=new Material(skyShader){name="Rooftop dusk atmosphere"};
                    sky.SetTexture("_Panorama",panorama);sky.SetFloat("_Rotation",15);sky.SetFloat("_Exposure",.88f);
                    RenderSettings.skybox=sky;camera.clearFlags=CameraClearFlags.Skybox;
                }
                else {RenderSettings.skybox=null;camera.clearFlags=CameraClearFlags.SolidColor;}
                camera.backgroundColor=haze;''')
# Far towers are smaller silhouettes; the two closer framing anchors carry the detail.
s=s.replace('float w = t.w, d = t.d, roof = t.roof;', '''float distance=Mathf.Sqrt(t.x*t.x+t.z*t.z);
                    float hierarchy=Mathf.Lerp(1,.70f,Mathf.InverseLerp(220,1250,distance));
                    float w=t.w*hierarchy,d=t.d*hierarchy,roof=Mathf.Lerp(SeaY+9,t.roof,hierarchy);''')
# Setbacks retain the layout but get real narrow architectural bronze fins in the near views.
s=s.replace('                    if (!slant)\n                        switch', '''                    if(!drum && distance<380)
                    {
                        for(int edge=-1;edge<=1;edge+=2)
                        {
                            gold.Solid(new Vector3(t.x+edge*(w*.5f+.12f),(baseY+roof-tierH)/2,t.z-d*.5f-.12f),new Vector3(.35f,roof-tierH-baseY,.35f));
                            gold.Solid(new Vector3(t.x+edge*(w*.5f+.12f),(baseY+roof-tierH)/2,t.z+d*.5f+.12f),new Vector3(.35f,roof-tierH-baseY,.35f));
                        }
                    }
                    if (!slant)
                        switch''')
# Broader window panes with varied reflections instead of uniformly framed empty squares.
s=s.replace('bool mull = fu < .07f || fu > .93f','bool mull = fu < .035f || fu > .965f').replace('bool fin = fu < .06f || fu > .96f','bool fin = fu < .025f || fu > .98f')
s=s.replace('h1 * .65f + (1 - fv) * .35f', 'Mathf.Clamp01(h1*.35f+(1-fv)*.45f+.20f*Mathf.Sin((fu+cx*.07f)*6.28f))')
p.write_text(s)
s=Path('Unity/Assets/Resources/Tennis/Shaders/TennisCloudAtmosphere.shader').read_text()
s=s.replace('TennisCloudAtmosphere','TennisRooftopSky').replace('"Queue"="Geometry" "RenderType"="Opaque"','"Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox"').replace('Cull Back ZWrite On','Cull Off ZWrite Off').replace('o.world=TransformObjectToWorld(a.p.xyz);','o.world=a.p.xyz;').replace('normalize(i.world-float3(0,4,0))','normalize(i.world)').replace('clamp(uv.y,.001,.499)','clamp(uv.y,.001,.999)')
Path('Unity/Assets/Resources/Tennis/Shaders/TennisRooftopSky.shader').write_text(s)
for n in ['TennisCloudAtmosphere','TennisRooftopSky']:
    Path(f'Unity/Assets/Resources/Tennis/Shaders/{n}.shader.meta').write_text(f'fileFormatVersion: 2\nguid: {uuid.uuid4().hex}\nShaderImporter:\n  externalObjects: {{}}\n  defaultTextures: []\n  nonModifiableTextures: []\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n')
Path('proof/full-visual-overhaul/tennis/rooftop-sky-provenance.md').write_text('Generated with built-in GPT Image. Production asset: Resources/Tennis/Premium/SkyRooftop.png. Prompt: seamless 360 degree latitude-longitude sky above a natural cloud sea, rich blue evening sky and restrained peach sunset, no buildings/court/characters, natural cloud-top volume, no foam balls or giant sun rings. Source: /Users/adnanyonathan/.codex/generated_images/01a114cb-8312-7363-a7bc-a81a6ff7ce35/exec-32a6b6dd-aa93-4b6b-ba8a-fb4c4a044697.png. Inspected before installation; actual venue proof remains required.\n')
