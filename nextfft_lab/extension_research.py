"""Bounded source checks of extension-coordinate grids and mixed-radix packing."""
from dataclasses import dataclass
from math import prod

from .exact import P
from .extension_coordinates import ONE, ZERO, add, auxiliary_root, mul
from .geometric import NewtonPlan, reciprocal

AUXILIARY_LENGTHS = (6, 12, 24, 48)
QUARTIC_ZERO = (0, 0, 0, 0)


def _base_scale(value, coefficient):
    return value[0] * coefficient % P, value[1] * coefficient % P


@dataclass(frozen=True)
class _AuxDFT:
    length: int
    powers: tuple
    inv_length: int

    @classmethod
    def build(cls, length):
        generator = auxiliary_root(length)
        powers = [ONE]
        for _ in range(length - 1):
            powers.append(mul(powers[-1], generator))
        return cls(length, tuple(powers), pow(length, -1, P))

    def apply(self, values, *, inverse=False):
        out = []
        for k in range(self.length):
            step = -k if inverse else k
            total = ZERO
            for j, value in enumerate(values):
                total = add(total, mul(value, self.powers[j * step % self.length]))
            out.append(_base_scale(total, self.inv_length) if inverse else total)
        return out


@dataclass(frozen=True)
class _PackedAxis:
    base: NewtonPlan
    dft: _AuxDFT
    spectrum: tuple
    reciprocal_spectrum: tuple

    @classmethod
    def build(cls, length, ratio):
        base = NewtonPlan.build(length, ratio)
        b = next(b for b in AUXILIARY_LENGTHS if b >= 2 * length)
        dft = _AuxDFT.build(b)

        def spectrum(kernel):
            return tuple(dft.apply([(c, 0) for c in kernel] + [ZERO] * (b - length)))

        return cls(base, dft, spectrum(base.Hinv), spectrum(reciprocal(base.Hinv)))

    def _toeplitz(self, values, spectrum, *, upper):
        n = self.base.n
        ordered = values[::-1] if upper else values
        freq = self.dft.apply(ordered + [ZERO] * (self.dft.length - n))
        out = self.dft.apply([mul(a, c) for a, c in zip(freq, spectrum)], inverse=True)[:n]
        return out[::-1] if upper else out

    def apply(self, values, *, inverse):
        base = self.base
        if inverse:
            diagonal, middle, spectrum = base.Hinv, base.midinv, self.reciprocal_spectrum
        else:
            diagonal, middle, spectrum = base.H, base.middle, self.spectrum

        def scaled(row, coefficients):
            return [_base_scale(x, c) for x, c in zip(row, coefficients)]

        row = self._toeplitz(scaled(values, diagonal), spectrum, upper=not inverse)
        row = self._toeplitz(scaled(row, middle), spectrum, upper=inverse)
        return scaled(row, diagonal)


@dataclass(frozen=True)
class QuadraticGeometricGrid:
    """Apply a base-defined geometric tensor product to independent packed grids."""

    axes: tuple
    size: int

    @classmethod
    def build(cls, shape, ratios):
        shape, ratios = tuple(shape), tuple(ratios)
        if (not 1 <= len(shape) <= 3 or len(shape) != len(ratios)
                or any(type(n) is not int or not 2 <= n <= 16 for n in shape)
                or prod(shape) > 128):
            raise ValueError("expected 1..3 axes of length 2..16 and volume <=128")
        return cls(tuple(_PackedAxis.build(n, q) for n, q in zip(shape, ratios)), prod(shape))

    def _rows(self, rows):
        if not 1 <= len(rows) <= 16 or any(len(row) != self.size for row in rows):
            raise ValueError("expected 1..16 independent grids of the plan volume")
        return [[int(value) % P for value in row] for row in rows]

    def _tensor(self, row, *, inverse, packed):
        stride = self.size
        for axis in self.axes:
            n = axis.base.n
            stride //= n
            plan = axis if packed else axis.base
            for block in range(0, self.size, n * stride):
                for start in range(block, block + stride):
                    stop = start + n * stride
                    row[start:stop:stride] = plan.apply(row[start:stop:stride], inverse=inverse)
        return row

    def apply(self, rows, *, inverse=False):
        normalized = self._rows(rows)
        output = []
        for offset in range(0, len(normalized), 2):
            first, *second = normalized[offset:offset + 2]
            packed = list(zip(first, second[0] if second else [0] * self.size))
            result = self._tensor(packed, inverse=inverse, packed=True)
            output.append([a for a, _ in result])
            if second:
                output.append([b for _, b in result])
            elif any(b for _, b in result):
                raise ArithmeticError("padded extension coordinate did not remain zero")
        return output

    def apply_base(self, rows, *, inverse=False):
        return [self._tensor(row, inverse=inverse, packed=False) for row in self._rows(rows)]

    def application_counts(self, row_count):
        """Base scalar additions/subtractions and multiplications, excluding setup."""
        if type(row_count) is not int or not 1 <= row_count <= 16:
            raise ValueError("expected 1..16 grids")
        extension_adds = extension_muls = base_adds = base_muls = 0
        for axis in self.axes:
            n = axis.base.n
            fibers = self.size // n
            b = axis.dft.length
            extension_adds += fibers * (16 * b * b + 4 * b)
            extension_muls += fibers * (20 * b * b + 14 * b + 6 * n)
            padded = axis.base.lower.padded
            butterflies = padded * (padded.bit_length() - 1) // 2
            base_adds += fibers * 8 * butterflies
            base_muls += fibers * (8 * butterflies + 4 * padded + 3 * n)
        pairs = (row_count + 1) // 2
        return {
            "base_add_sub": base_adds * row_count,
            "base_multiply": base_muls * row_count,
            "packed_add_sub": extension_adds * pairs,
            "packed_multiply": extension_muls * pairs,
            "extension_batches": pairs,
            "padded_coordinates": 2 * pairs - row_count,
        }


def _quartic_add(left, right):
    return tuple((a + b) % P for a, b in zip(left, right))


def _quartic_mul(left, right):
    coefficients = [0] * 7
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            coefficients[i + j] += a * b
    for i in range(3):
        coefficients[i] += 3 * coefficients[i + 4]
    return tuple(value % P for value in coefficients[:4])


@dataclass(frozen=True)
class QuarticProductPlan:
    """Half-box mixed-radix packing in Fp[t]/(t^4-3), with truncated jets."""

    n: int
    jet_count: int
    dft: _AuxDFT

    @classmethod
    def build(cls, n, jets, cyclic):
        if (type(n) is not int or not 1 <= n <= 64 or type(jets) is not int or jets < 1
                or type(cyclic) is not int or cyclic not in AUXILIARY_LENGTHS
                or not 8 * n <= 4 * jets * cyclic <= 9 * n):
            raise ValueError("expected n in 1..64, supported cyclic length and 8n <= 4rN <= 9n")
        return cls(n, jets, _AuxDFT.build(cyclic))

    def _cyclic(self, values, *, inverse=False):
        # The primitive root is in the subfield generated by t^2.
        even = self.dft.apply([(a, c) for a, _, c, _ in values], inverse=inverse)
        odd = self.dft.apply([(b, d) for _, b, _, d in values], inverse=inverse)
        return [(a, b, c, d) for (a, c), (b, d) in zip(even, odd)]

    def application_counts(self):
        """Executed base-field additions and multiplications, excluding setup."""
        n = self.n
        b = self.dft.length
        r = (self.jet_count + 1) // 2
        transforms = 2 * (4 * r - 1)
        inverse_transforms = 2 * (2 * r - 1)
        products = b * r * r
        gather_adds = sum(min(4, max(0, 2 * n - 1 - 2 * z - 2 * r * x))
                          for z in range(2 * r - 1) for x in range(b))
        padded = 1 << (2 * n - 2).bit_length()
        butterflies = padded * (padded.bit_length() - 1) // 2
        return {
            "packed_add_sub": 4 * b * b * transforms + 23 * products + gather_adds,
            "packed_multiply": 5 * b * b * transforms + 2 * b * inverse_transforms + 19 * products,
            "base_add_sub": 6 * butterflies,
            "base_multiply": 6 * butterflies + 2 * padded,
            "quadratic_dfts": transforms,
            "quartic_jet_products": products,
            "base_ntts": 3,
        }

    def _pack(self, values):
        # The paper's extension radix E0=ceil(4/2)=2 occupies 1 and t.
        occupied_jets = (self.jet_count + 1) // 2
        layers = [[QUARTIC_ZERO] * self.dft.length for _ in range(occupied_jets)]
        for i in range(0, self.n, 2):
            x, z = divmod(i // 2, occupied_jets)
            high = int(values[i + 1]) % P if i + 1 < self.n else 0
            layers[z][x] = (int(values[i]) % P, high, 0, 0)
        return layers

    def multiply(self, left, right):
        if len(left) != self.n or len(right) != self.n:
            raise ValueError("both polynomials must have the plan's input length")
        cyclic = self.dft.length
        occupied_jets = (self.jet_count + 1) // 2

        a = [self._cyclic(layer) for layer in self._pack(left)]
        b = [self._cyclic(layer) for layer in self._pack(right)]
        out = [0] * (2 * self.n - 1)
        for z in range(2 * occupied_jets - 1):
            lo, hi = max(0, z - occupied_jets + 1), min(z, occupied_jets - 1)
            layer = []
            for k in range(cyclic):
                total = QUARTIC_ZERO
                for j in range(lo, hi + 1):
                    total = _quartic_add(total, _quartic_mul(a[j][k], b[z - j][k]))
                layer.append(total)
            for x, value in enumerate(self._cyclic(layer, inverse=True)):
                for power, coefficient in enumerate(value):
                    index = power + 2 * z + 2 * occupied_jets * x
                    if index < len(out):
                        out[index] = (out[index] + coefficient) % P
        return out
