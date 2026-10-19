using System;
using System.Collections.Generic;
using UnityEngine;
namespace GolfArcade.Tennis
{
    // Isolated experiment: constraints depend on construction and the skeleton,
    // never on clip names, frame numbers or sampled pose banks.
    [DefaultExecutionOrder(2000)]
    public sealed class GarmentClothPrototype : MonoBehaviour
    {
        public Cloth cloth;
        readonly List<GameObject> proxies = new();
        [Serializable]sealed class Weight {public int[] ids;public float[] values;}
        [Serializable]sealed class Mapping {public int triangle;public Vector3 bary,offset;}
        [Serializable]sealed class Cage {public Vector3[] points;public int[] triangles;public Weight[] weights;public Mapping[] mapping;public bool[] rigidDetail;}
        Cage cage;Mesh detailMesh,cageMesh;Vector3[] output;int[] particles;SkinnedMeshRenderer sourceTop;MeshRenderer detailRenderer;
        bool constrained;CapsuleCollider[] collision;int[] edgeA,edgeB;float[] restLength,mobility;Vector3[] solved,targets;SkinnedMeshRenderer simulationSkin;
        public static void Attach(MatchHeroLook look, SkinnedMeshRenderer top)
        {
            if (!Application.isPlaying || Environment.GetEnvironmentVariable("GARMENT_CLOTH_PROTOTYPE") == "0" || string.IsNullOrEmpty(Environment.GetEnvironmentVariable("GARMENT_CLOTH_PROTOTYPE")) || !top || top.GetComponent<GarmentClothPrototype>()) return;
            top.gameObject.AddComponent<GarmentClothPrototype>().Build(look,top);
        }
        void Build(MatchHeroLook look,SkinnedMeshRenderer top)
        {
            var capsules = new List<CapsuleCollider>();
            void Segment(Transform parent,Vector3 start,Vector3 end,float radius)
            {
                var go=new GameObject("Garment collision proxy");proxies.Add(go);go.layer=2;
                go.transform.SetParent(parent,false);go.transform.position=(start+end)*.5f;
                go.transform.rotation=Quaternion.FromToRotation(Vector3.up,end-start);
                var collider=go.AddComponent<CapsuleCollider>();collider.isTrigger=true;collider.direction=1;
                float scale=go.transform.lossyScale.x;
                collider.radius=radius/scale;collider.height=((end-start).magnitude+2*radius)/scale;
                capsules.Add(collider);
            }
            foreach(bool right in new[]{false,true})
            {
                var a=look.Bone(right?HumanBodyBones.RightUpperArm:HumanBodyBones.LeftUpperArm);
                var b=look.Bone(right?HumanBodyBones.RightLowerArm:HumanBodyBones.LeftLowerArm);
                var c=look.Bone(right?HumanBodyBones.RightHand:HumanBodyBones.LeftHand);
                Segment(a,Vector3.Lerp(a.position,b.position,.12f),Vector3.Lerp(a.position,b.position,.90f),.060f*look.transform.lossyScale.x);
                Segment(b,Vector3.Lerp(b.position,c.position,.05f),Vector3.Lerp(b.position,c.position,.85f),.041f*look.transform.lossyScale.x);
            }
            // Source body coordinates are Z-up. Use its own bind transform so
            // these volumes follow the torso without moving the skeleton.
            int chest=Array.FindIndex(look.body.bones,b=>b.name=="UpperChest");
            var chestFrame=look.body.bones[chest].localToWorldMatrix*look.body.sharedMesh.bindposes[chest];
            for(int i=-1;i<=1;i++)
            {
                var a=chestFrame.MultiplyPoint3x4(new Vector3(i*.065f,0,1.07f));
                var b=chestFrame.MultiplyPoint3x4(new Vector3(i*.065f,0,1.28f));
                Segment(look.body.bones[chest],a,b,.090f*look.transform.lossyScale.x);
            }
            var simulated=top;
            if(Environment.GetEnvironmentVariable("GARMENT_CLOTH_PROTOTYPE")!="1")simulated=BuildCage(top);
            if(Environment.GetEnvironmentVariable("GARMENT_CLOTH_PROTOTYPE")=="3")
            {
                constrained=true;collision=capsules.ToArray();simulationSkin=simulated;
                foreach(var collider in collision)collider.enabled=false;
                PrepareConstraints();return;
            }
            cloth=simulated.gameObject.AddComponent<Cloth>();
            cloth.useGravity=true;cloth.stretchingStiffness=1;cloth.bendingStiffness=.8f;
            cloth.damping=.35f;cloth.friction=.3f;cloth.useTethers=true;
            cloth.clothSolverFrequency=120;cloth.stiffnessFrequency=120;
            cloth.enableContinuousCollision=true;cloth.worldVelocityScale=.1f;cloth.worldAccelerationScale=.05f;
            cloth.capsuleColliders=capsules.ToArray();
            var points=cloth.vertices;var coefficients=new ClothSkinningCoefficient[points.Length];
            for(int i=0;i<points.Length;i++)
            {
                var p=points[i];
                // Collar and the lower torso establish the garment; shoulder
                // and sleeve fabric can leave a folded skinning target.
                float shoulder=Mathf.SmoothStep(0,1,Mathf.InverseLerp(.10f,.18f,Mathf.Abs(p.x)));
                float height=Mathf.SmoothStep(0,1,Mathf.InverseLerp(1.11f,1.24f,p.z));
                float travel=.09f*shoulder*height;
                if(p.z>1.43f)travel=0;
                coefficients[i]=new ClothSkinningCoefficient{maxDistance=travel,collisionSphereDistance=0};
            }
            cloth.coefficients=coefficients;cloth.ClearTransformMotion();
            if(cage!=null)
            {
                particles=new int[cage.points.Length];
                for(int i=0;i<particles.Length;i++)
                {float distance=float.PositiveInfinity;for(int j=0;j<points.Length;j++){float d=(points[j]-cage.points[i]).sqrMagnitude;if(d<distance){particles[i]=j;distance=d;}}}
            }
            Debug.Log($"[GarmentClothPrototype] {points.Length} particles, {capsules.Count} body proxies; no animation lookup");
        }
        SkinnedMeshRenderer BuildCage(SkinnedMeshRenderer top)
        {
            cage=JsonUtility.FromJson<Cage>(Resources.Load<TextAsset>("GarmentClothPrototype/golf_cage").text);
            cageMesh=new Mesh{name="Sewn garment simulation cage"};cageMesh.vertices=cage.points;cageMesh.triangles=cage.triangles;
            var weights=new BoneWeight[cage.weights.Length];
            for(int i=0;i<weights.Length;i++) {var w=cage.weights[i];weights[i]=new BoneWeight{boneIndex0=w.ids[0],boneIndex1=w.ids[1],boneIndex2=w.ids[2],boneIndex3=w.ids[3],weight0=w.values[0],weight1=w.values[1],weight2=w.values[2],weight3=w.values[3]};}
            cageMesh.boneWeights=weights;cageMesh.bindposes=top.sharedMesh.bindposes;cageMesh.RecalculateNormals();cageMesh.RecalculateBounds();
            var go=new GameObject("Sewn garment simulation cage");proxies.Add(go);go.transform.SetParent(top.transform,false);
            var renderer=go.AddComponent<SkinnedMeshRenderer>();renderer.sharedMesh=cageMesh;renderer.bones=top.bones;renderer.rootBone=top.rootBone;
            renderer.updateWhenOffscreen=true;renderer.forceRenderingOff=true;renderer.sharedMaterial=top.sharedMaterial;renderer.quality=SkinQuality.Bone4;
            sourceTop=top;top.forceRenderingOff=true;
            detailMesh=Instantiate(top.sharedMesh);detailMesh.name="Garment carried by sewn simulation cage";detailMesh.ClearBlendShapes();
            output=new Vector3[detailMesh.vertexCount];
            go=new GameObject("Garment surface detail");proxies.Add(go);go.transform.SetParent(top.transform,false);
            go.AddComponent<MeshFilter>().sharedMesh=detailMesh;detailRenderer=go.AddComponent<MeshRenderer>();detailRenderer.sharedMaterials=top.sharedMaterials;detailRenderer.renderingLayerMask=top.renderingLayerMask;
            return renderer;
        }
        void LateUpdate()
        {
            if(cage==null)return;
            Vector3[] p;
            if(constrained){SolveConstraints();p=solved;}
            else
            {
            if(!cloth||particles==null)return;
            p=cloth.vertices;
            // Cloth exposes simulated positions in its root-bone frame after
            // initialization; the authored garment and detail use Z-up mesh space.
            var skin=cloth.GetComponent<SkinnedMeshRenderer>();
            // Verified against a pinned vertex's exact bone*bind skinning:
            // Cloth positions already contain skeleton scale. Applying root
            // scale again lifted the hem by roughly nine centimetres.
            var toMesh=transform.worldToLocalMatrix*Matrix4x4.TRS(skin.rootBone.position,skin.rootBone.rotation,Vector3.one);
            for(int i=0;i<p.Length;i++)p[i]=toMesh.MultiplyPoint3x4(p[i]);
            }
            var tri=cage.triangles;
            var sourcePositions=sourceTop.sharedMesh.vertices;var sourceWeights=sourceTop.sharedMesh.boneWeights;var sourceBinds=sourceTop.sharedMesh.bindposes;var sourceBones=sourceTop.bones;
            var detailMatrices=new Matrix4x4[sourceBones.Length];for(int j=0;j<sourceBones.Length;j++)detailMatrices[j]=transform.worldToLocalMatrix*sourceBones[j].localToWorldMatrix*sourceBinds[j];
            for(int i=0;i<output.Length;i++)
            {
                if(cage.rigidDetail!=null&&cage.rigidDetail[i])
                {
                    var w=sourceWeights[i];var v0=sourcePositions[i];
                    output[i]=detailMatrices[w.boneIndex0].MultiplyPoint3x4(v0)*w.weight0+detailMatrices[w.boneIndex1].MultiplyPoint3x4(v0)*w.weight1+detailMatrices[w.boneIndex2].MultiplyPoint3x4(v0)*w.weight2+detailMatrices[w.boneIndex3].MultiplyPoint3x4(v0)*w.weight3;continue;
                }
                var map=cage.mapping[i];int t=map.triangle*3;
                var a=p[particles[tri[t]]];var b=p[particles[tri[t+1]]];var c=p[particles[tri[t+2]]];
                var u=(b-a).normalized;var n=Vector3.Cross(b-a,c-a).normalized;var v=Vector3.Cross(n,u);
                output[i]=a*map.bary.x+b*map.bary.y+c*map.bary.z+u*map.offset.x+v*map.offset.y+n*map.offset.z;
            }
            detailMesh.vertices=output;detailMesh.RecalculateNormals();detailMesh.RecalculateBounds();
            detailRenderer.sharedMaterials=sourceTop.sharedMaterials;
        }
        void PrepareConstraints()
        {
            var edges=new HashSet<long>();var aa=new List<int>();var bb=new List<int>();var lengths=new List<float>();
            for(int t=0;t<cage.triangles.Length;t+=3)for(int k=0;k<3;k++)
            {
                int a=cage.triangles[t+k],b=cage.triangles[t+(k+1)%3];if(a>b)(a,b)=(b,a);
                if(!edges.Add(((long)a<<32)|(uint)b))continue;
                aa.Add(a);bb.Add(b);lengths.Add(Vector3.Distance(cage.points[a],cage.points[b]));
            }
            edgeA=aa.ToArray();edgeB=bb.ToArray();restLength=lengths.ToArray();
            solved=new Vector3[cage.points.Length];targets=new Vector3[solved.Length];mobility=new float[solved.Length];particles=new int[solved.Length];
            for(int i=0;i<solved.Length;i++)
            {
                var p=cage.points[i];particles[i]=i;
                mobility[i]=Mathf.SmoothStep(0,1,Mathf.InverseLerp(.075f,.15f,Mathf.Abs(p.x)))*Mathf.SmoothStep(0,1,Mathf.InverseLerp(1.10f,1.22f,p.z));
                if(p.z>1.405f)mobility[i]=0;
                var w=cage.weights[i];if(w.values[0]>.999f&&simulationSkin.bones[w.ids[0]].name.EndsWith("UpperArm"))mobility[i]=0;
            }
            Debug.Log($"[GarmentCageConstraints] {solved.Length} points, {edgeA.Length} sewn edges; current skeleton only");
        }
        void SolveConstraints()
        {
            var matrices=new Matrix4x4[simulationSkin.bones.Length];var binds=simulationSkin.sharedMesh.bindposes;var bones=simulationSkin.bones;
            for(int j=0;j<matrices.Length;j++)matrices[j]=transform.worldToLocalMatrix*bones[j].localToWorldMatrix*binds[j];
            for(int i=0;i<solved.Length;i++)
            {
                var w=cage.weights[i];var target=Vector3.zero;for(int k=0;k<4;k++)target+=matrices[w.ids[k]].MultiplyPoint3x4(cage.points[i])*w.values[k];
                targets[i]=solved[i]=target;
            }
            var starts=new Vector3[collision.Length];var ends=new Vector3[collision.Length];var radii=new float[collision.Length];
            for(int j=0;j<collision.Length;j++)
            {
                var c=collision[j];float half=Mathf.Max(0,c.height*.5f-c.radius);var m=transform.worldToLocalMatrix*c.transform.localToWorldMatrix;
                starts[j]=m.MultiplyPoint3x4(c.center+Vector3.up*half);ends[j]=m.MultiplyPoint3x4(c.center-Vector3.up*half);radii[j]=m.MultiplyVector(Vector3.right*c.radius).magnitude+.004f;
            }
            for(int iteration=0;iteration<24;iteration++)
            {
                for(int e=0;e<edgeA.Length;e++)
                {
                    int a=edgeA[e],b=edgeB[e];var d=solved[b]-solved[a];float length=d.magnitude,weight=mobility[a]+mobility[b];
                    if(length<1e-7f||weight<1e-7f)continue;
                    float error=length-Mathf.Clamp(length,restLength[e]*.85f,restLength[e]*1.08f);
                    var correction=d*(.65f*error/(length*weight));solved[a]+=correction*mobility[a];solved[b]-=correction*mobility[b];
                }
                for(int i=0;i<solved.Length;i++)
                {
                    if(mobility[i]<.0001f){solved[i]=targets[i];continue;}
                    var point=Vector3.Lerp(solved[i],targets[i],.025f);
                    for(int j=0;j<starts.Length;j++)
                    {
                        var axis=ends[j]-starts[j];float t=Mathf.Clamp01(Vector3.Dot(point-starts[j],axis)/Mathf.Max(axis.sqrMagnitude,1e-10f));
                        var center=starts[j]+axis*t;var radial=point-center;float length=radial.magnitude;
                        if(length<radii[j]&&length>1e-7f)point=center+radial*(radii[j]/length);
                    }
                    solved[i]=targets[i]+Vector3.ClampMagnitude(point-targets[i],.12f*mobility[i]);
                }
            }
        }
        void OnDestroy(){if(sourceTop)sourceTop.forceRenderingOff=false;foreach(var go in proxies)if(go)Destroy(go);if(detailMesh)Destroy(detailMesh);if(cageMesh)Destroy(cageMesh);}
    }
}
