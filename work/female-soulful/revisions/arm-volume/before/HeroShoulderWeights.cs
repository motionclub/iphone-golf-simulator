using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Diffuse the axilla weights along the existing surface, with fixed boundary
    /// weights. No rest positions, triangles, normals or armature are changed.
    public static class HeroShoulderWeights
    {
        static readonly Dictionary<Mesh,Mesh> Cache=new();
        public static Mesh Prepare(SkinnedMeshRenderer skin)
        {
            var src=skin.sharedMesh;if(Cache.TryGetValue(src,out var cached)&&cached)return cached;
            var p=src.vertices;var bw=src.boneWeights;var active=new List<int>();var local=new int[p.Length];
            for(int i=0;i<p.Length;i++)local[i]=-1;
            for(int i=0;i<p.Length;i++) if(Mathf.Abs(p[i].x)>.075f&&Mathf.Abs(p[i].x)<.225f&&p[i].z>1.055f&&p[i].z<1.37f) {local[i]=active.Count;active.Add(i);}
            var adjacent=new HashSet<int>[active.Count];for(int i=0;i<adjacent.Length;i++)adjacent[i]=new HashSet<int>();
            var tri=src.triangles;
            for(int t=0;t<tri.Length;t+=3)for(int k=0;k<3;k++){int a=tri[t+k],b=tri[t+(k+1)%3];if(local[a]>=0)adjacent[local[a]].Add(b);if(local[b]>=0)adjacent[local[b]].Add(a);}
            int count=skin.bones.Length;
            var original=new float[p.Length,count];for(int i=0;i<bw.Length;i++){var w=bw[i];original[i,w.boneIndex0]+=w.weight0;original[i,w.boneIndex1]+=w.weight1;original[i,w.boneIndex2]+=w.weight2;original[i,w.boneIndex3]+=w.weight3;}
            var weights=new float[active.Count,count];var next=new float[active.Count,count];
            for(int a=0;a<active.Count;a++)for(int b=0;b<count;b++)weights[a,b]=original[active[a],b];
            for(int pass=0;pass<48;pass++) {
                for(int a=0;a<active.Count;a++) {
                    int v=active[a];var q=p[v];float field=Smooth(.075f,.10f,Mathf.Abs(q.x))*(1-Smooth(.19f,.225f,Mathf.Abs(q.x)))*Smooth(1.055f,1.10f,q.z)*(1-Smooth(1.31f,1.37f,q.z));
                    for(int b=0;b<count;b++) {
                        float sum=0;foreach(int n in adjacent[a])sum+=local[n]>=0?weights[local[n],b]:original[n,b];
                        float mean=adjacent[a].Count>0?sum/adjacent[a].Count:weights[a,b];
                        next[a,b]=Mathf.Lerp(weights[a,b],mean,.55f*field);
                    }
                }
                (weights,next)=(next,weights);
            }
            int chest=System.Array.FindIndex(skin.bones,b=>b&&b.name=="Chest");
            int upperChest=System.Array.FindIndex(skin.bones,b=>b&&b.name=="UpperChest");
            var arm=new bool[count];for(int b=0;b<count;b++){string name=skin.bones[b]?skin.bones[b].name:"";arm[b]=name.EndsWith("UpperArm")||name.EndsWith("Shoulder");}
            for(int a=0;a<active.Count;a++) {
                var q=p[active[a]];
                // Front/back chest skin was weighted to the arm and clavicle even
                // below the armpit. Keep those panels on the ribcage; the medial
                // arm fold remains free to compress when the upper arm lifts.
                float torso=(1-Smooth(.12f,.16f,Mathf.Abs(q.x)))*Smooth(.020f,.065f,Mathf.Abs(q.y-.005f))
                    *Smooth(1.055f,1.10f,q.z)*(1-Smooth(1.27f,1.34f,q.z));
                float removed=0;for(int b=0;b<count;b++)if(arm[b]){float take=weights[a,b]*torso;weights[a,b]-=take;removed+=take;}
                float high=Smooth(1.14f,1.32f,q.z);weights[a,chest]+=removed*(1-high);weights[a,upperChest]+=removed*high;
                var ids=new int[4];var w=new float[4];
                for(int b=0;b<count;b++)for(int k=0;k<4;k++)if(weights[a,b]>w[k]) {for(int j=3;j>k;j--){ids[j]=ids[j-1];w[j]=w[j-1];}ids[k]=b;w[k]=weights[a,b];break;}
                float sum=w[0]+w[1]+w[2]+w[3];if(sum<.001f)continue;
                bw[active[a]]=new BoneWeight{boneIndex0=ids[0],boneIndex1=ids[1],boneIndex2=ids[2],boneIndex3=ids[3],weight0=w[0]/sum,weight1=w[1]/sum,weight2=w[2]/sum,weight3=w[3]/sum};
            }
            // UV/normal seams duplicate positions. Diffusing each triangle island
            // independently gave those duplicates different weights and tore open
            // the otherwise closed axilla during a raised-arm pose.
            var seams=new Dictionary<Vector3Int,List<int>>();
            for(int i=0;i<p.Length;i++) {
                var q=p[i];
                if(Mathf.Abs(q.x)<.075f||Mathf.Abs(q.x)>.225f||q.z<1.055f||q.z>1.37f)continue;
                var key=new Vector3Int(Mathf.RoundToInt(q.x*100000),Mathf.RoundToInt(q.y*100000),Mathf.RoundToInt(q.z*100000));
                if(!seams.TryGetValue(key,out var group))seams[key]=group=new List<int>();
                group.Add(i);
            }
            foreach(var group in seams.Values) {
                if(group.Count<2)continue;
                var sum=new float[count];
                foreach(int i in group) {var w=bw[i];sum[w.boneIndex0]+=w.weight0;sum[w.boneIndex1]+=w.weight1;sum[w.boneIndex2]+=w.weight2;sum[w.boneIndex3]+=w.weight3;}
                var ids=new int[4];var values=new float[4];
                for(int b=0;b<count;b++)for(int k=0;k<4;k++)if(sum[b]>values[k]) {
                    for(int j=3;j>k;j--){ids[j]=ids[j-1];values[j]=values[j-1];}
                    ids[k]=b;values[k]=sum[b];break;
                }
                float total=values[0]+values[1]+values[2]+values[3];
                var shared=new BoneWeight{boneIndex0=ids[0],boneIndex1=ids[1],boneIndex2=ids[2],boneIndex3=ids[3],weight0=values[0]/total,weight1=values[1]/total,weight2=values[2]/total,weight3=values[3]/total};
                foreach(int i in group)bw[i]=shared;
            }
            var mesh=Object.Instantiate(src);mesh.name+=" (continuous shoulder weights)";mesh.hideFlags=HideFlags.DontSave;mesh.boneWeights=bw;Cache[src]=mesh;return mesh;
        }
        static float Smooth(float a,float b,float x){float t=Mathf.Clamp01((x-a)/(b-a));return t*t*(3-2*t);}
    }
}
