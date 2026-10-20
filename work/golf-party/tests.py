from pathlib import Path
p=Path('Unity/Assets/Tests/EditMode/MultiplayerRulesTests.cs');s=p.read_text().replace('m.State.shot.duration+2.1','m.State.shot.duration+3.2');idx=s.index('        [Test] public void GolfRejects')
s=s[:idx]+'''        [Test] public void GolfResultGivesThreeSecondsAndFreezesWhenPaused() {
            var m=new NetworkGolfRound(new[]{0,1,2,3},20);
            m.Input(0,Golf(m),0);Step(m,m.State.shot.duration+.05);
            Assert.AreEqual("result",m.State.phase);Assert.AreEqual(0,m.State.turn);
            Assert.That(m.State.resultUntil-m.State.time,Is.InRange(2.94,3.001));
            double until=m.State.resultUntil,time=m.State.time;m.State.paused=true;Step(m,9);
            Assert.AreEqual(time,m.State.time);Assert.AreEqual(until,m.State.resultUntil);
            m.State.paused=false;Step(m,2.8);Assert.AreEqual("result",m.State.phase);
            Step(m,.3);Assert.AreEqual("aim",m.State.phase);Assert.AreEqual(1,m.State.turn);Assert.Null(m.State.shot);
            Step(m,.2);Assert.AreEqual(1,m.State.turn);
        }
        [Test] public void GolfEveryoneCanReactButCannotStealAShotOrExtendResult() {
            var m=new NetworkGolfRound(new[]{0,1,2,3},20);
            Assert.False(m.Input(0,new NetworkInput {action="emote",value=0,eventID=1,time=0},0));
            Assert.True(m.Input(1,new NetworkInput {action="emote",value=2,eventID=1,time=0},0));
            m.Input(0,Golf(m),0);Step(m,m.State.shot.duration+.05);double until=m.State.resultUntil;
            foreach(var p in m.State.golfers) Assert.True(m.Input(p.seat,new NetworkInput {action="emote",value=1,eventID=2,time=m.State.time},m.State.time));
            Assert.False(m.Input(1,new NetworkInput {action="emote",value=1,eventID=3,time=m.State.time},m.State.time));
            Assert.False(m.Input(1,new NetworkInput {action="swing",power=1,eventID=4,time=m.State.time},m.State.time));
            Assert.AreEqual(until,m.State.resultUntil);Assert.AreEqual(1,m.State.shotID);
        }
        [Test] public void SharedPhoneCannotControlAnotherPhonesSeat() {
            var c=new NetworkConfiguration {hostID="host",localID="host",lobbyID="room",matchID="match",sport="golf",participants=new[]{
                new NetworkParticipant {id="host",seat=0},new NetworkParticipant {id="guest",seat=1,controllerID="host"},new NetworkParticipant {id="peer",seat=2}}};
            Assert.True(c.Valid);Assert.True(c.Controls("host",1));Assert.False(c.Controls("peer",1));Assert.False(c.Controls("host",2));
            c.participants[1].controllerID="peer";Assert.False(c.Valid);
        }
''' + s[idx:];p.write_text(s)
# allow injected LAN host for protocol tests without network discovery side effects
p=Path('GolfArcade/Multiplayer/MultiplayerService.swift');s=p.read_text().replace('    var isNearby: Bool { local != nil && transport != nil }','    @ObservationIgnored private var sharedPhoneHost = false\n    var isNearby: Bool { (local != nil || sharedPhoneHost) && transport != nil }');s=s.replace('func host(using connection: any MultiplayerTransport) throws {','func host(using connection: any MultiplayerTransport, sharedPhone: Bool = false) throws {');s=s.replace('bind(connection); createLobby(owner: localID)','sharedPhoneHost = sharedPhone; bind(connection); createLobby(owner: localID)',1);s=s.replace('func leave() {','func leave() {\n        sharedPhoneHost = false',1);p.write_text(s)
p=Path('GolfArcadeTests/MultiplayerTests.swift');s=p.read_text();idx=s.index('    func testFourPersonParty')
s=s[:idx]+'''    func testSharedPhoneGuestsLoadWithHostAndKeepIndependentLooks() throws {
        let bus=Bus(); let phone=bus.connect("host"); let host=MultiplayerService(sendToRuntime:{_ in true},pollRuntime:{nil})
        host.onMatchRequested={ _ in }; defer { host.leave() }
        try host.host(using:phone,sharedPhone:true);try host.configure(.golf,venue:"postcards")
        try host.addLocalGuest();try host.addLocalGuest();try host.addLocalGuest()
        XCTAssertEqual(host.lobby?.participants.count,4);XCTAssertTrue(host.lobby!.valid())
        let guests=host.lobby!.participants.filter(\\.isGuest)
        XCTAssertEqual(Set(guests.compactMap{$0.loadout?.colours["shirt"]}).count,3)
        XCTAssertTrue(guests.allSatisfy{$0.controllerID==host.localID && $0.loadout?.valid()==true})
        XCTAssertThrowsError(try host.addLocalGuest());try host.setReady(true);try host.startMatch();host.runtimeLoaded()
        XCTAssertEqual(host.lobby?.phase,.playing);XCTAssertTrue(host.lobby!.competitors.allSatisfy(\\.loaded))
    }
    func testNearbyCodeAndForgedGuestOwnership() {
        XCTAssertEqual(LocalMultiplayerTransport.joinCode(for:"abc12345-6789-1234-5678-123456789012"),"ABC123")
        let host=MultiplayerParticipant(id:"host",name:"Host",seat:0)
        let guest=MultiplayerParticipant(id:"guest",name:"Guest",seat:1,controllerID:"intruder")
        XCTAssertFalse(MultiplayerLobby(ownerID:"host",sport:.golf,participants:[host,guest]).valid())
    }
''' + s[idx:];p.write_text(s)
