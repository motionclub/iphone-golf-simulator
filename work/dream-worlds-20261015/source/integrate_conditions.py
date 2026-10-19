from pathlib import Path
import re,shutil
root=Path.cwd()
def edit(p,old,new):
 p=root/p;s=p.read_text();assert old in s,(str(p),old[:90]);p.write_text(s.replace(old,new))
shutil.copy('work/dream-worlds-20261015/source/DreamConditions.cs','Unity/Assets/Scripts/Course/DreamConditions.cs')
shutil.copy('work/dream-worlds-20261015/source/DreamVisibility.cs','Unity/Assets/Scripts/Environment/DreamVisibility.cs')
p=Path('Unity/Assets/Scripts/Course/RoundEvents.cs');s=p.read_text();s=s.replace('The green is hidden: trust the flag and the map','Dense fog: play local ground; follow the compass bearing').replace('The wind shifts every shot','Wind changes between equivalent turns')
s=s.replace('if (!Enabled || (!twists && !world && !challenges)) return None;', '''#if UNITY_EDITOR || DEVELOPMENT_BUILD
            if (!Enabled) return None;
#endif
            world = true; // v5 ignores retired player world/weather overrides.''')
s=s.replace("flags.IndexOf('w') >= 0",'true')
s=s.replace('if (colon < 1) return None;','if (colon < 1) return Deal(seed, false, true, false);')
s=s.replace('(weatherOn ? "w" : "s") + (challengesOn', '(weatherOn ? "v5w" : "s") + (challengesOn')
a=s.index('            double u = Rng(holeIndex, 1).NextDouble();');b=s.index('\n        }',a);s=s[:a]+'            return DreamConditions.WeatherFor(Seed, holeIndex);'+s[b:]
a=s.index('            if (!weatherOn || shot < 1) return null;');b=s.index('\n        }',a);s=s[:a]+'            return null; // Stable hole identity; only bounded gust intensity changes at turn boundaries.'+s[b:]
s=s.replace('public PlayRules RulesFor(Weather weather)','public PlayRules RulesFor(Weather weather, Sky sky = Sky.Rain)').replace('weather.Bend(r);','weather.Bend(r, sky);')
s=s.replace('public static void Bend(this Weather w, PlayRules r)','public static void Bend(this Weather w, PlayRules r, Sky sky = Sky.Rain)').replace('r.FairwayDrag *= 1.6;\n            r.GreenDrag *= 1.3;\n            r.Bounce *= 0.7;', 'r.FairwayDrag *= sky == Sky.Snow ? 1.85 : sky == Sky.Ash ? 1.2 : 1.6;\n            r.GreenDrag *= sky == Sky.Snow ? 1.5 : sky == Sky.Ash ? 1.12 : 1.3;\n            r.Bounce *= sky == Sky.Snow ? .55 : sky == Sky.Ash ? .85 : .7;')
p.write_text(s)
for p in ['Unity/Assets/Scripts/Game/GolfGame.Events.cs','Unity/Assets/Scripts/Game/GolfGame.Challenges.cs']:
 s=Path(p).read_text().replace('worldWanted = world','worldWanted = true').replace('bool twistsWanted, worldWanted;','bool twistsWanted, worldWanted = true;').replace('events.RulesFor(weather)','events.RulesFor(weather, Weathers.SkyOf(hole))').replace('events.RulesFor(w)','events.RulesFor(w, Weathers.SkyOf(hole))');Path(p).write_text(s)
p=Path('Unity/Assets/Scripts/Multiplayer/NetworkGolfRound.cs');s=p.read_text().replace('int seat,strokes,club,total;','int seat,strokes,club,total,swings;').replace('p.strokes=0;p.holed','p.strokes=0;p.swings=0;p.holed').replace('swingsOnHole++;','swingsOnHole++;p.swings++;').replace('events.RulesFor(weather)','events.RulesFor(weather, Weathers.SkyOf(hole))').replace('events.RulesFor(turned)','events.RulesFor(turned, Weathers.SkyOf(hole))')
s=s.replace('events.GustBefore(State.hole,swingsOnHole,holeWind,weather)','events.GustBefore(State.hole,State.golfers.First(g=>g.seat==State.turn).swings,holeWind,weather)')
s=s.replace('            ShotEvents();\n','').replace('            LineUp(eligible.First(p=>p.seat==State.turn),course.Holes[State.hole]);','            State.windSpeed=holeWind.SpeedMPH;State.windDirection=holeWind.DirectionDegrees;\n            ShotEvents();\n            LineUp(eligible.First(p=>p.seat==State.turn),course.Holes[State.hole]);');p.write_text(s)
# Native and network ingress no longer honor retired weather flags.
edit('Unity/Assets/Scripts/Game/NativeSportsSession.cs','!m.noTwists,!m.noWeather,!m.noChallenges','!m.noTwists,true,!m.noChallenges')
edit('Unity/Assets/Scripts/Multiplayer/SportsMultiplayer.cs','world:!c.weatherOff','world:true')
edit('Unity/Assets/Scripts/Multiplayer/MultiplayerProtocol.cs','Version=4','Version=5')
edit('GolfArcade/Multiplayer/MultiplayerModels.swift','static let version = 4','static let version = 5')
p=Path('GolfArcade/Unity/SportsSession.swift');s=p.read_text();s=re.sub(r'    var golfWeather = .*?\n    }\n','',s,flags=re.S);s=s.replace(', "noWeather": tutorial || (daily == 0 && !golfWeather)','');p.write_text(s)
p=Path('GolfArcade/Unity/TennisMapScreen.swift');s=p.read_text();s='\n'.join(l for l in s.split('\n') if 'toggle("golf-weather"' not in l);s=s.replace('weather: session.golfWeather, ','').replace('twists: Bool, weather: Bool, challenges: Bool','twists: Bool, challenges: Bool');s=s.replace('        if !twists && !weather && !challenges { return "Classic golf: no twists, clear skies" }\n','').replace('weather ? "storms, fog, gusts and moving obstacles" : "clear skies"','"Automatic weather · EST day/night"');p.write_text(s)
p=Path('GolfArcade/Unity/IslandScreens.swift');s=p.read_text();s='\n'.join(l for l in s.split('\n') if 'case "golfWeather"' not in l and 'choices("Weather & hazards"' not in l);p.write_text(s)
p=Path('GolfArcade/Unity/TennisMenu.swift');s=p.read_text().replace('"golfTwists", "golfWeather",','"golfTwists",');s='\n'.join(l for l in s.split('\n') if 'case "golf-weather"' not in l and 'case "golfWeather"' not in l);s=s.replace('id.hasPrefix("net-twists-") || id.hasPrefix("net-weather-")','id.hasPrefix("net-twists-")');s=re.sub(r'try service.setGolfEvents\(twists:.*?\n\s*weather:.*?\)', 'try service.setGolfEvents(twists: id.hasSuffix("-on"))',s);p.write_text(s)
p=Path('GolfArcade/Multiplayer/MultiplayerService.swift');s=p.read_text();s='\n'.join(l for l in s.split('\n') if 'lobby?.weatherOff = sport' not in l);s=s.replace('func setGolfEvents(twists: Bool, weather: Bool)','func setGolfEvents(twists: Bool)').replace('; SportsSession.shared.golfWeather = weather','').replace('; lobby?.weatherOff = weather ? nil : true','').replace(', weatherOff: lobby.weatherOff','');p.write_text(s)
# Remove obsolete wire fields (unknown legacy JSON keys are ignored).
for path in ['GolfArcade/Multiplayer/MultiplayerModels.swift']:
 p=Path(path);p.write_text('\n'.join(l for l in p.read_text().split('\n') if 'var weatherOff:' not in l))
edit('Unity/Assets/Scripts/Multiplayer/MultiplayerProtocol.cs','bool twistsOff,weatherOff;','bool twistsOff;')
edit('Unity/Assets/Scripts/Game/NativeSportsSession.cs','bool noTwists,noWeather,noChallenges;','bool noTwists,noChallenges;')
