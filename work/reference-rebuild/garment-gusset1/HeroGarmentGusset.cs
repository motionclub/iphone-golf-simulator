using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Tennis
{
    // Opt-in source candidate. Invoke after IK and after the sleeve shape weights
    // are set: HeroGarmentGusset.Apply(look.female, look.transform, top).
    // Each renderer owns its deforming mesh. Full and LOD have separate profiles.
    internal static class HeroGarmentGusset
    {
        [Serializable] sealed class Profile
        {
            public int sourceVertexCount, vertexCount;
            public string[] bones;
            public float[] sourceVertices, sourceNormals, sourceWeights, weights;
            public int[] sourceTriangles, sourceIndices, boneIndices, triangles;
            public int[] freeVertices, aliases, contactTriangles;
            public int[] proxyBoneIndices, proxyTriangles;
            public float[] proxyBoneLocalPositions, proxyWeights, proxyRestPositions;
            public float clearance = .003f, maximumDisplacement = .04f;
            public float rayMinimum = -.012f, rayMaximum = .05f, contactStep = .008f;
            public int contactIterations = 6;
        }
        sealed class Shape
        {
            public float[] frameWeights;
            public Vector3[][] deltas;
        }
        static readonly bool Enabled = Environment.GetEnvironmentVariable("VISUAL_UNDERARM_GUSSET") == "1";
        static readonly Dictionary<int, Profile> profiles = new();
        static readonly Dictionary<SkinnedMeshRenderer, State> states = new();

        static Profile Load(int count)
        {
            if (profiles.TryGetValue(count, out var p)) return p;
            string detail = count == 13932 ? "Full" : count == 11533 ? "LOD" : null;
            if (detail == null) throw new InvalidOperationException("Unverified gusset source vertex count: " + count);
            var asset = Resources.Load<TextAsset>("Tennis/Correctives/UnderarmGusset_Female_" + detail);
            if (!asset) throw new InvalidOperationException("Missing gusset " + detail + " profile; capture must stop");
            p = JsonUtility.FromJson<Profile>(asset.text);
            if (p == null || p.sourceVertexCount != count || p.vertexCount <= count)
                throw new InvalidOperationException("Invalid gusset profile");
            profiles[count] = p;
            return p;
        }

        public static void Apply(bool female, Transform heroRoot, SkinnedMeshRenderer renderer)
        {
            if (!Enabled || !female || !renderer || !renderer.sharedMesh) return;
            if (!states.TryGetValue(renderer, out var state) || state.mesh != renderer.sharedMesh)
            {
                if (state != null) UnityEngine.Object.Destroy(state.mesh);
                state = new State(renderer, Load(renderer.sharedMesh.vertexCount));
                states[renderer] = state;
            }
            state.Apply(heroRoot, renderer);
        }

        sealed class State
        {
            public readonly Mesh mesh;
            readonly Profile p;
            readonly Vector3[] basis, normalBasis, shaped, posed, raw, geom, originalGeom;
            readonly Vector3[] delta, updates, output, outputNormals, aliasSums, proxy;
            readonly bool[] free;
            readonly int[] aliasCounts;
            readonly float[] counts;
            readonly Matrix4x4[] skinMatrices, boneToRoot, bindposes;
            readonly Transform[] bones;
            readonly BoneWeight[] bindings;
            readonly Shape[] shapes;
            readonly SmallBvh bvh;
            readonly Bounds bounds;

            Vector3 Interpolate(Vector3[] values, int i)
            {
                int q = i * 3;
                return values[p.sourceIndices[q]] * p.sourceWeights[q]
                    + values[p.sourceIndices[q+1]] * p.sourceWeights[q+1]
                    + values[p.sourceIndices[q+2]] * p.sourceWeights[q+2];
            }

            public State(SkinnedMeshRenderer r, Profile profile)
            {
                p = profile; bones = r.bones;
                var source = r.sharedMesh;
                if (!source.isReadable || source.subMeshCount != 1)
                    throw new InvalidOperationException("Gusset requires the verified readable single-material Top");
                var positions = source.vertices;
                var sourceNormals = source.normals;
                var sourceTriangles = source.triangles;
                if (p.sourceVertices.Length != positions.Length * 3 || p.sourceTriangles.Length != sourceTriangles.Length)
                    throw new InvalidOperationException("Gusset source geometry mismatch");
                for (int i = 0; i < positions.Length; i++)
                    if ((positions[i] - Read(p.sourceVertices, i)).sqrMagnitude > 2.5e-9f)
                        throw new InvalidOperationException("Gusset source basis moved at " + i);
                for (int i = 0; i < sourceTriangles.Length; i++)
                    if (sourceTriangles[i] != p.sourceTriangles[i])
                        throw new InvalidOperationException("Gusset source topology changed at " + i);
                if (bones.Length != p.bones.Length)
                    throw new InvalidOperationException("Gusset bone count mismatch");
                for (int i = 0; i < p.bones.Length; i++)
                    if (!bones[i] || bones[i].name != p.bones[i])
                        throw new InvalidOperationException("Gusset bone order mismatch at " + i);
                int n = p.vertexCount;
                basis = new Vector3[n]; normalBasis = new Vector3[n]; bindings = new BoneWeight[n];
                for (int i = 0; i < n; i++)
                {
                    basis[i] = Interpolate(positions, i);
                    normalBasis[i] = Interpolate(sourceNormals, i).normalized;
                    int j = i * 4;
                    bindings[i] = new BoneWeight {
                        boneIndex0=p.boneIndices[j], boneIndex1=p.boneIndices[j+1],
                        boneIndex2=p.boneIndices[j+2], boneIndex3=p.boneIndices[j+3],
                        weight0=p.weights[j], weight1=p.weights[j+1], weight2=p.weights[j+2], weight3=p.weights[j+3]
                    };
                }
                mesh = new Mesh { name=source.name+" (underarm gusset)", hideFlags=HideFlags.DontSave,
                    indexFormat=n>65535?IndexFormat.UInt32:IndexFormat.UInt16 };
                mesh.MarkDynamic(); mesh.vertices=basis; mesh.normals=normalBasis;
                var uvs = new List<Vector4>();
                for (int channel = 0; channel < 8; channel++)
                {
                    uvs.Clear(); source.GetUVs(channel, uvs); if (uvs.Count != positions.Length) continue;
                    var mapped = new List<Vector4>(n);
                    for (int i = 0; i < n; i++) { int q=i*3; mapped.Add(uvs[p.sourceIndices[q]]*p.sourceWeights[q]+uvs[p.sourceIndices[q+1]]*p.sourceWeights[q+1]+uvs[p.sourceIndices[q+2]]*p.sourceWeights[q+2]); }
                    mesh.SetUVs(channel, mapped);
                }
                var tangents=source.tangents;
                if (tangents.Length==positions.Length)
                {
                    var result=new Vector4[n];
                    for (int i=0;i<n;i++) {int q=i*3;result[i]=tangents[p.sourceIndices[q]]*p.sourceWeights[q]+tangents[p.sourceIndices[q+1]]*p.sourceWeights[q+1]+tangents[p.sourceIndices[q+2]]*p.sourceWeights[q+2];}
                    mesh.tangents=result;
                }
                var colors=source.colors;
                if (colors.Length==positions.Length)
                {
                    var result=new Color[n];
                    for(int i=0;i<n;i++){int q=i*3;result[i]=colors[p.sourceIndices[q]]*p.sourceWeights[q]+colors[p.sourceIndices[q+1]]*p.sourceWeights[q+1]+colors[p.sourceIndices[q+2]]*p.sourceWeights[q+2];}
                    mesh.colors=result;
                }
                bindposes=source.bindposes; mesh.bindposes=bindposes; mesh.boneWeights=bindings; mesh.triangles=p.triangles;
                shapes=new Shape[source.blendShapeCount]; var savedWeights=new float[shapes.Length];
                var dv=new Vector3[positions.Length];var dn=new Vector3[positions.Length];var dt=new Vector3[positions.Length];
                for(int s=0;s<shapes.Length;s++)
                {
                    savedWeights[s]=r.GetBlendShapeWeight(s);int frames=source.GetBlendShapeFrameCount(s);
                    var shape=new Shape{frameWeights=new float[frames],deltas=new Vector3[frames][]};shapes[s]=shape;
                    for(int f=0;f<frames;f++)
                    {
                        source.GetBlendShapeFrameVertices(s,f,dv,dn,dt);
                        var vd=new Vector3[n];var nd=new Vector3[n];var td=new Vector3[n];
                        for(int i=0;i<n;i++){vd[i]=Interpolate(dv,i);nd[i]=Interpolate(dn,i);td[i]=Interpolate(dt,i);}
                        shape.frameWeights[f]=source.GetBlendShapeFrameWeight(s,f);shape.deltas[f]=vd;
                        mesh.AddBlendShapeFrame(source.GetBlendShapeName(s),shape.frameWeights[f],vd,nd,td);
                    }
                }
                bounds=source.bounds;bounds.Expand(.20f);mesh.bounds=bounds;
                r.sharedMesh=mesh;for(int s=0;s<savedWeights.Length;s++)r.SetBlendShapeWeight(s,savedWeights[s]);
                shaped=new Vector3[n];posed=new Vector3[n];raw=new Vector3[n];geom=new Vector3[n];originalGeom=new Vector3[n];
                delta=new Vector3[n];updates=new Vector3[n];output=new Vector3[n];outputNormals=new Vector3[n];counts=new float[n];free=new bool[n];
                foreach(int i in p.freeVertices)free[i]=true;
                int aliases=0;foreach(int i in p.aliases)aliases=Math.Max(aliases,i+1);
                aliasSums=new Vector3[aliases];aliasCounts=new int[aliases];foreach(int i in p.aliases)aliasCounts[i]++;
                skinMatrices=new Matrix4x4[bones.Length];boneToRoot=new Matrix4x4[bones.Length];
                proxy=new Vector3[p.proxyWeights.Length/4];for(int i=0;i<proxy.Length;i++)proxy[i]=Read(p.proxyRestPositions,i);bvh=new SmallBvh(proxy,p.proxyTriangles,p.rayMinimum,p.rayMaximum);
                Debug.Log($"[HeroGarmentGusset] verified source {positions.Length}, result {n} vertices / {p.triangles.Length/3} triangles, proxy {proxy.Length} vertices / {p.proxyTriangles.Length/3} triangles");
            }

            void GeometricNormals(Vector3[] vertices, Vector3[] normals)
            {
                Array.Clear(normals,0,normals.Length);
                for(int f=0;f<p.triangles.Length;f+=3)
                {int a=p.triangles[f],b=p.triangles[f+1],c=p.triangles[f+2];var area=Vector3.Cross(vertices[b]-vertices[a],vertices[c]-vertices[a]);normals[a]+=area;normals[b]+=area;normals[c]+=area;}
                for(int i=0;i<normals.Length;i++)normals[i]=Normalize(normals[i]);
            }
            void Synchronize()
            {
                Array.Clear(aliasSums,0,aliasSums.Length);
                for(int i=0;i<delta.Length;i++)aliasSums[p.aliases[i]]+=delta[i];
                for(int i=0;i<delta.Length;i++){delta[i]=free[i]?aliasSums[p.aliases[i]]/aliasCounts[p.aliases[i]]:Vector3.zero;posed[i]=raw[i]+delta[i];}
            }
            void AddShape(Shape s,float w)
            {
                if(Mathf.Abs(w)<1e-7f||s.deltas.Length==0)return;
                int upper=0;while(upper<s.frameWeights.Length-1&&w>s.frameWeights[upper])upper++;
                int lower=upper-1;float low=lower<0?0:s.frameWeights[lower];
                float t=(w-low)/(s.frameWeights[upper]-low);
                var a=lower<0?null:s.deltas[lower];var b=s.deltas[upper];
                for(int i=0;i<shaped.Length;i++)shaped[i]+=a==null?b[i]*t:a[i]*(1-t)+b[i]*t;
            }
            public void Apply(Transform root,SkinnedMeshRenderer r)
            {
                var rootInverse=root.worldToLocalMatrix;var bind=bindposes;
                for(int b=0;b<skinMatrices.Length;b++){boneToRoot[b]=rootInverse*bones[b].localToWorldMatrix;skinMatrices[b]=boneToRoot[b]*bind[b];}
                Array.Copy(basis,shaped,basis.Length);
                for(int s=0;s<shapes.Length;s++)AddShape(shapes[s],r.GetBlendShapeWeight(s));
                for(int i=0;i<shaped.Length;i++)
                {
                    var w=bindings[i];var v=shaped[i];raw[i]=skinMatrices[w.boneIndex0].MultiplyPoint3x4(v)*w.weight0+skinMatrices[w.boneIndex1].MultiplyPoint3x4(v)*w.weight1+skinMatrices[w.boneIndex2].MultiplyPoint3x4(v)*w.weight2+skinMatrices[w.boneIndex3].MultiplyPoint3x4(v)*w.weight3;posed[i]=raw[i];
                }
                for(int i=0;i<proxy.Length;i++)
                {
                    Vector3 q=Vector3.zero;
                    for(int j=0;j<4;j++){int k=i*4+j;q+=boneToRoot[p.proxyBoneIndices[k]].MultiplyPoint3x4(Read(p.proxyBoneLocalPositions,k))*p.proxyWeights[k];}
                    proxy[i]=q;
                }
                bvh.Refit();GeometricNormals(raw,geom);Array.Copy(geom,originalGeom,geom.Length);Array.Clear(delta,0,delta.Length);
                foreach(int i in p.freeVertices)
                {float distance=bvh.Exit(raw[i],geom[i]);if(!float.IsPositiveInfinity(distance))delta[i]=geom[i]*Mathf.Clamp(distance+p.clearance,0,p.maximumDisplacement);}
                Synchronize();
                for(int iteration=0;iteration<p.contactIterations;iteration++)
                {
                    Array.Clear(updates,0,updates.Length);Array.Clear(counts,0,counts.Length);
                    for(int f=0;f<p.contactTriangles.Length;f+=3)
                    {
                        int a=p.contactTriangles[f],b=p.contactTriangles[f+1],c=p.contactTriangles[f+2];
                        var normal=Normalize(Vector3.Cross(posed[b]-posed[a],posed[c]-posed[a]));
                        float distance=bvh.Exit((posed[a]+posed[b]+posed[c])/3,normal);
                        if(float.IsPositiveInfinity(distance))continue;
                        float amount=Mathf.Clamp(distance+p.clearance,0,p.contactStep);if(amount<=0)continue;
                        int movable=(free[a]?1:0)+(free[b]?1:0)+(free[c]?1:0);
                        var push=normal*(amount*3/Math.Max(1,movable));
                        updates[a]+=push;updates[b]+=push;updates[c]+=push;counts[a]++;counts[b]++;counts[c]++;
                    }
                    for(int i=0;i<delta.Length;i++)
                    {var update=free[i]?updates[i]/Mathf.Max(1,counts[i]):Vector3.zero;delta[i]=Vector3.ClampMagnitude(posed[i]+update-raw[i],p.maximumDisplacement);}
                    Synchronize();
                }
                GeometricNormals(posed,geom);
                for(int i=0;i<output.Length;i++)
                {
                    // GPU blendshapes remain active. Write only the inverse-LBS
                    // collision delta into the unshaped mesh input.
                    var normalDelta=geom[i]-originalGeom[i];
                    if(delta[i].sqrMagnitude<1e-20f && normalDelta.sqrMagnitude<1e-20f){output[i]=basis[i];outputNormals[i]=normalBasis[i];continue;}
                    var linear=Blend(skinMatrices,bindings[i]);
                    output[i]=basis[i]+InverseVector(linear,delta[i]);
                    outputNormals[i]=normalBasis[i]+InverseVector(linear,normalDelta);
                }
                mesh.vertices=output;mesh.normals=outputNormals;mesh.bounds=bounds;
            }
        }
        static Vector3 Read(float[] data,int i)=>new Vector3(data[i*3],data[i*3+1],data[i*3+2]);
        static Vector3 Normalize(Vector3 v){float n=v.magnitude;return n>1e-12f?v/n:Vector3.zero;}
        static Vector3 InverseVector(Matrix4x4 m,Vector3 v)
        {
            var a=new Vector3(m.m00,m.m10,m.m20);var b=new Vector3(m.m01,m.m11,m.m21);var c=new Vector3(m.m02,m.m12,m.m22);
            var x=Vector3.Cross(b,c);var y=Vector3.Cross(c,a);var z=Vector3.Cross(a,b);float determinant=Vector3.Dot(a,x);
            if(Mathf.Abs(determinant)<1e-8f)throw new InvalidOperationException("Singular gusset skin transform; capture must stop");
            return new Vector3(Vector3.Dot(v,x),Vector3.Dot(v,y),Vector3.Dot(v,z))/determinant;
        }
        static Matrix4x4 Blend(Matrix4x4[] matrices,BoneWeight w)
        {
            var a=matrices[w.boneIndex0];var b=matrices[w.boneIndex1];var c=matrices[w.boneIndex2];var d=matrices[w.boneIndex3];
            var result=new Matrix4x4();for(int i=0;i<16;i++)result[i]=a[i]*w.weight0+b[i]*w.weight1+c[i]*w.weight2+d[i]*w.weight3;return result;
        }

        // Fixed balanced topology, refitted to 104 posed proxy points. No Body
        // BakeMesh, per-frame sorting, managed allocations, or broad-body search.
        sealed class SmallBvh
        {
            struct Node { public int start,count,left,right;public Vector3 min,max; }
            readonly Vector3[] vertices;readonly int[] triangles,order,stack;readonly Node[] nodes;
            readonly float minimum,maximum;int nodeCount;
            public SmallBvh(Vector3[] points,int[] faces,float min,float max)
            {vertices=points;triangles=faces;minimum=min;maximum=max;order=new int[faces.Length/3];for(int i=0;i<order.Length;i++)order[i]=i;nodes=new Node[order.Length*2];stack=new int[64];Build(0,order.Length);}
            int Build(int start,int count)
            {int index=nodeCount++;nodes[index]=new Node{start=start,count=count,left=-1,right=-1};if(count>8){
                Vector3 lo=new Vector3(float.PositiveInfinity,float.PositiveInfinity,float.PositiveInfinity),hi=-lo;
                for(int j=start;j<start+count;j++){var q=Centroid(order[j]);lo=Vector3.Min(lo,q);hi=Vector3.Max(hi,q);}var extent=hi-lo;int axis=extent.x>=extent.y&&extent.x>=extent.z?0:extent.y>=extent.z?1:2;
                Array.Sort(order,start,count,Comparer<int>.Create((a,b)=>Centroid(a)[axis].CompareTo(Centroid(b)[axis])));
                int half=count/2;int l=Build(start,half),r=Build(start+half,count-half);var n=nodes[index];n.left=l;n.right=r;nodes[index]=n;}return index;}
            Vector3 Centroid(int f)=>(vertices[triangles[f*3]]+vertices[triangles[f*3+1]]+vertices[triangles[f*3+2]])/3;
            public void Refit()
            {
                for(int i=nodeCount-1;i>=0;i--)
                {
                    var n=nodes[i];n.min=new Vector3(float.PositiveInfinity,float.PositiveInfinity,float.PositiveInfinity);n.max=-n.min;
                    if(n.left>=0){n.min=Vector3.Min(nodes[n.left].min,nodes[n.right].min);n.max=Vector3.Max(nodes[n.left].max,nodes[n.right].max);}
                    else for(int k=n.start;k<n.start+n.count;k++)for(int j=0;j<3;j++){var v=vertices[triangles[order[k]*3+j]];n.min=Vector3.Min(n.min,v);n.max=Vector3.Max(n.max,v);}
                    nodes[i]=n;
                }
            }
            bool Intersects(Node b,Vector3 p,Vector3 direction)
            {
                float low=minimum,high=maximum;
                for(int k=0;k<3;k++)
                {if(Mathf.Abs(direction[k])<1e-12f){if(p[k]<b.min[k]||p[k]>b.max[k])return false;}
                    else{float a=(b.min[k]-p[k])/direction[k],c=(b.max[k]-p[k])/direction[k];if(a>c){float t=a;a=c;c=t;}low=Mathf.Max(low,a);high=Mathf.Min(high,c);if(low>high)return false;}}
                return true;
            }
            float Triangle(int f,Vector3 p,Vector3 direction)
            {
                var a=vertices[triangles[f*3]];var e1=vertices[triangles[f*3+1]]-a;var e2=vertices[triangles[f*3+2]]-a;
                var h=Vector3.Cross(direction,e2);float determinant=Vector3.Dot(e1,h);
                if(determinant>=-1e-12f)return float.PositiveInfinity;
                var s=p-a;float u=Vector3.Dot(s,h)/determinant;if(u<0||u>1)return float.PositiveInfinity;
                var q=Vector3.Cross(s,e1);float v=Vector3.Dot(direction,q)/determinant;if(v<0||u+v>1)return float.PositiveInfinity;
                return Vector3.Dot(e2,q)/determinant;
            }
            public float Exit(Vector3 p,Vector3 direction)
            {
                float best=float.PositiveInfinity;int count=0;stack[count++]=0;
                while(count>0)
                {
                    var node=nodes[stack[--count]];if(!Intersects(node,p,direction))continue;
                    if(node.left>=0){stack[count++]=node.left;stack[count++]=node.right;}
                    else for(int j=node.start;j<node.start+node.count;j++)
                    {float t=Triangle(order[j],p,direction);if(t>=minimum&&t<=maximum&&Mathf.Abs(t)<Mathf.Abs(best))best=t;}
                }
                return best;
            }
        }
    }
}
