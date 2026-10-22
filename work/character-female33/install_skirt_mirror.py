from pathlib import Path
import shutil
r=Path('work/character-finish32/review-project/Unity/Assets');w=Path('work/character-female33');assert 'Traceback' not in (w/'skirt-author.log').read_text();shutil.copy2(w/'FemaleSkirt.fbx',r/'Resources/Tennis/KitsTailored/FemaleSkirt.fbx');shutil.copy2(w/'FemaleSkirt.fbx',r/'Resources/Tennis/KitsTailored/FemaleSkirtDistance.fbx')
p=r/'Scripts/Tennis/MatchHeroLook.cs';s=p.read_text();old='''            if (body)
            {
                // the soft skin normal''';new='''            if (!golfKit && female && kit != null && System.Environment.GetEnvironmentVariable("VISUAL_TAILORED_FEMALE_SKIRT") == "1") {
                var source = Resources.Load<GameObject>("Tennis/KitsTailored/FemaleSkirt");
                var src = source ? source.GetComponentsInChildren<SkinnedMeshRenderer>(true).FirstOrDefault(r => r.name == "Kit_Bottom") : null;
                var live = kit.FirstOrDefault(r => r && r.name == "Kit_Bottom");
                if (src && live) {
                    var bones = GetComponentsInChildren<Transform>(true).GroupBy(t => t.name).ToDictionary(g => g.Key, g => g.First());
                    live.sharedMesh = Object.Instantiate(src.sharedMesh); live.sharedMesh.name = "TailoredSkirt33 Female"; owned.Add(live.sharedMesh);
                    live.bones = src.bones.Select(b => bones[b.name]).ToArray(); live.sharedMaterials = src.sharedMaterials;
                }
            }
            if (body)
            {
                // the soft skin normal''';assert old in s;s=s.replace(old,new,1);s=s.replace('if (tag == "Top" && mesh && mesh.name.StartsWith("TailoredPolo"))','if (mesh && ((tag == "Top" && mesh.name.StartsWith("TailoredPolo")) || (tag == "Bottom" && mesh.name.StartsWith("TailoredSkirt"))))');p.write_text(s)
p=r/'Scripts/Tennis/HeroGarmentTailoring.cs';s=p.read_text().replace('if(src && src.name.StartsWith("TailoredPolo"))','if(src && src.name.StartsWith("TailoredSkirt")) return src;\n   if(src && src.name.StartsWith("TailoredPolo"))');p.write_text(s)
p=r/'Scripts/Tennis/HeroGarmentLOD.cs';s=p.read_text();s=s.replace('var selected = low;', 'bool skirt = live.sharedMesh.name.StartsWith("TailoredSkirt");\n                var selected = low;\n                if (skirt) selected = Resources.Load<GameObject>("Tennis/KitsTailored/FemaleSkirtDistance").GetComponentsInChildren<SkinnedMeshRenderer>(true).First(r => r.name == "Kit_Bottom");');s=s.replace('else matchMesh = HeroGarmentHemWeights.Prepare','else if (skirt) matchMesh = selected.sharedMesh;\n                else matchMesh = HeroGarmentHemWeights.Prepare');p.write_text(s)
p=r/'Editor/MatchHeroLockerExport.cs';s=p.read_text();s=s.replace('bool tailored=live.sharedMesh && live.sharedMesh.name.StartsWith("TailoredPolo");','bool skirt=live.sharedMesh && live.sharedMesh.name.StartsWith("TailoredSkirt");\n                        bool tailored=live.sharedMesh && live.sharedMesh.name.StartsWith("TailoredPolo");');s=s.replace('var selected=src;', 'var selected=src;\n                        if(skirt)selected=Resources.Load<GameObject>("Tennis/KitsTailored/FemaleSkirtDistance").GetComponentsInChildren<SkinnedMeshRenderer>(true).First(r=>r.name=="Kit_Bottom");');s=s.replace('else live.sharedMesh=HeroGarmentHemWeights.Prepare','else if(skirt) { }\n                        else live.sharedMesh=HeroGarmentHemWeights.Prepare');p.write_text(s)
