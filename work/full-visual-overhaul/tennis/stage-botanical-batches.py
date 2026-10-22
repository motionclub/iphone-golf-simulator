from pathlib import Path
W=Path('work/full-visual-overhaul/tennis');p=W/'TennisVenueArt.cs.stage6';s=p.read_text();a=s.index('        sealed class BotanicalBatch');b=s.index('\n    /// One coherent breeze',a)
s=s[:a]+'''        sealed class BotanicalBatch
        {
            static readonly Color[] Palette={new Color(.39f,.24f,.12f),new Color(.075f,.26f,.10f),new Color(.18f,.40f,.13f),new Color(.37f,.52f,.14f),new Color(.87f,.28f,.23f),new Color(.90f,.62f,.18f),new Color(.43f,.44f,.36f)};
            sealed class Cell
            {
                public readonly List<Vector3> vertices=new(),normals=new();
                public readonly List<Color> colours=new();
                public readonly List<Vector2> pivots=new();
                public readonly List<int> triangles=new();
            }
            readonly Dictionary<Vector2Int,Cell> cells=new();
            readonly Dictionary<string,(MeshFilter filter,Matrix4x4 matrix)> prototypes=new();
            public BotanicalBatch()
            {
                void Load(string path)
                {
                    var kit=Resources.Load<GameObject>(path);if(!kit)return;
                    foreach(var mf in kit.GetComponentsInChildren<MeshFilter>(true))
                        prototypes[mf.name]=(mf,kit.transform.worldToLocalMatrix*mf.transform.localToWorldMatrix);
                }
                Load("Course/Resort/BotanicalKit");Load("Tennis/Premium/TennisBotanicalKit");
            }
            static int Role(string name)
            {
                if(name.Contains("BARK"))return 0;if(name.Contains("LEAF_DARK"))return 1;
                if(name.Contains("LEAF_MID"))return 2;if(name.Contains("LEAF_LIGHT"))return 3;
                if(name.Contains("CORAL"))return 4;if(name.Contains("GOLD"))return 5;return 6;
            }
            public void Add(string name,Vector3 p,float radius,float height,float yaw)
            {
                if(!prototypes.TryGetValue(name,out var proto)||!proto.filter.sharedMesh)return;
                // One palette mesh per spatial pocket retains bounded culling while
                // avoiding a renderer per plant or per leaf material.
                var key=new Vector2Int(Mathf.FloorToInt(p.x/70),Mathf.FloorToInt(p.z/70));
                if(!cells.TryGetValue(key,out var cell))cells[key]=cell=new Cell();
                var mf=proto.filter;var source=mf.sharedMesh;var vertices=source.vertices;var normals=source.normals;var weight=source.colors;
                var sourceColours=new Color[vertices.Length];var renderer=mf.GetComponent<Renderer>();
                var matrix=Matrix4x4.TRS(p,Quaternion.Euler(0,yaw,0),new Vector3(radius,height,radius))*proto.matrix;
                var normalMatrix=matrix.inverse.transpose;int start=cell.vertices.Count;
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
                    cell.vertices.Add(matrix.MultiplyPoint3x4(vertices[i]));
                    cell.normals.Add(normals.Length==vertices.Length?normalMatrix.MultiplyVector(normals[i]).normalized:Vector3.up);
                    cell.colours.Add(sourceColours[i]);cell.pivots.Add(new Vector2(p.x,p.z));
                }
            }
            public void Build(Transform root)
            {
                const string key="Tennis spatial botanical vertex palette";
                if(!surfaces.TryGetValue(key,out var material)||!material)
                {
                    var shader=Resources.Load<Shader>("Tennis/Shaders/TennisBotanical");
                    material=shader?new Material(shader){name=key,enableInstancing=true}:Surface(key,Color.white,.16f);
                    surfaces[key]=material;
                }
                foreach(var pair in cells)
                {
                    var cell=pair.Value;var mesh=new Mesh{name="Tennis foliage pocket "+pair.Key,indexFormat=IndexFormat.UInt32};
                    mesh.SetVertices(cell.vertices);mesh.SetNormals(cell.normals);mesh.SetColors(cell.colours);mesh.SetUVs(2,cell.pivots);mesh.SetTriangles(cell.triangles,0);mesh.RecalculateBounds();
                    TennisVenueBuilder.MeshObject(root,mesh.name,mesh,material,true);
                }
                Debug.Log("[TennisArt] spatial foliage pockets="+cells.Count+"; one vertex palette renderer per pocket");
            }
        }
    }
''' +s[b:];p.write_text(s)
s=Path('Unity/Assets/Resources/Course/Shaders/GolfBotanical.shader').read_text().replace('GolfArcade/GolfBotanical','GolfArcade/TennisBotanical').replace('_VertexPalette("Use vertex botanical palette",Float)=0','_VertexPalette("Use vertex botanical palette",Float)=1').replace('half4 c:COLOR;','half4 c:COLOR;float2 pivot:TEXCOORD2;')
s=s.replace('float3 Sway(float3 world,half weight) {','float3 Sway(float3 world,half weight,float2 pivot) {').replace('dot(world.xz,float2(.47,.31))','dot(pivot,float2(.47,.31))').replace('TransformObjectToWorld(a.p.xyz),o.weight)','TransformObjectToWorld(a.p.xyz),o.weight,a.pivot)').replace('lerp(a.c.r,a.c.a,_VertexPalette)),n=','lerp(a.c.r,a.c.a,_VertexPalette),a.pivot),n=')
(W/'TennisBotanical.shader.stage6').write_text(s)
print('bounded spatial plant batches staged')
