using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Course
{
    /// Bounded cut-turf detail. Original ground/colliders remain unchanged; only
    /// two grass draw submissions are made, with a fixed near-detail allocation.
    public sealed class GolfCoastalTurf : MonoBehaviour
    {
        const float YardsPerMeter=1f/.9144f, RadiusMeters=12f, TileMeters=2f;
        const int NearLimit=20, CellLimit=121;
        sealed class Cell { public Matrix4x4 matrix; public Vector3 center; public Bounds bounds; public float distance; }
        readonly List<Cell> cells=new();
        readonly List<Matrix4x4> near=new(),far=new();
        readonly List<Material> groundMaterials=new();
        Mesh nearMesh,farMesh;Matrix4x4 nearBasis,farBasis;Material grass;
        Plane[] planes=new Plane[6];
        public int CellCount=>cells.Count;
        public int LastNearCells {get;private set;}
        public int LastFarCells {get;private set;}
        public int MaximumTriangles {get;private set;}

        public static void Apply(GameObject model,Hole hole)
        {
            if(hole.Number!=12||model.GetComponent<GolfCoastalTurf>())return;
            var prefab=Resources.Load<GameObject>("Course/Resort/CoastalTurf");
            var shader=Resources.Load<Shader>("Course/Shaders/GolfCoastalTurf");
            if(!prefab||!shader){Debug.LogError("[GolfCoastalTurf] missing authored turf tile/shader");return;}
            var owner=model.AddComponent<GolfCoastalTurf>();owner.Build(model,hole,prefab,shader);
        }
        static MeshFilter Find(GameObject prefab,string name)=>Array.Find(prefab.GetComponentsInChildren<MeshFilter>(),x=>x.name==name);
        void Build(GameObject model,Hole hole,GameObject prefab,Shader shader)
        {
            var n=Find(prefab,"TURF_NEAR");var f=Find(prefab,"TURF_FAR");
            if(!n||!f||!n.sharedMesh||!f.sharedMesh){Debug.LogError("[GolfCoastalTurf] invalid turf schema");return;}
            nearMesh=n.sharedMesh;farMesh=f.sharedMesh;
            nearBasis=prefab.transform.worldToLocalMatrix*n.transform.localToWorldMatrix;
            farBasis=prefab.transform.worldToLocalMatrix*f.transform.localToWorldMatrix;
            grass=new Material(shader){name="Coastal 12 short cut grass",enableInstancing=true};
            grass.SetColor("_RootColor",new Color(.19f,.36f,.16f));grass.SetColor("_TipColor",new Color(.39f,.56f,.245f));grass.SetFloat("_Smoothness",.08f);
            var colliders=model.GetComponentsInChildren<MeshCollider>();Physics.SyncTransforms();
            var tee=new Vector3((float)hole.Tee.X,0,(float)hole.Tee.D);var rng=new System.Random(121252);float size=TileMeters*YardsPerMeter;
            for(int z=-6;z<=6;z++)for(int x=-6;x<=6;x++){
                if(cells.Count>=CellLimit)continue;
                var p=tee+new Vector3(x*size,0,z*size);
                if(new Vector2(p.x-tee.x,p.z-tee.z).magnitude>(RadiusMeters-TileMeters*.7f)*YardsPerMeter)continue;
                if(!Ground(colliders,p,out var point,out var normal))continue;
                // Reject tiles crossing a raised tee edge or a cliff/bunker boundary.
                bool continuous=true;
                foreach(var d in new[]{new Vector3(-.88f,0,-.88f),new Vector3(.88f,0,-.88f),new Vector3(-.88f,0,.88f),new Vector3(.88f,0,.88f)})
                    if(!Ground(colliders,p+d*YardsPerMeter,out var corner,out var unused)||(corner.y-point.y)* (corner.y-point.y)>.025f*.025f){continuous=false;break;}
                if(!continuous)continue;
                var rotation=Quaternion.FromToRotation(Vector3.up,normal)*Quaternion.AngleAxis(rng.Next(4)*90,Vector3.up);
                cells.Add(new Cell{center=point,matrix=Matrix4x4.TRS(point-Vector3.up*.0015f,rotation,Vector3.one*YardsPerMeter),bounds=new Bounds(point,new Vector3(size,.14f,size))});
                if(cells.Count>=CellLimit)break;
            }
            MaximumTriangles=Mathf.Min(NearLimit,cells.Count)*(int)nearMesh.GetIndexCount(0)/3+Mathf.Max(0,cells.Count-NearLimit)*(int)farMesh.GetIndexCount(0)/3;
            FineGround(model,tee);
            Debug.Log($"[GolfCoastalTurf] {cells.Count} 2m cells within12m tee; near cap {NearLimit}, max {MaximumTriangles} triangles, 2 instanced submissions, no grass shadows/colliders");
        }
        static bool Ground(MeshCollider[] colliders,Vector3 p,out Vector3 point,out Vector3 normal)
        {
            point=normal=default;float closest=float.MaxValue;MeshCollider land=null;RaycastHit best=default;
            var ray=new Ray(new Vector3(p.x,1000,p.z),Vector3.down);
            foreach(var collider in colliders)if(collider.Raycast(ray,out var hit,2000)&&hit.distance<closest){land=collider;best=hit;closest=hit.distance;}
            if(!land||best.normal.y<.92f||!(land.name.StartsWith("TERRAIN")||land.name.StartsWith("TEE_BOX")||land.name.StartsWith("FAIRWAY")))return false;
            if(land.name.StartsWith("TERRAIN")){
                var mats=land.GetComponent<Renderer>()?.sharedMaterials;int triangle=best.triangleIndex,sub=0;
                for(;sub<land.sharedMesh.subMeshCount;sub++){int count=(int)land.sharedMesh.GetIndexCount(sub)/3;if(triangle<count)break;triangle-=count;}
                if(mats==null||sub>=mats.Length||!mats[sub]||!mats[sub].name.Contains(" Rough"))return false;
            }
            point=best.point;normal=best.normal;return true;
        }
        void FineGround(GameObject model,Vector3 tee)
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
                        detail.SetFloat("_TileYards",.5f*YardsPerMeter);detail.SetFloat("_NormalEnabled",1);detail.SetFloat("_BumpScale",.75f);
                        // Preserve the existing blade atlas instead of compressing its
                        // linear luminance into 3.6% of the generic green palette.
                        detail.SetFloat("_PaletteMode",1);detail.SetFloat("_PaletteDetail",1);
                        detail.SetFloat("_DetailContrast",6.5f);detail.SetColor("_BaseColor",Color.white);
                        bool rough=source.name.Contains(" Rough"),fringe=source.name.Contains(" Fringe");
                        detail.SetColor("_LowColor",rough?new Color(.145f,.29f,.145f):fringe?new Color(.18f,.34f,.15f):new Color(.235f,.38f,.17f));
                        detail.SetColor("_HighColor",rough?new Color(.30f,.46f,.205f):fringe?new Color(.335f,.505f,.22f):new Color(.41f,.565f,.255f));
                        detail.SetFloat("_Smoothness",.10f);detail.SetFloat("_Wrap",.32f);
                        detail.SetFloat("_SheenFromAlpha",0);groundMaterials.Add(detail);replacements[source]=detail;
                    }
                    mats[i]=detail;changed=true;
                }
                if(changed)renderer.sharedMaterials=mats;
            }
        }
        void LateUpdate()
        {
            var camera=Camera.main;if(!camera||!grass||!nearMesh||!SystemInfo.supportsInstancing)return;
            GeometryUtility.CalculateFrustumPlanes(camera,planes);near.Clear();far.Clear();
            foreach(var c in cells)c.distance=(c.center-camera.transform.position).sqrMagnitude;
            cells.Sort((a,b)=>a.distance.CompareTo(b.distance));
            foreach(var c in cells){
                if(c.distance>35f*35f*YardsPerMeter*YardsPerMeter||!GeometryUtility.TestPlanesAABB(planes,c.bounds))continue;
                if(near.Count<NearLimit&&c.distance<7.5f*7.5f*YardsPerMeter*YardsPerMeter)near.Add(c.matrix*nearBasis);else far.Add(c.matrix*farBasis);
            }
            LastNearCells=near.Count;LastFarCells=far.Count;
            if(near.Count>0)Graphics.DrawMeshInstanced(nearMesh,0,grass,near,null,ShadowCastingMode.Off,true,gameObject.layer,null,LightProbeUsage.Off);
            if(far.Count>0)Graphics.DrawMeshInstanced(farMesh,0,grass,far,null,ShadowCastingMode.Off,true,gameObject.layer,null,LightProbeUsage.Off);
        }
        void OnDestroy(){if(grass)Destroy(grass);foreach(var material in groundMaterials)if(material)Destroy(material);}
    }
}
