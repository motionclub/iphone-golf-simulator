import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
import numpy as np
import racket_geom as G
parts, info = G.build_frame(G.P)
poly = G.inner_polygon(G.P)
from matplotlib import path as mp
