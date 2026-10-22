from pathlib import Path
import difflib,json,hashlib
R=Path.cwd();O=R/'work/reference-rebuild/face-surface-diagnosis'
path='Unity/Assets/Scripts/Tennis/HeroSkinNormals.cs';old=(R/path).read_text();new=old
new=new.replace('static readonly Dictionary<Mesh,Mesh> softCache=new();','static readonly Dictionary<Mesh,Mesh> softCache=new();\n        static readonly Dictionary<Mesh,Mesh> areaCache=new();')
new=new.replace('string suffix=soft?" (soft skin normals)":" (continuous skin normals)";\n            var activeCache=soft?softCache:continuousCache;', '''// One work-only A/B: spatial filtering integrates represented surface
            // area, rather than giving each tessellation vertex equal influence.
            bool areaWeighted=!soft && System.Environment.GetEnvironmentVariable("VISUAL_CHARACTER_NORMAL_AREA")=="1";
            string suffix=areaWeighted?" (area continuous skin normals)":soft?" (soft skin normals)":" (continuous skin normals)";
            var activeCache=areaWeighted?areaCache:soft?softCache:continuousCache;''')
new=new.replace('var geometric=new Vector3[unique.Count];var triangles=source.triangles;', 'var geometric=new Vector3[unique.Count];var representedArea=new float[unique.Count];var triangles=source.triangles;')
new=new.replace('geometric[id[a]]+=area;geometric[id[b]]+=area;geometric[id[c]]+=area;', 'geometric[id[a]]+=area;geometric[id[b]]+=area;geometric[id[c]]+=area;\n                float size=area.magnitude;representedArea[id[a]]+=size;representedArea[id[b]]+=size;representedArea[id[c]]+=size;')
new=new.replace('var cell=Cell(unique[i]);Vector3 sum=geometric[i];float count=1;', 'var cell=Cell(unique[i]);float seed=areaWeighted?representedArea[i]:1;Vector3 sum=geometric[i]*seed;float count=seed;')
new=new.replace('float falloff=1-d/(radius*radius);float weight=falloff*falloff*agreement*agreement;', 'float falloff=1-d/(radius*radius);float weight=falloff*falloff*agreement*agreement;\n                        if(areaWeighted)weight*=representedArea[j];')
new=new.replace('field[i]=(sum/count).normalized;', 'field[i]=(sum/Mathf.Max(count,1e-12f)).normalized;')
new=new.replace('(soft?"soft":"continuous")+" source="', '(areaWeighted?"area-continuous":soft?"soft":"continuous")+" source="')
assert new!=old
(O/'HeroSkinNormals.cs').write_text(new)
(O/'HeroSkinNormals.cs.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=path,tofile=path)))
capPath='Unity/Assets/Editor/VisualOverhaulCharacterCapture.cs';capOld=(R/capPath).read_text();capNew=capOld
capNew=capNew.replace('foreach(var variant in variants){', 'bool twoFrontOnly=Environment.GetEnvironmentVariable("VISUAL_CHARACTER_TWO_FRONT_ONLY")=="1";\n                    foreach(var variant in variants){')
capNew=capNew.replace('if((blinkReview||fullReview)&&variant.name!="pigment")continue;', 'if((blinkReview||fullReview||twoFrontOnly)&&variant.name!="pigment")continue;')
capNew=capNew.replace('Shot(sex+"_"+variant.name+"_threequarter",front+reviewRight*.30f,reviewTarget,24,900,900,reviewUp);', '''if(twoFrontOnly){
                            audit.Add($"Two-front normal review {sex}: mesh={hero.body.sharedMesh.name}; eye, skin finish and open blink retained");
                            continue;
                        }
                        Shot(sex+"_"+variant.name+"_threequarter",front+reviewRight*.30f,reviewTarget,24,900,900,reviewUp);''')
(O/'VisualOverhaulCharacterCapture.cs').write_text(capNew)
(O/'VisualOverhaulCharacterCapture.cs.patch').write_text(''.join(difflib.unified_diff(capOld.splitlines(True),capNew.splitlines(True),fromfile=capPath,tofile=capPath)))
env=json.loads((R/'work/reference-rebuild/character-skin-finish2/revision1/capture-skin-finish2-revision1.json').read_text())[0]['env']
env.update(VISUAL_CHARACTER_OUT=str(R/'proof/reference-rebuild/face-area-normal1'),VISUAL_CHARACTER_TWO_FRONT_ONLY='1',VISUAL_CHARACTER_NORMAL_AREA='1',VISUAL_CHARACTER_FULL_REVIEW='0',VISUAL_CHARACTER_BLINK_POSES='',VISUAL_CHARACTER_CLIPS='')
(O/'capture-two-front.json').write_text(json.dumps([{'name':'reference-face-area-normal1-two-front','method':'GolfArcade.EditorTools.VisualOverhaulCharacterCapture.Run','env':env}],indent=2)+'\n')
manifest={path:{'baseline_sha256':hashlib.sha256(old.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(new.encode()).hexdigest()},capPath:{'baseline_sha256':hashlib.sha256(capOld.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(capNew.encode()).hexdigest()},'status':'SOURCE STAGED / UNITY PENDING','candidate_count':1,'assets_written':False,'source_meshes_written':False,'geometry_weights_rig_uv_blendshapes_unchanged_by_normal_candidate':True,'skin_eyes_blink_shaders_unchanged':True,'normal_radius_metres':.008,'normal_angle_cap_degrees':20,'candidate_flag':'VISUAL_CHARACTER_NORMAL_AREA=1'}
(O/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
