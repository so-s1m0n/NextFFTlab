"""Bounded matrix-pencil and spectral repair for binary XOR queries."""
from dataclasses import dataclass
from itertools import combinations, product
from math import comb

from .exact import P, root
from .matrix_pencil import MAX_PENCIL_ROWS, matrix_root
from .predictor import window
from .query_polynomial import compile_query_polynomial
from .spectral_repair import RepairPlan, compile_repair

MAX_ESTIMATED_OPERATIONS = 2_000_000


def binary_degree_coefficients(polynomial):
    """Coefficients by degree before the shift signs of the selected terms."""
    if polynomial.radix != 2:
        raise ValueError("binary query polynomial required")
    half = pow(2, -1, P)
    width = len(polynomial.weights) - 1
    m = len(polynomial.affine_factors)
    # All factors have constant term 1+T/2 and variable term +/-T/2.
    # Move the fixed initial series into the final linear functional.
    functional = [
        sum(a * b for a, b in zip(polynomial.initial_series,
                                   polynomial.weights[degree:])) % P
        for degree in range(width + 1)
    ]
    return tuple(
        pow(half, degree, P) * sum(
            comb(m - degree, h) * pow(half, h, P) * functional[degree + h]
            for h in range(min(m - degree, width - degree) + 1)
        ) % P
        for degree in range(polynomial.degree_bound + 1)
    )


@dataclass(frozen=True)
class BinaryRepair:
    pencils: tuple
    repair: RepairPlan

    @property
    def size(self):
        return len(self.repair.frequencies)

    def predict(self, rows):
        # Q_j is XOR by 2**j in ordinary coordinates and a sign under Walsh.
        out = []
        for block, pencil in enumerate(self.pencils):
            start = block * pencil.rows
            current = rows[start:start + pencil.rows]
            for _ in range(pencil.radix):
                result = [[0] * self.size for _ in current]
                for source, transitions in zip(current, pencil.columns):
                    for destination, form in transitions:
                        target = result[destination]
                        for term, coefficient in enumerate(form):
                            if not coefficient:
                                continue
                            mask = 0 if term == 0 else 1 << (term - 1)
                            for i in range(self.size):
                                target[i] = (target[i] + coefficient * source[i ^ mask]) % P
                current = result
            out.extend(current)
        return out

    def apply(self, batch):
        return self.repair.apply(batch, self.predict)


def compile_binary_repair(m, bounds=None):
    """Build a small binary instance using base-field Vandermonde nodes.

    None selects the paper's concentration window. Explicit limits are
    experiments with potentially different exceptional fractions.
    """
    default = window(m)
    if m >= MAX_PENCIL_ROWS.bit_length():
        raise ValueError(f"2^{m} shift blocks exceed the {MAX_PENCIL_ROWS}-row budget")
    lower, upper = default if bounds is None else bounds
    interpolation_width = upper - lower
    if interpolation_width < 0:
        raise ValueError("invalid window")
    radix = 1 << (max(2, interpolation_width) - 1).bit_length()
    root(radix)
    zero_shift = compile_query_polynomial((0,) * m, bounds=bounds)
    coefficients = binary_degree_coefficients(zero_shift)
    term_count = sum(comb(m, degree) for degree, a in enumerate(coefficients) if a)
    # Represent a zero polynomial with one zero factor so that the pencil still exists.
    width_bits = m + (radix.bit_length() - 1) * max(term_count, 1)
    if width_bits >= MAX_PENCIL_ROWS.bit_length():
        raise ValueError(f"radix {radix}, {term_count} terms, 2^{width_bits} rows exceeds budget")
    width, size = 1 << width_bits, 1 << m
    block_width = width // size
    outside = sum(comb(m, count) for count in range(m + 1) if not lower <= count <= upper)
    checks = outside * block_width
    predictor_calls = 4 if checks else 1
    work = (
        width * size * (max(term_count, 1) * radix * predictor_calls + 4 * checks)
        + 2 * size * checks * checks + size * checks * checks * checks
    )
    if work > MAX_ESTIMATED_OPERATIONS:
        raise ValueError(f"{width} rows, {size} frequencies, {checks} checks exceed work budget ({work})")

    shifts = tuple(product(range(2), repeat=m))
    unit_forms = tuple((0, *(int(i == j) for i in range(m))) for j in range(m))
    pencils, polynomials = [], []
    for shift in shifts:
        polynomial = compile_query_polynomial(shift, bounds=bounds)
        polynomials.append(polynomial)
        shift_scale = -1 if sum(shift) % 2 else 1
        terms = []
        for degree, coefficient in enumerate(coefficients):
            if not coefficient:
                continue
            for variables in combinations(range(m), degree):
                negatives = sum(1 - shift[j] for j in variables)
                scalar = coefficient * shift_scale * (-1 if negatives % 2 else 1) % P
                if not variables:
                    terms.append(((scalar, *((0,) * m)),))
                    continue
                first, *rest = variables
                terms.append((tuple(scalar * value for value in unit_forms[first]),
                              *(unit_forms[j] for j in rest)))
        pencils.append(matrix_root(radix, terms or [((0,) * (m + 1),)]))

    frequencies = []
    for frequency in range(size):
        digits = tuple((frequency >> bit) & 1 for bit in range(m))
        powers = tuple((P - 1 if bit else 1,) for bit in digits)
        exceptions, multipliers = [], []
        for block, (shift, polynomial) in enumerate(zip(shifts, polynomials)):
            # This integer count selects spectral metadata only.
            count = sum(a ^ b for a, b in zip(digits, shift))
            if not lower <= count <= upper:
                exceptions.extend(range(block * block_width, (block + 1) * block_width))
                multipliers.extend([polynomial.evaluate(powers)] * block_width)
        frequencies.append((P - 1 if frequency.bit_count() % 2 else 1, exceptions, multipliers))
    return BinaryRepair(tuple(pencils), compile_repair(range(width), frequencies))
