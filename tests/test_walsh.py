from random import Random

import pytest

from nextfft_lab.exact import P
from nextfft_lab.walsh import direct_walsh, walsh


@pytest.mark.parametrize("size", [1, 2, 4, 8, 16, 32])
def test_character_columns(size):
    for index in range(size):
        basis = [int(index == j) for j in range(size)]
        expected = [P - 1 if (index & k).bit_count() % 2 else 1 for k in range(size)]
        assert direct_walsh(basis) == walsh(basis) == expected
        assert walsh(expected, inverse=True) == basis


@pytest.mark.parametrize("size", [1, 8, 64, 128])
def test_seeded_signed_input(size):
    rng = Random(20261126 + size)
    row = [rng.randrange(-2 * P, 2 * P) for _ in range(size)]
    assert walsh(iter(row)) == direct_walsh(row)
    assert walsh(row, inverse=True) == direct_walsh(row, inverse=True)
    assert walsh(walsh(row), inverse=True) == [value % P for value in row]


@pytest.mark.parametrize("transform", [walsh, direct_walsh])
@pytest.mark.parametrize("row", [[], [0] * 3, [0] * 6])
def test_unsupported_length(transform, row):
    with pytest.raises(ValueError, match="power of two"):
        transform(row)
