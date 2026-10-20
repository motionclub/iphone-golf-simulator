from pathlib import Path
import hashlib,json
TASK=Path(__file__).resolve().parent;REPO=TASK.parents[2];PRIOR=TASK.parent/'original-native-parity1'
flags={'VISUAL_ORIGINAL_SEAM':'1','VISUAL_ORIGINAL_BLINK':'1','VISUAL_ORIGINAL_EYE_MATERIAL':'1','VISUAL_CHARACTER_SKIN_FINISH':'1','VISUAL_CHARACTER_NORMALS':'continuous','VISUAL_REFERENCE_HEAD':'0','MH_LOCKER_FACE_PARITY':'1'}
profiles={}
for id,method in [('tennis','Run'),('tennis-distance','RunDistance'),('golf','RunGolf')]:
 env=dict(flags,MH_LOCKER_OUT=str(TASK/'export'),MH_LOCKER_GOLDEN=str(TASK/'golden'),MH_LOCKER_REPORT=str(TASK/(id+'-export.txt')))
 profiles[id]={'method':'GolfArcade.EditorTools.MatchHeroLockerExport.'+method,'environment':env,'logFile':str(TASK/(id+'-unity.log'))}
# Explicit export-time rollback profile, never overwrites the accepted candidate.
profiles['legacy-control']={'method':'GolfArcade.EditorTools.MatchHeroLockerExport.Run','environment':dict(flags,VISUAL_ORIGINAL_SEAM='0',VISUAL_ORIGINAL_BLINK='0',VISUAL_CHARACTER_SKIN_FINISH='0',VISUAL_CHARACTER_NORMALS='legacy',MH_LOCKER_OUT=str(TASK/'legacy-control'),MH_LOCKER_GOLDEN=str(TASK/'legacy-golden'),MH_LOCKER_REPORT=str(TASK/'legacy-control-export.txt')),'logFile':str(TASK/'legacy-control-unity.log')}
(TASK/'export-configs.json').write_text(json.dumps({'projectPath':str(REPO/'Unity'),'serial_order':['tennis','tennis-distance','golf'],'profiles':profiles,'all_output_paths_work_only':True,'faceParity_note':'Adds forehand tracks only for tennis proof. Golf serve aliases Drive; independent six-clip-time goldens cover all golf swings.'},indent=2)+'\n')
bones=json.loads((PRIOR/'export/MatchHero_Male.json').read_text())['rig']['bones']
contract={'bones':bones,'golf_extra_bone':'Club','counts':{'Male':{'Body':33705,'Face':3824},'Female':{'Body':23230,'Face':3004}},'morph_names':['Hero_Blink_Half','Hero_Blink'],'luts':{},'source_files':{}}
for p in sorted((PRIOR/'export').glob('MatchHero_Original*.png')):contract['luts'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
for sex in ['Male','Female']:
 p=REPO/f'Unity/Assets/Resources/Tennis/OriginalSeamBlinkFinish/{sex}.fbx'
 contract['source_files'][str(p.relative_to(REPO))]=hashlib.sha256(p.read_bytes()).hexdigest()
(TASK/'accepted-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
