using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Points bucketed by integer cell, for the neighbourhood passes a hero runs when it is built (the eyelid normal field, the
    /// body's shape offsets followed by its garments). It is what those passes kept in a Dictionary of Vector3Int to List of int, as
    /// flat arrays: a look-up is a few integer operations instead of a hashed struct key and a list object, and nothing is allocated
    /// per cell (2026-11-15, work/perf-1115: a hero's first build spent most of its time in those dictionaries).
    ///
    /// A cell's points come back in the order they were added, ascending index, exactly as the lists had them. A pass that sums over
    /// its neighbours therefore adds the same numbers in the same order, and its result is bit for bit what the dictionary gave.
    public sealed class CellGrid
    {
        readonly long[] keys; readonly int[] first, size; readonly bool[] used; readonly int mask;
        /// The points, cell after cell; Find gives a cell's range in it.
        public readonly int[] Items;
        public readonly float Cell;

        static long Pack(int x, int y, int z) => ((long)(x & 0x1FFFFF) << 42) | ((long)(y & 0x1FFFFF) << 21) | (long)(z & 0x1FFFFF);
        static int Hash(long k) { unchecked { ulong h = (ulong)k; h ^= h >> 33; h *= 0xff51afd7ed558ccdUL; h ^= h >> 33; return (int)h; } }
        public static int Coord(float v, float cell) => Mathf.FloorToInt(v / cell);

        /// The first `count` of `points`, in cells `cell` wide (a point's cell is FloorToInt(coordinate / cell) on each axis).
        /// `include`: only the points it marks (null: all).
        public CellGrid(Vector3[] points, int count, float cell, bool[] include = null)
        {
            Cell = cell;
            int capacity = 16; while (capacity < count * 2) capacity <<= 1;
            keys = new long[capacity]; first = new int[capacity]; size = new int[capacity]; used = new bool[capacity]; mask = capacity - 1;
            var slotOf = new int[count];
            for (int i = 0; i < count; i++)
            {
                if (include != null && !include[i]) { slotOf[i] = -1; continue; }
                long key = Pack(Coord(points[i].x, cell), Coord(points[i].y, cell), Coord(points[i].z, cell));
                int s = Hash(key) & mask;
                while (used[s] && keys[s] != key) s = (s + 1) & mask;
                used[s] = true; keys[s] = key; size[s]++; slotOf[i] = s;
            }
            int total = 0;
            for (int s = 0; s < capacity; s++) if (used[s]) { first[s] = total; total += size[s]; size[s] = 0; }
            Items = new int[total];
            for (int i = 0; i < count; i++) { int s = slotOf[i]; if (s >= 0) Items[first[s] + size[s]++] = i; }
        }

        /// The points in cell (x, y, z): Items[start] to Items[end - 1], in the order they were added. False when it is empty.
        public bool Find(int x, int y, int z, out int start, out int end)
        {
            long key = Pack(x, y, z);
            int s = Hash(key) & mask;
            while (used[s])
            {
                if (keys[s] == key) { start = first[s]; end = start + size[s]; return true; }
                s = (s + 1) & mask;
            }
            start = end = 0; return false;
        }
    }
}
