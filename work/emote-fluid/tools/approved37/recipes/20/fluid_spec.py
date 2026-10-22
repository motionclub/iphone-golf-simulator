"""Beat specification from the approved choreography; thresholds copied unchanged from prompt 31."""
CLIPS = ['Emote_Spike','Emote_Scuba','Emote_Thrust','Intro_Wave','Intro_BringIt','Intro_Pushups']
BODY = ['Hips','Spine','Chest','Neck','Head','LeftUpperArm','LeftLowerArm','LeftHand','RightUpperArm','RightLowerArm','RightHand']
SPINE_CHAIN = ['Hips','Spine','Chest','Neck','Head']
def move(name,start,pose,bone,chain=SPINE_CHAIN,stretch=None,settle=4):
    return dict(name=name,start=start,pose=pose,settle=settle,bone=bone,chain=chain,anticipation=[start-6,start],stretch=stretch)
SPEC = {
 'Emote_Spike':dict(beats=[9,27,36,45,51,59,66,84],impacts=[36,59],fast=[[27,36],[51,59]],holds=[],money=[36,43],moves=[move('overhead wind-up',10,27,'Chest'),move('first slam',28,36,'Chest',stretch='squash'),move('smaller relift',45,51,'Chest'),move('second slam',52,59,'Chest',stretch='squash'),move('stand and glare',66,84,'Chest')]),
 'Emote_Scuba':dict(beats=[6,16,27,38,49,60,71,82,93,104,120,123,132],impacts=[18,123],fast=[],holds=[],money=[120,123],moves=[move('enter nose-pinch and swim',8,16,'Chest'),move('lower to pickup',105,120,'Chest',stretch='squash'),move('rise with racket',124,132,'Chest',stretch='stretch')],loop=[16,104]),
 'Emote_Thrust':dict(beats=[13,18,26,35,43,51,66,77,91],impacts=[],fast=[],holds=[[20,26],[37,43],[51,69],[77,91]],money=[51,63],moves=[move('first hip drive',14,18,'Chest'),move('second hip drive',31,35,'Chest'),move('third hip drive',47,51,'Chest'),move('strut arrival',69,77,'Chest')]),
 'Intro_Wave':dict(beats=[12,15,21,27,33,39,47,52],impacts=[],fast=[],holds=[[16,39]],money=[36,45],moves=[move('raise waving hand',6,12,'LeftUpperArm',['LeftUpperArm','LeftLowerArm','LeftHand']),move('lower waving hand',40,47,'LeftUpperArm',['LeftUpperArm','LeftLowerArm','LeftHand'])]),
 'Intro_BringIt':dict(beats=[20,26,33,41,48,56,63,71,81],impacts=[],fast=[],holds=[[20,70]],money=[63,72],moves=[move('present challenge',8,20,'LeftUpperArm',['LeftUpperArm','LeftLowerArm','LeftHand']),move('left step',26,33,'Chest'),move('right step',47,54,'Chest'),move('return to ready',72,81,'Chest')]),
 'Intro_Pushups':dict(beats=[9,13,17,28,35,41,48,55,64,70,73,82],impacts=[17,28,64,73],fast=[],holds=[],money=[55,63],moves=[move('set racket down',4,9,'Chest',stretch='squash'),move('reach floor',14,17,'Chest',stretch='squash'),move('extend plank',18,28,'Chest',stretch='stretch'),move('first pushup down',29,35,'Chest',stretch='squash'),move('first pushup up',36,41,'Chest',stretch='stretch'),move('second pushup down',42,48,'Chest',stretch='squash'),move('second pushup up',49,55,'Chest',stretch='stretch'),move('fold back',57,64,'Chest',stretch='squash'),move('stand after pickup',74,82,'Chest',stretch='stretch')])
}
# READY edges are existing animation samples (not a newly imposed pose).
READY_SECONDS = .25
LEVEL = 6

SPEC['Intro_Pushups']['moves'][0].update(leading_bone='RightHand',leading_space='world')
