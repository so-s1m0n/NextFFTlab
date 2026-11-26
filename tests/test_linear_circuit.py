import json
from pathlib import Path
from random import Random

import pytest

from nextfft_lab.exact import P
from nextfft_lab.linear_circuit import (
    LinearCircuit, butterfly_circuit, tensor_walsh_circuit, verify_walsh,
)
from nextfft_lab.walsh import walsh
from nextfft_lab.walsh_search import sussman_h8_circuit, synthesize_rank_one


@pytest.mark.parametrize("size", [1, 2, 4, 8, 64])
def test_butterfly_circuit(size):
    circuit = butterfly_circuit(size)
    rng = Random(size)
    row = [rng.randrange(-P, P) for _ in range(size)]
    assert verify_walsh(circuit)
    assert circuit.evaluate(row) == walsh(row)
    stats = circuit.counts()
    assert stats["binary_gates"] == stats["adds_subtracts"] == size * (size.bit_length() - 1)
    assert stats["scalar_multiplications"] == 0
    assert stats["binary_depth"] == size.bit_length() - 1


@pytest.mark.parametrize("size,dist,gate_count", [(4, 24, 7), (8, 13440, 22)])
def test_synthesized_result(size, dist, gate_count):
    result = synthesize_rank_one(size)
    assert result.configurations == dist
    assert result.circuit.counts()["binary_gates"] == gate_count
    assert verify_walsh(result.circuit)
    assert LinearCircuit.from_dict(json.loads(json.dumps(result.circuit.to_dict()))) == result.circuit


@pytest.mark.parametrize("size,gates,muls", [(8, 19, 9), (16, 54, 18), (64, 304, 80), (512, 3648, 704)])
def test_published_h8_and_tensor_lift(size, gates, muls):
    circuit = tensor_walsh_circuit(sussman_h8_circuit(), size)
    assert verify_walsh(circuit)
    assert circuit.counts()["binary_gates"] == gates
    assert circuit.counts()["scalar_multiplications"] == muls


@pytest.mark.parametrize("name", ["rank-one-h4", "rank-one-h8", "sussman-h8"])
def test_saved_circuit_is_valid(name):
    path = Path(__file__).resolve().parents[1] / "results" / "circuits" / f"{name}.json"
    assert verify_walsh(LinearCircuit.from_dict(json.loads(path.read_text(encoding="utf-8"))))


def test_bad_schema_coefficients_and_references():
    with pytest.raises(ValueError):
        LinearCircuit.from_dict({"schema": "nextfft-linear-circuit-v1", "field": 2})
    with pytest.raises(ValueError, match="reference"):
        LinearCircuit(2, ((1, 2, 1, 0),), ((2, 1), (1, 1)))
    with pytest.raises(ValueError):
        butterfly_circuit(1024)
    with pytest.raises(ValueError):
        synthesize_rank_one(16)
    with pytest.raises(ValueError):
        butterfly_circuit(8).evaluate([0])
    with pytest.raises(ValueError):
        tensor_walsh_circuit(butterfly_circuit(8), 4)
    broken = LinearCircuit(2, (), ((0, 1), (1, 1)))
    assert not verify_walsh(broken)
