using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
namespace GolfArcade.Tennis {
 /// Exact editable Blender counterpart: repair the unweighted thumb root using only
 /// Hand->ThumbProximal transfer inside its measured original rest-space segment.
 /// Geometry, rest/hierarchy, original clips and all four finger groups stay exact.
 public static class HeroHandWeights {
  static readonly Dictionary<Mesh,Mesh> cache=new();
  static float Smooth(float a,float b,float x){float t=Mathf.Clamp01((x-a)/(b-a));return t*t*(3-2*t);}
  public static Mesh Prepare(SkinnedMeshRenderer body,bool female) {
   var source=body.sharedMesh;if(!source||!source.isReadable||source.name.Contains("(thumb root weights)")||source.name.Contains("(continuous hands)")||source.name.Contains("(anatomical thumb chain weights)"))return source;if(cache.TryGetValue(source,out var copy)&&copy)return copy;
   var palette=body.bones;var bind=source.bindposes;var weights=source.boneWeights;var vertices=source.vertices;int changed=0;float maximum=0;
   foreach(string side in new[]{"Left","Right"}) {
    int hand=Array.FindIndex(palette,b=>b&&b.name==side+"Hand"),prox=Array.FindIndex(palette,b=>b&&b.name==side+"ThumbProximal"),middle=Array.FindIndex(palette,b=>b&&b.name==side+"ThumbIntermediate");if(hand<0||prox<0||middle<0)continue;
    var four=new HashSet<int>(palette.Select((b,i)=>new {b,i}).Where(v=>v.b&&v.b.name.StartsWith(side)&&new[]{"Index","Middle","Ring","Little"}.Any(d=>v.b.name.Contains(d))).Select(v=>v.i));
    Vector3 p=bind[prox].inverse.GetColumn(3),m=bind[middle].inverse.GetColumn(3);var axis=(m-p).normalized;float length=Vector3.Distance(p,m),radius=female ? .010f:.012f;
    int sideChanged=0;
    for(int vertex=0;vertex<weights.Length;vertex++) {
     var w=weights[vertex];
     // (2026-11-15, work/perf-1115: the hand and finger shares first, added up in the same order as below, so the 99 % of the
     // body that is no thumb root leaves before two arrays and a dictionary are allocated for it — the same weights come out)
     {
      float h0=0,f0=0;
      if(w.weight0>0){if(w.boneIndex0==hand)h0+=w.weight0;if(four.Contains(w.boneIndex0))f0+=w.weight0;}
      if(w.weight1>0){if(w.boneIndex1==hand)h0+=w.weight1;if(four.Contains(w.boneIndex1))f0+=w.weight1;}
      if(w.weight2>0){if(w.boneIndex2==hand)h0+=w.weight2;if(four.Contains(w.boneIndex2))f0+=w.weight2;}
      if(w.weight3>0){if(w.boneIndex3==hand)h0+=w.weight3;if(four.Contains(w.boneIndex3))f0+=w.weight3;}
      if(h0<.2f||f0>.05f)continue;
     }
     int[] indices={w.boneIndex0,w.boneIndex1,w.boneIndex2,w.boneIndex3};float[] amount={w.weight0,w.weight1,w.weight2,w.weight3};float hw=0,fw=0;var map=new Dictionary<int,float>();
     for(int k=0;k<4;k++){if(amount[k]<=0)continue;if(!map.ContainsKey(indices[k]))map[indices[k]]=0;map[indices[k]]+=amount[k];if(indices[k]==hand)hw+=amount[k];if(four.Contains(indices[k]))fw+=amount[k];}
     if(hw<.2f||fw>.05f)continue;
     var delta=vertices[vertex]-p;float along=Vector3.Dot(delta,axis),s=along/length,distance=(delta-axis*along).magnitude;
     float transfer=hw*.9f*Smooth(.02f,.50f,s)*(1-Smooth(.80f,1.50f,s))*(1-Smooth(radius*.45f,radius,distance));if(transfer<.005f)continue;
     map[hand]-=transfer;if(!map.ContainsKey(prox))map[prox]=0;map[prox]+=transfer;
     var sorted=map.OrderByDescending(k=>k.Value).Take(4).ToArray();float sum=sorted.Sum(k=>k.Value);var output=new BoneWeight();
     if(sorted.Length>0){output.boneIndex0=sorted[0].Key;output.weight0=sorted[0].Value/sum;}if(sorted.Length>1){output.boneIndex1=sorted[1].Key;output.weight1=sorted[1].Value/sum;}if(sorted.Length>2){output.boneIndex2=sorted[2].Key;output.weight2=sorted[2].Value/sum;}if(sorted.Length>3){output.boneIndex3=sorted[3].Key;output.weight3=sorted[3].Value/sum;}
     weights[vertex]=output;changed++;sideChanged++;maximum=Mathf.Max(maximum,transfer*2);
    }
    Debug.Log("[HeroHandWeights] "+(female?"Female":"Male")+" "+side+" thumb-root vertices="+sideChanged+" radius="+radius);
   }
   copy=UnityEngine.Object.Instantiate(source);copy.name=source.name+" (thumb root weights)";copy.hideFlags=HideFlags.DontSave;copy.boneWeights=weights;cache[source]=copy;
   Debug.Log("[HeroHandWeights] exact geometry/rest retained; changed="+changed+" maxWeightL1="+maximum);return copy;
  }
 }
}
