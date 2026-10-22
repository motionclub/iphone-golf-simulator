from common import *
M = {
 'cliffside': "Breezy seaside golf course intro, bright fingerpicked acoustic guitar, light strings, gentle hand percussion, windswept and sunny, optimistic, instrumental",
 'wildisles': "Tropical island jungle intro, steel drums, marimba, flutes, hand percussion, playful and bouncy, sun-soaked party energy, instrumental",
 'magma': "Volcanic magma course intro, heavy low synth bass, taiko-style war drums, ominous brass swells, smoldering tension building to a powerful hit, instrumental",
 'resort': "Sunny luxury resort tennis intro, upbeat bossa-nova pop, bright marimba, clean guitar, handclaps, breezy and stylish, instrumental",
 'skyscraper': "Rooftop city tennis intro, punchy synth-pop, tight electronic drums, driving bass, neon night energy, confident, instrumental",
 'volcano': "Volcano tennis intro, tribal drums, deep brass, chanting rhythm, fiery and intense but fun, rising excitement, instrumental",
}
items = [(f'music/intro_{k}_{t}.mp3', dict(prompt=p, music_length_ms=20000, model_id='music_v2_5')) for k, p in M.items() for t in (1, 2)]
run(items, lambda **kw: client.music.compose(**kw), 'music')
