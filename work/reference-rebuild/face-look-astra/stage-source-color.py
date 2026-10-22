from pathlib import Path
import difflib,json
root=Path.cwd();stage=root/'work/reference-rebuild/face-look-astra/source-color';stage.mkdir(parents=True,exist_ok=True)
def put(path,edits,name):
 source=(root/path).read_text(); candidate=source
 for old,new in edits:
  assert candidate.count(old)==1,(path,old[:70]);candidate=candidate.replace(old,new)
 out=stage/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(candidate)
 patch=''.join(difflib.unified_diff(source.splitlines(True),candidate.splitlines(True),fromfile=path,tofile=path));(stage/name).write_text(patch)
put('Unity/Assets/Scripts/Tennis/MatchHeroLook.cs',[
('''                authoredSkin = shared.Length > 0 && shared[0] ? (shared[0].HasProperty("_BaseColor") ? shared[0].GetColor("_BaseColor") : shared[0].color) : skinTone;
                for (int i = 0; i < shared.Length; i++)''','''                authoredSkin = shared.Length > 0 && shared[0] ? (shared[0].HasProperty("_BaseColor") ? shared[0].GetColor("_BaseColor") : shared[0].color) : skinTone;
                // OriginalSeam FBX retains Blender's linear Base Color values.
                // Unity Color properties and locker picks use sRGB authoring values.
                // Convert this imported default once; later SetSkin picks stay exact.
                if (originalSeam) { authoredSkin = authoredSkin.gamma; skinTone = authoredSkin; }
                for (int i = 0; i < shared.Length; i++)'''),
('''                        if(originalSeam){
                            HeroOriginalSeamAnatomy.ConfigurePigment(skinMaterials[i]);''','''                        if(originalSeam){
                            skinMaterials[i].SetColor("_BaseColor", skinMaterials[i].GetColor("_BaseColor").gamma);
                            HeroOriginalSeamAnatomy.ConfigurePigment(skinMaterials[i]);''')
],'source-color.patch')
put('Unity/Assets/Editor/TennisVenueCapture.cs',[
('''            HeroGarmentLOD.ForceFullDetail=true;''','''            var captureHero=game.Player.GetComponentInChildren<MatchHeroLook>();
            var authoredCaptureTone=captureHero && captureHero.body && captureHero.body.sharedMaterial
                ? ColorUtility.ToHtmlStringRGB(captureHero.body.sharedMaterial.GetColor("_BaseColor")) : "missing";
            var reviewSkin=System.Environment.GetEnvironmentVariable("HERO_VENUE_CHARACTER_SKIN");
            if(!string.IsNullOrEmpty(reviewSkin)){
                if(!ColorUtility.TryParseHtmlString("#"+reviewSkin.TrimStart('#'),out var tone))
                    throw new System.ArgumentException("Invalid HERO_VENUE_CHARACTER_SKIN: "+reviewSkin);
                var captureStyle=game.PlayerLook ?? HeroKit.Style.From(HeroKit.DefaultSkin,HeroKit.DefaultHair,0,default,5,game.FemalePlayer);
                captureStyle.SkinTint=tone;game.SetPlayerLook(captureStyle);
                for(int settle=0;settle<2;settle++)yield return null;
            }
            var activeCaptureTone=captureHero && captureHero.body && captureHero.body.sharedMaterial
                ? ColorUtility.ToHtmlStringRGB(captureHero.body.sharedMaterial.GetColor("_BaseColor")) : "missing";
            var toneAudit=$"sex={(game.FemalePlayer ? "female":"male")}; sourceDefault={authoredCaptureTone}; selectedOverride={reviewSkin ?? "none"}; activeBaseColor={activeCaptureTone}; playerLook={game.PlayerLook.HasValue}; skinPolish={Shader.GetGlobalFloat("_HeroSkinPolish")}; presentationFill={Shader.GetGlobalFloat("_HeroPresentationFill")}; filmResponse={Shader.GetGlobalFloat("_HeroFilmResponse")}";
            Debug.Log("[VenueCapture skin] "+toneAudit);
            File.WriteAllText(Path.Combine(Out,"skin-light-audit.txt"),toneAudit+"\\n");
            HeroGarmentLOD.ForceFullDetail=true;''')
],'capture-tone.patch')
base=json.loads((root/'work/reference-rebuild/face-finish30/root-map-queue.json').read_text())
queue=[]
for variant in ['defaults','matched']:
 for job in base:
  j=json.loads(json.dumps(job));sex=j['env']['HERO_VENUE_CHARACTER_SEX'];name='face-finish30-resort-color-'+variant+'-'+sex
  j['name']=name;j['env']['HERO_VENUE_OUT']=str(root/'proof/reference-rebuild'/name)
  j['env']['HERO_VENUE_ONLY']='16_player_face,17_player_intro'
  if variant=='matched':j['env']['HERO_VENUE_CHARACTER_SKIN']='FBAE8F' if sex=='female' else 'EA8D71'
  queue.append(j)
(stage/'map-color-queue.json').write_text(json.dumps(queue,indent=2)+'\n')
print('source-color.patch, capture-tone.patch and map-color-queue.json staged')
