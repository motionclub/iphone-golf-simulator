"""Asset registry: recipes register with @asset(name, **meta). Meta keys:
course A/B/C, holes, kind, where (from HOLE_BRIEFS), budget (LOD0 tris), dims {axis: (lo, hi) metres},
pivot ('base' = min z 0, centred), match (azimuth, elevation) of the target crop's view, target (targets/<name>.jpg),
target_aspect (object h/w measured on the crop), features (SHAPE_MATCH checklist), animated (separate parts + pivot)."""
REG = {}


def asset(name, **meta):
    def deco(fn):
        REG[name] = dict(name=name, fn=fn, **meta)
        return fn
    return deco
