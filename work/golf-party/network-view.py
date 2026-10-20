from pathlib import Path
p=Path('Unity/Assets/Scripts/Game/GolfGame.Network.cs');s=p.read_text()
s=s.replace('using System.Linq;', 'using System.Linq;\nusing System.Collections.Generic;\nusing GolfArcade.Profile;\nusing GolfArcade.Tennis;\nusing GolfArcade.UI;')
s=s.replace('bool networkConfigured;', '''bool networkConfigured;
        readonly Dictionary<int,GolferView> partyGolfers=new();
        readonly Dictionary<int,long> partyEmotes=new();
        GolferView soloGolfer;
        long resultShot=-1;
        Vector3 partyOrigin;
        bool wasNetworkResult;
        NetworkConfiguration partyConfiguration;''')
a='public void ConfigureNetwork(NetworkConfiguration c){networkConfigured=true;networkHole=-1;networkTurn=-1;networkClub=-1;networkCardRevision=-1;networkShot=-1;Swing.Armed=false;}'
b='''public void ConfigureNetwork(NetworkConfiguration c) {
            networkConfigured=true;networkHole=-1;networkTurn=-1;networkClub=-1;networkCardRevision=-1;networkShot=-1;resultShot=-1;Swing.Armed=false;
            partyConfiguration=c;
            if(!soloGolfer)soloGolfer=golfer;
            soloGolfer.SetVisible(false);
            foreach(var old in partyGolfers.Values)if(old)Destroy(old.gameObject);
            partyGolfers.Clear();partyEmotes.Clear();
            foreach(var p in c.participants.Where(p=>p.seat>=0)) {
                var look=new CharacterLook {Body=p.female?1:0,Skin=p.loadout?.skinHex??"",Shirt=p.loadout?.shirtHex??"",Shorts=p.loadout?.shortsHex??""};
                var style=GolferView.Look.Player;style.Hero=GolferStyle.HeroOf(look);
                var model=GolferView.CreatePlayer(transform,style);model.name="Party golfer · "+p.name;
                partyGolfers[p.seat]=model;partyEmotes[p.seat]=0;model.Perform("Idle");
            }
            golfer=partyGolfers.Values.First();
        }
        public bool CanNetworkEmote(int seat) {
            var n=SportsMultiplayer.Instance;var s=n?.GolfState;
            var player=s?.golfers.FirstOrDefault(p=>p.seat==seat);
            return n && n.Running && player!=null && !player.dnf && !s.paused && !s.complete && s.phase!="intro"
                && (seat!=s.turn || s.phase=="result") && s.time-player.emoteAt>=1.5 && n.Configuration.Controls(n.Configuration.localID,seat);
        }
        public bool PlayNetworkEmote(int seat,int slot) {
            if(slot<0||slot>2||!CanNetworkEmote(seat))return false;
            SportsMultiplayer.Instance.Submit(new NetworkInput {action="emote",value=slot,actorSeat=seat});return true;
        }
        void PlaceParty(NetworkGolfState state,Vector3 direction) {
            var right=Vector3.Cross(Vector3.up,direction).normalized;int index=0;
            foreach(var p in state.golfers) {
                if(!partyGolfers.TryGetValue(p.seat,out var model))continue;
                model.SetVisible(!p.dnf);if(p.dnf)continue;
                if(p.seat!=state.turn) {
                    // A semicircle behind the shot, clear of both the club and the ball path.
                    float side=index==0?-2.4f:index==1?2.4f:0;
                    var at=partyOrigin+right*side-direction*(index==2?3.4f:1.9f);index++;
                    model.transform.position=HoleView.ToWorld(HoleView.ToCourse(at));
                    model.transform.rotation=Quaternion.LookRotation(direction);
                    if(model.Performing==null)model.Perform("Idle");
                }
                if(p.emoteID>partyEmotes[p.seat]) {
                    partyEmotes[p.seat]=p.emoteID;
                    var participant=partyConfiguration.participants.First(x=>x.seat==p.seat);
                    var ids=TennisEmotes.Normalize(participant.loadout?.emotes);
                    if(p.emoteSlot>=0&&p.emoteSlot<3)model.Perform(TennisEmotes.ExportName(ids[p.emoteSlot]),(float)Math.Max(0,state.time-p.emoteAt),false);
                }
            }
        }'''
assert a in s;s=s.replace(a,b)
s=s.replace('bool myTurn=net.LocalSeat==state.turn', 'bool myTurn=net.Configuration.Controls(net.Configuration.localID,state.turn)')
s=s.replace('if(networkCardRevision!=state.revision', 'golfer=partyGolfers[state.turn];\n            if(networkCardRevision!=state.revision')
s=s.replace('if(active.card[i]>0)Card.Record', 'if(active.card[i]>0)networkCard.Record')
s=s.replace('if(networkTurn!=state.turn){networkTurn=state.turn;golfer.Settle();rig.SnapNext();}', '''if(networkTurn!=state.turn){networkTurn=state.turn;golfer.Settle();golfer.SetClub(club,false);rig.SnapNext();}
            NativeShotReady=myTurn;
            if(state.phase=="aim")partyOrigin=HoleView.ToWorld(ballAt);
            if(state.phase!="result" && wasNetworkResult) {wasNetworkResult=false;if(shotResultPanel)shotResultPanel.gameObject.SetActive(false);hud.ShowPlayHud(true);}
            PlaceParty(state,AimDirection());''')
s=s.replace('} else {\n                PlaceBall', '''} else if(state.phase=="result" && shot!=null && shot.id==state.shotID) {
                Current=State.Result;wasNetworkResult=true;
                golfer.transform.rotation=Quaternion.LookRotation(AimDirection());
                if(resultShot!=shot.id) {
                    resultShot=shot.id;golfer.Perform("Idle");
                    hud.HideLanding();hud.HideShotStats();hud.ShowPlayHud(false);aimLine.positionCount=0;effects.ClearTracer();
                    if(!shotResultPanel)shotResultPanel=ShotResultPanel.Create(transform,rig.Camera);
                    string outcome=shot.holed?"IN THE HOLE!":shot.penalty>0?"PENALTY +"+shot.penalty:shot.lie.ToUpperInvariant();
                    ShotResultTitle=outcome;
                    ShotStatistics=$"Carry {shot.carry:F0} yd · Roll {shot.roll:F0} yd · Total {shot.carry+shot.roll:F0} yd";
                    shotResultPanel.ShowGolf(NetworkName(shot.seat),outcome,shot.carry,shot.roll,shot.apex,
                        new CoursePoint(shot.restX,shot.restD).DistanceTo(hole.Pin),shot.club==(int)GolfClub.Putter,shot.holed);
                    rig.SnapNext();
                }
                shotResultPanel.SetCountdown((float)Math.Max(0,state.resultUntil-state.time),"NEXT PLAYER");
                rig.FrameGolfParty(partyOrigin,AimDirection(),true);
            } else {
                PlaceBall''')
s=s.replace('rig.FrameAddress(ball.position,AimDirection(),hole.LieAt(ballAt)==CourseLie.Green);','rig.FrameGolfParty(ball.position,AimDirection(),false);')
s=s.replace('hud.SetScore(Card.Total,Card.ToPar,holeStrokes);','hud.SetScore(networkCard.Total,networkCard.ToPar,holeStrokes);')
s=s.replace('RefreshControls();rig.ApplyFrame();return true;', 'RefreshControls();rig.ApplyFrame();return true;')
p.write_text(s)
p=Path('Unity/Assets/Scripts/Game/CameraRig.cs');s=p.read_text();a='        public void FrameShotResult()';s=s.replace(a,'''        public void FrameGolfParty(Vector3 origin,Vector3 direction,bool result) {
            RestoreFov();ResetZoom();direction=GroundDirection(direction);
            float back=Camera.aspect<1.2f?10.5f:7.5f;
            var center=origin-direction*1.3f;
            targetPosition=center+direction*(result?back:-back)+Vector3.up*3.4f;
            targetLookAt=center+Vector3.up*.85f;
            cueUp=Vector3.up;targetRoll=0;shotFrame=povThisFrame=false;
            positionLag=.22f;lookLag=.22f;ClearGround();
        }

'''+a);p.write_text(s)
print('Party characters and result camera implemented')
