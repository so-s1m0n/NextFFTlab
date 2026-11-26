"""Bounded algebraic synthesis from a signed center and matched sums."""
from dataclasses import dataclass
from time import perf_counter

from .exact import P
from .linear_circuit import LinearCircuit

MAX_CONFIGURATIONS = 13_440
MAX_SEARCH_SECONDS = 10


class _Builder:
    def __init__(self, size):
        self.size = size
        self.ops = []

    def gate(self, left, right, a=1, b=1):
        wire = self.size + len(self.ops)
        self.ops.append((a, left, b, right))
        return wire

    def finish(self, outputs, scale=1):
        return LinearCircuit(self.size, tuple(self.ops), tuple((i, scale) for i in outputs))


@dataclass(frozen=True)
class SearchResult:
    circuit: LinearCircuit
    configurations: int
    matching: tuple
    anchors: tuple


def _perfect_matchings(indices):
    if not indices:
        yield ()
        return
    left, *rest = indices
    for i, right in enumerate(rest):
        for matching in _perfect_matchings(rest[:i] + rest[i + 1:]):
            yield ((left, right), *matching)


def _choices(support, matching):
    """All routes in the grammar: singles, a matched pair, or a shared anchor."""
    options = [(len(support), 0, tuple((i,) for i in support))]
    pair = next((pair for pair in matching if all(i in support for i in pair)), ())
    if pair:
        options.append((len(support) - 1, 0, (pair, *((i,) for i in support if i not in pair))))
    if len(support) > 1:
        for i in support:
            remainder = tuple(j for j in support if j != i)
            if remainder == pair:
                options.append((1, i, (pair,)))
            else:
                options.append((len(remainder), i, tuple((j,) for j in remainder)))
    return tuple(sorted(options))


def synthesize_rank_one(size):
    """Exhaust the fixed grammar for H4 or H8.

    The grammar uses one matching with a singleton to compute the shared
    total and optionally precomputes D+2*x[i] for chosen anchors.
    """
    if type(size) is not int or size not in (4, 8):
        raise ValueError("search supports 4 or 8 inputs")
    supports = [tuple(i for i in range(1, size) if (k & i).bit_count() % 2 == 0)
                for k in range(1, size)]
    best = None
    configurations = 0
    deadline = perf_counter() + MAX_SEARCH_SECONDS
    for singleton in range(1, size):
        for matching in _perfect_matchings([i for i in range(1, size) if i != singleton]):
            options = [_choices(support, matching) for support in supports]
            for mask in range(1 << (size - 1)):
                if configurations >= MAX_CONFIGURATIONS or perf_counter() > deadline:
                    raise TimeoutError("algebraic search budget exceeded")
                configurations += 1
                paths = tuple(next(choice for choice in row
                                   if choice[1] == 0 or mask & (1 << (choice[1] - 1)))
                              for row in options)
                anchors = tuple(i for i in range(1, size) if mask & (1 << (i - 1)))
                # T takes size-2 gates. x0 +/- T takes two more.
                score = size + len(anchors) + sum(path[0] for path in paths)
                candidate = (score, anchors, matching, singleton, paths)
                if best is None or candidate < best:
                    best = candidate

    _, anchors, matching, singleton, paths = best
    builder = _Builder(size)
    pairs = {pair: builder.gate(*pair) for pair in matching}
    total = singleton
    for wire in pairs.values():
        total = builder.gate(total, wire)
    outputs = [builder.gate(0, total)]
    difference = builder.gate(0, total, b=-1)
    start = {i: builder.gate(difference, i, b=2) for i in anchors}
    for _, anchor, groups in paths:
        result = start[anchor] if anchor else difference
        for group in groups:
            result = builder.gate(result, group[0] if len(group) == 1 else pairs[group], b=2)
        outputs.append(result)
    return SearchResult(builder.finish(outputs), configurations, matching, anchors)


def sussman_h8_circuit():
    """Independent encoding of Sussman's published half-WHT identity.

    The center is shared at half scale. A common final factor of two
    restores H8 and can be deferred across tensor layers.
    """
    builder = _Builder(8)
    gate = builder.gate
    p = gate(0, 7)
    q = gate(1, 6)
    r = gate(2, 5, b=-1)
    s = gate(3, 4, b=-1)
    left = gate(p, q, b=-1)
    right = gate(r, s)
    center = gate(left, right, b=-1)
    half = -(P - 1) // 2
    center = gate(center, center, a=half, b=0)
    stem_a = gate(center, 7, b=-1)
    stem_b = gate(center, 5, b=-1)
    leg_a = gate(stem_a, 6)
    leg_b = gate(stem_b, 4, b=-1)
    leg_c = gate(stem_b, 3)
    leg_d = gate(stem_a, 1)
    return builder.finish((
        gate(p, leg_b, b=-1), gate(leg_a, r), leg_d, leg_c,
        gate(leg_d, right), gate(left, leg_c, b=-1), gate(leg_b, q), gate(leg_a, s),
    ), scale=2)
