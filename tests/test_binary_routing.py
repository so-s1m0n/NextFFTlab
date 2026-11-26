from random import Random

import pytest

import nextfft_lab.binary_routing as routing
from nextfft_lab.binary_kernel import binary_query
from nextfft_lab.exact import P


def reference(labels, queries, constant):
    output = []
    for block in labels:
        transformed = [block] + [[binary_query(row, 3, 1, 1, j) for row in block] for j in range(3)]
        result = []
        for dst in range(len(block)):
            result.append([
                sum(matrix[dst][src] * rows[src][address]
                    for matrix, rows in zip([constant, *queries], transformed)
                    for src in range(len(block))) % P
                for address in range(256)
            ])
        output.append(result)
    return output


def test_shared_routing_preserves_cross_row_pencil_and_counts_pair_calls(monkeypatch):
    rng = Random(761)
    matrices = [[[rng.randrange(-8, 8) for _ in range(2)] for _ in range(2)] for _ in range(4)]
    labels = [[[rng.randrange(P) for _ in range(256)] for _ in range(2)] for _ in range(4)]
    queries, constant = matrices[:3], matrices[3]
    expected = reference(labels, queries, constant)
    calls = []
    original = routing._pair_query

    def counted(row, position, half_bits):
        calls.append(position)
        return original(row, position, half_bits)

    monkeypatch.setattr(routing, "_pair_query", counted)
    plan = routing.compile_binary_square_routing()
    assert plan.apply(labels, queries, constant) == expected
    assert len(calls) == 2 * (4 * 3 * 2 + 8 * 2)


def test_each_label_keeps_its_own_basis_inputs():
    plan = routing.compile_binary_square_routing()
    for label in range(4):
        for address in (0, 85, 170, 255):
            inputs = [[[0] * 256] for _ in range(4)]
            inputs[label][0][address] = 1
            matrices = [[[1]], [[9]], [[0]]]
            assert plan.apply(inputs, matrices, [[-2]]) == reference(inputs, matrices, [[-2]])


def test_rejects_malformed_routing_batch():
    plan = routing.compile_binary_square_routing()
    with pytest.raises(ValueError, match="batch shape"):
        plan.apply([[[0]]] * 4, [[[1]]] * 3, [[1]])
