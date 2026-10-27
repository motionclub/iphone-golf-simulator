using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
namespace GolfArcade.Tennis {
 /// Female hand finish (2026-10-19, Adnan: "reshape the hands of the female so they look right everywhere").
 /// The built hand has pencil-thin fingers that taper to a point (distal radius 3.8 mm against ~5.5 mm in the hand reference sheets,
 /// ArtDir/style/alive/hand-reference-2026-10-19). Every finger vertex is moved radially away from its finger's bone axis: a little
 /// at the knuckle, more at the middle joint and most at the tip, so the fingers keep their length and bind pose but get fuller joints
 /// and rounded pads. Topology, weights, UVs, rest/hierarchy and all clips stay exactly as authored; only vertex positions move
 /// (female only; the male hands are untouched). FEMALE_HAND_SHAPE=0 turns it off in the Editor for A/B.
 public static class HeroHandShape {
  static readonly Dictionary<Mesh,Mesh> cache=new();
  /// Radial growth (fraction of the vertex's distance from the finger axis) at the knuckle, middle joint, tip joint and tip.
  public static readonly float[] Fingers={.03f,.09f,.15f,.34f};
  public static readonly float[] Thumb={0f,0f,.03f,.08f};
  static float Smooth(float a,float b,float x){float t=Mathf.Clamp01((x-a)/(b-a));return t*t*(3-2*t);}
  static int owner0(int v,BoneWeight[] weights){var w=weights[v];return w.weight0>=w.weight1?w.boneIndex0:w.boneIndex1;}
  /// Finger-chain weight share of a vertex (those vertices already have radial normals).
  static float share0(int v,Transform[] palette,BoneWeight[] weights,string side){
   var w=weights[v];int[] idx={w.boneIndex0,w.boneIndex1,w.boneIndex2,w.boneIndex3};float[] amt={w.weight0,w.weight1,w.weight2,w.weight3};float sum=0;
   for(int k=0;k<4;k++){if(amt[k]<=0||idx[k]<0||idx[k]>=palette.Length||!palette[idx[k]])continue;var n=palette[idx[k]].name;if(n.StartsWith(side)&&(n.Contains("Index")||n.Contains("Middle")||n.Contains("Ring")||n.Contains("Little")||n.Contains("Thumb")))sum+=amt[k];}
   return sum;
  }
  /// WRIST + PALM (10-27, Adnan: "the female character has fucked up wrists/hands, super obvious when she walks ... similar structure to the
  /// male"). Measured on the shipped bodies (work/hands-ball-20261027): her knuckle span index->little is 53 mm against his 94 mm on a hand
  /// only 12 % shorter (93 / 106 mm wrist->middle knuckle), and her wrist is a round rod (width/depth .85) where his is a flat oval (1.25)
  /// flaring into a broad flat palm. So, in the hand's bind frame: each finger chain moves sideways away from the middle finger (index 8,
  /// ring 10, little 14, thumb 10 mm; a sideways move is along the finger's own flexion axis, so every curl in every clip keeps it), the
  /// palm follows the fingers' spread toward the knuckles, and each section from mid forearm to the knuckles is re-proportioned about its
  /// own centre: wrist 1.22 x wide / .86 x deep, palm .82 x deep. Weights, topology, UVs and bones stay as authored.
  public static readonly float[] Spread={.008f,.010f,.014f,.010f};   // index, ring, little, thumb (m)
  public static float[] Wrist(Transform[] palette,Matrix4x4[] bind,BoneWeight[] weights,Vector3[] vertices,Vector3[] normals=null){
#if UNITY_EDITOR
   if(Environment.GetEnvironmentVariable("FEMALE_WRIST_SHAPE")=="0")return null;
#endif
   int N=vertices.Length;var moved=new float[N];var orig=(Vector3[])vertices.Clone();bool any=false;
   foreach(string side in new[]{"Left","Right"}){
    int I(string n)=>Array.FindIndex(palette,b=>b&&b.name==side+n);
    int H=I("Hand"),L=I("LowerArm"),MP=I("MiddleProximal"),IP=I("IndexProximal"),RP=I("RingProximal"),LP=I("LittleProximal"),TI=I("ThumbIntermediate");
    if(H<0||L<0||MP<0||IP<0||RP<0||LP<0||TI<0)continue;
    Vector3 P(int b)=>bind[b].inverse.GetColumn(3);
    Vector3 wr=P(H),mk=P(MP);float hl=(mk-wr).magnitude;var ax=(mk-wr)/hl;
    var lat=Vector3.ProjectOnPlane(P(IP)-P(LP),ax).normalized;var nr=Vector3.Cross(ax,lat);
    float X(Vector3 p)=>Vector3.Dot(p-wr,lat);
    // per-vertex weight on each finger chain, the hand and the forearm
    string[] digits={"Index","Middle","Ring","Little","Thumb"};
    var chain=new int[palette.Length];for(int b=0;b<chain.Length;b++)chain[b]=-1;
    for(int f=0;f<5;f++)foreach(var j in new[]{"Proximal","Intermediate","Distal"}){int b=I(digits[f]+j);if(b>=0)chain[b]=f;}
    float mx=X(mk);
    float Off(int f){if(f==1)return 0;float fx=f==4?X(P(TI)):X(P(f==0?IP:f==2?RP:LP));float amt=f==0?Spread[0]:f==2?Spread[1]:f==3?Spread[2]:Spread[3];return amt*Mathf.Sign(fx-mx);}
    var off=new float[5];for(int f=0;f<5;f++)off[f]=Off(f);
    // knuckle line for the palm field, sorted by lateral position
    var kx=new[]{X(P(LP)),X(P(RP)),X(P(MP)),X(P(IP))};var ko=new[]{off[3],off[2],0f,off[0]};Array.Sort(kx,ko);
    float Field(float x){if(x<=kx[0])return ko[0];for(int i=0;i<3;i++)if(x<=kx[i+1]){float t=(x-kx[i])/Mathf.Max(1e-6f,kx[i+1]-kx[i]);return Mathf.Lerp(ko[i],ko[i+1],t);}return ko[3];}
    var fw=new float[N];var hw=new float[N];var lo=new float[N];var sel=new bool[N];var dd=new float[N];var xx=new float[N];var yy=new float[N];
    for(int v=0;v<N;v++){
     var w=weights[v];int[] idx={w.boneIndex0,w.boneIndex1,w.boneIndex2,w.boneIndex3};float[] amt={w.weight0,w.weight1,w.weight2,w.weight3};float fs=0,h=0,l=0,o=0;
     for(int k=0;k<4;k++){if(amt[k]<=0||idx[k]<0||idx[k]>=chain.Length)continue;if(idx[k]==H)h+=amt[k];else if(idx[k]==L)l+=amt[k];else if(chain[idx[k]]>=0){fs+=amt[k];o+=amt[k]*off[chain[idx[k]]];}}
     var r=orig[v]-wr;float d=Vector3.Dot(r,ax),x=Vector3.Dot(r,lat),y=Vector3.Dot(r,nr);
     dd[v]=d;xx[v]=x;yy[v]=y;fw[v]=fs;hw[v]=h;lo[v]=o;
     sel[v]=h+l+fs>.9f&&d>-.16f&&x*x+y*y<.09f*.09f;
    }
    // slice centres every 5 mm (a +-2 slice window)
    var sumX=new Dictionary<int,float>();var sumY=new Dictionary<int,float>();var cnt=new Dictionary<int,int>();
    for(int v=0;v<N;v++)if(sel[v]){int b=Mathf.RoundToInt(dd[v]/.005f);sumX.TryGetValue(b,out var a);sumX[b]=a+xx[v];sumY.TryGetValue(b,out var c);sumY[b]=c+yy[v];cnt.TryGetValue(b,out var n);cnt[b]=n+1;}
    (float,float) Centre(int b){float sx=0,sy=0;int n=0;for(int k=b-2;k<=b+2;k++)if(cnt.TryGetValue(k,out var c)){sx+=sumX[k];sy+=sumY[k];n+=c;}return n>0?(sx/n,sy/n):(0,0);}
    float[] at={-.16f,-.10f,-.03f,0f,.03f,.06f,.8f*hl,hl};
    float[] sl={1,1.06f,1.22f*.97f,1.22f,1.10f,1.00f,1,1};
    float[] sd={1,.95f,.86f,.86f,.86f,.82f,.88f,1};
    float Interp(float[] ys,float x){x=Mathf.Clamp(x,at[0],at[at.Length-1]);for(int i=0;i<at.Length-1;i++)if(x<=at[i+1]){float t=(x-at[i])/Mathf.Max(1e-6f,at[i+1]-at[i]);return Mathf.Lerp(ys[i],ys[i+1],t);}return ys[ys.Length-1];}
    for(int v=0;v<N;v++){
     if(!sel[v])continue;
     float d=dd[v],x=xx[v],y=yy[v];
     float shift=lo[v]+Mathf.Clamp01(hw[v])*(1-Mathf.Clamp01(fw[v]))*Field(x)*Smooth(.05f*hl,.85f*hl,d);
     float k=1-Mathf.Clamp01(fw[v]*1.6f);
     var (cx,cy)=Centre(Mathf.RoundToInt(d/.005f));
     float gx=1+(Interp(sl,d)-1)*k,gy=1+(Interp(sd,d)-1)*k;
     float nx=cx+(x-cx)*gx+shift,ny=cy+(y-cy)*gy;
     // the authored normal through the same section stretch (inverse transpose): no recalculation, so the forearm's UV seam keeps one normal
     if(normals!=null&&normals.Length==N){var n0=normals[v];normals[v]=(ax*Vector3.Dot(n0,ax)+lat*(Vector3.Dot(n0,lat)/gx)+nr*(Vector3.Dot(n0,nr)/gy)).normalized;}
     var to=wr+ax*d+lat*nx+nr*ny;moved[v]=(to-orig[v]).magnitude;vertices[v]=to;if(moved[v]>1e-5f)any=true;
    }
   }
   if(any){float mx2=0;int n2=0;foreach(var m in moved){if(m>1e-5f)n2++;mx2=Mathf.Max(mx2,m);}Debug.Log("[HeroHandShape] Female wrist+palm reshape: vertices="+n2+" max="+(mx2*1000f).ToString("F1")+" mm");}
   return any?moved:null;
  }
  public static Mesh Prepare(SkinnedMeshRenderer body,bool female) {
   var source=body?body.sharedMesh:null;
   if(!female||!source||!source.isReadable||source.name.Contains("(hand shape)"))return source;
#if UNITY_EDITOR
   if(Environment.GetEnvironmentVariable("FEMALE_HAND_SHAPE")=="0")return source;
#endif
   if(cache.TryGetValue(source,out var done)&&done)return done;
   var palette=body.bones;var bind=source.bindposes;var weights=source.boneWeights;var vertices=source.vertices;var normals=source.normals;int moved=0,shaded=0;float maxMove=0;
   bool smoothNormals=normals!=null&&normals.Length==vertices.Length;
#if UNITY_EDITOR
   if(Environment.GetEnvironmentVariable("FEMALE_HAND_NORMALS")=="0")smoothNormals=false;
#endif
   foreach(string side in new[]{"Left","Right"}) {
    var chains=new List<(string name,int[] ids,float[] gain)>();
    foreach(string finger in new[]{"Index","Middle","Ring","Little","Thumb"}) {
     var ids=new[]{"Proximal","Intermediate","Distal"}.Select(j=>Array.FindIndex(palette,b=>b&&b.name==side+finger+j)).ToArray();
     if(ids.Any(i=>i<0))continue;chains.Add((finger,ids,finger=="Thumb"?Thumb:Fingers));
    }
    var owner=new int[vertices.Length];var share=new float[vertices.Length];
    for(int v=0;v<vertices.Length;v++){
     owner[v]=-1;var w=weights[v];int[] idx={w.boneIndex0,w.boneIndex1,w.boneIndex2,w.boneIndex3};float[] amt={w.weight0,w.weight1,w.weight2,w.weight3};
     for(int c=0;c<chains.Count;c++){float sum=0;for(int k=0;k<4;k++)if(amt[k]>0&&Array.IndexOf(chains[c].ids,idx[k])>=0)sum+=amt[k];if(sum>share[v]){share[v]=sum;owner[v]=c;}}
    }
    for(int c=0;c<chains.Count;c++) {
     var ids=chains[c].ids;var gain=chains[c].gain;
     Vector3 P0=bind[ids[0]].inverse.GetColumn(3),P1=bind[ids[1]].inverse.GetColumn(3),P2=bind[ids[2]].inverse.GetColumn(3);
     var dist=(P2-P1).normalized;float tip=.012f;
     for(int v=0;v<vertices.Length;v++)if(owner[v]==c&&share[v]>.5f)tip=Mathf.Max(tip,Vector3.Dot(vertices[v]-P2,dist));
     tip=Mathf.Min(tip,.030f);Vector3 P3=P2+dist*tip;
     Vector3[] pts={P0,P1,P2,P3};
     for(int v=0;v<vertices.Length;v++) {
      if(owner[v]!=c||share[v]<.35f)continue;
      // closest point on the finger's polyline, and the gain there
      float best=float.MaxValue;Vector3 at=P0;float g=0;
      for(int s=0;s<3;s++){
       var a=pts[s];var ab=pts[s+1]-a;float t=Mathf.Clamp01(Vector3.Dot(vertices[v]-a,ab)/Mathf.Max(1e-8f,ab.sqrMagnitude));var p=a+ab*t;float d=(vertices[v]-p).sqrMagnitude;
       if(d<best){best=d;at=p;float u=s==2?t*t*(3-2*t)*.85f+t*.15f:t;g=Mathf.Lerp(gain[s],gain[s+1],u);}
      }
      float blend=Smooth(.35f,.80f,share[v]);float amount=g*blend;
      var r=vertices[v]-at;var to=at+r*(1+amount);maxMove=Mathf.Max(maxMove,(to-vertices[v]).magnitude);vertices[v]=to;if(amount>1e-4f)moved++;
      // the finger is a cylinder with a domed tip: its surface normal is the radial direction from the axis (the tip's dome, from the tip point),
      // blended with the authored normal where the finger joins the palm, so the finger shades round instead of in flat facets
      if(smoothNormals&&r.sqrMagnitude>1e-10f){var radial=r.normalized;float k=.9f*Smooth(.5f,.9f,share[v]);normals[v]=Vector3.Slerp(normals[v].normalized,radial,k).normalized;shaded++;}
     }
    }
   }
#if UNITY_EDITOR
   if(Environment.GetEnvironmentVariable("HAND_SHAPE_LOG")=="1"){
    // bind-pose bend of each finger joint (deg), from the bone heads in the bind pose: how cupped the rest hand is
    foreach(string side in new[]{"Right"}){
     int H=Array.FindIndex(palette,b=>b&&b.name==side+"Hand");if(H<0)continue;Vector3 Hd=bind[H].inverse.GetColumn(3);var sb=new System.Text.StringBuilder("[HeroHandShape] bind bend "+side+": ");
     foreach(string f in new[]{"Index","Middle","Ring","Little","Thumb"}){
      var q=new[]{"Proximal","Intermediate","Distal"}.Select(j=>Array.FindIndex(palette,b=>b&&b.name==side+f+j)).ToArray();if(q.Any(i=>i<0))continue;
      Vector3 a=bind[q[0]].inverse.GetColumn(3),b2=bind[q[1]].inverse.GetColumn(3),c=bind[q[2]].inverse.GetColumn(3);
      sb.Append(f+" "+Vector3.Angle(a-Hd,b2-a).ToString("F0")+"/"+Vector3.Angle(b2-a,c-b2).ToString("F0")+"  ");
     }
     Debug.Log(sb.ToString());
    }
   }
#endif
   // PALM (10-19 r3, Adnan: "fix the thumb and the palm so it looks like a regular hand"): the palm was flat with the thumb tacked onto its edge. A soft
   // thenar pad (the muscle at the thumb's base, along the thumb's metacarpal) is raised on the palm side, and a lower hypothenar pad on the little-finger edge.
   int pads=0;
   foreach(string side in new[]{"Left","Right"}) {
    int H=Array.FindIndex(palette,b=>b&&b.name==side+"Hand"),TP=Array.FindIndex(palette,b=>b&&b.name==side+"ThumbProximal"),TI=Array.FindIndex(palette,b=>b&&b.name==side+"ThumbIntermediate");
    int MP=Array.FindIndex(palette,b=>b&&b.name==side+"MiddleProximal"),IP=Array.FindIndex(palette,b=>b&&b.name==side+"IndexProximal"),LP=Array.FindIndex(palette,b=>b&&b.name==side+"LittleProximal");
    int ID=Array.FindIndex(palette,b=>b&&b.name==side+"IndexDistal");
    if(H<0||TP<0||TI<0||MP<0||IP<0||LP<0||ID<0)continue;
    Vector3 hd=bind[H].inverse.GetColumn(3),tp=bind[TP].inverse.GetColumn(3),ti=bind[TI].inverse.GetColumn(3),mp=bind[MP].inverse.GetColumn(3),ip=bind[IP].inverse.GetColumn(3),lp=bind[LP].inverse.GetColumn(3);
    var along=(mp-hd).normalized;var lat=(ip-lp).normalized;var n=Vector3.Cross(along,lat).normalized;
    // the palm side is where the cupped fingers curl to
    Vector3 curl=(Vector3)bind[ID].inverse.GetColumn(3)-ip;var palmDir=Vector3.Dot(curl,n)>=0?n:-n;
    Vector3 thenar=Vector3.Lerp(tp,ti,.45f),hypo=Vector3.Lerp(hd,lp,.6f);
    for(int v=0;v<vertices.Length;v++){
     var w=weights[v];int[] idx={w.boneIndex0,w.boneIndex1,w.boneIndex2,w.boneIndex3};float[] amt={w.weight0,w.weight1,w.weight2,w.weight3};float h=0;
     for(int k=0;k<4;k++)if(amt[k]>0&&(idx[k]==H||idx[k]==TP))h+=amt[k];
     if(h<.4f||share0(v,palette,weights,side)>.3f&&Array.IndexOf(new[]{TP},owner0(v,weights))<0)continue;
     float face=normals!=null&&normals.Length==vertices.Length?Smooth(0f,.35f,Vector3.Dot(normals[v].normalized,palmDir)):1f;if(face<=0)continue;
     Vector3 d1=vertices[v]-thenar;d1-=palmDir*Vector3.Dot(d1,palmDir);Vector3 d2=vertices[v]-hypo;d2-=palmDir*Vector3.Dot(d2,palmDir);
     float push=.0050f*Mathf.Exp(-d1.sqrMagnitude/(2*.017f*.017f))+.0028f*Mathf.Exp(-d2.sqrMagnitude/(2*.016f*.016f));
     push*=face*Smooth(.4f,.8f,h);if(push<1e-5f)continue;
     vertices[v]+=palmDir*push;pads++;maxMove=Mathf.Max(maxMove,push);
    }
   }
   Debug.Log("[HeroHandShape] palm pads vertices="+pads);
   // after the finger fullness (it measures from each finger's bone axis) and the palm pads: the wrist + palm re-proportion and the finger spread
   Wrist(palette,bind,weights,vertices,smoothNormals?normals:null);
   done=UnityEngine.Object.Instantiate(source);done.name=source.name+" (hand shape)";done.hideFlags=HideFlags.DontSave;done.vertices=vertices;
   if(smoothNormals){
    // the palm, back of the hand and wrist: the angle-weighted smooth normal of the new surface replaces the authored one (it shaded in flat
    // facets on this coarse mesh), fading back to the authored normal toward the forearm so the wrist seam keeps matching
    var calc=UnityEngine.Object.Instantiate(done);calc.RecalculateNormals();var smooth=calc.normals;UnityEngine.Object.DestroyImmediate(calc);
    int smoothed=0;
    foreach(string side in new[]{"Left","Right"}) {
     int hand=Array.FindIndex(palette,b=>b&&b.name==side+"Hand");int lower=Array.FindIndex(palette,b=>b&&b.name==side+"LowerArm");if(hand<0)continue;
     for(int v=0;v<vertices.Length;v++){
      var w=weights[v];int[] idx={w.boneIndex0,w.boneIndex1,w.boneIndex2,w.boneIndex3};float[] amt={w.weight0,w.weight1,w.weight2,w.weight3};float h=0;
      for(int k=0;k<4;k++)if(amt[k]>0&&idx[k]==hand)h+=amt[k];
      float k2=Smooth(.25f,.75f,h)*.85f;
      if(k2<=.01f||share0(v,palette,weights,side)>.35f)continue;
      normals[v]=Vector3.Slerp(normals[v].normalized,smooth[v].normalized,k2).normalized;smoothed++;
     }
    }
    done.normals=normals;Debug.Log("[HeroHandShape] smooth palm/back normals="+smoothed);
   }
   done.RecalculateBounds();cache[source]=done;
   Debug.Log("[HeroHandShape] Female hands: fuller fingers, vertices moved="+moved+" shaded="+shaded+" maxMove="+(maxMove*1000f).ToString("F2")+" mm; topology, weights, UVs and rest retained");
   return done;
  }
 }
}
