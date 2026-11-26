"""Sparse matrix root from repair.tex, lem:matrix-root, over F_998244353."""
from dataclasses import dataclass

from .exact import P, root

MAX_PENCIL_ROWS = 4096


@dataclass(frozen=True)
class MatrixPencil:
    radix: int
    columns: tuple

    @property
    def rows(self):
        return len(self.columns)


def _matrix_root_inputs(radix, terms):
    if radix < 2 or radix & (radix - 1):
        raise ValueError("matrix root requires a power-of-two radix")
    xi = root(radix)
    terms = tuple(tuple(tuple(form) for form in term) for term in terms)
    if not terms or not terms[0] or not terms[0][0]:
        raise ValueError("provide at least one product of affine forms")
    form_width = len(terms[0][0])
    if any(not term or len(term) > radix or any(len(form) != form_width for form in term)
           for term in terms):
        raise ValueError("each term must contain 1..radix forms of matching width")
    row_bits = (radix.bit_length() - 1) * len(terms)
    if row_bits >= MAX_PENCIL_ROWS.bit_length():
        raise ValueError(f"pencil requires 2^{row_bits} rows, above {MAX_PENCIL_ROWS}")
    unit = (1,) + (0,) * (form_width - 1)
    terms = tuple(term + (unit,) * (radix - len(term)) for term in terms)

    return xi, terms, form_width, 1 << row_bits


def matrix_root(radix, terms):
    """Construct L from products of affine forms in a common variable order."""
    xi, terms, _, rows = _matrix_root_inputs(radix, terms)
    columns = []
    for source in range(rows):
        transitions = []
        prefix = 0
        stride = 1
        for factors in terms:
            digit = (source // stride) % radix
            destination = source + ((digit + 1) % radix - digit) * stride
            phase = pow(xi, prefix, P)
            transitions.append((destination, tuple(phase * value % P for value in factors[digit])))
            prefix += digit
            stride *= radix
        columns.append(tuple(transitions))
    return MatrixPencil(radix, tuple(columns))


def scalar_stage(pencil, values, variables):
    """Evaluate one stage at a scalar tuple to audit the matrix-root identity."""
    values, variables = tuple(values), tuple(variables)
    if len(values) != pencil.rows or len(variables) + 1 != len(pencil.columns[0][0][1]):
        raise ValueError("pencil row or variable count mismatch")
    out = [0] * pencil.rows
    for value, transitions in zip(values, pencil.columns):
        for destination, form in transitions:
            factor = form[0] + sum(a * x for a, x in zip(form[1:], variables))
            out[destination] = (out[destination] + value * factor) % P
    return out
