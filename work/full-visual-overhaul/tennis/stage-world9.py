from pathlib import Path
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
w=r/'work/full-visual-overhaul/tennis/world9';w.mkdir(exist_ok=True)
f=r/'Unity/Assets/Scripts/Tennis/TennisVenueArt.cs';s=f.read_text()
s=s.replace('readonly Dictionary<Vector2Int,Cell> cells=new();','readonly Dictionary<Vector2Int,Cell> cells=new(), treesNear=new(), treesFar=new();')
s=s.replace('Load("Course/Resort/BotanicalKit");Load("Tennis/Premium/TennisBotanicalKit");','Load("Tennis/Premium/TennisBotanicalKit");Load("Course/Resort/BotanicalKit");')
a=s.index('            public void Add(string name,Vector3 p,float radius,float height,float yaw)');b=s.index('            public void Build(Transform root)',a)
s=s[:a]+'''            public void Add(string name,Vector3 p,float radius,float height,float yaw)
            {
                bool tree=name=="PALM"||name=="PINE";
                Append(name,p,radius,height,yaw,tree?treesNear:cells);
                if(tree)Append(prototypes.ContainsKey(name+"_FAR")?name+"_FAR":name,p,radius,height,yaw,treesFar);
            }
            void Append(string name,Vector3 p,float radius,float height,float yaw,Dictionary<Vector2Int,Cell> pockets)
            {
                if(!prototypes.TryGetValue(name,out var proto)||!proto.filter.sharedMesh)return;
                // Shared-material spatial cells carry the expensive sculpted crowns
                // only nearby; their actual far meshes preserve the same silhouette.
                var key=new Vector2Int(Mathf.FloorToInt(p.x/70),Mathf.FloorToInt(p.z/70));
                if(!pockets.TryGetValue(key,out var cell))pockets[key]=cell=new Cell();
                var mf=proto.filter;var source=mf.sharedMesh;var vertices=source.vertices;var normals=source.normals;var weight=source.colors;var leafPivots=source.uv2;
                var sourceColours=new Color[vertices.Length];var renderer=mf.GetComponent<Renderer>();
                var placement=Matrix4x4.TRS(p,Quaternion.Euler(0,yaw,0),new Vector3(radius,height,radius));
                var matrix=placement*proto.matrix;var normalMatrix=matrix.inverse.transpose;
                var leafNormalMatrix=Matrix4x4.Rotate(Quaternion.Euler(0,yaw,0))*proto.matrix.inverse.transpose;
                int start=cell.vertices.Count;
                for(int sub=0;sub<source.subMeshCount;sub++)
                {
                    int role=renderer&&sub<renderer.sharedMaterials.Length&&renderer.sharedMaterials[sub]?Role(renderer.sharedMaterials[sub].name):Mathf.Min(sub,6);
                    foreach(int index in source.GetTriangles(sub))
                    {
                        var colour=Palette[role];colour.a=weight.Length==vertices.Length?weight[index].r:(role>0&&role<6?1:0);
                        sourceColours[index]=colour;cell.triangles.Add(start+index);
                    }
                }
                for(int i=0;i<vertices.Length;i++)
                {
                    var point=proto.matrix.MultiplyPoint3x4(vertices[i]);
                    bool leaf=leafPivots.Length==vertices.Length&&leafPivots[i].x>=0;
                    if(leaf)point.y=leafPivots[i].x+(point.y-leafPivots[i].x)*radius/Mathf.Max(height,.001f);
                    cell.vertices.Add(placement.MultiplyPoint3x4(point));
                    cell.normals.Add(normals.Length==vertices.Length?(leaf?leafNormalMatrix:normalMatrix).MultiplyVector(normals[i]).normalized:Vector3.up);
                    cell.colours.Add(sourceColours[i]);cell.pivots.Add(new Vector2(p.x,p.z));
                }
            }
''' +s[b:]
a=s.index('                foreach(var pair in cells)',s.index('public void Build(Transform root)',a));b=s.index('\n            }\n        }',a)
s=s[:a]+'''                Renderer BuildCell(Transform parent,string name,Vector2Int key,Cell cell)
                {
                    var mesh=new Mesh{name=name+key,indexFormat=IndexFormat.UInt32};
                    mesh.SetVertices(cell.vertices);mesh.SetNormals(cell.normals);mesh.SetColors(cell.colours);mesh.SetUVs(2,cell.pivots);mesh.SetTriangles(cell.triangles,0);mesh.RecalculateBounds();
                    return TennisVenueBuilder.MeshObject(parent,mesh.name,mesh,material,true).GetComponent<Renderer>();
                }
                foreach(var pair in cells)BuildCell(root,"Tennis foliage pocket ",pair.Key,pair.Value);
                foreach(var pair in treesNear)
                {
                    var group=new GameObject("Tennis tree LOD pocket "+pair.Key).transform;group.SetParent(root,false);
                    var near=BuildCell(group,"Tennis trees near ",pair.Key,pair.Value);
                    var far=BuildCell(group,"Tennis trees far ",pair.Key,treesFar[pair.Key]);
                    var lod=group.gameObject.AddComponent<LODGroup>();lod.SetLODs(new[]{new LOD(.24f,new[]{near}),new LOD(.008f,new[]{far})});lod.RecalculateBounds();
                }
                Debug.Log("[TennisArt] foliage pockets="+cells.Count+"; tree near/far LOD pockets="+treesNear.Count+"; shared vertex palette, sculpted leaf proportions");''' +s[b:]
(w/'TennisVenueArt.cs').write_text(s)
f=r/'Unity/Assets/Scripts/Tennis/TennisVenueBuilder.Volcano.cs';s=f.read_text()
a=s.index('            static void Profile()');b=s.index('            static void Bowl(Transform root)',a)
s=s[:a]+'''            // An eroded caldera shoulder replaces the old five overhanging shelves.
            // Its source/landing radii and maximum crest envelope stay outside play.
            static void Profile()
            {
                float[] radii={112,121,150,182,222,262,292,312,345,400,470,540};
                float[] elevations={-51,-46,-22,-1,18,35,50,53,36,-1,-50,-54};
                var slopes=new float[radii.Length-1];var tangents=new float[radii.Length];
                for(int i=0;i<slopes.Length;i++)slopes[i]=(elevations[i+1]-elevations[i])/(radii[i+1]-radii[i]);
                tangents[0]=slopes[0];tangents[tangents.Length-1]=slopes[slopes.Length-1];
                for(int i=1;i<tangents.Length-1;i++)tangents[i]=slopes[i-1]*slopes[i]>0?2*slopes[i-1]*slopes[i]/(slopes[i-1]+slopes[i]):0;
                var list=new List<Row>();float arc=0;
                for(int segment=0;segment<radii.Length-1;segment++)
                {
                    float span=radii[segment+1]-radii[segment];int steps=Mathf.CeilToInt(span/3.4f);
                    for(int n=segment==0?0:1;n<=steps;n++)
                    {
                        float t=n/(float)steps,t2=t*t,t3=t2*t;
                        float r=Mathf.Lerp(radii[segment],radii[segment+1],t);
                        float y=(2*t3-3*t2+1)*elevations[segment]+(t3-2*t2+t)*span*tangents[segment]
                            +(-2*t3+3*t2)*elevations[segment+1]+(t3-t2)*span*tangents[segment+1];
                        if(list.Count>0){var p=list[list.Count-1];arc+=new Vector2(r-p.r,y-p.y).magnitude;}
                        list.Add(new Row{r=r,y=y,kind=(byte)(r<292?0:2),terrace=Mathf.Clamp(segment-1,0,4),arc=arc});
                    }
                }
                rows=list.ToArray();
                for(int i=0;i<rows.Length;i++)
                {
                    var p0=rows[Mathf.Max(0,i-1)];var p1=rows[Mathf.Min(rows.Length-1,i+1)];
                    var tangent=new Vector2(p1.r-p0.r,p1.y-p0.y).normalized;rows[i].nx=-tangent.y;rows[i].ny=tangent.x;
                }
                for(int terrace=0;terrace<5;terrace++)
                {
                    int Nearest(float radius){int best=0;float distance=float.MaxValue;for(int i=0;i<rows.Length;i++){float d=Mathf.Abs(rows[i].r-radius);if(d<distance){distance=d;best=i;}}return best;}
                    riserStart[terrace]=Nearest(Foot[terrace]);treadStart[terrace]=Nearest(Foot[terrace]+18);
                }
            }

''' +s[b:]
s=s.replace('float amp = rw.kind == 0 ? 1.7f : rw.kind == 1 ? .8f : 2.6f;','float amp = rw.kind == 0 ? 2.6f : 3.5f;')
a=s.index('                        float nz =',s.index('static void Bowl'));b=s.index('                        grid[i][j] =',a)
s=s[:a]+'''                        // Broad radial gullies and rounded shoulders catch light;
                        // low frequency displacement avoids a uniform sawtooth rim.
                        float gully=(Periodic(th,5,7+rw.r*.004f)-.5f)*2;
                        float nz=(Noise(c*3.8f+rw.r*.012f,s*3.8f+rw.y*.02f)-.5f)*2*amp;
                        float warp=(Periodic(th,3,2)-.5f)*18+gully*3;
                        float rr=rw.r+rw.nx*nz+warp,yy=rw.y+rw.ny*nz;
                        float crest=Mathf.SmoothStep(0,1,Mathf.InverseLerp(230,292,rw.r))*(1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(320,405,rw.r)));
                        yy+=(Periodic(th,4,17)-.5f)*20*crest+gully*2.3f;
''' +s[b:]
a=s.index('                    Material Rock(float g)');b=s.index('                    total +=',a)
s=s[:a]+'''                    var mat=BasaltSurface(name+" quiet eroded basalt",a==0?new Color(.14f,.125f,.12f):a==b1?new Color(.115f,.12f,.13f):new Color(.16f,.16f,.17f));
                    var go=MeshObject(root,name,mb.ToMesh(name),mat,false);
                    if(mb.T2.Count>0)go.GetComponent<MeshRenderer>().sharedMaterials=new[]{mat,mat};
''' +s[b:]
a=s.index('            /// A lavafall:');b=s.index('            static void Falls(Transform root)',a)
s=s[:a]+'''            static Vector3 SlopePoint(float row,float theta)
            {
                int a=Mathf.Clamp(Mathf.FloorToInt(row),0,rows.Length-1),b=Mathf.Min(a+1,rows.Length-1);
                return Vector3.Lerp(Grid(a,theta/360*Around),Grid(b,theta/360*Around),row-a);
            }

            /// Closed shallow volume follows the actual continuous slope. Every
            /// ring stays in air above basalt, including the meandering side banks.
            static void Fall(MB mb,float thetaDeg,int topRow,int bottomRow,float widthTop,float widthRiser,float phase)
            {
                const int along=144,around=20;int start=mb.Count;float length=0;
                Vector3 Centre(float t)
                {
                    float row=Mathf.Lerp(bottomRow,topRow,t);
                    float theta=thetaDeg+Mathf.Sin(t*6.2f+phase)*1.6f+Mathf.Sin(t*11+phase*.7f)*.45f;
                    var point=SlopePoint(row,theta);
                    int a=Mathf.Clamp(Mathf.RoundToInt(row),0,rows.Length-1);var profile=rows[a];
                    var radial=new Vector3(point.x,0,point.z).normalized;
                    var air=radial*profile.nx+Vector3.up*profile.ny;
                    return point+air*3.4f;
                }
                Vector3 previous=Centre(0);
                for(int row=0;row<=along;row++)
                {
                    float t=row/(float)along;var c=Centre(t);length+=Vector3.Distance(previous,c);previous=c;
                    var tangent=(Centre(Mathf.Min(1,t+.004f))-Centre(Mathf.Max(0,t-.004f))).normalized;
                    var across=new Vector3(-c.z,0,c.x).normalized;var front=Vector3.Cross(across,tangent).normalized;
                    float width=Mathf.Lerp(widthRiser,widthTop,t)*(.84f+.12f*Mathf.Sin(t*7+phase)+.075f*Mathf.Sin(t*13+phase*1.6f));
                    for(int ring=0;ring<=around;ring++)
                    {
                        float angle=ring/(float)around*Mathf.PI*2;
                        var point=c+across*(Mathf.Cos(angle)*width*.5f)+front*(Mathf.Sin(angle)*(.56f+.08f*Mathf.Sin(t*13+phase)));
                        mb.Add(point,new Vector2(ring/(float)around,length/18));
                    }
                }
                for(int row=0;row<along;row++)for(int ring=0;ring<around;ring++)
                {
                    int p=start+row*(around+1)+ring,q=p+around+1;mb.T.AddRange(new[]{p,q,p+1,p+1,q,q+1});
                }
            }

''' +s[b:]
s=s.replace('Fall(mb, th, treadStart[t], riserStart[0], 10f, 13f, i * 1.7f)','Fall(mb, th, treadStart[t], 0, 7f, 11f, i * 1.7f)')
s=s.replace('                Log("volcano: lavafalls", mb.Tris);','''                var pools=new MB();
                foreach(var (theta,terrace) in falls)
                {
                    var at=SlopePoint(0,theta);var radial=new Vector3(at.x,0,at.z).normalized;at=radial*110;at.y=LakeY+.55f;
                    int centre=pools.Add(at,Vector2.zero);const int segments=48;
                    for(int n=0;n<=segments;n++)
                    {
                        float angle=n/(float)segments*Mathf.PI*2;
                        float radius=10.5f+(Noise(Mathf.Cos(angle)*2+theta,Mathf.Sin(angle)*2)-.5f)*4;
                        pools.Add(at+new Vector3(Mathf.Cos(angle)*radius,0,Mathf.Sin(angle)*radius),new Vector2(Mathf.Cos(angle),Mathf.Sin(angle)));
                    }
                    for(int n=0;n<segments;n++)pools.Tri(centre,centre+n+2,centre+n+1);
                }
                MeshObject(root,"Lavafall landing pools",pools.ToMesh("Lavafall landing pools"),MoltenSurface("Tennis cascade landing pools",crust,crustGlow,1,12,false),false);
                Log("volcano: lavafalls", mb.Tris);''')
s=s.replace('int count = TennisQuality.Current == TennisQuality.Tier.Low ? 70 : 150;','int count = TennisQuality.Current == TennisQuality.Tier.Low ? 25 : 54;')
s=s.replace('new Vector3(size * Rand(rng, .8f, 1.4f), size * Rand(rng, .5f, .9f), size * Rand(rng, .8f, 1.4f))','new Vector3(size * Rand(rng, 1.2f, 2.1f), size * Rand(rng, .22f, .40f), size * Rand(rng, 1.2f, 2.1f))')
s=s.replace('WithRelief(Lit(new Color(.9f, .84f, .8f), .12f, rock, Vector2.one * 1f), rockNormal, 1.4f, Vector2.one)','BasaltSurface("Volcanic eroded shoulder outcrops",new Color(.14f,.14f,.15f))')
s=s.replace('static Material MoltenSurface(','''static Material BasaltSurface(string name,Color colour)
            {
                var material=TennisVenueArt.Surface(name,colour,.14f,0,.065f,.004f);
                material.SetTexture("_WorldMap",Resources.Load<Texture2D>("Course/Resort/ResortBasalt_C"));
                material.SetFloat("_WorldMapWeight",.34f);material.SetFloat("_WorldMapScale",.024f);
                return material;
            }

            static Material MoltenSurface(''')
s=s.replace('MoltenSurface("Tennis cooling lava lake",crust,crustGlow,.88f,23,false)','MoltenSurface("Tennis cooling lava lake",crust,crustGlow,1,38,false)')
s=s.replace('var mat = Glowing(Color.white, .16f, rock, cracks, new Color(3.6f, 1.2f, .2f), Vector2.one);','var mat = BasaltSurface("Volcanic shaped rock keel",new Color(.13f,.12f,.135f));')
s=s.replace('MeshObject(root, "Rock keel", mb.ToMesh("Rock keel"), mat, false).AddComponent<TennisVenueFx.Pulse>().Material = mat;','MeshObject(root, "Rock keel", mb.ToMesh("Rock keel"), mat, false);')
(w/'TennisVenueBuilder.Volcano.cs').write_text(s)
# Shared broad lake field, retaining tennis's closed circumference stream UV contract.
f=r/'Unity/Assets/Resources/Tennis/Shaders/TennisLava.shader';s=f.read_text()
g=(r/'Unity/Assets/Resources/Course/Shaders/GolfLava.shader').read_text();a=g.index('                // Warped iso-flow');b=g.index('                if(_Cascade',a)
c=s.index('                // Large drifting');d=s.index('                if(_Stream',c)
s=s[:c]+g[a:b]+s[d:]
(w/'TennisLava.shader').write_text(s)
print('World9 stage ready: shared palm/pine actual LOD, leaf proportions, broad continuous basalt shoulder, slope-following shallow closed lava, irregular landing pools, broad lake cooling field')
