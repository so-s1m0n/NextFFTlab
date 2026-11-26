"""Constrained SMT search over power-of-two wire scales on a fixed DAG."""
from fractions import Fraction
from time import perf_counter

from .rational_circuit import RationalCircuit

EXPONENT_BOUND = 2
SMT_SECONDS = 12
SMT_MEMORY_MIB = 768


def _dyadic(value):
    value = abs(Fraction(value))
    if (not value or value.numerator.bit_count() != 1 or value.denominator.bit_count() != 1):
        raise ValueError("wire-scale search requires dyadic powers")
    return value.numerator.bit_length() - value.denominator.bit_length()


def _collapse(circuit):
    n = circuit.inputs
    aliases = {i: (Fraction(1), i) for i in range(n)}
    ops = []
    for i, (a, u, b, v) in enumerate(circuit.ops, n):
        gain, left = aliases[u]
        if b:
            other_gain, right = aliases[v]
            if left == right:
                raise ValueError("aliased binary parents are outside the fixed-DAG model")
            aliases[i] = Fraction(1), n + len(ops)
            ops.append((a * gain, left, b * other_gain, right))
        else:
            aliases[i] = a * gain, left
    return ops, [aliases[i] for i in circuit.outputs]


def _materialize(circuit, ops, outputs, exponents, common):
    n = circuit.inputs
    mapping = {i: i for i in range(n)}
    scaled = {}
    body = []

    def use(src, delta):
        wire = mapping[src]
        if delta == 0:
            return wire
        key = src, delta
        if key not in scaled:
            scaled[key] = n + len(body)
            body.append((Fraction(2)**delta, wire, 0, wire))
        return scaled[key]

    for dst, (a, u, b, v) in enumerate(ops, n):
        left = use(u, _dyadic(a) + exponents[dst] - exponents[u])
        right = use(v, _dyadic(b) + exponents[dst] - exponents[v])
        mapping[dst] = n + len(body)
        body.append((1 if a > 0 else -1, left, 1 if b > 0 else -1, right))
    restored = []
    for coefficient, source in outputs:
        wire = use(source, _dyadic(coefficient) + common - exponents[source])
        if coefficient < 0:
            body.append((-1, wire, 0, wire))
            wire = n + len(body) - 1
        restored.append(wire)
    return RationalCircuit(n, tuple(body), tuple(restored), circuit.scale * Fraction(2)**common)


def search_wire_scales(circuit, target_arithmetic=None):
    """Minimize shared scalar copies with integer potentials in [-2,2]."""
    import z3

    if circuit.inputs + len(circuit.ops) > 100:
        raise ValueError("fixed-DAG SMT search exceeds the small-model limit")
    z3.set_param("memory_max_size", SMT_MEMORY_MIB)
    started = perf_counter()
    n = circuit.inputs
    ops, outputs = _collapse(circuit)
    shifts = [z3.IntVal(0)] * n + [z3.Int(f"e{i}") for i in range(len(ops))]
    common = z3.Int("global_output_shift")
    solver = z3.Solver()
    for x in (*shifts[n:], common):
        solver.add(x >= -EXPONENT_BOUND, x <= EXPONENT_BOUND)

    demands = {}
    for dst, (a, u, b, v) in enumerate(ops, n):
        for coefficient, source in ((a, u), (b, v)):
            demands.setdefault(source, []).append((_dyadic(coefficient), shifts[dst] - shifts[source]))
    for coefficient, source in outputs:
        demands.setdefault(source, []).append((_dyadic(coefficient), common - shifts[source]))
    events = []
    for uses in demands.values():
        limit = max(abs(base) for base, _ in uses) + 2 * EXPONENT_BOUND
        for offset in range(-limit, limit + 1):
            if offset:
                events.append(z3.Or(*(base + difference == offset for base, difference in uses)))
    # Binary operations and their signs are fixed by the topology. Charge
    # all extra sign changes before comparing the total to the original.
    fixed = len(ops) + sum(a < 0 and b < 0 for a, _, b, _ in ops)
    fixed += sum(a < 0 for a, _ in outputs)
    best = circuit
    bound = circuit.cost()["scaled_arithmetic"] - fixed - 1
    attempts = []
    goal = target_arithmetic - fixed if target_arithmetic is not None else bound
    pending_goal = 0 <= goal < bound
    while bound >= 0:
        remaining = SMT_SECONDS - (perf_counter() - started)
        if remaining <= 0:
            break
        solver.set(timeout=max(1, int(1000 * remaining)))
        trial = goal if pending_goal else bound
        goal_probe = pending_goal
        pending_goal = False
        solver.push()
        solver.add(z3.PbLe([(event, 1) for event in events], trial))
        state = solver.check()
        log = {"max_scalar_copies": trial, "status": str(state), "goal_probe": goal_probe}
        attempts.append(log)
        if state != z3.sat:
            if state == z3.unknown:
                log["reason"] = solver.reason_unknown()
            solver.pop()
            if goal_probe and state == z3.unsat:
                continue
            break
        model = solver.model()
        exponents = [model.eval(x, model_completion=True).as_long() for x in shifts]
        output_shift = model.eval(common, model_completion=True).as_long()
        best = _materialize(circuit, ops, outputs, exponents, output_shift)
        bound = best.cost()["scaled_arithmetic"] - fixed - 1
        solver.pop()
    return best, {
        "exponent_bound": EXPONENT_BOUND, "time_limit_seconds": SMT_SECONDS, "memory_mib": SMT_MEMORY_MIB,
        "binary_wires": len(ops), "copy_indicators": len(events), "attempts": attempts,
        "elapsed_seconds": perf_counter() - started,
    }
