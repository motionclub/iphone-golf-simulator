"""Standard run cycle (seamless loop, in place): see gait.py."""
import gait

SUB = 1   # gait.py samples itself on the 60 Hz grid (see gait.S)

NAME = gait.RUN['name']


def build(H):
    return gait.build(H, gait.RUN, getattr(H, 'prop', 'racket') == 'none')
