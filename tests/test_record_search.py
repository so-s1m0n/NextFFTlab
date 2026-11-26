from dataclasses import replace
from fractions import Fraction
import json

import pytest

from nextfft_lab.circuit_rewrites import cse, search_rewrites
from nextfft_lab.circuit_scaling import search_wire_scales
from nextfft_lab.circuit_schedule import reduce_live_wires
from nextfft_lab.exact import P
from nextfft_lab.linear_circuit import butterfly_circuit
from nextfft_lab.projective_search import projective_exchange
from nextfft_lab.rational_circuit import RationalCircuit, parse_slp
from nextfft_lab.schedule_exact import improve_schedule_exact
from nextfft_lab.walsh_search import sussman_h8_circuit


def _butterflies():
    circuit = butterfly_circuit(4)
    return RationalCircuit(4, circuit.ops, tuple(w for w, _ in circuit.outputs), Fraction(1))


def _published_half():
    source = sussman_h8_circuit()
    ops = tuple((Fraction(1, 2) if a == -(P - 1) // 2 else Fraction(a), u, Fraction(b), v)
                for a, u, b, v in source.ops)
    return RationalCircuit(8, ops, tuple(w for w, _ in source.outputs), Fraction(1, 2))


def test_parse_and_export_without_executing_slp():
    text = """p=x0+x1
q=x0-x1
r=x2+x3
s=x2-x3
y0=p+r
y1=q+s
y2=p-r
y3=q-s"""
    program = parse_slp(text, 4)
    assert program.verify_rational() and program.verify_field()
    assert RationalCircuit.from_dict(json.loads(json.dumps(program.to_dict()))) == program
    for expression in ("p + unknown", "p;sys", "print(x1)", "p+x1*x2"):
        with pytest.raises(ValueError):
            parse_slp(text.replace("p+r", expression), 4)


def test_identifies_a_field_only_equivalence():
    circuit = _butterflies()
    a, u, b, v = circuit.ops[0]
    changed = replace(circuit, ops=((a + P, u, b, v),) + circuit.ops[1:])
    assert changed.verify_field()
    assert not changed.verify_rational()


def test_rewriting_eliminates_duplicate_and_disconnected_wire():
    circuit = _butterflies()
    extra = circuit.inputs + len(circuit.ops)
    extended = replace(circuit, ops=circuit.ops + (circuit.ops[-1], circuit.ops[0]),
                       outputs=circuit.outputs[:-1] + (extra,))
    assert cse(extended) == circuit
    best, result = search_rewrites(extended, "arithmetic")
    assert best.verify_rational() and best.verify_field()
    assert best.cost()["scaled_arithmetic"] <= 8
    assert result["neighborhood_candidates"] > 0


def test_schedule_certifies_equivalence_at_its_pressure_bound():
    start = _published_half()
    heuristic, record = reduce_live_wires(start)
    exact, bounds = improve_schedule_exact(heuristic)
    assert record["orders_tested"] == 256
    assert bounds["attempts"]
    assert exact.cost()["peak_live_wires"] <= start.cost()["peak_live_wires"]
    assert exact.cost()["scaled_arithmetic"] == start.cost()["scaled_arithmetic"]
    assert exact.verify_rational() and exact.verify_field()


def test_fixed_dag_scale_unsat_at_19():
    pytest.importorskip("z3")
    start = _published_half()
    best, result = search_wire_scales(start, 19)
    assert result["attempts"] == [{"goal_probe": False, "max_scalar_copies": 0, "status": "unsat"}]
    assert best.cost()["scaled_arithmetic"] == 20
    assert best.verify_rational() and best.verify_field()


def test_exact_helper_exchange_stays_within_its_declared_pool():
    result, log = projective_exchange(_published_half())
    assert log["base_directions"] == 27
    assert log["baseline_helpers"] == 11
    if result is None:
        assert log["stop"] == "exhausted"
        assert log["one_deletion"] == 11
        assert log["two_deletions_one_exchange"] == 55 * log["admitted_extras"]
    else:
        assert result.verify_rational() and result.verify_field()
        assert result.cost()["gates"] <= 18
