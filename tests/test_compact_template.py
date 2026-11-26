from random import Random

import pytest

import nextfft_lab.compact_template as compact
from nextfft_lab.exact import P
from nextfft_lab.walsh import walsh


def test_compact_routing_matches_dense_single_stage_and_counts_calls(monkeypatch):
    plan = compact.compile_compact_square_template(32)
    rng = Random(11)
    batch = [[[rng.randrange(P) for _ in range(256)] for _ in range(32)] for _ in range(4)]
    matrices = [[[0] * 32 for _ in range(32)] for _ in range(4)]
    for matrix, edges in zip(matrices, plan.edges):
        for dest, source, coeff in edges:
            matrix[dest][source] = coeff
    expected = plan.routing.apply(batch, matrices[1:], matrices[0])
    calls = []
    original = compact._pair_query

    def counted(row, position, half_bits):
        calls.append(position)
        return original(row, position, half_bits)

    monkeypatch.setattr(compact, "_pair_query", counted)
    assert plan.stage(batch) == expected
    assert len(calls) == plan.pair_calls_per_stage == 384


@pytest.mark.parametrize("width,inverse", [(128, False), (32, True)])
def test_compact_template_exact_and_independent(width, inverse):
    rng = Random(17)
    batch = [[[rng.randrange(P) for _ in range(256)] for _ in range(width)] for _ in range(4)]
    expected = [[walsh(row, inverse=inverse) for row in block] for block in batch]
    assert compact.compile_compact_square_template(width).apply(batch, inverse=inverse) == expected


def test_compact_rejects_oversized_batch():
    with pytest.raises(ValueError, match="maximum"):
        compact.compile_compact_square_template(160)
