"""Exact H8 helper deletion and exchange over a bounded rational direction pool."""
from fractions import Fraction
from itertools import combinations
from math import gcd, lcm
from time import perf_counter

from .circuit_rewrites import prune, wire_forms
from .rational_circuit import RationalCircuit

EXTRA_DIRECTIONS = 512
PROJECTIVE_SECONDS = 120


def _primitive(vector):
    den = lcm(*(x.denominator for x in vector))
    row = tuple(int(x * den) for x in vector)
    content = gcd(*row)
    if not content:
        return None
    first = next(x for x in row if x)
    sign = 1 if first > 0 else -1
    return tuple(x * sign // content for x in row)


def _span_table(directions, base_count, deadline):
    rules = [[] for _ in directions]
    tested = 0
    for u, v in combinations(range(len(directions)), 2):
        # Every tested configuration admits at most one new direction.
        if u >= base_count:
            continue
        if perf_counter() > deadline:
            raise TimeoutError("projective setup exceeded its time budget")
        x, y = directions[u], directions[v]
        j = next(i for i, value in enumerate(x) if value)
        k = next(i for i in range(len(x)) if x[j] * y[i] != x[i] * y[j])
        det = x[j] * y[k] - x[k] * y[j]
        for output, z in enumerate(directions):
            if output in (u, v) or (v >= base_count and output >= base_count):
                continue
            tested += 1
            a = z[j] * y[k] - z[k] * y[j]
            b = x[j] * z[k] - x[k] * z[j]
            if a and b and all(a * left + b * right == det * want for left, right, want in zip(x, y, z)):
                rules[output].append((u, v, Fraction(a, det), Fraction(b, det)))
    return rules, tested


def _closure(allowed, targets, rules, n):
    pending = sorted(set(allowed) | set(targets))
    made = {i: i for i in range(n)}
    ops = []
    while pending:
        missing = []
        for wire in pending:
            found = next((rule for rule in rules[wire] if rule[0] in made and rule[1] in made), None)
            if found is None:
                missing.append(wire)
                continue
            u, v, a, b = found
            made[wire] = n + len(ops)
            ops.append((a, made[u], b, made[v]))
        if all(i in made for i in targets):
            return prune(RationalCircuit(n, tuple(ops), tuple(made[i] for i in targets), Fraction(1)))
        if len(missing) == len(pending):
            return None
        pending = missing
    return None


def projective_exchange(seed):
    """Exhaust one deletion and two deletions plus one chosen rational direction."""
    if seed.inputs != 8 or len(seed.ops) > 30:
        raise ValueError("projective exchange accepts only a small H8 seed")
    started = perf_counter()
    deadline = started + PROJECTIVE_SECONDS
    raw = wire_forms(seed)
    normalized = [_primitive(row) for row in raw]
    if None in normalized:
        raise ValueError("projective exchange requires nonzero wire directions")
    outputs = list(dict.fromkeys(normalized[i] for i in seed.outputs))
    base = list(dict.fromkeys(normalized[:8] + outputs + normalized[8:]))
    if len(base) > 30 or len(outputs) != 8:
        raise ValueError("projective seed exceeds the direction budget")
    base_set = set(base)
    extras = set()
    for x, y in combinations(base, 2):
        for left, right in ((1, 1), (1, -1), (2, 1), (1, 2), (2, -1), (1, -2)):
            row = _primitive(tuple(left * a + right * b for a, b in zip(x, y)))
            if (row and row not in base_set and sum(bool(value) for value in row) <= 4
                    and max(map(abs, row)) <= 2):
                extras.add(row)
    ordered = sorted(extras, key=lambda row: (sum(bool(x) for x in row), sum(map(abs, row)), row))
    directions = base + ordered[:EXTRA_DIRECTIONS]
    rules, tests = _span_table(directions, len(base), deadline)
    target_ids = [base.index(form) for form in outputs]
    helpers = set(range(8, len(base))) - set(target_ids)
    if _closure(helpers, target_ids, rules, 8) is None:
        raise ArithmeticError("the seed helper pool could not reconstruct its own outputs")
    paths = ((removed, extra) for removed in combinations(sorted(helpers), 2)
             for extra in range(len(base), len(directions)))
    deletions = (((i,), None) for i in sorted(helpers))
    counts = {"one_deletion": 0, "two_deletions_one_exchange": 0}
    stop = "exhausted"
    answer = None
    for group in (deletions, paths):
        for removed, extra in group:
            if perf_counter() > deadline:
                stop = "time_limit"
                break
            allowed = helpers.difference(removed)
            if extra is not None:
                allowed.add(extra)
            trial = "one_deletion" if extra is None else "two_deletions_one_exchange"
            counts[trial] += 1
            answer = _closure(allowed, target_ids, rules, 8)
            if answer is not None:
                stop = "witness"
                break
        if stop != "exhausted":
            break
    return answer, {
        **counts, "base_directions": len(base), "baseline_helpers": len(helpers),
        "eligible_extras_before_cap": len(ordered), "admitted_extras": len(directions) - len(base),
        "exact_span_checks": tests, "stop": stop, "elapsed_seconds": perf_counter() - started,
    }
