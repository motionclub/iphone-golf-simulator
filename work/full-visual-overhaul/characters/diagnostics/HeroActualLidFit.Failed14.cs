using System;using System.Collections.Generic;using System.Linq;using UnityEngine;
namespace GolfArcade.Tennis {
 /// Same authored quad construction, fitted to the actual imported Body aperture.
 /// Skin-space head bind -> rigid Face local is exact; no bound-registration guess.
 public static class HeroActualLidFit {
  struct Edge:IEquatable<Edge>{public int a,b;public Edge(int x,int y){a=Mathf.Min(x,y);b=Mathf.Max(x,y);}public bool Equals(Edge o)=>a==o.a&&b==o.b;public override bool Equals(object o)=>o is Edge e&&Equals(e);public override int GetHashCode()=>a*397^b;}
  struct Point{public Vector3 p,n;public Point(Vector3 v,Vector3 normal){p=v;n=normal;}}
  public static bool Build(MatchHeroLook hero,out Vector3[] positions,out Vector3[] normals,out int[] triangles){
   positions=null;normals=null;triangles=null;if(!hero.body||!hero.face)return false;
   var mesh=hero.body.sharedMesh;int head=Array.FindIndex(hero.body.bones,b=>b&&b.name=="Head");if(head<0)return false;
   var map=hero.face.transform.worldToLocalMatrix*hero.body.bones[head].localToWorldMatrix*mesh.bindposes[head];var nm=map.inverse.transpose;
   var vertices=mesh.vertices;var sourceNormals=mesh.normals;var welded=new List<Point>();var ids=new int[vertices.Length];var keys=new Dictionary<Vector3Int,int>();
   for(int v=0;v<vertices.Length;v++){
    var p=map.MultiplyPoint3x4(vertices[v]);var n=nm.MultiplyVector(sourceNormals[v]).normalized;var k=new Vector3Int(Mathf.RoundToInt(p.x*100000),Mathf.RoundToInt(p.y*100000),Mathf.RoundToInt(p.z*100000));
    if(!keys.TryGetValue(k,out int id)){id=welded.Count;keys[k]=id;welded.Add(new Point(p,n));}ids[v]=id;
   }
   var edges=new Dictionary<Edge,int>();for(int sub=0;sub<mesh.subMeshCount;sub++){var t=mesh.GetTriangles(sub);for(int i=0;i<t.Length;i+=3)for(int e=0;e<3;e++){var edge=new Edge(ids[t[i+e]],ids[t[i+(e+1)%3]]);if(edge.a==edge.b)continue;if(!edges.ContainsKey(edge))edges[edge]=0;edges[edge]++;}}
   var adjacency=new Dictionary<int,List<int>>();foreach(var e in edges.Where(e=>e.Value==1).Select(e=>e.Key)){if(!adjacency.ContainsKey(e.a))adjacency[e.a]=new();if(!adjacency.ContainsKey(e.b))adjacency[e.b]=new();adjacency[e.a].Add(e.b);adjacency[e.b].Add(e.a);}
   var right=hero.face.transform.InverseTransformDirection(hero.transform.right).normalized;var up=hero.face.transform.InverseTransformDirection(hero.transform.up).normalized;var forward=hero.face.transform.InverseTransformDirection(hero.transform.forward).normalized;
   var eye=hero.face.GetComponent<MeshFilter>().sharedMesh;var mats=hero.face.sharedMaterials;var eyePoints=new List<Vector3>();for(int sub=0;sub<mats.Length;sub++)if(mats[sub]&&mats[sub].name.Contains("Sclera"))eyePoints.AddRange(eye.GetTriangles(sub).Select(i=>eye.vertices[i]));
   if(eyePoints.Count==0)return false;float eyeUp=eyePoints.Average(p=>Vector3.Dot(p,up));
   var remaining=new HashSet<int>(adjacency.Keys);var loops=new List<List<Point>>();
   while(remaining.Count>0){var todo=new Stack<int>();todo.Push(remaining.First());var loop=new List<Point>();while(todo.Count>0){int v=todo.Pop();if(!remaining.Remove(v))continue;loop.Add(welded[v]);foreach(int n in adjacency[v])todo.Push(n);}if(loop.Count>20&&Mathf.Abs(loop.Average(p=>Vector3.Dot(p.p,up))-eyeUp)<.04f)loops.Add(loop);}
   if(loops.Count!=2){Debug.LogWarning("[HeroActualLidFit] actual welded aperture loops="+loops.Count+"; retain authored fallback");return false;}
   var outP=new List<Vector3>();var outN=new List<Vector3>();var outT=new List<int>();
   foreach(var loop in loops.OrderBy(l=>l.Average(p=>Vector3.Dot(p.p,right)))){
    // Change only coordinate basis; source normals remain the adjacent actual skin.
    var contour=loop.Select(p=>new Point(new Vector3(Vector3.Dot(p.p,right),Vector3.Dot(p.p,up),Vector3.Dot(p.p,forward)),new Vector3(Vector3.Dot(p.n,right),Vector3.Dot(p.n,up),Vector3.Dot(p.n,forward)))).ToList();
    float cx=contour.Average(p=>p.p.x),cy=contour.Average(p=>p.p.y);contour=contour.OrderBy(p=>Mathf.Atan2(p.p.y-cy,p.p.x-cx)).ToList();float xmin=contour.Min(p=>p.p.x),xmax=contour.Max(p=>p.p.x);
    (Point lo,Point hi) Cut(float x){x=Mathf.Clamp(x,xmin+.0000001f,xmax-.0000001f);var cut=new List<Point>();for(int i=0;i<contour.Count;i++){var a=contour[i];var b=contour[(i+1)%contour.Count];if((a.p.x<=x&&x<b.p.x)||(b.p.x<=x&&x<a.p.x)){float t=(x-a.p.x)/(b.p.x-a.p.x);cut.Add(new Point(Vector3.Lerp(a.p,b.p,t),Vector3.Lerp(a.n,b.n,t).normalized));}}return(cut.OrderBy(p=>p.p.y).First(),cut.OrderBy(p=>p.p.y).Last());}
    const int N=64,M=20;int start=outP.Count;var sample=new List<Vector3>();var edgeNormals=new List<Vector3>();
    for(int i=0;i<=N;i++){
     float x=xmin-.0015f+(xmax-xmin+.003f)*i/N;var (lo,hi)=Cut(x);float span=Mathf.Max(.00001f,hi.p.y-lo.p.y);
     float Slope(Point p)=>-p.n.y/(Mathf.Abs(p.n.z)<.15f?Mathf.Sign(p.n.z)*.15f:p.n.z);
     for(int j=0;j<=M;j++){
      float y=Mathf.Lerp(lo.p.y-.0015f,hi.p.y+.0015f,(float)j/M),t=(y-lo.p.y)/span,z;
      if(t<0)z=lo.p.z+Slope(lo)*(y-lo.p.y);else if(t>1)z=hi.p.z+Slope(hi)*(y-hi.p.y);
      else{float t2=t*t,t3=t2*t;z=(2*t3-3*t2+1)*lo.p.z+(t3-2*t2+t)*span*Slope(lo)+(-2*t3+3*t2)*hi.p.z+(t3-t2)*span*Slope(hi);}
      z+=.00012f;var p=right*x+up*y+forward*z;sample.Add(p);edgeNormals.Add((right*Mathf.Lerp(lo.n.x,hi.n.x,Mathf.Clamp01(t))+up*Mathf.Lerp(lo.n.y,hi.n.y,Mathf.Clamp01(t))+forward*Mathf.Lerp(lo.n.z,hi.n.z,Mathf.Clamp01(t))).normalized);
     }
    }
    var smooth=new Vector3[sample.Count];for(int i=0;i<N;i++)for(int j=0;j<M;j++){
     int a=i*(M+1)+j,b=a+M+1,c=b+1,d=a+1;int[] t={a,b,c,a,c,d};for(int k=0;k<t.Length;k+=3){var n=Vector3.Cross(sample[t[k+1]]-sample[t[k]],sample[t[k+2]]-sample[t[k]]);if(Vector3.Dot(n,forward)<0)n=-n;for(int q=0;q<3;q++)smooth[t[k+q]]+=n;}outT.AddRange(t.Select(v=>v+start));
    }
    for(int i=0;i<=N;i++)for(int j=0;j<=M;j++){int v=i*(M+1)+j;float outer=Mathf.Clamp01(Mathf.Min(i,N-i)/3f)*Mathf.Clamp01(Mathf.Min(j,M-j)/3f);outP.Add(sample[v]);outN.Add(Vector3.Lerp(edgeNormals[v],smooth[v].normalized,outer).normalized);}
   }
   positions=outP.ToArray();normals=outN.ToArray();triangles=outT.ToArray();Debug.Log("[HeroActualLidFit] exact Body inverse-bind->Face apertures=2 vertices="+positions.Length);return true;
  }
 }
}
