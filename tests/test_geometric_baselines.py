from random import Random

import pytest

from nextfft_lab.exact import P, root
from nextfft_lab.geometric_baselines import GeometricChirp, divided_difference_geometric, horner_geometric


@pytest.mark.parametrize("n,q", [(1, 1), (4, 3), (7, 3), (8, root(8)), (17, root(17))])
def test_chirp_and_interpolation(n, q):
    chirp = GeometricChirp.build(n, q)
    rng = Random(n)
    for x in [[int(i == j) for i in range(n)] for j in range(n)] + [[rng.randrange(P) for _ in range(n)]]:
        y = [sum(v * pow(q, i * j, P) for j, v in enumerate(x)) % P for i in range(n)]
        assert chirp.apply(x) == horner_geometric(x, q) == y
        assert divided_difference_geometric(y, q) == x


def test_invalid():
    with pytest.raises(ValueError):
        GeometricChirp.build(4, P - 1)
    with pytest.raises(ValueError):
        GeometricChirp.build(2, 3).apply([1])
