using System;
using System.Collections.Generic;
using UnityEngine;
namespace GolfArcade.Tennis
{
    /// Volume-preserving support palette for the body's arm joints. The authored
    /// skeleton and rest vertices stay intact; garments keep their own palette.
    [DefaultExecutionOrder(1200)]
    public sealed class HeroArmSkinning : MonoBehaviour
    {
        struct Pair { public int a,b; public Transform[] support; }
        SkinnedMeshRenderer skin; Mesh owned; Transform supportRoot;
        Transform[] source; Matrix4x4[] bind; readonly List<Pair> pairs=new List<Pair>();
        const int Steps=8;
        public static void Build(SkinnedMeshRenderer body)
        {
            if(Environment.GetEnvironmentVariable("TENNIS_ARM_REPAIR")=="0" || !body || body.GetComponent<HeroArmSkinning>())return;
            body.gameObject.AddComponent<HeroArmSkinning>().Initialize(body);
        }
        static bool Arm(string n)=>n.EndsWith("UpperArm")||n.EndsWith("LowerArm")||n.EndsWith("Hand")||n.EndsWith("Shoulder");
        static bool Joint(string a,string b)
        {
            if(!Arm(a)&&!Arm(b))return false;
            bool Allowed(string n)=>Arm(n)||n=="Chest"||n=="Spine"||n=="UpperChest";
            return Allowed(a)&&Allowed(b);
        }
        void Initialize(SkinnedMeshRenderer body)
        {
            skin=body;source=body.bones;bind=body.sharedMesh.bindposes;
            owned=Instantiate(body.sharedMesh);owned.name=body.sharedMesh.name+" (arm volume)";
            supportRoot=new GameObject("ArmVolumePalette").transform;supportRoot.SetParent(body.transform,false);
            var palette=new List<Transform>(source);var binds=new List<Matrix4x4>(bind);var lookup=new Dictionary<long,int>();
            var weights=owned.boneWeights;
            bool limbOnly=body.sharedMesh.name.Contains("(anatomical arm weights)");
            // 2026-11-15 (work/perf-1115): what each bone is, worked out once per bone. Asked per vertex it was Transform.name
            // (into the engine, a new string each time) and up to twenty culture-aware EndsWith calls for each of 52,000
            // vertices, with two small arrays allocated per vertex: 0.2–0.6 s of the main thread on every hero spawn, first
            // or not. The weights that come out are the same (HeroPerfGuard's fingerprints, work/perf-1115).
            var names=new string[source.Length];var arm=new bool[source.Length];var shoulder=new bool[source.Length];var allowed=new bool[source.Length];
            for(int i=0;i<source.Length;i++){names[i]=source[i].name;arm[i]=Arm(names[i]);shoulder[i]=names[i].EndsWith("Shoulder");allowed[i]=arm[i]||names[i]=="Chest"||names[i]=="Spine"||names[i]=="UpperChest";}
            var ids=new int[4];var ws=new float[4];
            for(int v=0;v<weights.Length;v++)
            {
                var w=weights[v];ids[0]=w.boneIndex0;ids[1]=w.boneIndex1;ids[2]=w.boneIndex2;ids[3]=w.boneIndex3;ws[0]=w.weight0;ws[1]=w.weight1;ws[2]=w.weight2;ws[3]=w.weight3;
                // Sort explicitly: imported weights need not arrive in descending order.
                for(int i=0;i<4;i++)for(int j=i+1;j<4;j++)if(ws[j]>ws[i]){var f=ws[i];ws[i]=ws[j];ws[j]=f;var k=ids[i];ids[i]=ids[j];ids[j]=k;}
                // (= Joint(name, name): an arm bone on one side at least, and both among the arm, chest and spine)
                if(ws[1]<.00001f||!((arm[ids[0]]||arm[ids[1]])&&allowed[ids[0]]&&allowed[ids[1]]))continue;
                // The torso/arm fold needs linear skinning: rotating that thin
                // bridge through a DQ arc creates a broad web under a raised arm.
                if(limbOnly && (shoulder[ids[0]] || shoulder[ids[1]] || !arm[ids[0]] || !arm[ids[1]]))continue;
                int a=Mathf.Min(ids[0],ids[1]),b=Mathf.Max(ids[0],ids[1]);long key=((long)a<<32)|(uint)b;
                if(!lookup.TryGetValue(key,out int first))
                {
                    first=palette.Count;lookup.Add(key,first);var pair=new Pair{a=a,b=b,support=new Transform[Steps-1]};
                    for(int n=1;n<Steps;n++){var t=new GameObject((body.name.StartsWith("Acc_Glove")||body.name=="Kit_Top"?body.name+"_":"")+$"ArmBlend_{a}_{b}_{n}").transform;t.SetParent(supportRoot,false);pair.support[n-1]=t;palette.Add(t);binds.Add(Matrix4x4.identity);}pairs.Add(pair);
                }
                float total=ws[0]+ws[1],tweight=(ids[0]==b?ws[0]:ws[1])/total*Steps;int lo=Mathf.Clamp(Mathf.FloorToInt(tweight),0,Steps-1);float u=tweight-lo;
                int Index(int n)=>n==0?a:n==Steps?b:first+n-1;
                weights[v]=new BoneWeight{boneIndex0=Index(lo),weight0=total*(1-u),boneIndex1=Index(lo+1),weight1=total*u,boneIndex2=ids[2],weight2=ws[2],boneIndex3=ids[3],weight3=ws[3]};
            }
            owned.boneWeights=weights;owned.bindposes=binds.ToArray();body.sharedMesh=owned;body.bones=palette.ToArray();body.quality=SkinQuality.Bone4;Apply();
        }
        static Quaternion Scale(Quaternion q,float s)=>new Quaternion(q.x*s,q.y*s,q.z*s,q.w*s);
        static Quaternion Add(Quaternion a,Quaternion b)=>new Quaternion(a.x+b.x,a.y+b.y,a.z+b.z,a.w+b.w);
        static Quaternion Dual(Vector3 p,Quaternion q)=>Scale(new Quaternion(p.x,p.y,p.z,0)*q,.5f);
        public void Apply()
        {
            if(!skin||source==null)return;
            var inverse=skin.transform.worldToLocalMatrix;
            for(int pairIndex=0;pairIndex<pairs.Count;pairIndex++)
            {
                var pair=pairs[pairIndex];
                var a=inverse*source[pair.a].localToWorldMatrix*bind[pair.a];var b=inverse*source[pair.b].localToWorldMatrix*bind[pair.b];
                var qa=a.rotation;var qb=b.rotation;
                // Repaired clips keep neighbouring skin rotations below a half
                // turn, so the shortest dual-quaternion blend is continuous.
                if(Quaternion.Dot(qa,qb)<0)qb=Scale(qb,-1);
                var da=Dual(a.GetColumn(3),qa);var db=Dual(b.GetColumn(3),qb);
                for(int n=1;n<Steps;n++)
                {
                    float t=n/(float)Steps;var q=Add(Scale(qa,1-t),Scale(qb,t));var d=Add(Scale(da,1-t),Scale(db,t));
                    float norm=Mathf.Sqrt(Quaternion.Dot(q,q));q=Scale(q,1/norm);d=Scale(d,1/norm);d=Add(d,Scale(q,-Quaternion.Dot(q,d)));
                    var p=Scale(d*Quaternion.Inverse(q),2);var bone=pair.support[n-1];bone.localPosition=new Vector3(p.x,p.y,p.z);bone.localRotation=q;
                }
            }
        }
        void LateUpdate()=>Apply();
        void OnDestroy(){if(Application.isPlaying){if(owned)Destroy(owned);if(supportRoot)Destroy(supportRoot.gameObject);}else{if(owned)DestroyImmediate(owned);if(supportRoot)DestroyImmediate(supportRoot.gameObject);}}
    }
}
