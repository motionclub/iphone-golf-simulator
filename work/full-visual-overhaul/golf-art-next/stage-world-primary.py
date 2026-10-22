from pathlib import Path
R=Path(__file__).resolve().parents[3];W=R/'work/full-visual-overhaul/golf-art-next/runtime';W.mkdir(exist_ok=True)
def stage(name,fn):
 s=(R/'Unity/Assets/Scripts/Course'/name).read_text();s=fn(s);(W/name).write_text(s)
def dresser(s):
 s=s.replace('CliffModules<145&&rng.NextDouble()<.46','CliffModules<95&&rng.NextDouble()<.34')
 a=s.index('                    float height=Mathf.Min(span*.90f');b=s.index('                    Add("BLUFF_',a)
 s=s[:a]+'''                    // Broad fractured slabs start at the authored cliff foot. The
                    // shell and offset shoulders overlap, rather than float in rows.
                    float height=Mathf.Min(span*(.62f+(float)rng.NextDouble()*.31f),30.0f);
                    var center=point+normal*(.40f+(float)rng.NextDouble()*.60f);
                    center.y=node.low-.30f;
                    float width=8.0f+(float)rng.NextDouble()*9.0f,depth=4.8f+(float)rng.NextDouble()*2.4f;
                    float heading=Mathf.Atan2(normal.x,normal.z)*Mathf.Rad2Deg-22+(float)rng.NextDouble()*44;
''' +s[b:]
 s=s.replace('rimClusters<72','rimClusters<60').replace('float radius=2.7f+(float)rng.NextDouble()*1.4f;','float radius=1.9f+(float)rng.NextDouble()*1.3f;').replace('new Vector3(radius,2.7f+(float)rng.NextDouble()*1.4f,radius)','new Vector3(radius,1.2f+(float)rng.NextDouble()*.65f,radius)').replace('new Vector3(2.1f,1.3f,2.1f)','new Vector3(2.0f,1.1f,2.0f)')
 s=s.replace('placed%5==0?"FERN"','placed%3==0?"FERN"').replace('float height=kind=="BOULDER"?.45f:hole.Number==19?2.8f:1.95f;','float height=kind=="BOULDER"?.45f:hole.Number==19?1.65f:1.30f;')
 return s
stage('GolfResortDress.cs',dresser)
def sculpt(s):
 s=s.replace('var columns=new Dictionary<Vector2Int,Vector3>();','var columns=new Dictionary<Vector2Int,Vector3>();\n            var columnNormals=new Dictionary<Vector2Int,Vector3>();')
 anchor='            var crests=new List<Vector3>(columns.Values);'
 s=s.replace(anchor,'''            for(int sub=0;sub<rock.Length;sub++)if(rock[sub]){
                var ids=mesh.GetTriangles(sub);
                for(int t=0;t<ids.Length;t+=3){
                    var a=source.transform.TransformPoint(original[ids[t]]);var b=source.transform.TransformPoint(original[ids[t+1]]);var c=source.transform.TransformPoint(original[ids[t+2]]);
                    var face=Vector3.Cross(b-a,c-a);face.y=0;if(face.sqrMagnitude<.00001f)continue;
                    for(int j=0;j<3;j++){
                        var p=source.transform.TransformPoint(original[ids[t+j]]);var k=new Vector2Int(Mathf.RoundToInt(p.x*10),Mathf.RoundToInt(p.z*10));
                        columnNormals.TryGetValue(k,out var sum);columnNormals[k]=sum+face.normalized;
                    }
                }
            }
''' +anchor)
 s=s.replace('float closest=float.MaxValue,second=float.MaxValue,top=source.bounds.max.y,nextTop=top;','float closest=float.MaxValue,second=float.MaxValue,top=source.bounds.max.y,nextTop=top;\n                    Vector3 crestNormal=normal,nextNormal=normal;')
 s=s.replace('if(d<closest){second=closest;nextTop=top;closest=d;top=crest.y;}','if(d<closest){second=closest;nextTop=top;nextNormal=crestNormal;closest=d;top=crest.y;columnNormals.TryGetValue(new Vector2Int(Mathf.RoundToInt(crest.x*10),Mathf.RoundToInt(crest.z*10)),out crestNormal);}')
 s=s.replace('else if(d<second){second=d;nextTop=crest.y;}','else if(d<second){second=d;nextTop=crest.y;columnNormals.TryGetValue(new Vector2Int(Mathf.RoundToInt(crest.x*10),Mathf.RoundToInt(crest.z*10)),out nextNormal);}')
 s=s.replace('float erosion=(2.0f+broad*11.0f+shelves*4.5f+shelf*1.7f)*fade;','float erosion=(.35f+broad*2.1f+shelves*.65f+shelf*.24f)*fade;')
 s=s.replace('var outward=normal;outward.y=0;outward.Normalize();','var outward=(crestNormal.normalized+nextNormal.normalized)*.5f;if(outward.sqrMagnitude<.01f)outward=normal;outward.y=0;outward.Normalize();')
 s=s.replace(')*1.35f*fade',')*.24f*fade').replace('>30.25f','>16.0f')
 return s
stage('GolfCliffSculpt.cs',sculpt)
def atmosphere(s):
 s=s.replace('look.FillIntensity = volcanic ? .35f : .45f;','look.FillIntensity = volcanic ? .35f : .28f;\n            if(!volcanic){\n                look.SunColor=new Color(1,.91f,.77f);look.SunIntensity=1.80f;look.ShadowStrength=.76f;\n                look.AmbientSky=new Color(.34f,.46f,.65f);look.AmbientEquator=new Color(.36f,.40f,.37f);look.AmbientGround=new Color(.19f,.23f,.20f);\n            }')
 s=s.replace('look.SunElevation = 38; look.FillIntensity = .45f;','look.SunElevation = 38; look.FillIntensity = .30f;').replace('new Color(.57f,.55f,.50f)','new Color(.39f,.41f,.34f)').replace('new Color(.29f,.28f,.23f)','new Color(.20f,.24f,.17f)')
 return s
stage('GolfCourseAtmosphere.cs',atmosphere)
def palette(s):
 s=s.replace('low=new Color(.19f,.35f,.16f);high=new Color(.33f,.50f,.24f)','low=new Color(.22f,.38f,.16f);high=new Color(.36f,.54f,.24f)')
 s=s.replace('low=new Color(.30f,.47f,.18f);high=new Color(.43f,.59f,.25f)','low=new Color(.31f,.47f,.18f);high=new Color(.45f,.61f,.26f)')
 s=s.replace('low=new Color(.12f,.275f,.145f);high=new Color(.23f,.395f,.215f)','low=new Color(.085f,.22f,.125f);high=new Color(.18f,.335f,.185f)')
 s=s.replace('Surface.Fairway?.075f','Surface.Fairway?.09f').replace('Surface.Fairway?7.5f','Surface.Fairway?9.5f')
 return s
stage('GolfLook.cs',palette)
def surfaces(s):
 s=s.replace('m.SetFloat("_GeologicalMacro",.22f);m.SetFloat("_RockScale",.048f)','m.SetFloat("_GeologicalMacro",.12f);m.SetFloat("_RockScale",.065f)')
 s=s.replace('m.SetFloat("_PaletteDetail",.44f)','m.SetFloat("_PaletteDetail",.24f)')
 s=s.replace('new Color(.39f,.40f,.37f));m.SetColor("_HighColor",new Color(.72f,.70f,.65f))','new Color(.34f,.33f,.28f));m.SetColor("_HighColor",new Color(.77f,.73f,.62f))')
 s=s.replace('m.SetFloat("_HeightStrength",.36f);m.SetFloat("_BumpScale",.36f)','m.SetFloat("_HeightStrength",.27f);m.SetFloat("_BumpScale",.56f)')
 return s
stage('GolfCourseLook.cs',surfaces)
