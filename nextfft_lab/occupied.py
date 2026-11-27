"""Scalar register check of layers.tex, up:toeplitz, over F_998244353."""
from dataclasses import dataclass

from .exact import P, radix2, root
from .geometric import NewtonPlan, _size, reciprocal


def _ntt_at(registers, start, n, inverse=False):
    """Classical radix-2 transform of one register range, without slicing."""
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            registers[start + i], registers[start + j] = registers[start + j], registers[start + i]
    width = 2
    while width <= n:
        step = root(width, inverse)
        half = width // 2
        for offset in range(start, start + n, width):
            twiddle = 1
            for lo in range(offset, offset + half):
                hi = lo + half
                x, y = registers[lo], registers[hi] * twiddle % P
                registers[lo], registers[hi] = (x + y) % P, (x - y) % P
                twiddle = twiddle * step % P
        width *= 2
    if inverse:
        inv_n = pow(n, -1, P)
        for i in range(start, start + n):
            registers[i] = registers[i] * inv_n % P


def _add(registers, source, destination, length, sign=1):
    for i in range(length):
        registers[destination + i] = (registers[destination + i] + sign * registers[source + i]) % P


def _scale_at(registers, coefficients, start=0):
    for i, coefficient in enumerate(coefficients, start):
        registers[i] = registers[i] * coefficient % P


@dataclass(frozen=True)
class OccupiedToeplitz:
    n: int
    padded: int
    spectrum: tuple

    @classmethod
    def build(cls, column, row):
        column = tuple(int(v) % P for v in column)
        row = tuple(int(v) % P for v in row)
        n = len(column)
        _size(n)
        if len(row) != n or column[0] != row[0]:
            raise ValueError("Toeplitz row and column must share length and diagonal")
        b = 1 << (2 * n - 1).bit_length()
        kernel = column + (0,) * (b - 2 * n + 1) + tuple(reversed(row[1:]))
        return cls(n, b, tuple(radix2(kernel)))

    @property
    def register_count(self):
        return 2 * self.n + 2 * self.padded

    def _circulant(self, registers, x, y, sign):
        b = self.padded
        _ntt_at(registers, x, b)
        _ntt_at(registers, y, b)
        for i, w in enumerate(self.spectrum):
            registers[y + i] = (registers[y + i] + sign * w * registers[x + i]) % P
        _ntt_at(registers, x, b, inverse=True)
        _ntt_at(registers, y, b, inverse=True)

    def _lj(self, registers, source, sign):
        p = 2 * self.n
        q = p + self.padded
        _add(registers, source, p, self.n)
        self._circulant(registers, p, q, sign)
        _add(registers, source, p, self.n, -1)
        self._circulant(registers, p, q, -sign)

    def _shear(self, registers, source, destination, sign):
        q = 2 * self.n + self.padded
        self._lj(registers, source, 1)
        _add(registers, q, destination, self.n, sign)
        self._lj(registers, source, -1)
        _add(registers, q, destination, self.n, -sign)

    def shear(self, registers, *, inverse=False):
        """Map (x,y,p,q) to (x,y±Ax,p,q) in canonical residue registers."""
        if len(registers) != self.register_count:
            raise ValueError("wrong register count")
        self._shear(registers, 0, self.n, -1 if inverse else 1)


@dataclass(frozen=True)
class OccupiedTriangular:
    forward: OccupiedToeplitz
    backward: OccupiedToeplitz
    d: tuple
    dinv: tuple
    diagonal: int

    @classmethod
    def build(cls, column):
        h = tuple(int(v) % P for v in column)
        n = len(h)
        _size(n)
        if not h[0]:
            raise ValueError("triangular factor must be invertible")
        unit = pow(h[0], -1, P)
        hnorm = tuple(x * unit % P for x in h)
        u = root(1 << (2 * n - 1).bit_length())
        d = tuple(pow(u, i, P) for i in range(n))
        f = [1]
        for i in range(1, n):
            rhs = sum(hnorm[j] * f[i - j] for j in range(1, i + 1))
            f.append(rhs * pow(d[i] - 1, -1, P) % P)
        row = (1,) + (0,) * (n - 1)
        return cls(OccupiedToeplitz.build(f, row), OccupiedToeplitz.build(reciprocal(f), row),
                   d, tuple(pow(v, -1, P) for v in d), h[0])

    @property
    def register_count(self):
        return self.forward.register_count

    @staticmethod
    def _block(registers, forward, backward):
        n = forward.n
        for i in range(n):
            registers[i], registers[n + i] = -registers[n + i] % P, registers[i]
        forward._shear(registers, n, 0, 1)
        backward._shear(registers, 0, n, -1)
        forward._shear(registers, n, 0, 1)

    def apply(self, registers, *, upper=False):
        if len(registers) != self.register_count:
            raise ValueError("wrong register count")
        n = self.forward.n
        if upper:
            self._reverse(registers, n)
        self._block(registers, self.backward, self.forward)
        _scale_at(registers, self.dinv)
        self._block(registers, self.forward, self.backward)
        for i, w in enumerate(self.d):
            registers[i] = registers[i] * w * self.diagonal % P
        if upper:
            self._reverse(registers, n)

    @staticmethod
    def _reverse(registers, n):
        for i in range(n // 2):
            j = n - 1 - i
            registers[i], registers[j] = registers[j], registers[i]


@dataclass(frozen=True)
class OccupiedNewton:
    diagonal: tuple
    middle: tuple
    lower: OccupiedTriangular
    inverse_diagonal: tuple
    inverse_middle: tuple
    reciprocal_lower: OccupiedTriangular

    @classmethod
    def build(cls, n, q):
        plan = NewtonPlan.build(n, q)
        return cls(plan.H, plan.middle, OccupiedTriangular.build(plan.Hinv),
                   plan.Hinv, plan.midinv, OccupiedTriangular.build(reciprocal(plan.Hinv)))

    @property
    def register_count(self):
        return self.lower.register_count

    def apply(self, registers, *, inverse=False):
        if len(registers) != self.register_count:
            raise ValueError("wrong register count")
        diagonal, middle, lower = ((self.inverse_diagonal, self.inverse_middle, self.reciprocal_lower)
                                   if inverse else (self.diagonal, self.middle, self.lower))
        _scale_at(registers, diagonal)
        lower.apply(registers, upper=not inverse)
        _scale_at(registers, middle)
        lower.apply(registers, upper=inverse)
        _scale_at(registers, diagonal)
