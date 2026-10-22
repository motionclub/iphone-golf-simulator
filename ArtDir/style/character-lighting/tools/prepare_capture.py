"""Install the supplied capture test plus diagnostics in a scratch Unity project.
CHARLIGHT_QUICK=1: Resort + hole 7 Clear, four normal sport heroes.
CHARLIGHT_ALL=1: every selectable golf hole x all five weather states.
Other runs preserve the supplied 44-shot matrix. All variants capture a same-frame
original-shader-lighting baseline (VISUAL_HERO_LIGHTING=0 path) alongside the after.
"""
from pathlib import Path
import sys
src=Path(__file__).resolve().parent
assert Path(sys.argv[1]).resolve()!=src.parents[3]/'Unity', 'Capture tests must be installed in a scratch clone'
dst=Path(sys.argv[1])/'Assets/Tests/PlayMode';dst.mkdir(parents=True,exist_ok=True)
s=(src/'CharLightCaptureTests.cs.txt').read_text().replace('using System.IO;','using System.IO;\nusing System.Linq;')
a=s.index('            // hero-only mask pass');b=s.index('            File.AppendAllText',a)
s=s[:a]+'''            CharLightDiagnostics.Capture(cam, $"{Out}/{name}.mask.png", hero);
'''+s[b:]
s=s.replace('cam.targetTexture = rt; cam.aspect = w / (float)h; cam.Render();','''cam.targetTexture = rt; cam.aspect = w / (float)h; cam.Render();
            float lighting=Shader.GetGlobalFloat("_HeroLightingEnabled"),fill=Shader.GetGlobalFloat("_HeroPresentationFill");
            // Both images use the same geometry, pose, camera, post, weather and light state.
            if(lighting>.5f) {
                Shader.SetGlobalFloat("_HeroLightingEnabled",0);Shader.SetGlobalFloat("_HeroPresentationFill",.12f);
                cam.Render();var old=RenderTexture.active;RenderTexture.active=rt;
                var baseline=new Texture2D(w,h,TextureFormat.RGB24,false);baseline.ReadPixels(new Rect(0,0,w,h),0,0);baseline.Apply();
                Directory.CreateDirectory(Out+"/paired-before");File.WriteAllBytes($"{Out}/paired-before/{name}.png",baseline.EncodeToPNG());Object.Destroy(baseline);RenderTexture.active=old;
                Shader.SetGlobalFloat("_HeroLightingEnabled",lighting);Shader.SetGlobalFloat("_HeroPresentationFill",fill);cam.Render();
            }''')
s=s.replace('new[] { TennisVenueKind.Resort, TennisVenueKind.Skyscraper, TennisVenueKind.Volcano }','(System.Environment.GetEnvironmentVariable("CHARLIGHT_QUICK")=="1" ? new[] {TennisVenueKind.Resort} : new[] { TennisVenueKind.Resort, TennisVenueKind.Skyscraper, TennisVenueKind.Volcano })')
needle='            foreach (var female in new[] { false, true })\n            foreach (var (number, w) in shots)'
s=s.replace(needle,'''            if(System.Environment.GetEnvironmentVariable("CHARLIGHT_QUICK")=="1")shots=new[] {(7,Weather.Clear)};
            else if(System.Environment.GetEnvironmentVariable("CHARLIGHT_ALL")=="1")shots=GolfArcade.Course.Course.All().SelectMany(c=>c.Holes).SelectMany(h=>System.Enum.GetValues(typeof(Weather)).Cast<Weather>().Select(w=>(h.Number,w))).ToArray();
            if(System.Environment.GetEnvironmentVariable("CHARLIGHT_WEATHER_ONLY")=="1")shots=shots.Where(s=>s.w!=Weather.Clear).ToArray();
'''+needle)
s=s.replace('                yield return Wait(() => game.Current == GolfGame.State.Aim, 60);', '                yield return Wait(() => { if(game.Current!=GolfGame.State.Aim)game.SkipPresentation(); return game.Current==GolfGame.State.Aim; }, 60);')
s=s.replace('                yield return new WaitForSecondsRealtime(1.5f);','''                yield return new WaitForSecondsRealtime(1.5f);
                Assert.AreEqual(number,game.CurrentHole.Number,"Capture must use the requested hole");
                Assert.AreEqual(w,Object.FindFirstObjectByType<WeatherView>().Weather,"Capture must use requested weather");''')
s=s.replace('        [UnityTest, Timeout(900000)] public IEnumerator C_Hub()\n        {','''        [UnityTest, Timeout(900000)] public IEnumerator C_Hub()
        {
            if(System.Environment.GetEnvironmentVariable("CHARLIGHT_QUICK")=="1")yield break;''')
s=s.replace('            CharLightDiagnostics.Capture(cam,', '            FreezeForLookDev(name,hero);\n            CharLightDiagnostics.Capture(cam,')
pos=s.rfind('    }')
s=s[:pos]+(src/'CrossLookDev.cs.fragment').read_text()+s[pos:]
(dst/'CharLightCaptureTests.cs').write_text(s)
for n in ['CharLightDiagnostics.cs','CharLightMask.shader','CharLightActivationTests.cs']:(dst/n).write_bytes((src/(n+'.txt')).read_bytes())
