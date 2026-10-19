using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Pose-space axilla compression. The hanging-arm rest mesh is unchanged;
    /// the low underarm fold tucks towards the shoulder as the arm lifts.
    [DefaultExecutionOrder(1210)]
    public sealed class HeroShoulderDeformation : MonoBehaviour
    {
        MatchHeroLook look;
        readonly int[] shapes = { -1, -1 };
        readonly Vector3[] down = new Vector3[2];
        bool separateGarment;
        Transform chest;SkinnedMeshRenderer top;Mesh ownedBody,ownedTop;readonly int[] clothShapes={-1,-1};
        public static void Attach(MatchHeroLook hero)
        {
            if (!hero || !hero.female || !hero.body || hero.GetComponent<HeroShoulderDeformation>()) return;
            hero.gameObject.AddComponent<HeroShoulderDeformation>().Initialize(hero);
        }
        void Initialize(MatchHeroLook hero)
        {
            look=hero; chest=hero.Bone(HumanBodyBones.Chest);
            separateGarment=hero.kit!=null && hero.kit.Any(r=>r&&r.sharedMesh&&r.sharedMesh.name.Contains("FemaleSoulful"));
            var mesh=Instantiate(hero.body.sharedMesh);ownedBody=mesh; mesh.name += " (shoulder folds)";
            mesh.hideFlags=HideFlags.DontSave;
            var points=mesh.vertices;var normal=new Vector3[points.Length];
            var bind=mesh.bindposes;var bones=hero.body.bones;
            int ci=Array.FindIndex(bones,b=>b==chest);
            for(int side=0;side<2;side++) {
                string prefix=side==0?"Left":"Right";
                int ui=Array.FindIndex(bones,b=>b&&b.name==prefix+"UpperArm"),li=Array.FindIndex(bones,b=>b&&b.name==prefix+"LowerArm");
                Vector3 shoulder=bind[ui].inverse.GetColumn(3),elbow=bind[li].inverse.GetColumn(3);
                down[side]=bind[ci].MultiplyVector(elbow-shoulder).normalized;
                float sign=Mathf.Sign(shoulder.x);
                var delta=new Vector3[points.Length];
                for(int i=0;i<points.Length;i++) {
                    var p=points[i];float x=p.x*sign;
                    float field=Smooth(.085f,.125f,x)*(1-Smooth(.150f,.185f,x))
                        *Smooth(1.04f,1.16f,p.z)
                        *(1-Smooth(.040f,.100f,Mathf.Abs(p.y-.005f)));
                    delta[i]=new Vector3(0,0,Mathf.Max(0,1.275f-p.z)*field);
                }
                string name="ShoulderFold_"+prefix;
                mesh.AddBlendShapeFrame(name,100,delta,NormalDelta(mesh,delta),normal);shapes[side]=mesh.GetBlendShapeIndex(name);
            }
            hero.body.sharedMesh=mesh;
            if(!hero.golfKit) BindTankToTorso(hero);
            if(separateGarment)FemaleShoulderFit.Attach(hero);
            if(separateGarment)FemaleGarmentFinish.Attach(hero);
        }
        static float Smooth(float a,float b,float x){float t=Mathf.Clamp01((x-a)/(b-a));return t*t*(3-2*t);}
        void BindTankToTorso(MatchHeroLook hero)
        {
            top=hero.kit?.FirstOrDefault(r=>r&&r.name=="Kit_Top");
            if(!top||!MatchHeroLook.IsKitV2(top))return;
            // This independently built tank carries torso bindings and its own CV2 targets.
            if(top.sharedMesh.name.Contains("FemaleSoulful"))return;
            // A garment-pipeline mesh (" [gp]") carries its own limb-wrap weights and GP_Pose correctives: this arm->chest rewrite and the
            // old tank's ShoulderCloth shapes (fitted to today's vertex order) would overwrite them, or throw on the new topology.
            if(top.sharedMesh.name.Contains("[gp]"))return;
            var mesh=Instantiate(top.sharedMesh);ownedTop=mesh;mesh.name += " (torso binding)";mesh.hideFlags=HideFlags.DontSave;
            var palette=top.bones.ToList();var bind=mesh.bindposes.ToList();var bodyBones=hero.body.bones;
            int Index(string name) {
                int i=palette.FindIndex(b=>b&&b.name==name);if(i>=0)return i;
                int bi=Array.FindIndex(bodyBones,b=>b&&b.name==name);
                palette.Add(bodyBones[bi]);bind.Add(hero.body.sharedMesh.bindposes[bi]);return palette.Count-1;
            }
            int chest=Index("Chest"),upper=Index("UpperChest");
            var weights=mesh.boneWeights;var p=mesh.vertices;
            for(int v=0;v<weights.Length;v++) {
                var b=weights[v];var map=new Dictionary<int,float>();
                void Add(int i,float w){if(w<=0)return;map[i]=map.TryGetValue(i,out float a)?a+w:w;}
                void Real(string n,float w){
                    if(n.EndsWith("UpperArm")||n.EndsWith("LowerArm")||n.EndsWith("Hand")) {
                        float up=Smooth(1.14f,1.32f,p[v].z);Add(chest,w*(1-up));Add(upper,w*up);
                    }else Add(Index(n),w);
                }
                void Expand(int i,float w){
                    if(w<=0)return;string n=palette[i].name;
                    if(n.StartsWith("ArmBlend_")) {var a=n.Split('_');float t=int.Parse(a[3])/8f;Real(bodyBones[int.Parse(a[1])].name,w*(1-t));Real(bodyBones[int.Parse(a[2])].name,w*t);}
                    else Real(n,w);
                }
                Expand(b.boneIndex0,b.weight0);Expand(b.boneIndex1,b.weight1);Expand(b.boneIndex2,b.weight2);Expand(b.boneIndex3,b.weight3);
                var sorted=map.OrderByDescending(a=>a.Value).Take(4).ToArray();float sum=sorted.Sum(a=>a.Value);var ids=new int[4];var ws=new float[4];
                for(int k=0;k<sorted.Length;k++){ids[k]=sorted[k].Key;ws[k]=sorted[k].Value/sum;}
                weights[v]=new BoneWeight{boneIndex0=ids[0],boneIndex1=ids[1],boneIndex2=ids[2],boneIndex3=ids[3],weight0=ws[0],weight1=ws[1],weight2=ws[2],weight3=ws[3]};
            }
            mesh.boneWeights=weights;mesh.bindposes=bind.ToArray();top.bones=palette.ToArray();
            // Previous shapes were fitted to the arm-weighted tank. They must not
            // pull the new torso binding back into that deformation.
            var retained = new List<(string name, float frame, Vector3[] delta, Vector3[] normal, Vector3[] tangent)>();
            var retainedWeights = new Dictionary<string, float>();
            for (int shape = 0; shape < mesh.blendShapeCount; shape++) {
                string name = mesh.GetBlendShapeName(shape);
                if (name.StartsWith("CV2_Pose") || name.StartsWith("TailoredSleeve_") || name.StartsWith("LocalUnderarm_")) continue;
                retainedWeights[name] = top.GetBlendShapeWeight(shape);
                for (int frame = 0; frame < mesh.GetBlendShapeFrameCount(shape); frame++) {
                    var delta = new Vector3[mesh.vertexCount]; var normal = new Vector3[mesh.vertexCount]; var tangent = new Vector3[mesh.vertexCount];
                    mesh.GetBlendShapeFrameVertices(shape, frame, delta, normal, tangent);
                    retained.Add((name, mesh.GetBlendShapeFrameWeight(shape, frame), delta, normal, tangent));
                }
            }
            mesh.ClearBlendShapes();
            foreach (var frame in retained) mesh.AddBlendShapeFrame(frame.name, frame.frame, frame.delta, frame.normal, frame.tangent);
            var data=Resources.Load<TextAsset>("Tennis/KitsV2/Female/ShoulderCloth");
            if(data)using(var reader=new System.IO.BinaryReader(new System.IO.MemoryStream(data.bytes))) {
                int count=reader.ReadInt32();if(count!=mesh.vertexCount)throw new InvalidOperationException("Tank shoulder corrective topology mismatch");
                for(int side=0;side<2;side++) {
                    var delta=new Vector3[count];for(int i=0;i<count;i++)delta[i]=new Vector3(reader.ReadSingle(),reader.ReadSingle(),reader.ReadSingle());
                    string name="ShoulderCloth_"+side;mesh.AddBlendShapeFrame(name,100,delta,NormalDelta(mesh,delta),new Vector3[count]);clothShapes[side]=mesh.GetBlendShapeIndex(name);
                }
            }
            top.sharedMesh=mesh;
            foreach (var weight in retainedWeights) top.SetBlendShapeWeight(mesh.GetBlendShapeIndex(weight.Key), weight.Value);
        }
        public void Apply()
        {
            if(!look||!chest)return;
            for(int side=0;side<2;side++) {
                var upper=look.Bone(side==0?HumanBodyBones.LeftUpperArm:HumanBodyBones.RightUpperArm);
                var lower=look.Bone(side==0?HumanBodyBones.LeftLowerArm:HumanBodyBones.RightLowerArm);
                float angle=Vector3.Angle(down[side],chest.InverseTransformDirection(lower.position-upper.position));
                float weight=100*Smooth(20,90,angle);
                // The axilla compresses near shoulder height, then opens again
                // overhead. Keeping the fully compressed fold at a serve's full reach
                // inverts the inner shoulder surface.
                float foldWeight=weight*Mathf.Lerp(1,.6f,Smooth(110,155,angle));
                // The new separate garments retain the complete original axilla.
                // The old compression morph folds that surface through itself.
                if(separateGarment)foldWeight=0;
                look.body.SetBlendShapeWeight(shapes[side],foldWeight);
                if(top&&clothShapes[side]>=0)top.SetBlendShapeWeight(clothShapes[side],weight);
            }
        }
        static Vector3[] NormalDelta(Mesh mesh,Vector3[] delta)
        {
            var p=mesh.vertices;var tris=mesh.triangles;var a=new Vector3[p.Length];var b=new Vector3[p.Length];
            for(int i=0;i<tris.Length;i+=3){int x=tris[i],y=tris[i+1],z=tris[i+2];var n=Vector3.Cross(p[y]-p[x],p[z]-p[x]);var m=Vector3.Cross(p[y]+delta[y]-p[x]-delta[x],p[z]+delta[z]-p[x]-delta[x]);a[x]+=n;a[y]+=n;a[z]+=n;b[x]+=m;b[y]+=m;b[z]+=m;}
            var source=mesh.normals;var output=new Vector3[p.Length];
            for(int i=0;i<p.Length;i++)if((a[i]-b[i]).sqrMagnitude>1e-18f)output[i]=Quaternion.FromToRotation(a[i],b[i])*source[i]-source[i];
            return output;
        }
        void LateUpdate()=>Apply();
        void OnDestroy(){foreach(var mesh in new[]{ownedBody,ownedTop})if(mesh){if(Application.isPlaying)Destroy(mesh);else DestroyImmediate(mesh);}}
    }
}
