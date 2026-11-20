using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

namespace GolfArcade.Tennis
{
    // Preview garment patterns are triangle anchors on the outer shell. Build after
    // the normal fit so the trim follows the dressed mesh, including its correctives.
    internal static class GarmentConstruction
    {
        [Serializable] internal class Anchor
        {
            public int a, b, c;
            public float u, v;

            public Vector3 Sample(Vector3[] data) => data[a] * (1 - u - v) + data[b] * u + data[c] * v;
            public Vector4 Sample(Vector4[] data) => data[a] * (1 - u - v) + data[b] * u + data[c] * v;
        }

        [Serializable] internal class Rail
        {
            public string name;
            public float width, rise;
            public int style;
            public bool closed;
            public Anchor[] anchors;
        }

        [Serializable] internal class Pattern
        {
            public int vertices, cut;
            public Rail[] rails;
            public Panel panel;
        }

        [Serializable] internal class PanelVertex
        {
            public Anchor anchor;
            public Vector3 offset, normal, tangent;
            public Vector4 cloth;
        }

        [Serializable] internal class Panel
        {
            public PanelVertex[] points;
            public int[] triangles, covered;
        }

        static readonly float[] Section = { -1f, -.64f, 0, .64f, 1f };
        static readonly float[] Rise = { -.24f, .64f, 1f, .64f, -.24f };

        public static void Apply(MatchHeroLook look, List<Object> owned)
        {
            if (!look.kitV2 || look.kit == null) return;
            string sex = look.female ? "Female" : "Male";
            string sport = look.KitSportFolder;
            var only = Environment.GetEnvironmentVariable("CONSTRUCTION_HERO");
            if (!string.IsNullOrEmpty(only) && only != sport + "_" + sex) return;
            foreach (var renderer in look.kit)
            {
                if (!renderer || (renderer.name != "Kit_Top" && renderer.name != "Kit_Bottom")) continue;
                if (sport == "Tennis" && sex == "Male" && renderer.name == "Kit_Top" && PoloCloth.Enabled) continue;   // live polo owns this top
                var asset = Resources.Load<TextAsset>($"GarmentConstruction/{sport}_{sex}_{renderer.name}");
                if (!asset) continue;
                var pattern = JsonUtility.FromJson<Pattern>(asset.text);
                var source = renderer.sharedMesh;
                if (!source || source.vertexCount != pattern.vertices)
                {
                    Debug.LogWarning($"[GarmentConstruction] {asset.name} expected {pattern.vertices} fitted vertices.");
                    continue;
                }
                var currentWeights = new float[source.blendShapeCount];
                for (int i = 0; i < currentWeights.Length; i++) currentWeights[i] = renderer.GetBlendShapeWeight(i);
                var dressed = Append(source, pattern);
                renderer.sharedMesh = dressed;
                for (int i = 0; i < currentWeights.Length; i++) renderer.SetBlendShapeWeight(i, currentWeights[i]);
                owned.Add(dressed);
                int panelTriangles = pattern.panel?.triangles?.Length / 3 ?? 0;
                Debug.Log($"[GarmentConstruction] {asset.name}: {pattern.rails.Length} sewn paths, {panelTriangles} panel triangles, +{dressed.vertexCount - source.vertexCount} vertices");
            }
        }

        static Mesh Append(Mesh source, Pattern pattern)
        {
            int count = source.vertexCount;
            var originalPositions = source.vertices;
            var originalNormals = source.normals;
            ShapeCut(originalPositions, pattern.cut);
            var weights = source.boneWeights;
            var bindPoses = source.bindposes;
            var positions = originalPositions.ToList();
            var normals = originalNormals.ToList();
            var tangents = source.tangents.ToList();
            var bones = weights.ToList();
            var attachments = new List<Anchor>();
            var extra = new List<Vector4>();
            var originalTriangles = source.GetTriangles(0);
            var triangles = new List<int>(originalTriangles.Length);
            var replaced = new HashSet<int>(pattern.panel?.covered ?? Array.Empty<int>());
            if (replaced.Count > 0 && source.subMeshCount != 1)
                throw new InvalidOperationException($"Expected one cloth submesh for the replacement panel on {source.name}.");
            for (int i = 0; i < originalTriangles.Length; i += 3)
            {
                int a = originalTriangles[i], b = originalTriangles[i + 1], c = originalTriangles[i + 2];
                if (replaced.Contains(a) && replaced.Contains(b) && replaced.Contains(c)) continue;
                triangles.Add(a); triangles.Add(b); triangles.Add(c);
            }

            if (pattern.panel?.points is { Length: > 0 })
            {
                int start = positions.Count;
                foreach (var point in pattern.panel.points)
                {
                    positions.Add(point.anchor.Sample(originalPositions) + point.offset);
                    normals.Add(point.normal);
                    tangents.Add(new Vector4(point.tangent.x, point.tangent.y, point.tangent.z, 1));
                    bones.Add(BlendWeights(point.anchor, weights));
                    attachments.Add(point.anchor);
                    extra.Add(point.cloth);
                }
                triangles.AddRange(pattern.panel.triangles.Select(index => index + start));
            }

            foreach (var rail in pattern.rails)
                AddRail(rail, originalPositions, originalNormals, weights, positions, normals, tangents, bones, attachments, extra, triangles);

            var mesh = Object.Instantiate(source);
            mesh.name = source.name + " (sewn construction)";
            mesh.hideFlags = HideFlags.DontSave;
            mesh.ClearBlendShapes();
            // Original vertices remain first. UVs, skinning and corrective frames
            // are extended from the same triangle anchors as the seam positions.
            mesh.SetVertices(positions);
            mesh.SetNormals(normals);
            mesh.SetTangents(tangents);
            if (mesh.vertexCount > ushort.MaxValue) mesh.indexFormat = IndexFormat.UInt32;
            mesh.subMeshCount = source.subMeshCount;
            mesh.SetTriangles(triangles, 0, false);
            for (int sub = 1; sub < source.subMeshCount; sub++) mesh.SetTriangles(source.GetTriangles(sub), sub, false);
            mesh.boneWeights = bones.ToArray();
            mesh.bindposes = bindPoses;
            for (int channel = 0; channel < 8; channel++)
            {
                var original = new List<Vector4>();
                source.GetUVs(channel, original);
                if (channel == 4)
                {
                    if (original.Count != 0) throw new InvalidOperationException($"Construction UV channel already used by {source.name}.");
                    var data = new List<Vector4>(new Vector4[count]);
                    data.AddRange(extra);
                    mesh.SetUVs(channel, data);
                }
                else if (original.Count == count)
                {
                    var originalUV = original.ToArray();
                    var data = original.Concat(attachments.Select(a => a.Sample(originalUV))).ToList();
                    var attr = (VertexAttribute)((int)VertexAttribute.TexCoord0 + channel);
                    switch (source.GetVertexAttributeDimension(attr))
                    {
                        case 2: mesh.SetUVs(channel, data.Select(v => new Vector2(v.x, v.y)).ToList()); break;
                        case 3: mesh.SetUVs(channel, data.Select(v => new Vector3(v.x, v.y, v.z)).ToList()); break;
                        default: mesh.SetUVs(channel, data); break;
                    }
                }
            }
            var colors = source.colors;
            if (colors.Length == count)
                mesh.colors = colors.Concat(attachments.Select(a => colors[a.a] * (1 - a.u - a.v) + colors[a.b] * a.u + colors[a.c] * a.v)).ToArray();
            CopyShapes(source, mesh, attachments);
            var bounds = source.bounds;
            bounds.Expand(.025f);
            mesh.bounds = bounds;
            return mesh;
        }

        static void ShapeCut(Vector3[] positions, int cut)
        {
            if (cut == 0) return;
            for (int i = 0; i < positions.Length; i++)
            {
                var p = positions[i];
                if (cut == 1)
                {
                    // A raised, nearly level polo hem with a little relief over
                    // the outseam. Fade all motion back into the body of the shirt.
                    float side = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.077f, .163f, Mathf.Abs(p.x)));
                    float lower = 1 - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.875f, .976f, p.z));
                    p.z += (.013f + .013f * side) * lower;
                    float collar = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(1.390f, 1.454f, p.z))
                                 * (1 - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.070f, .120f, Mathf.Abs(p.x))));
                    p.z -= .0045f * collar;
                }
                else
                {
                    // Carry the shorts waistband behind both sides of the raised polo hem.
                    p.z += .012f * Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.851f, .893f, p.z));
                }
                positions[i] = p;
            }
        }

        static void AddRail(Rail rail, Vector3[] source, Vector3[] sourceNormals, BoneWeight[] sourceWeights,
            List<Vector3> positions, List<Vector3> normals, List<Vector4> tangents, List<BoneWeight> bones,
            List<Anchor> attachments, List<Vector4> control, List<int> tris)
        {
            var points = rail.anchors.Select(a => a.Sample(source)).ToArray();
            int count = points.Length;
            int start = positions.Count;
            int width = Section.Length;
            int rings = rail.closed ? count + 1 : count;
            float distance = 0;
            for (int i = 0; i < rings; i++)
            {
                int at = i % count;
                int before = rail.closed ? (at + count - 1) % count : Mathf.Max(0, at - 1);
                int after = rail.closed ? (at + 1) % count : Mathf.Min(count - 1, at + 1);
                var anchor = rail.anchors[at];
                var normal = anchor.Sample(sourceNormals).normalized;
                var travel = Vector3.ProjectOnPlane(points[after] - points[before], normal).normalized;
                if (travel.sqrMagnitude < .5f) travel = Vector3.Cross(normal, Vector3.up).normalized;
                var across = Vector3.Cross(normal, travel);
                var weight = BlendWeights(anchor, sourceWeights);
                if (i > 0) distance += Vector3.Distance(points[(i - 1) % count], points[at]);
                float taper = rail.closed ? 1f : Mathf.Lerp(.26f, 1f, Mathf.Min(1f, Mathf.Min(i, rings - i - 1) / 3f));
                for (int j = 0; j < Section.Length; j++)
                {
                    float x = Section[j];
                    var position = points[at] + across * (x * rail.width * .5f * taper) + normal * (Rise[j] * rail.rise * taper);
                    var lit = (normal + across * (x * Mathf.Min(.54f, rail.rise * 2 / rail.width))).normalized;
                    positions.Add(position);
                    normals.Add(lit);
                    tangents.Add(new Vector4(travel.x, travel.y, travel.z, 1));
                    bones.Add(weight);
                    attachments.Add(anchor);
                    control.Add(new Vector4(distance, x, rail.style, taper));
                }
                if (i == 0) continue;
                int row = start + (i - 1) * width;
                for (int j = 0; j < width - 1; j++)
                {
                    int a = row + j, b = a + width;
                    tris.Add(a); tris.Add(b); tris.Add(b + 1);
                    tris.Add(a); tris.Add(b + 1); tris.Add(a + 1);
                }
            }
        }

        static BoneWeight BlendWeights(Anchor anchor, BoneWeight[] original)
        {
            var combined = new Dictionary<int, float>(12);
            Accumulate(combined, original[anchor.a], 1 - anchor.u - anchor.v);
            Accumulate(combined, original[anchor.b], anchor.u);
            Accumulate(combined, original[anchor.c], anchor.v);
            var top = combined.OrderByDescending(it => it.Value).ThenBy(it => it.Key).Take(4).ToArray();
            float sum = top.Sum(it => it.Value);
            var index = new int[4];
            var weight = new float[4];
            for (int n = 0; n < top.Length; n++) { index[n] = top[n].Key; weight[n] = top[n].Value / sum; }
            return new BoneWeight { boneIndex0 = index[0], boneIndex1 = index[1], boneIndex2 = index[2], boneIndex3 = index[3],
                weight0 = weight[0], weight1 = weight[1], weight2 = weight[2], weight3 = weight[3] };
        }

        static void Accumulate(Dictionary<int, float> combined, BoneWeight value, float blend)
        {
            AddWeight(combined, value.boneIndex0, value.weight0 * blend);
            AddWeight(combined, value.boneIndex1, value.weight1 * blend);
            AddWeight(combined, value.boneIndex2, value.weight2 * blend);
            AddWeight(combined, value.boneIndex3, value.weight3 * blend);
        }

        static void AddWeight(Dictionary<int, float> combined, int index, float weight)
        {
            if (weight <= 0) return;
            combined.TryGetValue(index, out float total);
            combined[index] = total + weight;
        }

        static void CopyShapes(Mesh source, Mesh target, List<Anchor> attachments)
        {
            int n = source.vertexCount;
            var displacement = new Vector3[target.vertexCount];
            var normals = new Vector3[target.vertexCount];
            var tangents = new Vector3[target.vertexCount];
            var oldD = new Vector3[n];
            var oldN = new Vector3[n];
            var oldT = new Vector3[n];
            for (int shape = 0; shape < source.blendShapeCount; shape++)
            for (int frame = 0; frame < source.GetBlendShapeFrameCount(shape); frame++)
            {
                source.GetBlendShapeFrameVertices(shape, frame, oldD, oldN, oldT);
                Array.Copy(oldD, displacement, n);
                Array.Copy(oldN, normals, n);
                Array.Copy(oldT, tangents, n);
                for (int i = 0; i < attachments.Count; i++)
                {
                    var anchor = attachments[i];
                    int at = n + i;
                    displacement[at] = anchor.Sample(oldD);
                    normals[at] = anchor.Sample(oldN) * .6f;
                    tangents[at] = anchor.Sample(oldT) * .6f;
                }
                target.AddBlendShapeFrame(source.GetBlendShapeName(shape), source.GetBlendShapeFrameWeight(shape, frame), displacement, normals, tangents);
            }
        }
    }
}
