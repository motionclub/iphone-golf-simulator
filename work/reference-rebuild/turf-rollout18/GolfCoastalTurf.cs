using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Course
{
    /// Bounded cut-turf detail. Original ground/colliders remain unchanged; only
    /// three grass draw submissions are made, with fixed near/mid allocations.
    public sealed class GolfCoastalTurf : MonoBehaviour
    {
        const float YardsPerMeter=1f/.9144f, RadiusMeters=12f, TileMeters=1f, RoughHeightScale=1.8f;
        const int NearLimit=48, MidLimit=96, CellLimit=640;
        sealed class Cell { public Matrix4x4 matrix; public Vector3 center; public Bounds bounds; public float distance; public bool rough; public float surface; }
        readonly List<Cell> cells=new();
        readonly List<Matrix4x4> near=new(),mid=new(),far=new();
        readonly List<float> nearTypes=new(),midTypes=new(),farTypes=new();
        MaterialPropertyBlock nearProperties,midProperties,farProperties;
        readonly List<Material> groundMaterials=new();
        Mesh nearMesh,midMesh,farMesh;Matrix4x4 nearBasis,midBasis,farBasis;Material grass;Bounds tileBounds;
        Plane[] planes=new Plane[6];
        public int CellCount=>cells.Count;
        public int LastNearCells {get;private set;}
        public int LastMidCells {get;private set;}
        public int LastFarCells {get;private set;}
        public int MaximumTriangles {get;private set;}

        public static void Apply(GameObject model,Hole hole)
        {
            if(hole.Number!=12)return;
            ApplyAroundTee(model,hole);
        }
        // Reusable entry point for a later measured rollout. This pilot invokes
        // it only on12; it queries current course ground instead of authored coordinates.
        public static void ApplyAroundTee(GameObject model,Hole hole)
        {
            if(model.GetComponent<GolfCoastalTurf>())return;
            var prefab=Resources.Load<GameObject>("Course/Resort/CoastalTurf");
            var shader=Resources.Load<Shader>("Course/Shaders/GolfCoastalTurf");
            if(!prefab||!shader){Debug.LogError("[GolfCoastalTurf] missing authored turf tile/shader");return;}
            var owner=model.AddComponent<GolfCoastalTurf>();owner.Build(model,hole,prefab,shader);
        }
        static MeshFilter Find(GameObject prefab,string name)=>Array.Find(prefab.GetComponentsInChildren<MeshFilter>(),x=>x.name==name);
        void Build(GameObject model,Hole hole,GameObject prefab,Shader shader)
        {
            var n=Find(prefab,"TURF_NEAR");var m=Find(prefab,"TURF_MID");var f=Find(prefab,"TURF_FAR");
            if(!n||!m||!f||!n.sharedMesh||!m.sharedMesh||!f.sharedMesh){Debug.LogError("[GolfCoastalTurf] invalid turf schema");return;}
            nearMesh=n.sharedMesh;midMesh=m.sharedMesh;farMesh=f.sharedMesh;
            nearProperties=new MaterialPropertyBlock();midProperties=new MaterialPropertyBlock();farProperties=new MaterialPropertyBlock();
            nearProperties.SetFloatArray("_TurfSurface",new float[NearLimit]);midProperties.SetFloatArray("_TurfSurface",new float[MidLimit]);farProperties.SetFloatArray("_TurfSurface",new float[CellLimit]);
            nearBasis=prefab.transform.worldToLocalMatrix*n.transform.localToWorldMatrix;
            midBasis=prefab.transform.worldToLocalMatrix*m.transform.localToWorldMatrix;
            farBasis=prefab.transform.worldToLocalMatrix*f.transform.localToWorldMatrix;
            tileBounds=TransformBounds(nearMesh.bounds,nearBasis);
            tileBounds.Encapsulate(TransformBounds(midMesh.bounds,midBasis));
            tileBounds.Encapsulate(TransformBounds(farMesh.bounds,farBasis));
            grass=new Material(shader){name="Coastal 12 short cut grass",enableInstancing=true};
            GolfTurfPalette.ApplyBlades(grass,hole);grass.SetFloat("_Smoothness",.08f);
            var mowing=new Vector3((float)(hole.Pin.X-hole.Tee.X),0,(float)(hole.Pin.D-hole.Tee.D)).normalized;
            grass.SetVector("_StripeDirection",new Vector4(mowing.z,0,-mowing.x,0));
            
            var colliders=model.GetComponentsInChildren<MeshCollider>();Physics.SyncTransforms();
            var tee=new Vector3((float)hole.Tee.X,0,(float)hole.Tee.D);var rng=new System.Random(121252);float size=TileMeters*YardsPerMeter;
            for(int z=-12;z<=12;z++)for(int x=-12;x<=12;x++){
                if(cells.Count>=CellLimit)continue;
                var p=tee+new Vector3(x*size,0,z*size);
                if(new Vector2(p.x-tee.x,p.z-tee.z).magnitude>(RadiusMeters-TileMeters*.7f)*YardsPerMeter)continue;
                AddCell(colliders,p,1,rng,true);
            }
            MaximumTriangles=Mathf.Min(NearLimit,cells.Count)*(int)nearMesh.GetIndexCount(0)/3+Mathf.Min(MidLimit,Mathf.Max(0,cells.Count-NearLimit))*(int)midMesh.GetIndexCount(0)/3+Mathf.Max(0,cells.Count-NearLimit-MidLimit)*(int)farMesh.GetIndexCount(0)/3;
            FineGround(model,hole,tee);
            int roughCells=0;foreach(var cell in cells)if(cell.rough)roughCells++;
            Debug.Log($"[GolfCoastalTurf] {cells.Count} 1m clustered cells within12m tee ({cells.Count-roughCells} cut / {roughCells} rough); near/mid caps {NearLimit}/{MidLimit}, max {MaximumTriangles} triangles, 3 instanced submissions, no grass shadows/colliders");
        }
        void AddCell(MeshCollider[] colliders,Vector3 p,float span,System.Random rng,bool subdivide)
        {
            if(cells.Count>=CellLimit||!Ground(colliders,p,out var point,out var normal,out var rough,out var surface))return;
            bool continuous=true;
            foreach(var d in new[]{new Vector3(-.44f,0,-.44f),new Vector3(.44f,0,-.44f),new Vector3(-.44f,0,.44f),new Vector3(.44f,0,.44f)})
                if(!Ground(colliders,p+d*span*YardsPerMeter,out var corner,out var unused,out var cornerRough,out var cornerSurface)||cornerRough!=rough||Mathf.Abs(Vector3.Dot(corner-point,normal))>.025f){continuous=false;break;}
            if(!continuous){
                // A smaller real ground query fills the existing cut/rough edge;
                // no invented rough strip or blade roots over bunker/cliff gaps.
                if(subdivide)foreach(var d in new[]{new Vector3(-.25f,0,-.25f),new Vector3(.25f,0,-.25f),new Vector3(-.25f,0,.25f),new Vector3(.25f,0,.25f)})AddCell(colliders,p+d*YardsPerMeter,.5f,rng,false);
                return;
            }
            var rotation=Quaternion.FromToRotation(Vector3.up,normal)*Quaternion.AngleAxis(rng.Next(4)*90,Vector3.up);
            var matrix=Matrix4x4.TRS(point-Vector3.up*.0015f,rotation,new Vector3(span,rough?RoughHeightScale:1,span)*YardsPerMeter);
            // Enclose every LOD after its ground tilt and rough-height scale,
            // with a conservative margin for the small shader wind displacement.
            var bounds=TransformBounds(tileBounds,matrix);bounds.Expand(.12f);
            cells.Add(new Cell{center=point,rough=rough,surface=surface,matrix=matrix,bounds=bounds});
        }
        static Bounds TransformBounds(Bounds bounds,Matrix4x4 matrix)
        {
            var e=bounds.extents;
            var x=matrix.MultiplyVector(new Vector3(e.x,0,0));
            var y=matrix.MultiplyVector(new Vector3(0,e.y,0));
            var z=matrix.MultiplyVector(new Vector3(0,0,e.z));
            var extents=new Vector3(Mathf.Abs(x.x)+Mathf.Abs(y.x)+Mathf.Abs(z.x),Mathf.Abs(x.y)+Mathf.Abs(y.y)+Mathf.Abs(z.y),Mathf.Abs(x.z)+Mathf.Abs(y.z)+Mathf.Abs(z.z));
            return new Bounds(matrix.MultiplyPoint3x4(bounds.center),extents*2);
        }
        static bool Ground(MeshCollider[] colliders,Vector3 p,out Vector3 point,out Vector3 normal,out bool rough,out float surface)
        {
            point=normal=default;rough=false;surface=0;float closest=float.MaxValue;MeshCollider land=null;RaycastHit best=default;
            var ray=new Ray(new Vector3(p.x,1000,p.z),Vector3.down);
            foreach(var collider in colliders)if(collider.Raycast(ray,out var hit,2000)&&hit.distance<closest){land=collider;best=hit;closest=hit.distance;}
            if(!land||best.normal.y<.92f||!(land.name.StartsWith("TERRAIN")||land.name.StartsWith("TEE_BOX")||land.name.StartsWith("FAIRWAY")))return false;
            if(land.name.StartsWith("TERRAIN")){
                var mats=land.GetComponent<Renderer>()?.sharedMaterials;int triangle=best.triangleIndex,sub=0;
                for(;sub<land.sharedMesh.subMeshCount;sub++){int count=(int)land.sharedMesh.GetIndexCount(sub)/3;if(triangle<count)break;triangle-=count;}
                if(mats==null||sub>=mats.Length||!mats[sub]||!mats[sub].name.Contains(" Rough"))return false;
                rough=true;
            }
            if(!rough) {
                // Visual role only: roots, queries, height and collider membership
                // retain the accepted Dense15 cut/rough placement contract.
                var mats=land.GetComponent<Renderer>()?.sharedMaterials;
                int triangle=best.triangleIndex,sub=0;
                for(;sub<land.sharedMesh.subMeshCount;sub++){int count=(int)land.sharedMesh.GetIndexCount(sub)/3;if(triangle<count)break;triangle-=count;}
                surface=mats!=null&&sub<mats.Length&&mats[sub]&&mats[sub].HasProperty("_Surface")?mats[sub].GetFloat("_Surface"):land.name.StartsWith("TEE")?3:1;
            }
            point=best.point;normal=best.normal;return true;
        }
        void FineGround(GameObject model,Hole hole,Vector3 tee)
        {
            var colour=Resources.Load<Texture2D>("Course/Resort/CoastalTurf_C");var normal=Resources.Load<Texture2D>("Course/Resort/CoastalTurf_N");
            if(!colour||!normal){Debug.LogError("[GolfCoastalTurf] missing micro-turf surface maps");return;}
            colour.anisoLevel=16;normal.anisoLevel=16;
            var replacements=new Dictionary<Material,Material>();
            foreach(var renderer in model.GetComponentsInChildren<MeshRenderer>()){
                if(!renderer.enabled)continue;
                var closest=renderer.bounds.ClosestPoint(new Vector3(tee.x,renderer.bounds.center.y,tee.z));
                if(new Vector2(closest.x-tee.x,closest.z-tee.z).sqrMagnitude>RadiusMeters*RadiusMeters*YardsPerMeter*YardsPerMeter)continue;
                var mats=renderer.sharedMaterials;bool changed=false;
                for(int i=0;i<mats.Length;i++){
                    var source=mats[i];if(!source||source.shader.name!="GolfArcade/GolfGround"||!(source.name.Contains(" Rough")||source.name.Contains(" Tee")||source.name.Contains(" Fairway")||source.name.Contains(" Fringe")))continue;
                    if(!replacements.TryGetValue(source,out var detail)){
                        detail=new Material(source){name=source.name,enableInstancing=true};
                        detail.SetTexture("_BaseMap",colour);detail.SetTexture("_BumpMap",normal);
                        detail.SetFloat("_TileYards",1f*YardsPerMeter);detail.SetFloat("_NormalEnabled",1);detail.SetFloat("_BumpScale",.65f);
                        // The source atlas uses curved folded lamina and root AO. Its
                        // measured linear luminance preserves the accepted palette midpoint.
                        detail.SetFloat("_PaletteMode",1);detail.SetFloat("_PaletteDetail",1);detail.SetFloat("_TurfMidpoint",0.0907707f);
                        detail.SetFloat("_DetailContrast",6.5f);detail.SetColor("_BaseColor",Color.white);
                        var role=source.name.Contains(" Rough")?GolfCourseLook.Surface.Rough:source.name.Contains(" Fringe")?GolfCourseLook.Surface.Fringe:source.name.Contains(" Tee")?GolfCourseLook.Surface.Tee:GolfCourseLook.Surface.Fairway;
                        GolfTurfPalette.ApplyGround(detail,hole,role,true);
                        // Keep the course-coordinate map for longitudinal fairway
                        // bands; the tee uses its own much quieter mowing treatment.
                        detail.SetFloat("_Wrap",.32f);
                        detail.SetFloat("_SheenFromAlpha",0);groundMaterials.Add(detail);replacements[source]=detail;
                    }
                    mats[i]=detail;changed=true;
                }
                if(changed)renderer.sharedMaterials=mats;
            }
        }
        void LateUpdate()
        {
            var camera=Camera.main;if(!camera||!grass||!nearMesh||!midMesh||!farMesh||!SystemInfo.supportsInstancing)return;
            GeometryUtility.CalculateFrustumPlanes(camera,planes);near.Clear();mid.Clear();far.Clear();nearTypes.Clear();midTypes.Clear();farTypes.Clear();
            foreach(var c in cells)c.distance=(c.center-camera.transform.position).sqrMagnitude;
            cells.Sort((a,b)=>a.distance.CompareTo(b.distance));
            foreach(var c in cells){
                if(c.distance>35f*35f*YardsPerMeter*YardsPerMeter||!GeometryUtility.TestPlanesAABB(planes,c.bounds))continue;
                if(near.Count<NearLimit&&c.distance<10f*10f*YardsPerMeter*YardsPerMeter){near.Add(c.matrix*nearBasis);nearTypes.Add(c.surface);}
                else if(mid.Count<MidLimit&&c.distance<17f*17f*YardsPerMeter*YardsPerMeter){mid.Add(c.matrix*midBasis);midTypes.Add(c.surface);}
                else{far.Add(c.matrix*farBasis);farTypes.Add(c.surface);}
            }
            LastNearCells=near.Count;LastMidCells=mid.Count;LastFarCells=far.Count;
            if(near.Count>0){nearProperties.SetFloatArray("_TurfSurface",nearTypes);Graphics.DrawMeshInstanced(nearMesh,0,grass,near,nearProperties,ShadowCastingMode.Off,true,gameObject.layer,null,LightProbeUsage.Off);}
            if(mid.Count>0){midProperties.SetFloatArray("_TurfSurface",midTypes);Graphics.DrawMeshInstanced(midMesh,0,grass,mid,midProperties,ShadowCastingMode.Off,true,gameObject.layer,null,LightProbeUsage.Off);}
            if(far.Count>0){farProperties.SetFloatArray("_TurfSurface",farTypes);Graphics.DrawMeshInstanced(farMesh,0,grass,far,farProperties,ShadowCastingMode.Off,true,gameObject.layer,null,LightProbeUsage.Off);}
        }
        void OnDestroy(){if(grass)Destroy(grass);foreach(var material in groundMaterials)if(material)Destroy(material);}
    }
}
