"""tiny numpy-only morphology helpers (no scipy in this environment)"""
import numpy as np


def erode(mask, r):
    m = mask.copy()
    for _ in range(r):
        p = np.pad(m, 1, constant_values=False)
        m = m & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    return m


def dilate(mask, r):
    m = mask.copy()
    for _ in range(r):
        p = np.pad(m, 1, constant_values=False)
        m = m | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return m
