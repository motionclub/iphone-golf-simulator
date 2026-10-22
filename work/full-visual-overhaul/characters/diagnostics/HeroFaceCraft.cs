using System;using System.Collections.Generic;using System.Linq;using UnityEngine;
namespace GolfArcade.Tennis {
 /// Editable surface construction on the existing approved facial feature bounds.
 /// Preserve the bald body/head silhouette, eye glass and all feature centers;
 /// rebuild the brows as smooth arches and fit a fine liner to the actual cornea.
 public static class HeroFaceCraft {
  static readonly Dictionary<Mesh,Mesh> cache=new();
  public static Mesh Prepare(MatchHeroLook hero,Mesh source,Material[] materials){
   if(!source||!source.isReadable||source.name.Contains("(crafted face)"))return source;
   foreach(var material in materials)if(material&&material.name.Contains("Brow")&&!material.name.Contains("BrowSoft"))material.SetFloat("_CraftedPaint",1);
   if(cache.TryGetValue(source,out var ready)&&ready)return ready;
   HeroFaceBasis.Get(hero,out var right,out var up,out var forward);var projection=new HeroFaceProjection(hero);var raw=source.vertices;var oldNormals=source.normals;var oldUV=source.uv;
   var vertices=raw.ToList();var normals=oldNormals.ToList();var uv=(oldUV.Length==raw.Length?oldUV:Enumerable.Repeat(Vector2.zero,raw.Length).ToArray()).ToList();
   var submeshes=Enumerable.Range(0,source.subMeshCount).Select(i=>source.GetTriangles(i)).ToArray();
   float X(Vector3 p)=>Vector3.Dot(p,right);float Y(Vector3 p)=>Vector3.Dot(p,up);float Z(Vector3 p)=>Vector3.Dot(p,forward);
   var eyes=new List<Vector3>();for(int s=0;s<Mathf.Min(materials.Length,source.subMeshCount);s++)if(materials[s]&&materials[s].name.Contains("Sclera"))eyes.AddRange(submeshes[s].Select(i=>raw[i]));
   if(eyes.Count<6)return source;float mid=eyes.Average(X);
   Vector3 EyeEdge(float x,bool left){
    float best=-float.MaxValue;var point=eyes[0];
    for(int s=0;s<Mathf.Min(materials.Length,source.subMeshCount);s++)if(materials[s]&&materials[s].name.Contains("Sclera")){
     var triangles=submeshes[s];for(int t=0;t<triangles.Length;t+=3)for(int e=0;e<3;e++){
      var a=raw[triangles[t+e]];var b=raw[triangles[t+(e+1)%3]];if((X((a+b)*.5f)<mid)!=left)continue;float ax=X(a),bx=X(b);
      if((ax<=x&&x<=bx)||(bx<=x&&x<=ax)){float f=Mathf.Abs(bx-ax)>.000001f?(x-ax)/(bx-ax):.5f;var p=Vector3.Lerp(a,b,f);if(Y(p)>best){best=Y(p);point=p;}}
     }
    }return point;
   }
   int added=0,projected=0,missing=0;float projectionDelta=0;
   for(int s=0;s<Mathf.Min(materials.Length,source.subMeshCount);s++){
    string role=materials[s]?materials[s].name:"";
    if(role.Contains("BrowSoft")){submeshes[s]=Array.Empty<int>();continue;}
    if(role.Contains("LidLine")){
     var lineTriangles=new List<int>();
     foreach(bool left in new[]{true,false}){
      var glass=eyes.Where(p=>(X(p)<mid)==left).ToArray();float xmin=glass.Min(X),xmax=glass.Max(X);int start=vertices.Count;const int columns=80;
      for(int i=0;i<=columns;i++){float t=(float)i/columns;float x=Mathf.Lerp(xmin+.00005f,xmax-.00005f,t);var edge=EyeEdge(x,left);float thickness=.00065f*Mathf.Sqrt(Mathf.Max(0,Mathf.Sin(t*Mathf.PI)))+.000015f;
       vertices.Add(edge+up*.00010f+forward*.00008f);vertices.Add(edge+up*(.00010f+thickness)+forward*.00008f);normals.Add(forward);normals.Add(forward);uv.Add(Vector2.zero);uv.Add(Vector2.zero);
      }
      for(int i=0;i<columns;i++){int a=start+i*2,b=a+2,c=b+1,d=a+1;int[] tr={a,b,c,a,c,d};for(int k=0;k<6;k+=3)if(Vector3.Dot(Vector3.Cross(vertices[tr[k+1]]-vertices[tr[k]],vertices[tr[k+2]]-vertices[tr[k]]),forward)<0)(tr[k+1],tr[k+2])=(tr[k+2],tr[k+1]);lineTriangles.AddRange(tr);}
     }submeshes[s]=lineTriangles.ToArray();
    }
    if(!role.Contains("Brow")||role.Contains("BrowSoft"))continue;
    var triangles=new List<int>();
    foreach(bool left in new[]{true,false}){
     var ids=submeshes[s].Distinct().Where(i=>(X(raw[i])<mid)==left).ToArray();if(ids.Length<3)continue;var glass=eyes.Where(p=>(X(p)<mid)==left).ToArray();float eyeMin=glass.Min(X),eyeMax=glass.Max(X),eyeY=(glass.Max(Y)+glass.Min(Y))*.5f,eyeHalf=(glass.Max(Y)-glass.Min(Y))*.5f,eyeZ=glass.Average(Z);float width=(eyeMax-eyeMin)*(hero.female?.80f:.98f),eyeX=(eyeMin+eyeMax)*.5f;float xmin=eyeX-width*.5f,xmax=eyeX+width*.5f;
     // Author a continuous arch in the true eye/head frame, then fit every
     // sample to the same refined skin surface as the surrounding face.
     const int segments=64,rows=6;int start=vertices.Count;
     for(int i=0;i<=segments;i++){
      float a=(float)i/segments;float arch=Mathf.Max(0,Mathf.Sin(a*Mathf.PI));float x=Mathf.Lerp(xmin,xmax,a);
      float centre=eyeY+eyeHalf*1.65f+.008f+(hero.female?.0035f:.0028f)*arch;
      float thickness=(hero.female?.0020f:.0016f)*Mathf.Pow(arch,.5f)+.00002f;
      for(int j=0;j<=rows;j++){float t=(float)j/rows;float y=centre+Mathf.Lerp(-thickness,thickness,t),z=eyeZ-.015f;
       if(projection.Fit(x,y,z,out var fitted,out var fittedNormal)){projected++;projectionDelta=Mathf.Max(projectionDelta,Mathf.Abs(Vector3.Dot(fitted,forward)-z));}else missing++;vertices.Add(fitted);normals.Add(fittedNormal);uv.Add(new Vector2(a,t));
      }
     }
     for(int i=0;i<segments;i++)for(int j=0;j<rows;j++){int a=start+i*(rows+1)+j,b=a+rows+1,c=b+1,d=a+1;int[] t={a,b,c,a,c,d};for(int k=0;k<6;k+=3)if(Vector3.Dot(Vector3.Cross(vertices[t[k+1]]-vertices[t[k]],vertices[t[k+2]]-vertices[t[k]]),normals[t[k]])<0)(t[k+1],t[k+2])=(t[k+2],t[k+1]);triangles.AddRange(t);}
     added+=(segments+1)*(rows+1);
    }
    submeshes[s]=triangles.ToArray();materials[s].SetFloat("_CraftedPaint",1);
   }
   // Project skin-following paint independently of eyes and their closure shell.
   for(int s=0;s<Mathf.Min(materials.Length,source.subMeshCount);s++){
    var role=materials[s]?materials[s].name:"";if(!role.Contains("Lip")&&!role.Contains("Nostril"))continue;
    foreach(int i in submeshes[s].Distinct())if(projection.Fit(X(vertices[i]),Y(vertices[i]),Z(vertices[i]),out var fitted,out var fittedNormal)){vertices[i]=fitted;normals[i]=fittedNormal;}
   }
   for(int i=0;i<vertices.Count;i++)if(float.IsNaN(vertices[i].x)||float.IsNaN(vertices[i].y)||float.IsNaN(vertices[i].z)||float.IsInfinity(vertices[i].x)||float.IsInfinity(vertices[i].y)||float.IsInfinity(vertices[i].z))throw new InvalidOperationException("Crafted face non-finite vertex "+i);
   var mesh=UnityEngine.Object.Instantiate(source);mesh.name=source.name+" (crafted face)";mesh.hideFlags=HideFlags.DontSave;mesh.vertices=vertices.ToArray();mesh.normals=normals.ToArray();mesh.uv=uv.ToArray();for(int s=0;s<source.subMeshCount;s++)mesh.SetTriangles(submeshes[s],s);mesh.RecalculateBounds();cache[source]=mesh;
   Debug.Log("[HeroFaceCraft] Body-fitted="+projected+" missing="+missing+" maxDepthDelta="+projectionDelta+" smooth brow vertices="+added+" fitted1mm upper liner; original bald silhouette/eyes/feature centers unchanged");return mesh;
  }
 }
}
