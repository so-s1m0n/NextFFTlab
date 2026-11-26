from itertools import product

import pytest

from nextfft_lab.binary_kernel import binary_rank
from nextfft_lab.routing_bounds import binary_hamming_gram_rank


@pytest.mark.parametrize("length,alphabet", [(1, 2), (6, 2), (1, 4), (2, 4), (3, 4), (2, 6), (2, 8)])
def test_gram_rank_formula_by_elimination(length, alphabet):
    labels = tuple(product(range(alphabet), repeat=length))
    gram = [sum((1 << j) for j, y in enumerate(labels)
                if sum(a != b for a, b in zip(x, y)) % 2 == 0) for x in labels]
    assert binary_hamming_gram_rank(length, alphabet) == binary_rank(gram)


def test_gram_rank_rejects_unsupported_parameters():
    with pytest.raises(ValueError):
        binary_hamming_gram_rank(0, 2)
    with pytest.raises(ValueError):
        binary_hamming_gram_rank(2, 3)
