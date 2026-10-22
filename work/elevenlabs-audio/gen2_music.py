from common import *
P = {
 'menu_lounge': "Chill premium country-club lounge music for a menu, mellow jazz guitar, soft Rhodes piano, brushed drums, upright bass, warm and relaxed, no vocals, seamless loop",
 'game_light': "Light, airy loopable gameplay background music, gentle acoustic guitar and soft mallets, easygoing groove, unobtrusive, no vocals, seamless loop",
}
run([(f'v2/music/{k}.mp3', dict(prompt=p, music_length_ms=75000, model_id='music_v2_5')) for k, p in P.items()], lambda **kw: client.music.compose(**kw), 'music2')
