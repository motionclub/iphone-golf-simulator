using System;
using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    // Apply AFTER HeroSkinNormals.Prepare: imported shape-normal deltas belong
    // to the imported normal basis and cannot be added to a replacement field.
    // This rebuilds only the two eyelid normal frames from their actual surfaces.
    // Positions, topology, UVs, weights, material ownership and shape weights stay intact.
    public static class HeroBlinkNormalField
    {
        static readonly Dictionary<Mesh, Mesh> Cache = new();
        struct Frame { public string name; public float weight; public Vector3[] p,n,t; }
        public static Mesh Prepare(Mesh source)
        {
            if (!source || !source.isReadable || source.blendShapeCount == 0) return source;
            // The fitted face replaces its resting normal field, so matching
            // blink deltas are required in player builds as well as in review.
            // Other meshes retain their existing opt-in diagnostic behavior.
            if (!source.name.Contains("reference face fit") &&
                Environment.GetEnvironmentVariable("VISUAL_BLINK_NORMAL_FIELD") != "1") return source;
            if (Cache.TryGetValue(source,out var cached) && cached) return cached;
            var p=source.vertices; var old=source.normals; var triangles=source.triangles;
            if (old.Length != p.Length) return source;
            var groups=new Dictionary<Vector3Int,int>(); var alias=new int[p.Length]; var unique=new List<Vector3>();
            for(int i=0;i<p.Length;i++) {
                var k=new Vector3Int(Mathf.RoundToInt(p[i].x*1000000),Mathf.RoundToInt(p[i].y*1000000),Mathf.RoundToInt(p[i].z*1000000));
                if(!groups.TryGetValue(k,out int j)) {j=unique.Count;groups[k]=j;unique.Add(p[i]);} alias[i]=j;
            }
            var rest=Field(p,triangles,alias,unique.Count,null);var baseField=rest.field;
            var frames=new List<Frame>(); int rewritten=0;
            for(int s=0;s<source.blendShapeCount;s++) for(int f=0;f<source.GetBlendShapeFrameCount(s);f++) {
                var frame=new Frame {name=source.GetBlendShapeName(s),weight=source.GetBlendShapeFrameWeight(s,f),p=new Vector3[p.Length],n=new Vector3[p.Length],t=new Vector3[p.Length]};
                source.GetBlendShapeFrameVertices(s,f,frame.p,frame.n,frame.t);
                if(frame.name=="Hero_Blink" || frame.name=="Hero_Blink_Half") {
                    var posed=(Vector3[])p.Clone();var moved=new bool[p.Length];
                    for(int i=0;i<p.Length;i++) {posed[i]+=frame.p[i];moved[i]=frame.p[i].sqrMagnitude>1e-14f;}
                    var target=Field(posed,triangles,alias,unique.Count,rest).field;
                    // Differential transport retains the accepted static head field
                    // and has exactly zero response where the surface did not rotate.
                    for(int i=0;i<p.Length;i++) {
                        int j=alias[i];var b=baseField[j];var q=target[j];
                        Vector3 n=old[i];
                        if(b.sqrMagnitude>.5f && q.sqrMagnitude>.5f)
                            n=Vector3.Slerp(old[i],(Quaternion.FromToRotation(b,q)*old[i]).normalized,.35f).normalized;
                        frame.n[i]=n-old[i];frame.t[i]=Vector3.zero;
                        if(frame.n[i].sqrMagnitude>1e-12f) rewritten++;
                    }
                }
                frames.Add(frame);
            }
            var result=UnityEngine.Object.Instantiate(source);result.name=source.name+" (coherent blink normals)";result.hideFlags=HideFlags.DontSave;
            result.ClearBlendShapes();foreach(var f in frames)result.AddBlendShapeFrame(f.name,f.weight,f.p,f.n,f.t);
            Cache[source]=result;Debug.Log("[HeroBlinkNormalField] rebuilt="+rewritten+"; source vertices/shape positions unchanged; accepted base normals retained");return result;
        }
        sealed class FieldData { public Vector3[] q,g,field; public CellGrid grid; }
        const float R=.008f;
        static bool Same(Vector3 a,Vector3 b)=>a.x==b.x&&a.y==b.y&&a.z==b.z;
        static void Mark(CellGrid grid,Vector3 at,bool[] todo)
        {
            int cx=CellGrid.Coord(at.x,R),cy=CellGrid.Coord(at.y,R),cz=CellGrid.Coord(at.z,R);
            for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)for(int z=-1;z<=1;z++)
                if(grid.Find(cx+x,cy+y,cz+z,out int s,out int e))for(int k=s;k<e;k++)todo[grid.Items[k]]=true;
        }
        /// The smoothed surface-normal field of `p` (one normal per welded position). With `rest` (the same mesh unposed): only
        /// the positions a posed vertex, or a face normal it changed, is within reach of are worked out again; everywhere else
        /// the field is `rest`'s, which is what working it out again gave (the same neighbours, the same numbers, the same order).
        /// 2026-11-15 (work/perf-1115): a blink moves the eyelids, and all 52,000 body vertices were smoothed three times over
        /// through a dictionary, 0.7–1.0 s of every hero's first build.
        static FieldData Field(Vector3[] p,int[] t,int[] alias,int count,FieldData rest)
        {
            var g=new Vector3[count];var q=new Vector3[count];var seen=new bool[count];
            for(int i=0;i<p.Length;i++) if(!seen[alias[i]]) {q[alias[i]]=p[i];seen[alias[i]]=true;}
            for(int f=0;f<t.Length;f+=3) {
                int a=t[f],b=t[f+1],c=t[f+2];var n=Vector3.Cross(p[b]-p[a],p[c]-p[a]);
                g[alias[a]]+=n;g[alias[b]]+=n;g[alias[c]]+=n;
            }
            const float r=R;
            for(int i=0;i<count;i++) g[i]=g[i].normalized;
            var grid=new CellGrid(q,count,r);
            bool[] todo=null;
            if(rest!=null) {
                todo=new bool[count];
                for(int j=0;j<count;j++) {
                    if(Same(q[j],rest.q[j]) && Same(g[j],rest.g[j])) continue;
                    // (its neighbours in either pose: an unposed neighbour sits in the same cell of both grids)
                    todo[j]=true;Mark(rest.grid,rest.q[j],todo);Mark(rest.grid,q[j],todo);
                }
            }
            var field=new Vector3[count];
            for(int i=0;i<count;i++) {
                if(todo!=null && !todo[i]) {field[i]=rest.field[i];continue;}
                var sum=g[i];int cx=CellGrid.Coord(q[i].x,r),cy=CellGrid.Coord(q[i].y,r),cz=CellGrid.Coord(q[i].z,r);
                for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)for(int z=-1;z<=1;z++)
                    if(grid.Find(cx+x,cy+y,cz+z,out int s,out int e))for(int k=s;k<e;k++) {
                        int j=grid.Items[k];
                        float d=(q[i]-q[j]).sqrMagnitude;if(d>=r*r)continue;float agreement=Vector3.Dot(g[i],g[j]);if(agreement<.5f)continue;
                        float w=1-d/(r*r);sum+=g[j]*(w*w*agreement*agreement);
                    }
                field[i]=sum.normalized;
            }
            return new FieldData{q=q,g=g,field=field,grid=grid};
        }
    }
}
