"""Small source checks for packing.tex and grids.tex over F_998244353."""
from math import gcd

from .exact import P, direct, radix2, root


def packed_product(left, right, *, jets, cyclic):
    """Mixed-radix packing with e=1 and a classical cyclic NTT backend."""
    n = len(left)
    if not 1 <= n <= 64 or n != len(right):
        raise ValueError("equal input lengths in 1..64 required")
    if (type(jets) is not int or type(cyclic) is not int or jets < 1 or cyclic < 1
            or cyclic & (cyclic - 1) or not 8 * n <= jets * cyclic <= 9 * n):
        raise ValueError("expected power-of-two cyclic length and 8n <= jets*cyclic <= 9n")
    r0 = (jets + 1) // 2

    def pack(values):
        layers = [[0] * cyclic for _ in range(r0)]
        for i, value in enumerate(values):
            x, z = divmod(i, r0)
            layers[z][x] = int(value) % P
        return [radix2(row) for row in layers]

    a, b = pack(left), pack(right)
    out = [0] * (2 * n - 1)
    for j in range(2 * r0 - 1):
        lo, hi = max(0, j - r0 + 1), min(j, r0 - 1)
        layer = [sum(a[k][i] * b[j-k][i] for k in range(lo, hi + 1)) % P
                 for i in range(cyclic)]
        for x, value in enumerate(radix2(layer, inverse=True)):
            index = j + r0 * x
            if index < len(out):
                out[index] = (out[index] + value) % P
    return out


def good_factor(values, a, b, *, inverse=False):
    """Good's exact CRT factorization, with classical small axis kernels."""
    n = len(values)
    if min(a, b) < 2 or a * b != n or n > 512 or gcd(a, b) != 1:
        raise ValueError("coprime factors >=2 of a length <=512 required")
    root(n)
    inv_b, inv_a = pow(b, -1, a), pow(a, -1, b)

    def axis(row):
        transform = radix2 if not len(row) & (len(row) - 1) else direct
        return transform(row, inverse)

    rows = [axis([values[(i * b * inv_b + j * a * inv_a) % n] for i in range(a)])
            for j in range(b)]
    columns = [axis([rows[j][i] for j in range(b)]) for i in range(a)]
    return [columns[k * inv_b % a][k * inv_a % b] for k in range(n)]
