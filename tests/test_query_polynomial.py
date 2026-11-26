from itertools import product
from random import Random

import pytest

from nextfft_lab.exact import P, root
from nextfft_lab.predictor import predict, window
from nextfft_lab.query_polynomial import compile_query_polynomial


def query_powers(digits, ell):
    return [tuple(pow(root(ell), digit * a, P) for a in range(1, ell))
            for digit in digits]


@pytest.mark.parametrize("bounds", [(1, 2), (2, 2), (4, 5), (-2, 3), None])
def test_exhaustive_binary_shifts(bounds):
    digits = list(product(range(2), repeat=3))
    for shift in digits:
        polynomial = compile_query_polynomial(shift, bounds=bounds)
        for k in digits:
            assert polynomial.evaluate(query_powers(k, 2)) == predict(k, shift, bounds=bounds)[0]


@pytest.mark.parametrize("ell,m", [(2, 128), (7, 16), (17, 16)])
def test_general_window(ell, m):
    rng = Random(42 + ell)
    shift = [rng.randrange(ell) for _ in range(m)]
    polynomial = compile_query_polynomial(shift, ell)
    lower, upper = window(m, ell)
    assert polynomial.degree_bound == min(upper - lower, m)
    for k in ([(-b) % ell for b in shift], [(ell - 1 - b) % ell for b in shift],
              *([rng.randrange(ell) for _ in range(m)] for _ in range(4))):
        want, target, inside = predict(k, shift, ell)
        assert polynomial.evaluate(query_powers(k, ell)) == want
        if inside:
            assert want == target


def test_affine_variable_and_term_bound_in_toy_window():
    polynomial = compile_query_polynomial([0, 0, 0], bounds=(1, 2))
    assert polynomial.evaluate([(7,), (11,), (19,)]) == P - 37
    assert polynomial.degree_bound == 1
    assert polynomial.expanded_term_bound == 4


def test_invalid_inputs():
    with pytest.raises(ValueError):
        compile_query_polynomial([0, 2])
    with pytest.raises(ValueError):
        compile_query_polynomial([0, 0], ell=3)
    with pytest.raises(ValueError):
        compile_query_polynomial([0, 0], bounds=(2, 1))
    polynomial = compile_query_polynomial([0, 0], bounds=(1, 1))
    with pytest.raises(ValueError):
        polynomial.evaluate([(), ()])
