from pathlib import Path
p=Path('work/character-finish32/review-project/Unity/Assets/Editor/VisualOverhaulCharacterCapture.cs');s=p.read_text();old='''                                Shot(sex+"_polo_threequarter",hero.transform.TransformPoint(new Vector3(.7f,1.38f,1.75f)),hero.transform.TransformPoint(new Vector3(0,1.30f,0)),24,900,900);''';new=old+'''
                                if(sex=="female") {
                                    Shot("female_skirt_front",hero.transform.TransformPoint(new Vector3(0,.92f,1.9f)),hero.transform.TransformPoint(new Vector3(0,.84f,0)),24,900,900);
                                    Shot("female_skirt_threequarter",hero.transform.TransformPoint(new Vector3(.8f,.95f,1.75f)),hero.transform.TransformPoint(new Vector3(0,.84f,0)),24,900,900);
                                }''';assert old in s;s=s.replace(old,new);old='''                                    audit.Add($"Garment swatch {sex}: requested={swatch}, material={applied}");''';new=old+'''
                                    if(sex=="female") {
                                        hero.SetKit(null,swatch,null);yield return Frames(2);
                                        Shot("female_skirt_swatch_"+swatch,hero.transform.TransformPoint(new Vector3(.6f,.95f,1.8f)),hero.transform.TransformPoint(new Vector3(0,.84f,0)),24,900,900);
                                        if(!hero.TryGetKitColour(MatchHeroLook.RoleShorts,out var skirtColour) || !hero.TryGetKitColour(MatchHeroLook.RoleShortsBand,out var bandColour))throw new InvalidOperationException("Skirt palette roles missing");
                                        audit.Add($"Skirt swatch: requested={swatch}, skirt={skirtColour}, waistband={bandColour}");
                                    }''';assert old in s;s=s.replace(old,new);p.write_text(s)
