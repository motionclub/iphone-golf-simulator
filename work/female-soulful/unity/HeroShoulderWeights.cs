using System;
using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Correct arm/chest weight spill on the accepted female body without changing
    /// its rest vertices, topology, bind transforms or source animation clips.
    public static class HeroShoulderWeights
    {
        static readonly Dictionary<Mesh, Mesh> Cache = new();
        static float Smooth(float a, float b, float x) { float t = Mathf.Clamp01((x-a)/(b-a)); return t*t*(3-2*t); }
        static BoneWeight Pack(int[] ids, float[] weights)
        {
            for (int i=0;i<4;i++) for (int j=i+1;j<4;j++) if (weights[j]>weights[i])
            { (weights[i],weights[j])=(weights[j],weights[i]); (ids[i],ids[j])=(ids[j],ids[i]); }
            float sum=weights[0]+weights[1]+weights[2]+weights[3];
            return new BoneWeight { boneIndex0=ids[0],boneIndex1=ids[1],boneIndex2=ids[2],boneIndex3=ids[3],
                weight0=weights[0]/sum,weight1=weights[1]/sum,weight2=weights[2]/sum,weight3=weights[3]/sum };
        }
        public static Mesh Prepare(SkinnedMeshRenderer skin)
        {
            var src=skin.sharedMesh; if (Cache.TryGetValue(src,out var cached)&&cached) return cached;
            var points=src.vertices; var weights=src.boneWeights; var bones=skin.bones; var bind=src.bindposes;
            int chest=Array.FindIndex(bones,b=>b&&b.name=="Chest");
            for (int side=0;side<2;side++)
            {
                string prefix=side==0?"Left":"Right";
                int upper=Array.FindIndex(bones,b=>b&&b.name==prefix+"UpperArm"),lower=Array.FindIndex(bones,b=>b&&b.name==prefix+"LowerArm");
                if (upper<0||lower<0||chest<0) continue;
                var shoulder=(Vector3)bind[upper].inverse.GetColumn(3); var elbow=(Vector3)bind[lower].inverse.GetColumn(3);
                var axis=(elbow-shoulder).normalized; float sign=Mathf.Sign(shoulder.x);
                for (int i=0;i<points.Length;i++)
                {
                    var p=points[i]; float along=Vector3.Dot(p-shoulder,axis);
                    if (p.z<1.07f||p.z>1.40f||p.x*sign<.065f||(p-shoulder-axis*along).magnitude>.16f) continue;
                    var w=weights[i]; var ids=new[]{w.boneIndex0,w.boneIndex1,w.boneIndex2,w.boneIndex3}; var values=new[]{w.weight0,w.weight1,w.weight2,w.weight3};
                    float arm=0; for(int k=0;k<4;k++) if(ids[k]==upper||ids[k]==lower) arm+=values[k];
                    if (arm<1e-5f) continue;
                    // The narrow gap between the hanging arm and ribcage is the
                    // anatomical boundary. Heat weights crossed it onto both sides.
                    float boundary=Mathf.Lerp(.130f,.105f,Mathf.InverseLerp(1.18f,1.37f,p.z));
                    float target=Smooth(boundary-.003f,boundary+.003f,p.x*sign);
                    float fade=Smooth(1.07f,1.11f,p.z)*(1-Smooth(1.37f,1.40f,p.z)); target=Mathf.Lerp(arm,target,fade);
                    for(int k=0;k<4;k++) values[k]*=(ids[k]==upper||ids[k]==lower) ? target/arm : (1-target)/Mathf.Max(1-arm,1e-6f);
                    if (arm>.999999f&&target<1) { ids[3]=chest; values[3]=1-target; }
                    weights[i]=Pack(ids,values);
                }
            }
            // Split normals/UVs must not split a joint during motion.
            var seams=new Dictionary<Vector3Int,List<int>>();
            for(int i=0;i<points.Length;i++)
            {
                var p=points[i]; if(Mathf.Abs(p.x)<.075f||Mathf.Abs(p.x)>.235f||p.z<1.04f||p.z>1.40f)continue;
                var key=new Vector3Int(Mathf.RoundToInt(p.x*100000),Mathf.RoundToInt(p.y*100000),Mathf.RoundToInt(p.z*100000));
                if(!seams.TryGetValue(key,out var group))seams[key]=group=new List<int>(); group.Add(i);
            }
            foreach(var group in seams.Values)
            {
                if(group.Count<2)continue; var sum=new float[bones.Length];
                foreach(int i in group){var w=weights[i];sum[w.boneIndex0]+=w.weight0;sum[w.boneIndex1]+=w.weight1;sum[w.boneIndex2]+=w.weight2;sum[w.boneIndex3]+=w.weight3;}
                var ids=new int[4];var values=new float[4];
                for(int b=0;b<sum.Length;b++)for(int k=0;k<4;k++)if(sum[b]>values[k]){for(int j=3;j>k;j--){ids[j]=ids[j-1];values[j]=values[j-1];}ids[k]=b;values[k]=sum[b];break;}
                var shared=Pack(ids,values);foreach(int i in group)weights[i]=shared;
            }
            var mesh=UnityEngine.Object.Instantiate(src); mesh.name+=" (anatomical arm weights)"; mesh.hideFlags=HideFlags.DontSave;
            mesh.boneWeights=weights; Cache[src]=mesh; return mesh;
        }
    }
}
