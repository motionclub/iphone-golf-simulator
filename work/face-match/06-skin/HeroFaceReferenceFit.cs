using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Local, continuous head correction. Body, neck base, weights, bindposes,
    /// topology and animation sources are retained. Blink endpoints follow the
    /// same mapping as the resting face, so the lid remains attached.
    public static class HeroFaceReferenceFit
    {
        const int AcceptedStage = 5;
        static readonly Dictionary<Mesh, Mesh> cache = new();
        public static Mesh Prepare(SkinnedMeshRenderer source, SkinnedMeshRenderer body, SkinnedMeshRenderer features, string headName, bool female)
        {
            if (!source || !body || !features || !source.sharedMesh.isReadable) return source ? source.sharedMesh : null;
            var mesh = source.sharedMesh;
            if (cache.TryGetValue(mesh, out var ready) && ready) return ready;
            int hi = Array.FindIndex(body.bones, b => b && b.name == headName);
            int fi = Array.FindIndex(features.bones, b => b && b.name == headName);
            int si = Array.FindIndex(source.bones, b => b && b.name == headName);
            if (hi < 0 || fi < 0 || si < 0) return mesh;
            var rest = body.sharedMesh.bindposes[hi].inverse;
            var featureMap = rest * features.sharedMesh.bindposes[fi];
            var sourceMap = rest * mesh.bindposes[si];
            var fv = features.sharedMesh.vertices; var fn = features.sharedMesh.normals;
            var indices = new List<int>();
            for (int s = 0; s < features.sharedMaterials.Length; s++)
                if (features.sharedMaterials[s].name.Contains("Sclera")) indices.AddRange(features.sharedMesh.GetTriangles(s));
            if (indices.Count == 0) return mesh;
            Vector3 up = rest.MultiplyVector(Vector3.up).normalized;
            Vector3 forward = featureMap.inverse.transpose.MultiplyVector(indices.Aggregate(Vector3.zero, (sum, i) => sum + fn[i]));
            forward = (forward - up * Vector3.Dot(forward, up)).normalized;
            Vector3 right = Vector3.Cross(up, forward).normalized; up = Vector3.Cross(forward, right).normalized;
            Vector3 eye = featureMap.MultiplyPoint3x4(indices.Aggregate(Vector3.zero, (sum, i) => sum + fv[i]) / indices.Count);
            Vector3 ToFace(Vector3 p) { var d = sourceMap.MultiplyPoint3x4(p) - eye; return new Vector3(Vector3.Dot(d, right), Vector3.Dot(d, up), Vector3.Dot(d, forward)); }
            Vector3 FromFace(Vector3 p) => sourceMap.inverse.MultiplyPoint3x4(eye + right * p.x + up * p.y + forward * p.z);
            float Smooth(float a, float b, float x) => Mathf.SmoothStep(0, 1, Mathf.Clamp01((x - a) / (b - a)));
            var browVertices = new HashSet<int>();
            if (source == features) for (int sub = 0; sub < features.sharedMaterials.Length; sub++)
                if (features.sharedMaterials[sub].name.Contains("Brow")) foreach (int i in mesh.GetTriangles(sub)) browVertices.Add(i);
            Vector3 Warp(Vector3 original, int vertex)
            {
                var p = ToFace(original);
                float head = Smooth(-.17f, -.12f, p.y) * (1 - Smooth(.16f, .20f, Mathf.Abs(p.x)));
                if (head < .00001f) return original;
                float front = Smooth(-.075f, -.045f, p.z);
                float orbit = Smooth(-.055f, -.024f, p.y) * (1 - Smooth(.045f, .080f, p.y)) * (1 - Smooth(.070f, .105f, Mathf.Abs(p.x))) * front;
                float eyeRegion = (1 - Smooth(.016f, .032f, Mathf.Abs(p.y))) * (1 - Smooth(.060f, .085f, Mathf.Abs(p.x))) * front;
                float eyeCenter = female ? .0453f : .0367f;
                float side = p.x / Mathf.Sqrt(p.x * p.x + .0001f);
                if (!female && !browVertices.Contains(vertex)) {
                    p.y += p.y * .32f * eyeRegion;
                    float irisRegion = Mathf.Exp(-Mathf.Pow((Mathf.Abs(p.x) - eyeCenter) / .013f, 4)) * eyeRegion;
                    p.x += (p.x - side * eyeCenter) * .20f * irisRegion;
                }
                float orbitalSides = Smooth(.003f, .010f, Mathf.Abs(p.x));
                p.x -= side * (female ? .0028f : .0035f) * orbit * orbitalSides;
                p.y -= .010f * orbit * orbitalSides;
                if (browVertices.Contains(vertex) && female) p.y = .0249f + (p.y - .0249f) * .88f;
                float mouth = Mathf.Exp(-Mathf.Pow((p.y + .079f) / .022f, 4)) * (1 - Smooth(.045f, .075f, Mathf.Abs(p.x))) * front;
                if (!female) p.x *= 1 + .16f * mouth;
                // Male plate has a fuller cranium and mandible. Fade completely
                // above the neck base; no body or skeletal scaling.
                if (!female) p.x *= 1 + .085f * head;
                return FromFace(p);
            }
            var before = mesh.vertices; var after = new Vector3[before.Length]; var normals = mesh.normals;
            var adjusted = (Vector3[])normals.Clone(); int changed = 0;
            const float epsilon = .0001f;
            for (int i = 0; i < before.Length; i++) {
                after[i] = Warp(before[i], i);
                if ((after[i] - before[i]).sqrMagnitude < 1e-14f) { after[i] = before[i]; continue; }
                changed++;
                var jacobian = Matrix4x4.identity;
                jacobian.SetColumn(0, (Warp(before[i] + Vector3.right * epsilon, i) - after[i]) / epsilon);
                jacobian.SetColumn(1, (Warp(before[i] + Vector3.up * epsilon, i) - after[i]) / epsilon);
                jacobian.SetColumn(2, (Warp(before[i] + Vector3.forward * epsilon, i) - after[i]) / epsilon);
                adjusted[i] = jacobian.inverse.transpose.MultiplyVector(normals[i]).normalized;
            }
            ready = UnityEngine.Object.Instantiate(mesh); ready.name = mesh.name + " (reference face fit)"; ready.hideFlags = HideFlags.DontSave;
            ready.vertices = after; ready.normals = adjusted; ready.ClearBlendShapes();
            for (int shape = 0; shape < mesh.blendShapeCount; shape++) for (int frame = 0; frame < mesh.GetBlendShapeFrameCount(shape); frame++) {
                var dp = new Vector3[before.Length]; var dn = new Vector3[before.Length]; var dt = new Vector3[before.Length];
                mesh.GetBlendShapeFrameVertices(shape, frame, dp, dn, dt);
                for (int i = 0; i < dp.Length; i++) if (dp[i].sqrMagnitude > 1e-14f) dp[i] = Warp(before[i] + dp[i], i) - after[i];
                ready.AddBlendShapeFrame(mesh.GetBlendShapeName(shape), mesh.GetBlendShapeFrameWeight(shape, frame), dp, dn, dt);
            }
            ready.RecalculateBounds(); cache[mesh] = ready;
            Debug.Log($"[HeroFaceReferenceFit] {(female ? "female" : "male")} stage={AcceptedStage} {source.name}: moved={changed}; weights/binds/triangles retained");
            return ready;
        }
    }
}
