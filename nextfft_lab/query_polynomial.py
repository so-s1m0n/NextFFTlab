"""Factored query-power polynomial from repair.tex, lem:count-predict."""
from dataclasses import dataclass
from math import comb

from .exact import P, root
from .predictor import _binomial, window


@dataclass(frozen=True)
class QueryPolynomial:
    """One affine form per digit and positive T degree, then a truncated product."""

    radix: int
    affine_factors: tuple
    initial_series: tuple
    weights: tuple
    degree_bound: int
    expanded_term_bound: int

    def evaluate(self, query_powers):
        """Evaluate at supplied query powers, without decoding an integer count."""
        rows = tuple(tuple(row) for row in query_powers)
        if len(rows) != len(self.affine_factors) or any(
            len(row) != self.radix - 1 for row in rows
        ):
            raise ValueError("one row of nonconstant powers per query required")

        series = list(self.initial_series)
        for powers, forms in zip(rows, self.affine_factors):
            product = series.copy()
            for degree, form in enumerate(forms, start=1):
                coefficient = (form[0] + sum(
                    scalar * value for scalar, value in zip(form[1:], powers)
                )) % P
                for index in range(degree, len(series)):
                    product[index] = (product[index] + coefficient * series[index - degree]) % P
            series = product
        return sum(coefficient * weight for coefficient, weight in zip(series, self.weights)) % P


def compile_query_polynomial(beta, ell=2, bounds=None):
    """Precompute field coefficients for a shift; custom bounds are for experiments."""
    beta = tuple(beta)
    default = window(len(beta), ell)
    if any(not isinstance(digit, int) or not 0 <= digit < ell for digit in beta):
        raise ValueError("shift digits must be integers in range")
    lower, upper = default if bounds is None else bounds
    if not isinstance(lower, int) or not isinstance(upper, int) or lower > upper:
        raise ValueError("invalid window")

    degree = upper - lower
    zeta = root(ell)
    inv_ell = pow(ell, -1, P)
    # I_{j,d} contributes zeta**(a*(beta_j-d))/ell to the a-th power.
    unshifted = [
        tuple(inv_ell * sum(
            comb(digit, exponent) * pow(zeta, -power * digit, P)
            for digit in range(exponent, ell)
        ) % P for power in range(ell))
        for exponent in range(1, min(ell - 1, degree) + 1)
    ]
    factors = tuple(
        tuple(tuple(value * pow(zeta, power * shift, P) % P
                    for power, value in enumerate(form))
              for form in unshifted)
        for shift in beta
    )
    scale = pow(zeta, lower - sum(beta), P)
    degree_bound = min(degree, len(beta))
    return QueryPolynomial(
        ell,
        factors,
        tuple(_binomial(-lower, h) % P for h in range(degree + 1)),
        tuple(scale * pow(zeta - 1, h, P) % P for h in range(degree + 1)),
        degree_bound,
        sum(comb(len(beta), d) * (ell - 1)**d for d in range(degree_bound + 1)),
    )
