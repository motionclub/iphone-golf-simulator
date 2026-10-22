"""Copy a model .fbx.meta with every clip range (firstFrame / lastFrame, in frames) doubled: the same seconds at 60 fps."""
import re, sys
for src, dst in zip(sys.argv[1::2], sys.argv[2::2]):
    text = open(src).read(); n = 0
    def dbl(m):
        global n; n += 1
        v = float(m.group(2)); return f"{m.group(1)}{v * 2:g}"
    out = re.sub(r"^(\s+(?:firstFrame|lastFrame): )(-?[0-9.]+)\s*$", dbl, text, flags=re.M)
    open(dst, "w").write(out); print("META", src.split("/")[-1], "ranges doubled:", n)
