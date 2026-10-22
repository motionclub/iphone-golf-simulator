from pathlib import Path
def edit(file,a,b):
 p=Path(file);s=p.read_text();assert a in s,(file,a[:90]);p.write_text(s.replace(a,b,1))
p='Unity/Assets/Scripts/Game/GolfGame.Native.cs'
edit(p,'[System.Serializable] public sealed class ControllerReading {','''[System.Serializable] public sealed class PartyControllerPlayer {
            public int seat; public string name; public bool controlled,canEmote; public string[] emotes;
        }
        [System.Serializable] public sealed class PartyControllerReading {
            public int turn; public long shotID; public string player,outcome,phase;
            public bool myTurn,shared,putt; public double resultSeconds,carry,roll,apex,total;
            public PartyControllerPlayer[] players;
        }
        [System.Serializable] public sealed class ControllerReading {
            public PartyControllerReading party;''')
edit(p,'            return reading;','''            if(networkConfigured)FillPartyReading(reading);
            return reading;''')
p='Unity/Assets/Scripts/Game/GolfGame.Network.cs'
edit(p,'        string NetworkName(int seat)', '''        void FillPartyReading(ControllerReading reading) {
            var net=SportsMultiplayer.Instance;var state=net?.GolfState;
            if(state==null)return;
            var shot=state.shot;
            reading.party=new PartyControllerReading {
                turn=state.turn,player=NetworkName(state.turn),phase=state.phase,shotID=state.shotID,
                myTurn=net.Configuration.Controls(net.Configuration.localID,state.turn),
                shared=net.Configuration.participants.Any(p=>p.controllerID==net.Configuration.localID),
                resultSeconds=state.phase=="result"?Math.Max(0,state.resultUntil-state.time):0,
                carry=shot?.carry??0,roll=shot?.roll??0,apex=shot?.apex??0,total=(shot?.carry??0)+(shot?.roll??0),
                putt=shot?.club==(int)GolfClub.Putter,
                outcome=shot==null?"":shot.holed?"IN THE HOLE!":shot.penalty>0?"PENALTY +"+shot.penalty:shot.lie.ToUpperInvariant(),
                players=state.golfers.Where(p=>!p.dnf).Select(p=>new PartyControllerPlayer {
                    seat=p.seat,name=NetworkName(p.seat),controlled=net.Configuration.Controls(net.Configuration.localID,p.seat),canEmote=CanNetworkEmote(p.seat),
                    emotes=TennisEmotes.Normalize(net.Configuration.participants.First(n=>n.seat==p.seat).loadout?.emotes)
                }).ToArray()
            };
        }
        string NetworkName(int seat)''')
p='GolfArcade/Unity/GolfController.swift'
edit(p,'    struct Point: Codable', '''    struct PartyPlayer: Codable, Identifiable {
        var seat: Int; var name: String; var controlled: Bool; var canEmote: Bool; var emotes: [String]
        var id: Int { seat }
    }
    struct Party: Codable {
        var turn: Int; var shotID: Int64; var player: String; var outcome: String; var phase: String
        var myTurn: Bool; var shared: Bool; var putt: Bool
        var resultSeconds: Double; var carry: Double; var roll: Double; var apex: Double; var total: Double
        var players: [PartyPlayer]
    }
    var party: Party?
    struct Point: Codable''')
edit(p,'session.golfPhase == "Aim" && !session.paused }','session.golfPhase == "Aim" && !session.paused && (reading.party?.myTurn ?? true) }')
edit(p,'            sectionTitle("CLUB", lines: true)', '''            if let party=reading.party {
                GolfPartyEmoteControls(session:session,party:party).frame(width:424,height:354).position(x:232,y:722)
                    .background(.clear).opacity(party.phase == "result" || !party.myTurn ? 1 : 0)
                    .allowsHitTesting(party.phase == "result" || !party.myTurn)
            }
            sectionTitle("CLUB", lines: true)''')
# Put opaque party controls above club/aim elements, including spectators and reaction window.
edit(p,'        }.buttonStyle(GolfControllerPressStyle())','''        }.overlay {
            if let party=reading.party, party.phase == "result" || !party.myTurn {
                GolfPartyEmoteControls(session:session,party:party).padding(20).frame(width:424,height:410)
                    .background(GolfControllerStyle.blue,in:RoundedRectangle(cornerRadius:24)).position(x:232,y:760)
            }
        }.buttonStyle(GolfControllerPressStyle())''')
# Remove redundant lower layer inserted above.
s=Path(p).read_text();a=s.index('            if let party=reading.party {');b=s.index('            sectionTitle("CLUB", lines: true)',a);s=s[:a]+s[b:];Path(p).write_text(s)
p='GolfArcade/Unity/SportsHome.swift'
s=Path(p).read_text();a=s.index('struct GolfShotResultControls: View {');s=s[:a]+'''struct GolfShotResultControls: View {
    @Bindable var session: SportsSession
    var body: some View {
        if let party=session.golfController.party {
            VStack(spacing:12) {
                Text(party.outcome).font(Club.ui(22,900)).foregroundStyle(.white)
                HStack {
                    stat("CARRY",party.carry); stat("ROLL",party.roll); stat("TOTAL",party.total)
                }
                Text("Next player in \\(Int(ceil(party.resultSeconds)))").font(Club.ui(16,700)).monospacedDigit().foregroundStyle(.white)
                ProgressView(value:max(0,min(1,party.resultSeconds/3))).tint(IslandUI.lime)
            }.accessibilityIdentifier("golf-party-shot-result")
        } else {
            EquippedEmoteControls(title:"YOUR SHOT · EMOTE",ids:session.matchEmotes,
                enabled:!session.paused && session.golfPhase == "Result",notice:"Next shot starts automatically.",identifier:"golf-emote") {
                    session.command("golfEmote",value:Double($0))
                }
        }
    }
    private func stat(_ title:String,_ yards:Double) -> some View {
        VStack { Text(title).font(Club.ui(11,700)); Text("\\(Int(yards.rounded())) yd").font(Club.ui(22,900)).monospacedDigit() }
            .frame(maxWidth:.infinity).foregroundStyle(.white)
    }
}

/// A host can choose any guest sharing this phone; peers only receive controls for their own seat.
struct GolfPartyEmoteControls: View {
    @Bindable var session: SportsSession
    let party: GolfControllerReading.Party
    @State private var selectedSeat: Int = -1
    private var localPlayers: [GolfControllerReading.PartyPlayer] { party.players.filter(\\.controlled) }
    private var selected: GolfControllerReading.PartyPlayer? {
        localPlayers.first { $0.seat == selectedSeat } ?? localPlayers.first { $0.seat == party.turn } ?? localPlayers.first
    }
    var body: some View {
        VStack(alignment:.leading,spacing:14) {
            Text(party.phase == "result" ? "EVERYONE CAN REACT" : "\\(party.player.uppercased())’S TURN")
                .font(Club.ui(20,900)).foregroundStyle(.white)
            if party.shared {
                Text("Pass the phone to \\(party.player) for their shot.").font(Club.ui(14,600)).foregroundStyle(.white)
            }
            if localPlayers.count > 1 {
                Picker("Emote as",selection:Binding(get:{selected?.seat ?? -1},set:{selectedSeat=$0})) {
                    ForEach(localPlayers) { player in Text(player.name).tag(player.seat) }
                }.pickerStyle(.menu).tint(.white).accessibilityIdentifier("golf-emote-player")
            }
            if let selected {
                EquippedEmoteControls(title:selected.name.uppercased(),ids:selected.emotes,
                    enabled:selected.canEmote && !session.paused,notice:selected.canEmote ? "Pick an emote" : "Watch the shot · react after it lands",identifier:"golf-party-emote") { slot in
                        session.command("golfEmote",value:Double(slot),value2:Double(selected.seat))
                    }
            }
        }.accessibilityIdentifier("golf-party-controls")
    }
}
''';Path(p).write_text(s)
print('Phone party controls implemented')
