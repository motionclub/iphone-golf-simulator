"""Standard walk cycle (seamless loop, in place): see gait.py."""
import gait

SUB = 1   # gait.py samples itself on the 60 Hz grid (see gait.S)

NAME = gait.WALK['name']


def build(H):
    return gait.build(H, gait.WALK, getattr(H, 'prop', 'racket') == 'none')
