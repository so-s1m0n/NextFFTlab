from random import Random

import pytest

from nextfft_lab.binary_template import compile_binary_square_template
from nextfft_lab.exact import P
from nextfft_lab.walsh import walsh


@pytest.mark.parametrize("inverse", [False, True])
def test_materialized_shared_template(inverse):
    rng = Random(938)
    plan = compile_binary_square_template()
    assert (plan.rows_per_label, plan.stages) == (128, 16)
    if inverse:
        labels = [[[0] * 256 for _ in range(128)] for _ in range(4)]
        for label in range(4):
            labels[label][31 * label][85 * label] = label + 1
    else:
        labels = [[[rng.randrange(P) for _ in range(256)] for _ in range(128)]
                  for _ in range(4)]
    expected = [[walsh(row, inverse=inverse) for row in block] for block in labels]
    assert plan.apply(labels, inverse=inverse) == expected
