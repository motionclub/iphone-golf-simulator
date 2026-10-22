using System.Collections.Generic;
using UnityEngine;
namespace GolfArcade.Tennis
{
    /// Lossless shading correction: positions/topology/weights stay identical. Average
    /// noisy head normals within 18mm, retaining opposing and sharp anatomical normals.
    public static class HeroSkinNormals
    {
        static readonly Dictionary<Mesh,Mesh> cache=new();
        public static Mesh Prepare(SkinnedMeshRenderer body,Transform head)
        {
            if(!body||!head||!body.sharedMesh.isReadable)return body ? body.sharedMesh:null;
            var source=body.sharedMesh;if(cache.TryGetValue(source,out var ready))return ready;
            var p=source.vertices;var old=source.normals;var n=(Vector3[])old.Clone();var weights=source.boneWeights;
            int headIndex=System.Array.FindIndex(body.bones,b=>b==head);if(headIndex<0)return source;
            const float radius=.018f;var grid=new Dictionary<Vector3Int,List<int>>();var selected=new List<int>();
            Vector3Int Cell(Vector3 v)=>new(Mathf.FloorToInt(v.x/radius),Mathf.FloorToInt(v.y/radius),Mathf.FloorToInt(v.z/radius));
            for(int i=0;i<p.Length;i++){
                var w=weights[i];float h=(w.boneIndex0==headIndex?w.weight0:0)+(w.boneIndex1==headIndex?w.weight1:0)+(w.boneIndex2==headIndex?w.weight2:0)+(w.boneIndex3==headIndex?w.weight3:0);
                if(h<.75f)continue;selected.Add(i);var cell=Cell(p[i]);if(!grid.TryGetValue(cell,out var list))grid[cell]=list=new List<int>();list.Add(i);
            }
            float largest=0;
            foreach(int i in selected){
                var cell=Cell(p[i]);var sum=old[i]*.35f;float count=.35f;
                for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)for(int z=-1;z<=1;z++)if(grid.TryGetValue(cell+new Vector3Int(x,y,z),out var list))foreach(int j in list){
                    float d=(p[i]-p[j]).sqrMagnitude;if(d>=radius*radius||Vector3.Dot(old[i],old[j])<.35f)continue;
                    float w=1-d/(radius*radius);sum+=old[j]*w;count+=w;
                }
                n[i]=(sum/count).normalized;largest=Mathf.Max(largest,Vector3.Angle(old[i],n[i]));
            }
            ready=Object.Instantiate(source);ready.name=source.name+" (refined skin normals)";ready.hideFlags=HideFlags.DontSave;ready.normals=n;cache[source]=ready;
            Debug.Log("[HeroSkinNormals] "+source.name+" head vertices="+selected.Count+" max normal correction="+largest+"deg; geometry unchanged");return ready;
        }
    }
}
