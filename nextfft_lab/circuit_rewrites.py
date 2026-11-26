"""Bounded rational CSE, one-wire replacement and two-gate reassociation."""
from dataclasses import replace
from fractions import Fraction
from math import lcm
from random import Random
from time import perf_counter

COEFFICIENTS = tuple(Fraction(s) * Fraction(2)**e for e in (0, -1, 1)
                     for s in (1, -1))
MAX_BEAM = 6
MAX_ROUNDS = 8
MAX_NEIGHBORS = 6_000
WALL_SECONDS = 120


def wire_forms(circuit):
    n = circuit.inputs
    wires = [tuple(Fraction(i == j) for j in range(n)) for i in range(n)]
    for a, u, b, v in circuit.ops:
        wires.append(tuple(a * x + b * y for x, y in zip(wires[u], wires[v])))
    return wires


def prune(circuit):
    live = set(circuit.outputs)
    for i in range(len(circuit.ops) - 1, -1, -1):
        if circuit.inputs + i in live:
            _, u, b, v = circuit.ops[i]
            live.add(u)
            if b:
                live.add(v)
    mapping = {i: i for i in range(circuit.inputs)}
    ops = []
    for i, (a, u, b, v) in enumerate(circuit.ops, circuit.inputs):
        if i in live:
            mapping[i] = circuit.inputs + len(ops)
            ops.append((a, mapping[u], b, mapping[v]))
    return replace(circuit, ops=tuple(ops), outputs=tuple(mapping[i] for i in circuit.outputs))


def cse(circuit):
    """Deduplicate equal rational wire values and prune disconnected ops."""
    forms = wire_forms(circuit)
    seen = {form: i for i, form in enumerate(forms[:circuit.inputs])}
    mapping = {i: i for i in range(circuit.inputs)}
    ops = []
    for i, (a, u, b, v) in enumerate(circuit.ops, circuit.inputs):
        form = forms[i]
        if form in seen:
            mapping[i] = seen[form]
            continue
        left, right = mapping[u], mapping[v]
        if left == right:
            a, b = a + b, 0
            if not a:
                # The present seed and rewrite grammar never need a new zero wire.
                return prune(circuit)
        mapping[i] = seen[form] = circuit.inputs + len(ops)
        ops.append((a, left, b, right))
    return prune(replace(circuit, ops=tuple(ops), outputs=tuple(mapping[i] for i in circuit.outputs)))


def _direct_replacements(circuit):
    rational = wire_forms(circuit)
    denominator = 2 * lcm(*(x.denominator for row in rational for x in row))
    forms = [tuple(int(x * denominator) for x in row) for row in rational]
    seen = {}
    for wire, target in enumerate(forms):
        if wire >= circuit.inputs:
            original = circuit.ops[wire - circuit.inputs]
            for a, u in seen.get(target, ()):
                op = (a, u, 0, u)
                if op != original:
                    yield _replace(circuit, wire, op)
            for u, left in enumerate(forms[:wire]):
                for a in COEFFICIENTS:
                    residual = tuple(x - _scaled(y, a) for x, y in zip(target, left))
                    for b, v in seen.get(residual, ()):
                        op = (a, u, b, v)
                        if u < v and op != original and (b, v, a, u) != original:
                            yield _replace(circuit, wire, op)
        for a in COEFFICIENTS:
            key = tuple(_scaled(value, a) for value in target)
            seen.setdefault(key, []).append((a, wire))


def _scaled(value, multiplier):
    return value * multiplier.numerator // multiplier.denominator


def _replace(circuit, wire, op):
    index = wire - circuit.inputs
    return replace(circuit, ops=circuit.ops[:index] + (op,) + circuit.ops[index + 1:])


def _reassociate(circuit):
    n = circuit.inputs
    for wire, (a, u, b, v) in enumerate(circuit.ops, n):
        if not b:
            continue
        for gain, child, other_gain, other in ((a, u, b, v), (b, v, a, u)):
            if child < n:
                continue
            c, x, d, y = circuit.ops[child - n]
            if not d or len({x, y, other}) != 3:
                continue
            for left, left_gain, right, right_gain in ((x, c, y, d), (y, d, x, c)):
                if gain * left_gain in COEFFICIENTS and gain * right_gain in COEFFICIENTS:
                    helper = (gain * left_gain, left, other_gain, other)
                    new = (1, wire, gain * right_gain, right)
                    tail = tuple((j, p + int(p >= wire), k, q + int(q >= wire))
                                 for j, p, k, q in circuit.ops[wire - n + 1:])
                    yield replace(circuit, ops=circuit.ops[:wire - n] + (helper, new) + tail,
                                  outputs=tuple(i + int(i >= wire) for i in circuit.outputs))


def _score(circuit, objective):
    counts = circuit.cost()
    if objective == "gates":
        lead = counts["gates"], counts["scaled_arithmetic"]
    else:
        lead = counts["scaled_arithmetic"], counts["gates"]
    return (*lead, counts["wire_depth"], counts["peak_live_wires"])


def search_rewrites(seed, objective="arithmetic", *, random_seed=20261126):
    """Beam search with one seeded exploratory slot per round."""
    started = perf_counter()
    rng = Random(random_seed)
    initial = cse(seed)
    best = initial
    expanded = evaluated = rounds = 0
    best_score = _score(initial, objective)
    frontier = [initial]
    visited = {(initial.ops, initial.outputs)}
    stopped = "round_limit"
    for _ in range(MAX_ROUNDS):
        rounds += 1
        kept = {}
        exploratory = None
        eligible = 0
        for entry in frontier:
            expanded += 1
            for generator in (_reassociate, _direct_replacements):
                for raw in generator(entry):
                    if evaluated >= MAX_NEIGHBORS or perf_counter() - started > WALL_SECONDS:
                        stopped = "neighbor_or_time_limit"
                        break
                    evaluated += 1
                    candidate = cse(raw)
                    key = candidate.ops, candidate.outputs
                    if key in visited or key in kept:
                        continue
                    score = _score(candidate, objective)
                    if score < best_score:
                        best, best_score = candidate, score
                    kept[key] = score, candidate
                    if len(kept) > MAX_BEAM - 1:
                        worst = max(kept, key=lambda item: (kept[item][0], item))
                        discarded = kept.pop(worst)
                        if discarded[0][0] <= best_score[0] + 1:
                            eligible += 1
                            if rng.randrange(eligible) == 0:
                                exploratory = discarded[1]
                if stopped == "neighbor_or_time_limit":
                    break
            if stopped == "neighbor_or_time_limit":
                break
        frontier = [candidate for _, candidate in sorted(kept.values(), key=lambda x: x[0])]
        if exploratory is not None:
            frontier.append(exploratory)
        visited.update((candidate.ops, candidate.outputs) for candidate in frontier)
        if not frontier or stopped != "round_limit":
            if not frontier and stopped == "round_limit":
                stopped = "frontier_exhausted"
            break
    return best, {
        "objective": objective, "seed": random_seed, "neighborhood_candidates": evaluated,
        "expanded_states": expanded, "rounds": rounds, "stop": stopped,
        "elapsed_seconds": perf_counter() - started,
    }
