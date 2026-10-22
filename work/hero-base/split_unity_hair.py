from pathlib import Path
p=Path('Unity/Assets/Editor/HeroBaseStaticImport.cs')
s=p.read_text()
a=s.index(' public static void Run(){');b=s.index(' static Material MakeMaterial(',a)
s=s[:a]+''' [Serializable] class Attachment { public string body_fbx,default_hair_fbx; public float[] hair_anchor_metres; public bool body_contains_hair; public float bald_height_m; }
 public static void Run(){
  try {
   audit.Clear();
   foreach(var folder in new[]{"Models","Materials","Textures","Bodies","Hair"})Directory.CreateDirectory(Dir+"/"+folder);
   Directory.CreateDirectory(Proof+"/unity");
   foreach(var sex in new[]{"Male","Female"}){
    foreach(var filename in new[]{"HeroBase_"+sex+"_Body.fbx","Hair_Default_"+sex+".fbx"})File.Copy("../ArtDir/hero/base_lock/unity_import/"+filename,Dir+"/Models/"+filename,true);
    File.Copy("../ArtDir/hero/base_lock/unity_import/Textures/Head_"+sex+"_Albedo.png",Dir+"/Textures/Head_"+sex+"_Albedo.png",true);
   }
   AssetDatabase.Refresh();
   foreach(var sex in new[]{"Male","Female"}){
    var ti=(TextureImporter)AssetImporter.GetAtPath(Dir+"/Textures/Head_"+sex+"_Albedo.png");ti.sRGBTexture=true;ti.crunchedCompression=false;ti.textureCompression=TextureImporterCompression.Uncompressed;ti.maxTextureSize=2048;ti.mipmapEnabled=true;ti.SaveAndReimport();
    var attachment=JsonUtility.FromJson<Attachment>(File.ReadAllText("../ArtDir/hero/base_lock/unity_import/HeroBase_"+sex+"_Attachments.json"));
    if(attachment.body_contains_hair||attachment.hair_anchor_metres.Length!=3)throw new Exception("Invalid independent hair contract: "+sex);
    SavePart(sex,attachment.body_fbx,BodyPath(sex),false);
    SavePart(sex,attachment.default_hair_fbx,HairPath(sex),true);
    var assembled=new GameObject("HeroBase_"+sex);
    var body=(GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(BodyPath(sex)));body.transform.SetParent(assembled.transform,false);
    var hairRoot=new GameObject("HairRoot");hairRoot.transform.SetParent(assembled.transform,false);var a=attachment.hair_anchor_metres;hairRoot.transform.localPosition=new Vector3(a[0],a[1],a[2]);
    var hair=(GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(HairPath(sex)));hair.transform.SetParent(hairRoot.transform,false);
    PrefabUtility.SaveAsPrefabAsset(assembled,Dir+"/HeroBase_"+sex+".prefab");
    var bodyMesh=body.GetComponentInChildren<MeshFilter>().sharedMesh;
    // Actually delete the optional hairstyle, then verify that the independent body is unchanged.
    Object.DestroyImmediate(hairRoot);
    var after=assembled.GetComponentsInChildren<MeshRenderer>();
    if(after.Length!=1||after[0].GetComponent<MeshFilter>().sharedMesh!=bodyMesh)throw new Exception("Deleting hairstyle changed body: "+sex);
    audit.Add(sex+" REMOVE_HAIR_ROOT body_mesh_unchanged=True body_renderers="+after.Length);
    Object.DestroyImmediate(assembled);
    var dependencies=AssetDatabase.GetDependencies(BodyPath(sex),true);
    if(dependencies.Any(p=>p.StartsWith(Dir+"/Hair/")||p.StartsWith(Dir+"/Models/Hair_")||p.StartsWith(Dir+"/Materials/Hair_")))throw new Exception("Body prefab depends on hair: "+sex);
    audit.Add(sex+" BODY_PREFAB hair_dependencies=0 path="+BodyPath(sex)+" scalp_height="+attachment.bald_height_m+" hair_anchor="+new Vector3(a[0],a[1],a[2]));
   }
   // Remove only the obsolete generated combined models, after replacing their prefab references.
   foreach(var sex in new[]{"Male","Female"}){string legacy=Dir+"/Models/HeroBase_"+sex+".fbx";if(AssetDatabase.LoadMainAssetAtPath(legacy))AssetDatabase.DeleteAsset(legacy);}
   File.WriteAllLines(Proof+"/unity-mesh-material-audit.txt",audit);AssetDatabase.SaveAssets();
   if(File.Exists(Proof+"/unity-error.txt"))File.Delete(Proof+"/unity-error.txt");
   SessionState.SetBool(Key,true);step=-1;EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);SetupStudio();EditorApplication.isPlaying=true;
  } catch(Exception ex){Fail(ex);}
 }
 static string BodyPath(string sex)=>Dir+"/Bodies/HeroBase_"+sex+"_Body.prefab";
 static string HairPath(string sex)=>Dir+"/Hair/Hair_Default_"+sex+".prefab";
 static void SavePart(string sex,string filename,string prefabPath,bool isHair){
  string path=Dir+"/Models/"+filename;var imp=(ModelImporter)AssetImporter.GetAtPath(path);
  imp.globalScale=1;imp.useFileScale=true;imp.bakeAxisConversion=true;imp.animationType=ModelImporterAnimationType.None;imp.importAnimation=false;imp.importCameras=false;imp.importLights=false;imp.meshCompression=ModelImporterMeshCompression.Off;imp.importNormals=ModelImporterNormals.Import;imp.importTangents=ModelImporterTangents.CalculateMikk;imp.isReadable=true;imp.materialImportMode=ModelImporterMaterialImportMode.ImportStandard;imp.SaveAndReimport();
  var instance=Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(path));instance.name=Path.GetFileNameWithoutExtension(prefabPath);
  var renderers=instance.GetComponentsInChildren<MeshRenderer>();if(renderers.Length!=1)throw new Exception("Expected one independent mesh in "+path);
  var renderer=renderers[0];renderer.name=(isHair?"Hair_":"Body_")+(sex=="Male"?"M":"F");
  renderer.sharedMaterials=renderer.sharedMaterials.Select(m=>MakeMaterial(m.name,sex)).ToArray();
  if(renderer.sharedMaterials.Any(m=>m.name.StartsWith("Hair_"))!=isHair)throw new Exception("Hair material leaked across asset boundary: "+path);
  foreach(var mat in renderer.sharedMaterials)audit.Add(sex+" "+renderer.name+" material="+mat.name+" shader="+mat.shader.name+" surface="+mat.GetFloat("_Surface")+" queue="+mat.renderQueue+" baseMap="+(mat.GetTexture("_BaseMap")?AssetDatabase.GetAssetPath(mat.GetTexture("_BaseMap")):"flat"));
  var mesh=renderer.GetComponent<MeshFilter>().sharedMesh;audit.Add(sex+" "+renderer.name+" vertices="+mesh.vertexCount+" tris="+mesh.triangles.Length/3+" bounds="+mesh.bounds+" normals="+mesh.normals.Length);
  foreach(var animator in instance.GetComponentsInChildren<Animator>())Object.DestroyImmediate(animator);
  PrefabUtility.SaveAsPrefabAsset(instance,prefabPath);Object.DestroyImmediate(instance);
  audit.Add(sex+" importer="+filename+" globalScale="+imp.globalScale+" fileScale="+imp.fileScale+" meshCompression="+imp.meshCompression+" normals="+imp.importNormals+" animator=None");
 }
''' + s[b:]
a=s.index('   if(step==6){');b=s.index('   int angle=step%3',a)
s=s[:a]+'''   if(step==12){if(root)Object.DestroyImmediate(root);File.WriteAllLines(Proof+"/unity-import.txt",audit);SessionState.SetBool(Key,false);EditorApplication.isPlaying=false;EditorApplication.delayCall+=SaveSceneAndExit;return;}
   string sex=(step/3)%2==0?"Male":"Female";bool bald=step>=6;
   if(step%3==0){
    if(root)Object.DestroyImmediate(root);root=Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(bald?BodyPath(sex):Dir+"/HeroBase_"+sex+".prefab"));root.name="HeroBase_"+sex+(bald?"_Bald":"");
    var bounds=new Bounds();bool first=true;foreach(var renderer in root.GetComponentsInChildren<Renderer>()){if(first){bounds=renderer.bounds;first=false;}else bounds.Encapsulate(renderer.bounds);}
    if(bald&&root.GetComponentsInChildren<MeshRenderer>().Any(r=>r.name.StartsWith("Hair_")))throw new Exception("Bald proof contains hair");
    audit.Add(sex+(bald?" BALD":" DEFAULT_HAIR")+" WORLD_BOUNDS="+bounds+" HEIGHT="+bounds.size.y+" scale="+root.transform.lossyScale+" renderers="+root.GetComponentsInChildren<Renderer>().Length);
   }
''' + s[b:]
s=s.replace('string suffix=index<3?"M":"F";', 'string suffix=(index/3)%2==0?"M":"F";if(index>=6)suffix+="_bald";')
p.write_text(s)
