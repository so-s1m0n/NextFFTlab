"""Bounded exact live-wire schedule feasibility for one immutable DAG."""
from dataclasses import replace
from time import perf_counter

MAX_STATES = 100_000
WALL_SECONDS = 5


def _reorder(circuit, order):
    n = circuit.inputs
    mapping = {i: i for i in range(n)}
    ops = []
    for i in order:
        a, u, b, v = circuit.ops[i]
        mapping[n + i] = n + len(ops)
        ops.append((a, mapping[u], b, mapping[v]))
    return replace(circuit, ops=tuple(ops), outputs=tuple(mapping[i] for i in circuit.outputs))


def improve_schedule_exact(circuit):
    """Try all schedules under descending pressure bounds until one fails or caps."""
    n = circuit.inputs
    size = len(circuit.ops)
    edges = [(u, v) if b else (u,) for _, u, b, v in circuit.ops]
    dependencies = [sum(1 << (src - n) for src in edge if src >= n) for edge in edges]
    consumers = [0] * (n + size)
    for i, edge in enumerate(edges):
        for parent in edge:
            consumers[parent] |= 1 << i
    retained = set(circuit.outputs)
    initial_live = sum(bool(consumers[i] or i in retained) for i in range(n))
    all_made = (1 << size) - 1
    start = perf_counter()
    best = circuit
    states = 0
    logs = []
    for cap in range(circuit.cost()["peak_live_wires"] - 1, initial_live - 1, -1):
        failed = set()
        order = []
        truncated = False
        before = states

        def visit(mask, pressure):
            nonlocal states, truncated
            if mask == all_made:
                return True
            if mask in failed:
                return False
            if states >= MAX_STATES or perf_counter() - start > WALL_SECONDS:
                truncated = True
                return False
            states += 1
            for j, edge in enumerate(edges):
                bit = 1 << j
                if mask & bit or dependencies[j] & ~mask:
                    continue
                after = mask | bit
                freed = sum(parent not in retained and not consumers[parent] & ~after for parent in edge)
                next_pressure = pressure - freed + int(bool(consumers[n + j] or n + j in retained))
                if next_pressure <= cap:
                    order.append(j)
                    if visit(after, next_pressure):
                        return True
                    order.pop()
                    if truncated:
                        return False
            failed.add(mask)
            return False

        found = visit(0, initial_live)
        logs.append({"peak_cap": cap, "states": states - before,
                     "status": "sat" if found else "budget" if truncated else "unsat"})
        if not found:
            break
        best = _reorder(circuit, order)
        if best.cost()["peak_live_wires"] > cap:
            raise ArithmeticError("schedule certificate exceeds its pressure limit")
    return best, {"state_limit": MAX_STATES, "time_limit_seconds": WALL_SECONDS,
                  "attempts": logs, "elapsed_seconds": perf_counter() - start}
