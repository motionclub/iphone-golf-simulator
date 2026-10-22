from common import *
import sys
L = {
 'welcome_cliffside':"Welcome to Cliffside!",'welcome_wildisles':"Welcome to Wild Isles!",'welcome_magma':"Welcome to Magma!",
 'welcome_resort':"Welcome to Resort!",'welcome_skyscraper':"Welcome to Skyscraper!",'welcome_volcano':"Welcome to Volcano!",
 'nice_shot':"Nice shot!",'great_shot':"Great shot!",'long_drive':"What a drive!",'fairway':"Fairway!",'close':"So close!",
 'on_green':"On the green!",'long_putt':"Drained it!",'chip_in':"Chip in!",'bunker_save':"Sand save!",'birdie':"Birdie!",'eagle':"Eagle!",
 'ace_golf':"Hole in one!",'par':"Par.",'bogey':"Bogey.",'double':"Double bogey.",'water':"Splash!",'lava':"Into the lava!",'oob':"Out of bounds!",
 'whiff':"Air shot!",'shank':"Ooh, ugly.",'three_putt':"Three putts.",'tree':"Tree!",'round_over':"Round over!",
 'ace':"Ace!",'winner':"Winner!",'smash':"Smashed it!",'line':"On the line!",'rally':"Great rally!",'comeback':"Comeback!",
 'net':"Into the net.",'out':"Out!",'fault':"Fault.",'double_fault':"Double fault!",'break_point':"Break point!",'match_point':"Match point!",
 'game':"Game.",'set':"Set!",'match':"Game, set, match!",'deuce':"Deuce.",'quiet':"Quiet, please.",'play':"Play!",
 'fifteen_love':"Fifteen, love.",'thirty_love':"Thirty, love.",'forty_love':"Forty, love.",'love_fifteen':"Love, fifteen.",'love_thirty':"Love, thirty.",
 'love_forty':"Love, forty.",'fifteen_all':"Fifteen all.",'thirty_all':"Thirty all.",'forty_fifteen':"Forty, fifteen.",'forty_thirty':"Forty, thirty.",
 'fifteen_thirty':"Fifteen, thirty.",'thirty_fifteen':"Thirty, fifteen.",'fifteen_forty':"Fifteen, forty.",'thirty_forty':"Thirty, forty.",
 'advantage_server':"Advantage, server.",'advantage_receiver':"Advantage, receiver.",
}
items=[(f'v2/voice/{k}_{i+1}.mp3',dict(text=t)) for k,t in L.items() for i in range(3)]
print(len(items),sum(len(k['text']) for _,k in items),'credits')
if 'dry' not in sys.argv: run(items, lambda text: client.text_to_speech.convert(voice_id=JAX,text=text,model_id='eleven_multilingual_v2',output_format='mp3_44100_128',voice_settings={'stability':.5,'similarity_boost':.75,'style':.1}), 'voice2')
