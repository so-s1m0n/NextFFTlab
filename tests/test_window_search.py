from itertools import product
from math import comb

import pytest

from nextfft_lab.exact import P
from nextfft_lab.predictor import predict
from nextfft_lab.window_search import (
    endpoint_predictor, endpoint_shift_masks, narrowest_symmetric_window, window_cost,
)


@pytest.mark.parametrize("m", [2, 3, 8, 13, 15, 16, 25, 63, 128, 256])
def test_window_is_minimal_by_integer_binomial_enumeration(m):
    low, high, count = narrowest_symmetric_window(m)
    valid = []
    for u in range(m // 2 + 1):
        v = m - u
        tail = sum(comb(m, k) for k in range(m + 1) if not u <= k <= v)
        if 2 * m**3 * tail <= 1 << m:
            valid.append((u, v, tail))
    assert (low, high, count) == valid[-1]


def test_m15_factorization_and_cost():
    assert narrowest_symmetric_window(15) == (1, 14, 2)
    assert 2 * sum(comb(15, k) for k in (0, 1)) == 32
    stats = window_cost(15, (1, 14))
    assert (stats["degree"], stats["expanded_terms"], stats["endpoint_factored_log2_rows_upper"]) == (
        13, 16383, 27
    )
    for count in range(16):
        digits = [1] * count + [0] * (15 - count)
        assert endpoint_predictor(1 - 2 * k for k in digits) == predict(
            digits, [0] * 15, bounds=(1, 14)
        )[0]


def test_small_cube_and_unsupported_input():
    for q in product((1, P - 1), repeat=5):
        digits = [int(value == P - 1) for value in q]
        assert endpoint_predictor(q) == predict(digits, [0] * 5, bounds=(1, 4))[0]
    with pytest.raises(ValueError):
        endpoint_predictor([1] * 4)
    with pytest.raises(ValueError):
        narrowest_symmetric_window(1025)


def test_m15_reduced_end_shift_cover_is_tight_at_every_frequency():
    masks = endpoint_shift_masks(15)
    assert len(masks) == 6750
    incidences = [int(k in masks) + int((k ^ 32767) in masks) for k in range(32768)]
    assert (max(incidences), sum(incidences)) == (1, 2 * len(masks))
    assert 2 * 15**3 * max(incidences) == len(masks)
    with pytest.raises(ValueError, match="exceeds"):
        endpoint_shift_masks(13)
