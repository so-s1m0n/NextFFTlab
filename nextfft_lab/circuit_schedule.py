"""Bounded topological rescheduling without changing any mathematical wire."""
from dataclasses import replace
from random import Random
from time import perf_counter

MAX_ORDERS = 256
SCHEDULE_SECONDS = 15


def reduce_live_wires(circuit, *, seed=20261126):
    n = circuit.inputs
    total = n + len(circuit.ops)
    users = [[] for _ in range(total)]
    parents = [()] * n + [(u, v) if b else (u,) for _, u, b, v in circuit.ops]
    for wire in range(n, total):
        for parent in parents[wire]:
            users[parent].append(wire)
    uses = [len(row) for row in users]
    for output in circuit.outputs:
        uses[output] += 1
    pending = [sum(parent >= n for parent in row) for row in parents]
    first = [wire for wire in range(n, total) if pending[wire] == 0]
    rng = Random(seed)
    started = perf_counter()
    best = circuit
    best_peak = circuit.cost()["peak_live_wires"]
    trials = 0
    for trial in range(MAX_ORDERS):
        if perf_counter() - started > SCHEDULE_SECONDS:
            break
        trials += 1
        ready, missed, counts = first.copy(), pending.copy(), uses.copy()
        priorities = [rng.random() for _ in range(total)]
        ops = []
        mapping = {i: i for i in range(n)}
        while ready:
            def key(wire):
                freed = sum(counts[parent] == 1 for parent in parents[wire])
                delta = int(bool(counts[wire])) - freed
                jitter = priorities[wire]
                return delta + (jitter * 2 if trial % 4 == 3 else 0), jitter, wire
            chosen = min(ready, key=key)
            ready.remove(chosen)
            a, u, b, v = circuit.ops[chosen - n]
            mapping[chosen] = n + len(ops)
            ops.append((a, mapping[u], b, mapping[v]))
            for parent in parents[chosen]:
                counts[parent] -= 1
            for user in users[chosen]:
                missed[user] -= 1
                if not missed[user]:
                    ready.append(user)
        candidate = replace(circuit, ops=tuple(ops), outputs=tuple(mapping[i] for i in circuit.outputs))
        peak = candidate.cost()["peak_live_wires"]
        if peak < best_peak:
            best, best_peak = candidate, peak
    return best, {
        "orders_tested": trials, "seed": seed, "limit_seconds": SCHEDULE_SECONDS,
        "stop": "order_limit" if trials == MAX_ORDERS else "time_limit",
        "elapsed_seconds": perf_counter() - started,
    }
