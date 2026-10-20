from pathlib import Path
import difflib,json,hashlib
out=Path('work/reference-rebuild/original-native-parity1');p=out/'MatchHeroLockerExport.cs';s=p.read_text()
s=s.replace('WriteGolden(root, motions, sources, rig, clipInfos, baseName);','WriteGolden(root, motions, sources, rig, clipInfos, baseName);\n                WriteBlinkParity(root, motions, sources, clipInfos, baseName);')
pos=s.index('        /// Independent Unity samples')
s=s[:pos]+'''        [Serializable] class BlinkVertex { public int index; public float[] position; }
        [Serializable] class BlinkSample { public string clip, part; public float time, blink; public BlinkVertex[] vertices; }
        [Serializable] class BlinkProof { public BlinkSample[] samples; }
        static void WriteBlinkParity(GameObject root, List<MotionSource> motions, List<PartSource> sources, List<ClipInfo> clips, string baseName)
        {
            var face = sources.First(p => p.name == "Face");
            if (!face.skinned || face.mesh.GetBlendShapeIndex("Hero_Blink_Half") < 0) return;
            Directory.CreateDirectory(GoldenDir);
            var result = new List<BlinkSample>();
            var look = root.GetComponent<MatchHeroLook>();
            foreach (var ci in clips.Where(c => c.id == "ready" || c.id == "serve" || c.id == "wave")) {
                var clip = motions.First(m => m.id == ci.id).clip;
                int frame = Mathf.RoundToInt((ci.frames - 1) * .5f);
                float t = ci.times != null ? ci.times[frame] : frame * clip.length / (ci.frames - 1);
                foreach (float blink in new[] { 0f, .25f, .5f, .75f, 1f }) {
                    SamplePose(root, clip, t); look.SetFacePerformance(blink, Vector2.zero);
                    foreach (var part in sources.Where(p => p.name == "Body" || p.name == "Face")) {
                        Pose(root, part);
                        var indices = new SortedSet<int>();
                        int stride = Mathf.Max(1, part.pos.Length / 160);
                        for (int i = 0; i < part.pos.Length; i += stride) indices.Add(i);
                        // Include every moved eyelid vertex, not a sparse anatomical guess.
                        if (part.name == "Body") foreach (string name in new[] { "Hero_Blink_Half", "Hero_Blink" }) {
                            int shape = part.mesh.GetBlendShapeIndex(name); if (shape < 0) continue;
                            var dp = new Vector3[part.mesh.vertexCount]; var dn = new Vector3[dp.Length]; var dt = new Vector3[dp.Length];
                            part.mesh.GetBlendShapeFrameVertices(shape, part.mesh.GetBlendShapeFrameCount(shape)-1, dp, dn, dt);
                            for (int i = 0; i < dp.Length; i++) if (dp[i].sqrMagnitude > 1e-12f) indices.Add(i);
                        }
                        result.Add(new BlinkSample { clip=ci.id, part=part.name, time=t, blink=blink,
                            vertices=indices.Select(i => new BlinkVertex { index=i, position=new[] {part.pos[i].x,part.pos[i].y,-part.pos[i].z} }).ToArray() });
                    }
                }
            }
            look.SetFacePerformance(0, Vector2.zero);
            File.WriteAllText(Path.Combine(GoldenDir, baseName + "_blink_parity.json"), JsonUtility.ToJson(new BlinkProof { samples=result.ToArray() }, true));
        }

''' +s[pos:]
p.write_text(s)
old=(out/'MatchHeroLockerExport.cs.baseline').read_text();target='Unity/Assets/Editor/MatchHeroLockerExport.cs'
(out/'MatchHeroLockerExport.cs.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=target,tofile=target)))
m=json.loads((out/'source-manifest.json').read_text());m[target]['candidate_sha256']=hashlib.sha256(s.encode()).hexdigest();(out/'source-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
