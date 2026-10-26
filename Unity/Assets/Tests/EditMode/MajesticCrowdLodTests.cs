using System.Collections.Generic;
using System.Linq;
using GolfArcade.Majestic;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// MajesticCrowd's lod path (bowling rooms): the decimated fan parts are a subset of the authored _FAR vertices
    /// (same palette roles), keep each part's extent, and cut a fan to under a third of its triangles.
    public class MajesticCrowdLodTests
    {
        static IEnumerable<MeshFilter> FarParts(GameObject prefab, int v)
        {
            var fan = prefab.GetComponentsInChildren<Transform>(true).First(t => t.name == "FAN_" + v);
            return fan.GetComponentsInChildren<MeshFilter>(true).Where(mf => mf.sharedMesh && mf.name.Contains("_FAR"));
        }

        [Test]
        public void EveryFanIsUnderAThirdOfItsTrianglesAndKeepsItsShape()
        {
            var prefab = Resources.Load<GameObject>("Tennis/Premium/TennisSeatedHero3");
            Assert.IsNotNull(prefab);
            for (int v = 0; v < 6; v++)
            {
                long full = 0, lod = 0;
                foreach (var mf in FarParts(prefab, v))
                {
                    var src = mf.sharedMesh; bool head = mf.name.StartsWith("HEAD");
                    var m = mf.name.StartsWith("ARM") ? src : MajesticMeshLod.Decimated(src, head ? MajesticCrowd.LodHeadTris : MajesticCrowd.LodBodyTris);
                    full += MajesticMeshLod.Tris(src); lod += MajesticMeshLod.Tris(m);
                    if (m == src) continue;
                    Assert.LessOrEqual(MajesticMeshLod.Tris(m), (head ? MajesticCrowd.LodHeadTris : MajesticCrowd.LodBodyTris) + 2, mf.name);

                    // every kept vertex is an authored one: same position, normal and palette colour (role in alpha)
                    var authored = new HashSet<(Vector3, Vector3, Color32)>();
                    var sv = src.vertices; var sn = src.normals; var sc = src.colors32;
                    for (int i = 0; i < sv.Length; i++) authored.Add((sv[i], sn[i], sc[i]));
                    var mv = m.vertices; var mn = m.normals; var mc = m.colors32;
                    Assert.AreEqual(mv.Length, mc.Length, mf.name + " colours");
                    for (int i = 0; i < mv.Length; i++) Assert.IsTrue(authored.Contains((mv[i], mn[i], mc[i])), $"{mf.name} vertex {i} is not authored");

                    // same extent within 3 % of the part's size on every axis
                    var b0 = new Bounds(sv[0], Vector3.zero); foreach (var p in sv) b0.Encapsulate(p);
                    var b1 = new Bounds(mv[0], Vector3.zero); foreach (var p in mv) b1.Encapsulate(p);
                    float tol = b0.size.magnitude * .03f;
                    Assert.Less((b0.min - b1.min).magnitude, tol, mf.name + " min");
                    Assert.Less((b0.max - b1.max).magnitude, tol, mf.name + " max");

                    // no degenerate triangles, and every palette role the part had is still there
                    var idx = m.triangles;
                    for (int i = 0; i < idx.Length; i += 3)
                        Assert.Greater(Vector3.Cross(mv[idx[i + 1]] - mv[idx[i]], mv[idx[i + 2]] - mv[idx[i]]).sqrMagnitude, 0f, mf.name + " degenerate");
                    int Role(Color32 c) => c.a >= 204 ? 3 : c.a >= 102 ? 2 : c.a >= 34 ? 1 : 0;
                    var roles0 = sc.Select(Role).ToHashSet(); var roles1 = mc.Select(Role).ToHashSet();
                    Assert.IsTrue(roles0.SetEquals(roles1), $"{mf.name} roles {string.Join(",", roles0)} -> {string.Join(",", roles1)}");
                }
                Debug.Log($"[MajesticCrowdLod] FAN_{v} {full} -> {lod} tris");
                Assert.Less(lod * 3, full, $"FAN_{v} {full} -> {lod}");
            }
        }

        [Test]
        public void MeshesAtOrUnderTheTargetComeBackAsIs()
        {
            var m = new Mesh { vertices = new[] { Vector3.zero, Vector3.right, Vector3.up }, triangles = new[] { 0, 1, 2 } };
            Assert.AreSame(m, MajesticMeshLod.Decimated(m, 10));
            Object.DestroyImmediate(m);
        }
    }
}
