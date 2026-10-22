from pathlib import Path
root=Path('work/character-finish32/review-project/Unity/Assets/Scripts/Tennis')
p=root/'HeroGarmentPoseCorrectives.cs';s=p.read_text();s=s.replace('Dictionary<bool,Profile> profiles','Dictionary<string,Profile> profiles')
a=s.index('  static Profile Load(bool female){');b=s.index('  public static Mesh Prepare',a)
s=s[:a]+'''  static Profile Load(bool female,Mesh mesh=null){
   bool tailored=mesh&&mesh.name.StartsWith("TailoredPolo");
   string resource=tailored?"Tennis/Correctives/TailoredPolo_"+(female?"Female":"Male")+(mesh.name.Contains("distance")?"_Distance":"_Full") : "Tennis/Correctives/SleeveFit_"+(female?"Female":"Male");
   if(profiles.TryGetValue(resource,out var p))return p;
   var text=Resources.Load<TextAsset>(resource);if(!text)return null;
   p=JsonUtility.FromJson<Profile>(text.text);if(p?.anchors==null||p.vertexCount<=0)throw new InvalidOperationException("Invalid garment profile "+resource);
   profiles[resource]=p;return p;
  }
''' +s[b:]
s=s.replace('var p=Load(hero.female);','var p=Load(hero.female,src);')
s=s.replace('   else {\n    // Bounded', '   else {\n    if(src.name.StartsWith("TailoredPolo"))throw new InvalidOperationException("Tailored polo requires its exact full/distance corrective basis");\n    // Bounded')
s=s.replace('   HeroGarmentLocalFit.Prepare(hero.female,result,p,transfer);','   if(!src.name.StartsWith("TailoredPolo"))HeroGarmentLocalFit.Prepare(hero.female,result,p,transfer);')
a=s.index('  bool Init(){');b=s.index('  public void Apply()',a)
s=s[:a]+'''  bool Init(){
   if(!look)look=GetComponent<MatchHeroLook>();if(!look||look.golfKit)return false;
   top??=look.kit?.FirstOrDefault(r=>r&&r.name=="Kit_Top");if(!top||!top.sharedMesh)return false;
   var selected=Load(look.female,top.sharedMesh);if(selected==null)return false;
   if(profile!=selected){profile=selected;previous=null;weights=new float[profile.anchors.Length];}
   if(joints==null){var all=look.GetComponentsInChildren<Transform>(true);joints=new Transform[8,2];for(int i=0;i<8;i++)for(int j=0;j<2;j++){joints[i,j]=all.FirstOrDefault(t=>t.name==Segments[i,j]);if(!joints[i,j])return false;}}
   if(previous!=top.sharedMesh){previous=top.sharedMesh;indices=profile.anchors.Select(a=>previous.GetBlendShapeIndex(Prefix+a.shape)).ToArray();}
   return true;
  }
''' +s[b:]
s=s.replace('   HeroGarmentLocalFit.Apply(look.female,top,features);','   bool tailored=top.sharedMesh.name.StartsWith("TailoredPolo");\n   if(!tailored)HeroGarmentLocalFit.Apply(look.female,top,features);')
s=s.replace('   float confidence=','   if(tailored){var order=Enumerable.Range(0,weights.Length).OrderByDescending(i=>weights[i]).ToArray();sum=0;for(int n=0;n<order.Length;n++){int i=order[n];if(n>=3)weights[i]=0;sum+=weights[i];}}\n   float confidence=')
s=s.replace('   HeroGarmentGusset.Apply(look.female,look.transform,top);','   if(!tailored)HeroGarmentGusset.Apply(look.female,look.transform,top);')
p.write_text(s)
p=root/'HeroGarmentTailoring.cs';s=p.read_text().replace('if(src && src.name.StartsWith("TailoredPolo")) return src; // Source-authored garment has its own coherent binding.','if(src && src.name.StartsWith("TailoredPolo")) return HeroGarmentPoseCorrectives.Prepare(hero,r,src); // Candidate-specific authored basis; skip legacy geometry and weights.');p.write_text(s)
