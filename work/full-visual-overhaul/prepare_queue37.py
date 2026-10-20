import json
from pathlib import Path
r = Path(__file__).resolve().parents[2]
p = r / 'proof/full-visual-overhaul'
jobs = [
    {'name':'starter-palette-1','method':'GolfArcade.EditorTools.HeroStarterPaletteProbe.Run','env':{'HSP_OUT':str(p/'characters/starter-palette-builder-audit.txt')}},
    {'name':'character-pass-20-all33','method':'GolfArcade.EditorTools.VisualOverhaulCharacterCapture.Run','env':{'VISUAL_CHARACTER_OUT':str(p/'character-pass-20-all33')}},
    {'name':'golf-characters-pass-5','method':'GolfArcade.EditorTools.VisualOverhaulGolfCharacterCapture.Run','env':{'VISUAL_GOLF_CHARACTER_OUT':str(p/'golf-characters-pass-5')}}
]
(r/'work/full-visual-overhaul/capture-checkpoint-37-cloth.json').write_text(json.dumps(jobs,indent=2)+'\n')
