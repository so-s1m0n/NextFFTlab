"""Stride-based evaluation of a tensor matrix root at one scalar query tuple."""
from dataclasses import dataclass

from .exact import P
from .matrix_pencil import _matrix_root_inputs


@dataclass(frozen=True)
class ImplicitMatrixPencil:
    radix: int
    rows: int
    variable_count: int
    factors: tuple
    phases: tuple

    def apply_power(self, values, variables):
        """Apply the root radix times with no materialized transition table."""
        current = list(values)
        variables = (1, *variables)
        if len(current) != self.rows or len(variables) != self.variable_count + 1:
            raise ValueError("pencil row or variable count mismatch")
        tables = [tuple(sum(variables[i] * coeff for i, coeff in form) % P for form in term)
                  for term in self.factors]
        for _ in range(self.radix):
            out = [0] * self.rows
            for source, value in enumerate(current):
                prefix = 0
                stride = 1
                for factors in tables:
                    digit = (source // stride) % self.radix
                    coefficient = factors[digit]
                    if coefficient:
                        dest = source + ((digit + 1) % self.radix - digit) * stride
                        phase = self.phases[prefix % self.radix]
                        out[dest] = (out[dest] + coefficient * phase * value) % P
                    prefix += digit
                    stride *= self.radix
            current = out
        return current


def compile_implicit_matrix_root(radix, terms):
    xi, terms, width, rows = _matrix_root_inputs(radix, terms)
    factors = tuple(tuple(tuple((i, c % P) for i, c in enumerate(form) if c % P)
                          for form in term) for term in terms)
    return ImplicitMatrixPencil(radix, rows, width - 1, factors,
                                tuple(pow(xi, j, P) for j in range(radix)))


def endpoint_factors(m):
    """Three products of affine forms for the odd [1,m-1] window."""
    if not isinstance(m, int) or not 3 <= m <= 15 or m % 2 == 0:
        raise ValueError("endpoint pencil requires odd 3 <= m <= 15")
    neg_half = -pow(2, -1, P)
    terms = []
    for shift, scale in ((0, 1), (1, neg_half), (-1, neg_half)):
        forms = []
        for variable in range(m):
            factor = scale if variable == 0 else 1
            forms.append((factor * shift, *(factor if i == variable else 0 for i in range(m))))
        terms.append(tuple(forms))
    return tuple(terms)
