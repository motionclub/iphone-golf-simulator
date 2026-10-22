using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
namespace GolfArcade.Tennis {
 /// Distal skin weights on the existing original golf hand. No pose/mesh/rig edits.
 public static class HeroGolfFingerWeights {
  static readonly Dictionary<Mesh,Mesh> cache=new();
  const string Tag=" (golf distal finger weights)";
  static float Smooth(float a,float b,float x){float t=Mathf.Clamp01((x-a)/(b-a));return t*t*(3-2*t);}
  public static Mesh Prepare(MatchHeroLook hero,SkinnedMeshRenderer body){
   var source=body ? body.sharedMesh:null;
   // Independent of wrist-roll experiments: an accepted weight field can ship
   // with the original clip pose. The male probe is held for its source regression.
   if(!hero||!hero.golfKit||!hero.female||!source||!source.isReadable||Environment.GetEnvironmentVariable("VISUAL_GOLF_FINGER_WEIGHTS")!="1")return source;
   if(source.name.Contains(Tag))return source;if(cache.TryGetValue(source,out var hit)&&hit)return hit;
   var palette=body.bones;var bind=source.bindposes;var vertices=source.vertices;var original=source.boneWeights;var weights=(BoneWeight[])original.Clone();int changed=0;float maxL1=0;
   foreach(string side in new[]{"Left","Right"}){
    int Find(string name)=>Array.FindIndex(palette,b=>b&&b.name==name);
    int hand=Find(side+"Hand");if(hand<0)return source;
    var sets=new int[4][];var points=new Vector3[4][];var lengths=new float[4][];string[] digits={"Index","Middle","Ring","Little"};
    for(int d=0;d<4;d++){
     sets[d]=new[]{Find(side+digits[d]+"Proximal"),Find(side+digits[d]+"Intermediate"),Find(side+digits[d]+"Distal")};if(sets[d].Any(i=>i<0))return source;
     var p=(Vector3)bind[sets[d][0]].inverse.GetColumn(3);var m=(Vector3)bind[sets[d][1]].inverse.GetColumn(3);var end=(Vector3)bind[sets[d][2]].inverse.GetColumn(3);
     points[d]=new[]{p,m,end,end+(end-m).normalized*.018f};lengths[d]=new[]{Vector3.Distance(p,m),Vector3.Distance(m,end),.018f};if(lengths[d].Any(l=>l<.0001f))return source;
    }
    var family=new HashSet<int>();var thumbs=new HashSet<int>();
    for(int i=0;i<palette.Length;i++){string name=palette[i]?palette[i].name:"";if(name==side+"Hand"||new[]{"Thumb","Index","Middle","Ring","Little"}.Any(d=>name.StartsWith(side+d)))family.Add(i);if(name.StartsWith(side+"Thumb"))thumbs.Add(i);}
    for(int v=0;v<vertices.Length;v++){
     var before=weights[v];int[] ids={before.boneIndex0,before.boneIndex1,before.boneIndex2,before.boneIndex3};float[] amounts={before.weight0,before.weight1,before.weight2,before.weight3};float mass=0,thumb=0;
     for(int k=0;k<4;k++){if(family.Contains(ids[k]))mass+=amounts[k];if(thumbs.Contains(ids[k]))thumb+=amounts[k];}if(mass<=.2f||thumb>.02f)continue;
     float best=float.PositiveInfinity,station=0;int choice=-1;
     for(int d=0;d<4;d++){float prefix=0;for(int j=0;j<3;j++){
      var axis=(points[d][j+1]-points[d][j])/lengths[d][j];float along=Mathf.Clamp(Vector3.Dot(vertices[v]-points[d][j],axis),0,lengths[d][j]);float distance=Vector3.Distance(vertices[v],points[d][j]+axis*along);
      if(distance<best){best=distance;choice=d;station=prefix+along;}prefix+=lengths[d][j];
     }}
     float first=lengths[choice][0],second=lengths[choice][1];float strength=Smooth(.45f*first,.9f*first,station)*(1-Smooth(.010f,.016f,best))*Smooth(.2f,.6f,mass);if(strength<=.000001f)continue;
     float basal=Smooth(0,.014f,station),mid=Smooth(first-.007f,first+.007f,station),endWeight=Smooth(first+second-.006f,first+second+.006f,station);
     var map=new Dictionary<int,float>();for(int k=0;k<4;k++)if(amounts[k]>0){if(!map.ContainsKey(ids[k]))map[ids[k]]=0;map[ids[k]]+=amounts[k]*(1-strength);}
     int[] target={hand,sets[choice][0],sets[choice][1],sets[choice][2]};float[] field={1-basal,basal*(1-mid),mid*(1-endWeight),endWeight};
     for(int k=0;k<4;k++){if(!map.ContainsKey(target[k]))map[target[k]]=0;map[target[k]]+=field[k]*strength;}
     var ranked=map.Where(p=>p.Value>0).OrderByDescending(p=>p.Value).Take(4).ToArray();float sum=ranked.Sum(p=>p.Value);if(sum<=0)continue;var after=new BoneWeight();
     if(ranked.Length>0){after.boneIndex0=ranked[0].Key;after.weight0=ranked[0].Value/sum;}if(ranked.Length>1){after.boneIndex1=ranked[1].Key;after.weight1=ranked[1].Value/sum;}if(ranked.Length>2){after.boneIndex2=ranked[2].Key;after.weight2=ranked[2].Value/sum;}if(ranked.Length>3){after.boneIndex3=ranked[3].Key;after.weight3=ranked[3].Value/sum;}
     var difference=new Dictionary<int,float>();for(int k=0;k<4;k++){if(!difference.ContainsKey(ids[k]))difference[ids[k]]=0;difference[ids[k]]-=amounts[k];}for(int k=0;k<ranked.Length;k++){if(!difference.ContainsKey(ranked[k].Key))difference[ranked[k].Key]=0;difference[ranked[k].Key]+=ranked[k].Value/sum;}
     float l1=difference.Values.Sum(x=>Mathf.Abs(x));if(l1<=.000001f)continue;weights[v]=after;changed++;maxL1=Mathf.Max(maxL1,l1);
    }
   }
   if(changed==0)return source;var copy=UnityEngine.Object.Instantiate(source);copy.name=source.name+Tag;copy.hideFlags=HideFlags.DontSave;copy.boneWeights=weights;cache[source]=copy;
   Debug.Log($"[GolfFingerWeights] Female changed={changed} maxWeightL1={maxL1:R}; rest vertices/normals/UVs/topology/morphs/palette exact; thumb/wrist excluded; clip pose untouched");return copy;
  }
 }
}
