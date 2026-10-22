from pathlib import Path
def edit(file,a,b):
 p=Path(file);s=p.read_text();assert a in s,(file,a[:80]);p.write_text(s.replace(a,b,1))
p='Unity/Assets/Scripts/Multiplayer/MultiplayerProtocol.cs'
edit(p,'public string[] emotes;', 'public string[] emotes; public string skinHex,shirtHex,shortsHex;')
edit(p,'public string id,name;', 'public string id,name,controllerID;')
edit(p,'public int Seat(string id)=>','''public bool Controls(string device, int seat) => participants != null && participants.Any(p=>p.seat==seat && p.connected && (p.id==device || (sport=="golf" && device==hostID && p.controllerID==device)));
        public int Seat(string id)=>''')
edit(p,'&& participants.All(p=>p.seat>=-1','&& participants.All(p=>string.IsNullOrEmpty(p.controllerID) || (sport=="golf" && p.controllerID==hostID && p.id!=hostID))\n            && participants.All(p=>p.seat>=-1')
edit(p,'public const int Version=2;', 'public const int Version=3;')
edit(p,'public int club;', 'public int club; public int actorSeat=-1;')
p='Unity/Assets/Scripts/Multiplayer/NetworkGolfRound.cs'
edit(p,'public int seat,strokes,club,total;', 'public int seat,strokes,club,total; public int emoteSlot=-1; public long emoteID; public double emoteAt=-100;')
edit(p,'windDirection,presentationUntil;', 'windDirection,presentationUntil,resultUntil;')
edit(p,'public readonly NetworkGolfState State;', 'public const double ResultSeconds=3;\n        public readonly NetworkGolfState State;')
edit(p,'if(p==null||p.dnf||p.holed||State.complete||State.paused||State.turn!=seat||State.phase!="aim"||input==null||!input.Valid||input.time>hostTime+.05||input.time<hostTime-.5)return false;', '''if(p==null||p.dnf||State.complete||State.paused||input==null||!input.Valid||input.time>hostTime+.05||input.time<hostTime-.5)return false;
            if(input.action=="emote") {
                if(State.phase=="intro" || (State.turn==seat && State.phase!="result") || input.value<0 || input.value>2 || input.value!=Math.Floor(input.value) || State.time-p.emoteAt<1.5 || input.eventID<=lastEvent[seat])return false;
                lastEvent[seat]=input.eventID;p.emoteSlot=(int)input.value;p.emoteID++;p.emoteAt=State.time;State.revision++;return true;
            }
            if(p.holed || State.turn!=seat || State.phase!="aim")return false;''')
edit(p,'if(State.phase=="flight" && State.time>=State.shot.start+State.shot.duration+2) {','''if(State.phase=="flight" && State.time>=State.shot.start+State.shot.duration) {
                State.phase="result";State.resultUntil=State.time+ResultSeconds;State.revision++;
            } else if(State.phase=="result" && State.time>=State.resultUntil) {''')
p='Unity/Assets/Scripts/Multiplayer/SportsMultiplayer.cs'
edit(p,'public int LocalSeat=>Configuration?.Seat(Configuration.localID)??-1;', '''public int LocalSeat => Configuration==null ? -1 : GolfState!=null && Configuration.Controls(Configuration.localID,GolfState.turn) ? GolfState.turn : Configuration.Seat(Configuration.localID);''')
edit(p,'var seat=Configuration.Seat(p.sender);if(seat<0)return;', 'var seat=Configuration.Seat(p.sender);if(seat<0)return;')
edit(p,'ApplyInput(seat,value);break;', '''if(value!=null && value.actorSeat>=0) {
                        if(!Configuration.Controls(p.sender,value.actorSeat))return;
                        seat=value.actorSeat;
                    }
                    ApplyInput(seat,value);break;''')
edit(p,'if(!Running||LocalSeat<0||input==null||!input.Valid)return;', '''if(!Running||LocalSeat<0||input==null||!input.Valid)return;
            int actor=input.actorSeat>=0?input.actorSeat:LocalSeat;
            if(!Configuration.Controls(Configuration.localID,actor))return;
            input.actorSeat=actor;''')
edit(p,'if(IsHost){ApplyInput(LocalSeat,input);return;}', 'if(IsHost){ApplyInput(actor,input);return;}')
edit(p,'case "emote":\n', '''case "golfEmote":
                    Instance.Submit(new NetworkInput {action="emote",value=m.value,actorSeat=(int)m.value2});return true;
                case "emote":
''')
p='Unity/Assets/Scripts/Game/GolferView.cs'
edit(p,'public static GolferView CreateSpectator(Transform parent, Look look)', '''public static GolferView CreatePlayer(Transform parent, Look look)
        {
            var go = new GameObject("Party golfer"); go.transform.SetParent(parent, false);
            var v = go.AddComponent<GolferView>(); v.own = look; v.ApplyStyle(); return v;
        }

        public static GolferView CreateSpectator(Transform parent, Look look)''')
p='Unity/Assets/Scripts/Game/GolfGame.Results.cs'
edit(p,': .5f;', ': 3f;')
# Solo screen uses the same animated card; timer cannot be bypassed with a stray touch.
p='Unity/Assets/Scripts/Game/GolfGame.cs'
edit(p,'if (stateTime >= ResultReactionSeconds || (stateTime >= ResultSkipAfter && Input.GetMouseButtonDown(0))) ContinueShotResult();','if (stateTime >= Mathf.Max(3f,ResultReactionSeconds)) ContinueShotResult();')
print('Authority and input routing implemented')
