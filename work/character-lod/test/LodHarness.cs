// Offline test of HeroLodSimplifier on dumped Unity meshes (tools/unity_mesh.py write_bin). Plain mono, no Unity.
using System;
using System.Diagnostics;
using System.IO;
using GolfArcade.CharacterLod;

static class LodHarness
{
    static void Main(string[] args)
    {
        double ratio = double.Parse(args[1]), err = double.Parse(args[2]);
        using var r = new BinaryReader(File.OpenRead(args[0]));
        int nv = r.ReadInt32(), ns = r.ReadInt32();
        float[] F(int n) { var a = new float[n]; for (int i = 0; i < n; i++) a[i] = r.ReadSingle(); return a; }
        var pos = F(nv * 3); var w = F(nv * 4); var bi = new int[nv * 4]; for (int i = 0; i < bi.Length; i++) bi[i] = r.ReadInt32();
        var nrm = F(nv * 3); var uv = F(nv * 2);
        var subs = new int[ns][];
        for (int s = 0; s < ns; s++) { int c = r.ReadInt32(); subs[s] = new int[c]; for (int i = 0; i < c; i++) subs[s][i] = r.ReadInt32(); }
        // features: skin "centroid" over pseudo bone positions (0.3 m apart) x 0.05 + normal x 0.004
        var feat = new float[nv * 6];
        for (int v = 0; v < nv; v++)
        {
            for (int k = 0; k < 4; k++)
            {
                int b = bi[v * 4 + k]; float ww = w[v * 4 + k];
                var rng = new Random(b * 7919 + 13);
                for (int d = 0; d < 3; d++) feat[v * 6 + d] += (float)(ww * (rng.NextDouble() - .5) * .6 * .05);
            }
            for (int d = 0; d < 3; d++) feat[v * 6 + 3 + d] = nrm[v * 3 + d] * .010f;
        }
        int before = 0; foreach (var s in subs) before += s.Length / 3;
        var sw = Stopwatch.StartNew();
        var res = HeroLodSimplifier.Simplify(new HeroLodSimplifier.Input { positions = pos, submeshes = subs, features = feat, featureDim = 6 }, ratio, err);
        sw.Stop();
        Console.WriteLine($"{Path.GetFileName(args[0])}: {before} -> {res.triangles} tris ({100.0 * res.triangles / before:F1}%), maxErr {res.maxError * 1000:F2} mm, passes {res.passes}, {sw.ElapsedMilliseconds} ms");
        if (args.Length > 3)
            using (var o = new BinaryWriter(File.Create(args[3])))
            {
                o.Write(res.submeshes.Length);
                foreach (var s in res.submeshes) { o.Write(s.Length); foreach (var i in s) o.Write(i); }
            }
    }
}
