import sys, time
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb/scripts')
import numpy as np
from sdf import *
g = Grid((-0.15,-0.15,-0.15),(0.15,0.15,0.15), 0.01)
X,Y,Z = g.coords()
F = (np.sqrt(X**2+Y**2+Z**2) - 0.1).astype(np.float32)
F = np.broadcast_to(F, tuple(g.n)).copy()
V, Q = surface_nets(F, g)
T = quads_to_tris(V, Q)
r = np.linalg.norm(V,axis=1)
print("sphere: verts", len(V), "quads", len(Q), "tris", len(T), "radius mean", r.mean(), "min", r.min(), "max", r.max())
# orientation: normals vs radial
fn = np.cross(V[T[:,1]]-V[T[:,0]], V[T[:,2]]-V[T[:,0]]); cen = V[T].mean(1)
print("outward fraction", np.mean(np.sum(fn*cen,1)>0))
# closed manifold? boundary edges
be = boundary_edges(T); print("boundary edges", len(be))
# volume
vol = np.sum(np.einsum('ij,ij->i', V[T[:,0]], np.cross(V[T[:,1]], V[T[:,2]])))/6
print("volume", vol, "expected", 4/3*np.pi*0.1**3)
# clip test: remove z>0.03
c = V[:,2]-0.03
V2,F2,att,nm = clip_mesh(V, T, c)
print("clip: verts", len(V2), "tris", len(F2), "z max", V2[:,2].max(), "boundary loops", [len(l) for l in boundary_loops(F2)])
# check boundary verts lie on z=0.03
bl = boundary_loops(F2)[0]
print("boundary z err max", np.abs(V2[bl,2]-0.03).max())
# smoothing
V3 = taubin(V, T, 10)
print("taubin radius mean", np.linalg.norm(V3,axis=1).mean(), "std", np.linalg.norm(V3,axis=1).std(), "vs raw std", r.std())
# gauss test: blur of linear field unchanged
G = gauss3(F, 1.5); print("blur sphere center", G[g.n[0]//2, g.n[1]//2, g.n[2]//2], "vs", F[g.n[0]//2, g.n[1]//2, g.n[2]//2])
# components
print("components", len(np.unique(components(T, len(V)))))
