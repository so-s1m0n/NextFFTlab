"""Exact prime-five coordinates and the one-axis deformation in packing.tex."""

from dataclasses import dataclass
from fractions import Fraction
from functools import cache
from math import comb


@dataclass(frozen=True, slots=True)
class Gaussian:
    """An exact Gaussian rational a + bi, without floating-point coercions."""

    real: Fraction = Fraction(0)
    imag: Fraction = Fraction(0)

    def __post_init__(self):
        if not isinstance(self.real, (int, Fraction)) or not isinstance(self.imag, (int, Fraction)):
            raise TypeError("Gaussian rational coordinates must be integers or Fractions")
        object.__setattr__(self, "real", Fraction(self.real))
        object.__setattr__(self, "imag", Fraction(self.imag))

    def __add__(self, other):
        return Gaussian(self.real + other.real, self.imag + other.imag)

    def __sub__(self, other):
        return Gaussian(self.real - other.real, self.imag - other.imag)

    def __neg__(self):
        return Gaussian(-self.real, -self.imag)

    def __mul__(self, other):
        a, b = self.real, self.imag
        c, d = other.real, other.imag
        return Gaussian(a * c - b * d, a * d + b * c)

    def __truediv__(self, other):
        a, b = self.real, self.imag
        c, d = other.real, other.imag
        norm = c * c + d * d
        return Gaussian((a * c + b * d) / norm, (b * c - a * d) / norm)


_ZERO, _ONE, _I = Gaussian(), Gaussian(1), Gaussian(0, 1)
_RESIDUES = (1, 2, 4, 3)


def _scalar(value):
    return value if isinstance(value, Gaussian) else Gaussian(value)


def _dft4(values, inverse=False):
    """Unnormalized, positive powers of i (negative powers for inverse)."""
    a, b, c, d = values
    even_sum, odd_sum = a + c, b + d
    even_difference = a - c
    twist = (-_I if inverse else _I) * (b - d)
    return (even_sum + odd_sum, even_difference + twist,
            even_sum - odd_sum, even_difference - twist)


def _reduce_phi(dense):
    # x^5=1, and x^4=-(1+x+x^2+x^3) in the cyclotomic factor.
    cyclic = [sum(dense[k::5], _ZERO) for k in range(5)]
    return tuple(cyclic[k] - cyclic[4] for k in range(4))


def _cyclotomic_product(left, right):
    dense = [_ZERO] * 7
    for j, a in enumerate(left):
        for k, b in enumerate(right):
            dense[j + k] += a * b
    return _reduce_phi(dense)


@cache
def prime5_constants():
    """Return lambda and (kappa_1, kappa_2, kappa_3) for g=2, omega=i."""
    roots = (_ONE, _I, -_ONE, -_I)

    def resolvent(j):
        coefficients = [_ZERO] * 5
        for t, residue in enumerate(_RESIDUES):
            coefficients[residue] = roots[-j * t % 4]
        return _reduce_phi(coefficients)

    gamma = resolvent(1)
    power = gamma
    kappas = [_ONE]
    for j in (2, 3):
        eigenvector = resolvent(j)
        power = _cyclotomic_product(power, gamma)
        pivot = next(k for k, value in enumerate(eigenvector) if value != _ZERO)
        scale = power[pivot] / eigenvector[pivot]
        if scale == _ZERO or power != tuple(scale * value for value in eigenvector):
            raise ArithmeticError("prime-five resolvent identity failed")
        kappas.append(scale)
    lam, *tail = _cyclotomic_product(power, gamma)
    if lam == _ZERO or any(value != _ZERO for value in tail):
        raise ArithmeticError("fourth resolvent power is not a nonzero scalar")
    return lam, tuple(kappas)


def prime5_split(coefficients):
    """Apply the paper's DFT-based map to the scalar and binomial factors."""
    if len(coefficients) != 5:
        raise ValueError("five coefficients required")
    vector = tuple(map(_scalar, coefficients))
    w = _dft4(vector[j] for j in _RESIDUES)
    four = Gaussian(4)
    _, kappas = prime5_constants()
    tail = tuple(w[j] / (four * kappa) for j, kappa in enumerate(kappas, 1))
    return vector[0] + w[0], (vector[0] - w[0] / four, *tail)


def prime5_join(scalar, coordinates):
    """Invert prime5_split in the original coefficient order."""
    if len(coordinates) != 4:
        raise ValueError("four binomial coordinates required")
    scalar = _scalar(scalar)
    c, *tail = map(_scalar, coordinates)
    four = Gaussian(4)
    _, kappas = prime5_constants()
    w0 = four * (scalar - c) / Gaussian(5)
    w = (w0, *(four * kappa * value for kappa, value in zip(kappas, tail)))
    values = [scalar - w0] + [_ZERO] * 4
    for j, v in zip(_RESIDUES, _dft4(w, inverse=True)):
        values[j] = v / four
    return values


def _jet_product(left, right, order):
    return [
        sum((left[j] * right[k - j] for j in
             range(max(0, k + 1 - len(right)), min(k + 1, len(left)))), _ZERO)
        for k in range(order)
    ]


def _unit(slope, exponent, order):
    coefficients = [_ONE]
    for k in range(1, order):
        step = Gaussian((exponent - (k - 1)) / k) * slope
        coefficients.append(coefficients[-1] * step)
    return tuple(coefficients)


def _shift_matrix(length, shift, order):
    return tuple(tuple(Gaussian(comb(j, k) * shift ** (j - k)) for j in range(k, length))
                 for k in range(order))


def _shift(coefficients, matrix):
    return [sum((a * b for a, b in zip(coefficients[k:], row)), _ZERO)
            for k, row in enumerate(matrix)]


def _parameters(lam, order):
    lam = _scalar(lam)
    if lam == _ZERO or type(order) is not int or not 1 <= order <= 3:
        raise ValueError("nonzero lambda and jet order in 1..3 required")
    return lam


def _rows(rows, order):
    if len(rows) != 4 or any(len(row) != order for row in rows):
        raise ValueError("four rows with the specified jet order required")
    return [tuple(map(_scalar, row)) for row in rows]


class WidthFourPlan:
    """Reusable setup for Q(i)[z,Y]/(z**order, Y**4-lambda), order 1..3."""

    def __init__(self, lam, order):
        lam = _parameters(lam, order)
        self.order = order
        self.length = 2 * order + 1
        self.to_zero = _shift_matrix(order, -1, order)
        # The last coefficient must vanish, so shift only degree <= 2r-1.
        self.to_one = _shift_matrix(self.length - 1, 1, order)
        slope = lam - _ONE
        endpoint_slope = slope / lam
        exponents = [Fraction(j, 4) for j in range(4)]
        self.undo_one = tuple(_unit(endpoint_slope, -a, order) for a in exponents)
        self.apply_zero = tuple(_unit(slope, a, self.length) for a in exponents)
        self.undo_zero = tuple(_unit(slope, -a, self.length) for a in exponents)
        self.apply_one = tuple(_unit(endpoint_slope, a, order) for a in exponents)
        self.inverse_width = Gaussian(Fraction(1, 4))

    def _evaluate(self, rows):
        lifted = []
        for j, row in enumerate(_rows(rows, self.order)):
            endpoint = _jet_product(row, self.undo_one[j], self.order)
            polynomial = _shift(endpoint, self.to_zero)
            lifted.append(_jet_product(polynomial, self.apply_zero[j], self.length))
        return list(zip(*(_dft4(column) for column in zip(*lifted))))

    def multiply(self, left, right):
        """Lift at one, multiply via split evaluation at zero, recover at one."""
        products = [_jet_product(a, b, self.length)
                    for a, b in zip(self._evaluate(left), self._evaluate(right))]
        recovered = zip(*(_dft4(column, inverse=True) for column in zip(*products)))
        result = []
        for j, row in enumerate(recovered):
            scaled = [value * self.inverse_width for value in row]
            polynomial = _jet_product(scaled, self.undo_zero[j], self.length)
            if polynomial[-1] != _ZERO:
                raise ArithmeticError("lifted product exceeds degree 2r-1")
            endpoint = _shift(polynomial[:-1], self.to_one)
            result.append(_jet_product(endpoint, self.apply_one[j], self.order))
        return result


def schoolbook_product(left, right, lam, order):
    """Direct truncated convolution and one monic binomial reduction."""
    lam = _parameters(lam, order)
    left, right = _rows(left, order), _rows(right, order)
    dense = [[_ZERO] * order for _ in range(7)]
    for j, a in enumerate(left):
        for k, b in enumerate(right):
            for u, coefficient in enumerate(a):
                for v in range(order - u):
                    dense[j + k][u + v] += coefficient * b[v]
    for j in range(3):
        tail = dense[j + 4]
        if lam != _ONE:
            tail = [lam * value for value in tail]
        dense[j] = [a + b for a, b in zip(dense[j], tail)]
    return dense[:4]


def cyclic5_product(left, right):
    """Multiply rational five-coefficient vectors modulo X**5-1 via the split."""
    if len(left) != 5 or len(right) != 5:
        raise ValueError("five coefficients required per operand")
    left = tuple(map(_scalar, left))
    right = tuple(map(_scalar, right))
    if any(v.imag for v in (*left, *right)):
        raise ValueError("rational cyclic coefficients required")
    left_scalar, a = prime5_split(left)
    right_scalar, b = prime5_split(right)
    product = _prime5_plan().multiply([(v,) for v in a], [(v,) for v in b])
    recovered = prime5_join(left_scalar * right_scalar, [row[0] for row in product])
    if any(v.imag for v in recovered):
        raise ArithmeticError("cyclic product did not descend to the rationals")
    return [v.real for v in recovered]


@cache
def _prime5_plan():
    lam, _ = prime5_constants()
    return WidthFourPlan(lam, 1)
