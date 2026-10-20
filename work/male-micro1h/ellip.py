"""Tilted-ellipsoid helpers: front (most forward, smallest y) surface of an ellipsoid at (x,z), and smooth unions.
Ellipsoid in the (y,z) plane is rotated about the x axis by theta (radians): the local frame (u along the long axis, w normal) =
  u = dz*cos(th) - dy*sin(th)    w = dy*cos(th) + dz*sin(th)     (th>0 tilts the +u axis toward -y as z decreases... see test)
"""
import numpy as np


def ell_front_y(x, z, cx, cy, cz, ax, au, aw, th):
    """smallest y on the ellipsoid surface at (x,z); nan where (x,z) is outside the footprint"""
    dx = x - cx; dz = z - cz
    c, s = np.cos(th), np.sin(th)
    # point (dy,dz) -> (u,w) = (dz*c - dy*s, dy*c + dz*s)
    # quadratic in dy:  (dx/ax)^2 + ((dz*c - dy*s)/au)^2 + ((dy*c + dz*s)/aw)^2 = 1
    A = (s * s) / au ** 2 + (c * c) / aw ** 2
    B = 2.0 * dz * (-(c * s) / au ** 2 + (s * c) / aw ** 2)
    C = (dx / ax) ** 2 + dz * dz * ((c * c) / au ** 2 + (s * s) / aw ** 2) - 1.0
    D = B * B - 4 * A * C
    ok = D >= 0
    dy = (-B - np.sqrt(np.where(ok, D, 0.0))) / (2 * A)
    return np.where(ok, cy + dy, np.nan)
