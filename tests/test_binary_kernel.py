from random import Random

import pytest

from nextfft_lab.binary_kernel import binary_endpoint, binary_query, binary_rank, binary_rectangles
from nextfft_lab.exact import P
from nextfft_lab.walsh import direct_walsh, walsh


@pytest.mark.parametrize("m,aux,columns", [(3, 0, 1), (3, 1, 1), (3, 0, 2), (5, 1, 1)])
def test_query_multipliers_and_monomial_identity(m, aux, columns):
    half_bits = (m + aux) * columns
    size = 1 << (2 * half_bits)
    rng = Random(242)
    row = [rng.randrange(P) for _ in range(size)]
    spectra = walsh(row)
    half_mask = (1 << half_bits) - 1
    mask_unit = (1 << columns) - 1
    for j in range(m):
        mask = (mask_unit << (j * columns)) | (half_mask ^ ((1 << (m * columns)) - 1))
        want = [(-value if (k & (k >> half_bits) & mask).bit_count() % 2 else value) % P
                for k, value in enumerate(spectra)]
        assert walsh(binary_query(row, m, aux, columns, j)) == want

    corrected = binary_endpoint(row, m, aux, columns)
    reverse = corrected
    for j in range(m):
        corrected = binary_query(corrected, m, aux, columns, j)
        reverse = binary_query(reverse, m, aux, columns, m - j - 1)
    assert corrected == reverse
    assert binary_endpoint(corrected, m, aux, columns, output=True) == walsh(row)


def test_kernel_identity_on_every_basis_at_length_64():
    for i in range(64):
        basis = [int(i == j) for j in range(64)]
        corrected = binary_endpoint(basis, 3, 0, 1)
        for j in range(3):
            corrected = binary_query(corrected, 3, 0, 1, j)
        assert binary_endpoint(corrected, 3, 0, 1, output=True) == direct_walsh(basis)


@pytest.mark.parametrize("length,alphabet", [(2, 2), (2, 4), (3, 2), (4, 2), (2, 8), (3, 4)])
def test_rectangles_are_identity_and_free_rectangles_are_orthogonal(length, alphabet):
    gram, rectangles = binary_rectangles(length, alphabet)
    n = alphabet**length
    transfer = [[0] * n for _ in range(n)]
    for rect in rectangles:
        for source in rect.sources:
            for destination in rect.destinations:
                transfer[destination][source] = (transfer[destination][source] + rect.weight) % P
                if not rect.charged:
                    assert not (gram[source] >> destination & 1)
    assert transfer == [[int(i == j) for j in range(n)] for i in range(n)]
    assert 0 < binary_rank(gram) <= n


def test_kernel_limits():
    with pytest.raises(ValueError, match="odd"):
        binary_query([], 4, 0, 1, 0)
    with pytest.raises(ValueError, match="4096"):
        binary_query([], 3, 1, 2, 0)
    with pytest.raises(ValueError, match="size"):
        binary_endpoint([0], 3, 0, 1)
    with pytest.raises(ValueError, match="64 labels"):
        binary_rectangles(4, 4)
