from pathlib import Path
import shutil
W=Path(__file__).resolve().parents[1];R=W.parents[1];D=W/'candidate/Unity/Assets/Scripts/Game';D.mkdir(parents=True,exist_ok=True)
for name in ['GolferView.cs','GolfGame.cs','GolfGame.Network.cs']:
 shutil.copy2(R/'Unity/Assets/Scripts/Game'/name,D/name)
p=D/'GolferView.cs';s=p.read_text().replace('using GolfArcade.Course;','using GolfArcade.Course;\nusing GolfArcade.Shot;')
s=s.replace('GameObject modelGo;','GameObject modelGo;\n        GolfHeroMotion golfMotion;\n        GolfClub visualClub = GolfClub.Driver; CourseLie visualLie = CourseLie.Tee; float visualPower = 1;')
s=s.replace('hasModel = false; body = null; modelGo = null;','hasModel = false; body = null; modelGo = null; golfMotion = null; standardArms = null; standardGrip = null;')
s=s.replace('var model = Resources.Load<GameObject>(GolferStyle.ModelPath);','var dedicated = Resources.Load<GameObject>("Golf/GolfHero_" + (GolferStyle.Body == GolferStyle.BodyKind.Female ? "Female" : "Male"));\n            if (dedicated) { BuildGolf(dedicated); return; }\n            var model = Resources.Load<GameObject>(GolferStyle.ModelPath);')
pos=s.index('        bool BuildModel(')
s=s[:pos]+'''        void BuildGolf(GameObject prefab) {
            modelGo = Instantiate(prefab, transform); modelGo.name = "Articulated golf hero";
            modelGo.transform.localPosition = Vector3.zero; modelGo.transform.localRotation = Quaternion.identity;
            modelGo.transform.localScale = Vector3.one * MetresToYards;
            var look = modelGo.GetComponent<GolfArcade.Tennis.MatchHeroLook>();
            look.SetSkin(GolferStyle.SkinColor);modelGo.GetComponent<GolfHeroAppearance>().Apply(GolferStyle.Outfit);
            golfMotion = modelGo.GetComponent<GolfHeroMotion>(); golfMotion.Initialize(NativeSportsSession.Left);
            FloatingHandsPreview = false; hasModel = true;
            VisualContext(visualClub, visualLie, visualPower);
        }
        public void VisualContext(GolfClub selectedClub, CourseLie lie, float power) {
            visualClub=selectedClub;visualLie=lie;visualPower=power;
            if (!golfMotion) return;
            golfMotion.Context(selectedClub, lie, power);
            // The selected equipment's authored impact point is aligned to the
            // same existing stance anchor. Shot calculations remain unchanged.
            var entry=golfMotion.Selected;float shown=golfMotion.TimeShown;
            golfMotion.Show(entry.impact);var contact=modelGo.GetComponent<GolfHeroDefinition>().contact;
            modelGo.transform.localPosition+=new Vector3(0,0,.75f)-transform.InverseTransformPoint(contact.position);
            golfMotion.Show(shown);
        }

'''+s[pos:]
s=s.replace('transform.rotation = Quaternion.LookRotation(side, Vector3.up);\n            transform.localScale = new Vector3(1,1,NativeSportsSession.Left ? -1 : 1);','transform.rotation = Quaternion.LookRotation(golfMotion && NativeSportsSession.Left ? -side : side, Vector3.up);\n            transform.localScale = golfMotion ? Vector3.one : new Vector3(1,1,NativeSportsSession.Left ? -1 : 1);')
s=s.replace('shownLoad = load;\n            if','shownLoad = load;\n            if (golfMotion) { golfMotion.ShowLoad(load); return; }\n            if')
s=s.replace('swingThrough = 0;\n            if','swingThrough = 0;\n            if (golfMotion) return golfMotion.Strike();\n            if')
s=s.replace('phase = 0; loadTarget = 0;\n            if','phase = 0; loadTarget = 0;\n            if (golfMotion) { golfMotion.Settle(); return; }\n            if')
s=s.replace('if (hasModel) UpdateModel(); else UpdateFigure();','if (golfMotion) golfMotion.Tick(Time.deltaTime); else if (hasModel) UpdateModel(); else UpdateFigure();')
p.write_text(s)
p=D/'GolfGame.cs';s=p.read_text().replace('golfer.ShowLoad((float)load);','golfer.VisualContext(club, hole.LieAt(ballAt), (float)load);\n            golfer.ShowLoad((float)load);').replace('float toBall = golfer.Strike();','golfer.VisualContext(club, lie, (float)impact.Power);\n            float toBall = golfer.Strike();').replace('golfer.ShowLoad(power);','golfer.VisualContext(club, hole.LieAt(ballAt), power);\n            golfer.ShowLoad(power);');p.write_text(s)
p=D/'GolfGame.Network.cs';s=p.read_text().replace('golfer.Strike();','golfer.VisualContext((GolfClub)shot.club, hole.LieAt(ballAt), .7f);golfer.Strike();');p.write_text(s)
print('UNITY_GAME_CANDIDATE_READY')
