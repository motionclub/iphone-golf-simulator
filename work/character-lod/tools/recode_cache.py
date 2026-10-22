"""Rewrite a HeroLodCache.bytes with uint16 index lists (negative count) wherever an entry's indices all fit. Same version."""
import struct, sys
src, dst = sys.argv[1], sys.argv[2]; d = open(src, 'rb').read()
magic, ver, n = struct.unpack_from('<iii', d, 0); assert magic == 0x444F4C48
index = [struct.unpack_from('<Qii', d, 12 + 16 * i) for i in range(n)]
entries = {}
for h, off, ln in index:
    o = off; subs, = struct.unpack_from('<i', d, o); o += 4; lists = []
    while o < off + ln:
        c, = struct.unpack_from('<i', d, o); o += 4
        if c >= 0: lists.append(list(struct.unpack_from(f'<{c}i', d, o))); o += 4 * c
        else: lists.append(list(struct.unpack_from(f'<{-c}H', d, o))); o += -2 * c
    narrow = all(i < 65536 for l in lists for i in l)
    b = bytearray(struct.pack('<i', subs))
    for l in lists: b += struct.pack('<i', -len(l)) + struct.pack(f'<{len(l)}H', *l) if narrow else struct.pack('<i', len(l)) + struct.pack(f'<{len(l)}i', *l)
    entries[h] = bytes(b)
out = bytearray(struct.pack('<iii', magic, ver, len(entries))); off = 12 + 16 * len(entries); body = bytearray()
for h in sorted(entries): out += struct.pack('<Qii', h, off, len(entries[h])); off += len(entries[h]); body += entries[h]
open(dst, 'wb').write(out + body); print(f'{len(d):,} -> {len(out) + len(body):,} bytes, {len(entries)} entries, version {ver}')
