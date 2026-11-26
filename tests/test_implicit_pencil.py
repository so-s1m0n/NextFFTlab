from random import Random

import pytest

from nextfft_lab.exact import P
from nextfft_lab.implicit_pencil import compile_implicit_matrix_root, endpoint_factors
from nextfft_lab.matrix_pencil import matrix_root, scalar_stage
from nextfft_lab.window_search import endpoint_predictor


def test_implicit_equals_materialized_on_basis():
    terms = [[(3, 2, 0), (1, 0, 1)], [(5, 0, -1)]]
    implicit = compile_implicit_matrix_root(4, terms)
    explicit = matrix_root(4, terms)
    for index in range(implicit.rows):
        values = [int(index == i) for i in range(implicit.rows)]
        expected = values
        for _ in range(4):
            expected = scalar_stage(explicit, expected, (9, P - 7))
        assert implicit.apply_power(values, (9, P - 7)) == expected


@pytest.mark.parametrize("count", [0, 6, 15])
def test_m15_implicit_one_shift_on_independent_rows(count):
    rng = Random(20261126 + count)
    pencil = compile_implicit_matrix_root(16, endpoint_factors(15))
    assert pencil.rows == 4096
    values = [rng.randrange(P) for _ in range(pencil.rows)]
    signs = [1] * (15 - count) + [-1] * count
    expected = endpoint_predictor(signs)
    assert pencil.apply_power(values, signs) == [expected * value % P for value in values]


def test_implicit_rejects_oversized_or_wrong_shape():
    with pytest.raises(ValueError, match="above"):
        compile_implicit_matrix_root(32, endpoint_factors(15))
    with pytest.raises(ValueError, match="mismatch"):
        compile_implicit_matrix_root(2, [[(0, 1)]]).apply_power([1], [1])
