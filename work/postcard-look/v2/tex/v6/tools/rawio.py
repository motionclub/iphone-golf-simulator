import numpy as np
def load(stem):
    h, w, c = map(int, open(stem + '.shape').read().split())
    return np.frombuffer(open(stem + '.raw', 'rb').read(), np.uint8).reshape(h, w, c)
def save_raw(stem, a):
    a = np.ascontiguousarray(a, np.uint8)
    open(stem + '.raw', 'wb').write(a.tobytes()); open(stem + '.shape', 'w').write(' '.join(map(str, a.shape)))
