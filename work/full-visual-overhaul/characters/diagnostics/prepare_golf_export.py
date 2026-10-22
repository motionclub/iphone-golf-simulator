from pathlib import Path
p=Path('Unity/Assets/Editor/MatchHeroLockerExport.cs')
s=p.read_text().replace('using GolfArcade.Tennis;','using GolfArcade.Tennis;\nusing GolfArcade.Game;')
s=s.replace('public float specularStrength, environmentStrength;','public float specularStrength, environmentStrength, metallic;')
s=s.replace('[Serializable] class RigPart {','[Serializable] class RigMorph { public string name; public int positionOffset, normalOffset; }\n        [Serializable] class MorphTrack { public string part; public int offset, count; }\n        class MotionSource { public AnimationClip clip; public string id, equipment; public bool loop; public float contact; }\n        [Serializable] class RigPart {').replace('public int[] bones; }','public int[] bones; public RigMorph[] morphs; }')
s=s.replace('public float[] boundsMin, boundsMax, times; }','public float[] boundsMin, boundsMax, times; public MorphTrack[] morphWeights; public string equipment; }')
a=s.index('            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "Player" + sex + (golf ? "GolfKit" : "") + ".prefab");')
b=s.index('            try\n',a)
s=s[:a]+'''            GameObject root;
            if(golf) {
                var golfer=HeroGolfer.Build(null,new HeroLook {Female=sex=="Female",Haircut=(int)HeroGolfer.Haircut.Bald,Skin=Color.white,HairColor=Color.black});
                if(golfer==null)throw new FileNotFoundException("Actual golf hero "+sex);
                root=golfer.Root;
            } else {
                var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir+"Player"+sex+".prefab");
                if(!prefab)throw new FileNotFoundException("prefab "+sex);
                root=(GameObject)Object.Instantiate(prefab);
            }
'''+s[b:]
s=s.replace('                driver.ResolvePerformanceClips();','                if(driver)driver.ResolvePerformanceClips();',1)
a=s.index('                var racketRoot = root.GetComponentsInChildren<Transform>(true).First(t => t.name == "Racket_Classic");',a)
b=s.index('                var sources = Collect(root);',a)
s=s[:a]+'''                if(!golf)root.GetComponentsInChildren<Transform>(true).First(t=>t.name=="Racket_Classic").localScale*=TennisRules.HeroRacketScale;
                var motions=golf ? GolfMotions(sex):RigClips.Select(entry=>{var slot=driver.slots.First(s=>s.id==entry.slot);return new MotionSource{clip=slot.clip,id=entry.id,loop=entry.loop,contact=slot.contact};}).ToList();
                var ready=motions.First(m=>m.id=="ready").clip;
                var fore=golf ? motions.First(m=>m.id=="golfDrive"):new MotionSource{clip=driver.slots.First(s=>s.id==HeroTennisDriver.Clip.Forehand).clip,contact=driver.slots.First(s=>s.id==HeroTennisDriver.Clip.Forehand).contact};
'''+s[b:]
s=s.replace('!(golf && x.name == "Hair_F" && x.s.look.shader == "Universal Render Pipeline/Lit")','!(golf && x.name.StartsWith("Club_") && x.s.look.shader == "Universal Render Pipeline/Lit")')
s=s.replace('source = golf ? "Resources/Tennis/Customization/Player" + sex + "GolfKit.prefab"','source = golf ? "HeroGolfer.Build(Resources/Hero/golfer_" + (sex=="Female" ? "f":"m") + "), detailed golf kit + actual Club palette"')
s=s.replace('man.rig = golf ? null : ExportRig(root, driver, sources, ready, sb, baseName);','man.rig = ExportRig(root, motions, sources, ready, sb, baseName);')
s=s.replace('look.specularStrength = F("_SpecularStrength"); look.environmentStrength = F("_EnvironmentStrength");','look.specularStrength = F("_SpecularStrength"); look.environmentStrength = F("_EnvironmentStrength"); look.metallic=F("_Metallic");')
s=s.replace('            HeroGripPolish.ApplyGrip(root.GetComponent<MatchHeroLook>());','            HeroGripPolish.ApplyGrip(root.GetComponent<MatchHeroLook>());\n            root.GetComponent<GolfGarmentCorrectives>()?.Apply();')
s=s.replace('static Rig ExportRig(GameObject root, HeroTennisDriver driver,','static Rig ExportRig(GameObject root, List<MotionSource> motions,')
s=s.replace('            foreach (var (slotId, id, loop) in RigClips)\n            {\n                var slot = driver.slots.First(s => s.id == slotId); var clip = slot.clip;\n                if (!clip) throw new InvalidOperationException("Missing lobby clip: " + slotId);','            foreach (var motion in motions)\n            {\n                var clip=motion.clip;var id=motion.id;var loop=motion.loop;\n                if(!clip)throw new InvalidOperationException("Missing lobby clip: "+id);')
s=s.replace('contact = slot.contact, frames = frames,','contact = motion.contact, equipment=motion.equipment, frames = frames,')
s=s.replace('var clip = driver.slots.First(s => s.id == RigClips.First(c => c.id == ci.id).slot).clip;','var clip = motions.First(m=>m.id==ci.id).clip;')
s=s.replace('WriteGolden(root, driver, sources, rig, clipInfos, baseName);','WriteGolden(root, motions, sources, rig, clipInfos, baseName);').replace('WriteEmoteParity(root, driver, bones, rigid, rigidRef, baseName);','WriteEmoteParity(root, motions, bones, rigid, rigidRef, baseName);')
s=s.replace('static void WriteEmoteParity(GameObject root, HeroTennisDriver driver,','static void WriteEmoteParity(GameObject root, List<MotionSource> motions,')
s=s.replace('foreach (var entry in RigClips.Where(e => !e.loop && e.id != "serve")) {\n                var clip = driver.slots.First(s => s.id == entry.slot).clip;','foreach (var entry in motions.Where(e => !e.loop && e.id != "serve")) {\n                var clip=entry.clip;')
s=s.replace('static void WriteGolden(GameObject root, HeroTennisDriver driver,','static void WriteGolden(GameObject root, List<MotionSource> motions,')
s=s.replace('First(r => r.name.StartsWith("Body_"))','First(r => r.enabled && (r.name.StartsWith("Body_")||r.name=="Body"))')
s=s.replace('.Where(r => r.name.StartsWith("Kit_")).OrderBy', '.Where(r => r.name.StartsWith("Kit_") && (r.enabled||r.name=="Kit_Glove_R")).OrderBy')
s=s.replace('            if (root.GetComponent<MatchHeroLook>().golfKit) return list;','''            if(root.GetComponent<MatchHeroLook>().golfKit) {
                foreach(var club in root.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(r=>r.name.StartsWith("CLUB_")).OrderBy(r=>r.name))
                    list.Add(new PartSource{name="Club_"+club.name.Substring(5).ToLowerInvariant(),kind="equipment",mesh=club.sharedMesh,renderer=club,skinned=club,materials=club.sharedMaterials});
                return list;
            }''')
s=s.replace('            if (hair) list.Add(', '            if (hair && hair.enabled) list.Add(').replace('            if (rigidHair) list.Add(', '            if (rigidHair && rigidHair.enabled) list.Add(')
# Morph targets preserve actual corrective deltas before skinning, all offsets exact.
s=s.replace('                rig.parts[partNo++] = rp;\n            }\n            foreach (var p in rigid)', '''                if(mesh.blendShapeCount>0) {
                    rp.morphs=new RigMorph[mesh.blendShapeCount];var baseVertices=mesh.vertices;var baseNormals=mesh.normals;
                    for(int shape=0;shape<mesh.blendShapeCount;shape++) {
                        var dv=new Vector3[mesh.vertexCount];var dn=new Vector3[mesh.vertexCount];var dt=new Vector3[mesh.vertexCount];int frame=mesh.GetBlendShapeFrameCount(shape)-1;
                        mesh.GetBlendShapeFrameVertices(shape,frame,dv,dn,dt);var target=new RigMorph{name=mesh.GetBlendShapeName(shape),positionOffset=blob.Count};
                        AddV3(blob,baseVertices.Zip(dv,(v,d)=>v+d).ToArray(),true);target.normalOffset=blob.Count;AddV3(blob,baseNormals.Zip(dn,(v,d)=>v+d).ToArray(),true);rp.morphs[shape]=target;
                    }
                    sb.AppendLine("  corrective targets "+p.name+": "+string.Join(",",rp.morphs.Select(m=>m.name)));
                }
                rig.parts[partNo++] = rp;
            }
            foreach (var p in rigid)''')
s=s.replace('                clipInfos.Add(ci); clipFrames[id] = data;', '''                var morphTracks=new List<MorphTrack>();
                foreach(var p in skinned.Where(p=>p.mesh.blendShapeCount>0)) {
                    var mt=new MorphTrack{part=p.name,offset=blob.Count,count=p.mesh.blendShapeCount};
                    for(int k=0;k<frames;k++) {
                        float at=sampleTimes!=null ? sampleTimes[k]:k*clip.length/(frames-1);SamplePose(root,clip,at);
                        for(int shape=0;shape<mt.count;shape++)blob.AddRange(BitConverter.GetBytes(p.skinned.GetBlendShapeWeight(shape)/p.mesh.GetBlendShapeFrameWeight(shape,p.mesh.GetBlendShapeFrameCount(shape)-1)));
                    }
                    morphTracks.Add(mt);
                }
                ci.morphWeights=morphTracks.ToArray();
                clipInfos.Add(ci); clipFrames[id] = data;''')
# Selfcheck adds live sampled morph deltas in bind space. Golden samples independently come from Pose().
s=s.replace('                        var m = new Matrix4x4[rp.bones.Length];','''                        if(mesh.blendShapeCount>0) {
                            var dv=new Vector3[verts.Length];var dn=new Vector3[verts.Length];var dt=new Vector3[verts.Length];
                            foreach(var mt in ci.morphWeights.Where(mt=>mt.part==rp.part))for(int shape=0;shape<mt.count;shape++) {
                                float weight=BitConverter.ToSingle(blob.ToArray(),mt.offset+(k*mt.count+shape)*4);mesh.GetBlendShapeFrameVertices(shape,mesh.GetBlendShapeFrameCount(shape)-1,dv,dn,dt);
                                for(int vertex=0;vertex<verts.Length;vertex++)verts[vertex]+=dv[vertex]*weight;
                            }
                        }
                        var m = new Matrix4x4[rp.bones.Length];''')
# Keep blob conversion out of per shape hotloop for parity audit.
s=s.replace('            // ---- self check: skin the exported bind mesh', '            var parityBlob=blob.ToArray();\n            // ---- self check: skin the exported bind mesh').replace('BitConverter.ToSingle(blob.ToArray(),mt.offset+', 'BitConverter.ToSingle(parityBlob,mt.offset+')
# Golf actual clips and contact metadata from unchanged resource landmarks.
insert='''        [Serializable] class GolfLandmarks { public string gender;public GolferView.ClipInfo[] clips; }
        static List<MotionSource> GolfMotions(string sex) {
            string path=HeroGolfer.PathFor(sex=="Female");
            var clips=Resources.LoadAll<AnimationClip>(path).Where(c=>!c.name.StartsWith("__preview__")).ToDictionary(c=>c.name);
            var landmarks=JsonUtility.FromJson<GolfLandmarks>(Resources.Load<TextAsset>(path+"_clips").text).clips;
            var definitions=new[]{("ready","Idle",true),("idle","Idle",true),("serve","Drive",false),("golfDrive","Drive",false),("golfIron","IronSwing",false),("golfHalf","HalfSwing",false),("golfChip","Chip",false),("golfPutt","Putt",false),("wave","Wave",false),("cheer","Cheer",false),("matchWin","Cheer",false),("hitPerfect","FistPump",false),("celebratePoint","FistPump",false)};
            return definitions.Select(d=>{var mark=landmarks.First(m=>m.name==d.Item2);return new MotionSource{clip=clips[d.Item2],id=d.Item1,loop=d.Item3,contact=mark.fps>0 ? (float)mark.impact/mark.fps:0,equipment=string.IsNullOrEmpty(mark.club)?"iron":mark.club.ToLowerInvariant()};}).ToList();
        }

'''
s=s.replace('        static string ExportSex(',insert+'        static string ExportSex(')
Path('work/full-visual-overhaul/characters/diagnostics/MatchHeroLockerExport.cs').write_text(s)
print('prepared',len(s),'bytes')
