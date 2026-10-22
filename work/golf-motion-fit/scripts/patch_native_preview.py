from pathlib import Path
import shutil
W=Path(__file__).resolve().parents[1];R=W.parents[1];D=W/'candidate/GolfArcade/Unity';D.mkdir(parents=True,exist_ok=True)
for name in ['CharacterModelPreview.swift','LockerStudio.swift']:
 shutil.copy2(R/'GolfArcade/Unity'/name,D/name)
p=D/'CharacterModelPreview.swift';s=p.read_text().replace('case \"Kit_Shirt\", \"Kit_GolfGlove\":', 'case \"Kit_Shirt\":')
s=s.replace('context.coordinator.update(player, sport: outfitSport)','context.coordinator.update(player, sport: idleSport ?? outfitSport)')
s=s.replace('previous = nil; update(equipped); clubKey = key','previous = nil; update(equipped, sport: outfitSport); clubKey = key')
s=s.replace('guard hero != nil else { return }\n            practiceTimer', '''guard hero != nil else { return }
            if outfitSport == .golf, let asset=MatchHero.asset(female:previous?.standardFemale ?? false,golf:true),asset.manifest.isGolf {
                play(MenuMotion(kind:.clipOnce("golfPractice"),lead:0,fadeIn:0.12,fadeOut:0.3));return
            }
            practiceTimer''')
s=s.replace('stopLink(); rig?.detach(); rig = nil\n            motion = m', '''stopLink(); if outfitSport != .golf { rig?.detach() }; rig = nil
            motion = m
            if m == nil, outfitSport == .golf,let root=hero,let asset=MatchHero.asset(female:root.value(forKey:"heroFemale") as? Bool ?? false,golf:true),asset.manifest.isGolf,let r=HeroRig(root:root,asset:asset) { r.attach();r.apply(.ready,at:0);rig=r;return }''')
s=s.replace('stopLink(); rig?.detach(); rig = nil; motion = nil','stopLink(); if rig?.data.isGolf == true { rig?.apply(.ready,at:0) } else { rig?.detach() }; rig = nil; motion = nil')
s=s.replace('guard let sport else { return }','''guard let sport else { return }
            if sport == .golf, let asset=MatchHero.asset(female:previous?.standardFemale ?? false,golf:true),asset.manifest.isGolf {
                play(animate ? .ready : nil);return
            }''')
s=s.replace('if sport == .golf { root.addChildNode(golfClub(player: p)) }','if sport == .golf && !asset.manifest.isGolf { root.addChildNode(golfClub(player: p)) }')
s=s.replace('struct Hero { var container: SCNNode; var player: Player;','struct Hero { var container: SCNNode; var player: Player; var sport: MultiplayerSport;')
s=s.replace('if old?.player != player {','if old?.player != player || old?.sport != state.sport {')
s=s.replace('guard let root = MatchHero.build(player), let asset = MatchHero.asset(female:player.standardFemale),','guard let root = MatchHero.build(player, sport:state.sport == .golf ? .golf:.tennis), let asset = MatchHero.asset(female:player.standardFemale,golf:state.sport == .golf),')
s=s.replace('Hero(container:holder,player:player,motion:motion','Hero(container:holder,player:player,sport:state.sport,motion:motion')
p.write_text(s)
p=D/'LockerStudio.swift';s=p.read_text().replace('LockerThumbs.key(player, slot: item.slot, item: item)','LockerThumbs.key(player, slot: item.slot, item: item, sport: sport)').replace('LockerThumbs.image(player, slot: item.slot, item: item)','LockerThumbs.image(player, slot: item.slot, item: item, sport: sport)')
s=s.replace('static func key(_ p: Player, slot: LockerSlot, item: LockerItem) -> String {','static func key(_ p: Player, slot: LockerSlot, item: LockerItem, sport: Sport = .tennis) -> String {')
s=s.replace('"\\(p.standardFemale)|\\(p.skinHex)|','"\\(sport.rawValue)|\\(p.handedness.rawValue)|\\(p.standardFemale)|\\(p.skinHex)|')
s=s.replace('static func image(_ p: Player, slot: LockerSlot, item: LockerItem) -> UIImage? {','static func image(_ p: Player, slot: LockerSlot, item: LockerItem, sport: Sport = .tennis) -> UIImage? {').replace('let k = key(p, slot: slot, item: item)','let k = key(p, slot: slot, item: item, sport: sport)')
s=s.replace('c.update(p, sport: item.sports == [.golf] ? .golf : .tennis)','c.update(p, sport: sport)')
p.write_text(s)
# An explicit LH still pose is needed for thumbnails / reduced motion as well.
p=D/'MatchHeroData.swift';s=p.read_text().replace('return root\n    }\n}', 'if m.isGolf,let rig=HeroRig(root:root,asset:asset) { rig.attach();rig.apply(.ready,at:0) }\n        return root\n    }\n}')
p.write_text(s)
p=D/'MatchHeroMotion.swift';s=p.read_text().replace('root.addChildNode(skeleton)','if data.isGolf { root.childNode(withName:"skeleton",recursively:false)?.removeFromParentNode() }\n        root.addChildNode(skeleton)',1)
s=s.replace('let samples=motion.samples(data,at:time)','''let samples=motion.samples(data,at:time)
        if data.isGolf,let selected=samples.max(by:{$0.2 < $1.2})?.0.info.equipment {
            for part in asset.manifest.parts { if let equipment=part.equipment { root.childNode(withName:part.name,recursively:true)?.isHidden=equipment != selected } }
        }''')
s=s.replace('data.sample(t)','data.sample(clip.info.loop ? t.truncatingRemainder(dividingBy:clip.length):t)')
p.write_text(s)
print('NATIVE_PREVIEW_CANDIDATE_READY')
