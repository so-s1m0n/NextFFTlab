from random import Random

import pytest

from nextfft_lab.exact import P, root
from nextfft_lab.geometric_baselines import GeometricChirp, divided_difference_geometric
from nextfft_lab.geometric_interpolation import BostanSchostPlan


@pytest.mark.parametrize("n,q", [(1, 1), (7, 3), (8, 3), (7, root(7)), (16, root(16)), (17, 3)])
def test_interpolation_matches_independent_divided_differences(n, q):
    plan = BostanSchostPlan.build(n, q)
    rng = Random(n)
    for values in [[int(i == j) for i in range(n)] for j in range(n)] + [
        [rng.randrange(P) for _ in range(n)]
    ]:
        expected = divided_difference_geometric(values, q)
        assert plan.interpolate(values) == expected
        assert [sum(c * pow(q, i * j, P) for j, c in enumerate(expected)) % P
                for i in range(n)] == values


def test_non_root_grid_product():
    left, right = [1, 2, 0, 7], [P - 1, 2, 8]
    n = len(left) + len(right) - 1
    evaluate = GeometricChirp.build(n, 3)
    interpolate = BostanSchostPlan.build(n, 3)
    a = evaluate.apply(left + [0] * (n - len(left)))
    b = evaluate.apply(right + [0] * (n - len(right)))
    expected = [sum(x*y for j, x in enumerate(left) for k, y in enumerate(right) if j+k == i) % P
                for i in range(n)]
    assert interpolate.interpolate([x*y % P for x, y in zip(a, b)]) == expected


def test_rejects_invalid_grid_and_sample_length():
    with pytest.raises(ValueError):
        BostanSchostPlan.build(0, 3)
    with pytest.raises(ValueError):
        BostanSchostPlan.build(513, 3)
    with pytest.raises(ValueError):
        BostanSchostPlan.build(1, 0)
    with pytest.raises(ValueError):
        BostanSchostPlan.build(4, P - 1)
    with pytest.raises(ValueError):
        BostanSchostPlan.build(3, 3).interpolate([1, 2])
