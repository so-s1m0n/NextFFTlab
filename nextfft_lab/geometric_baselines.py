"""Independent classical baselines for bounded square geometric grids."""
from dataclasses import dataclass

from .exact import P, radix2
from .geometric import _size


def _nodes(n, q):
    _size(n)
    q = int(q) % P
    nodes = tuple(pow(q, i, P) for i in range(n))
    if not q or len(set(nodes)) != n:
        raise ValueError("nonzero q and distinct geometric nodes required")
    return nodes


def _values(values):
    values = [int(v) % P for v in values]
    _size(len(values))
    return values


def horner_geometric(values, q):
    coefficients = _values(values)
    result = []
    for node in _nodes(len(coefficients), q):
        value = 0
        for coefficient in reversed(coefficients):
            value = (value * node + coefficient) % P
        result.append(value)
    return result


def divided_difference_geometric(values, q):
    """Classical quadratic interpolation using Newton divided differences."""
    work = _values(values)
    nodes = _nodes(len(work), q)
    for k in range(1, len(work)):
        for i in range(len(work) - 1, k - 1, -1):
            work[i] = (work[i] - work[i - 1]) * pow(nodes[i] - nodes[i - k], -1, P) % P
    result = [work[-1]]
    for i in range(len(work) - 2, -1, -1):
        result.append(0)
        for j in range(len(result) - 1, 0, -1):
            result[j] = (result[j - 1] - nodes[i] * result[j]) % P
        result[0] = (work[i] - nodes[i] * result[0]) % P
    return result


@dataclass(frozen=True)
class GeometricChirp:
    n: int
    diagonal: tuple
    spectrum: tuple

    @classmethod
    def build(cls, n, q):
        _nodes(n, q)
        q = int(q) % P
        chirp = tuple(pow(q, i * (i - 1) // 2, P) for i in range(2 * n - 1))
        diagonal = tuple(pow(x, -1, P) for x in chirp[:n])
        b = 1 << (2 * n - 2).bit_length()
        return cls(n, diagonal, tuple(radix2(chirp + (0,) * (b - len(chirp)))))

    def apply(self, values):
        x = _values(values)
        if len(x) != self.n:
            raise ValueError("wrong input length")
        x = [v * d % P for v, d in zip(x, self.diagonal)][::-1]
        x.extend([0] * (len(self.spectrum) - len(x)))
        transformed = radix2(x)
        y = radix2([v * d % P for v, d in zip(transformed, self.spectrum)], inverse=True)
        return [y[self.n - 1 + i] * d % P for i, d in enumerate(self.diagonal)]
