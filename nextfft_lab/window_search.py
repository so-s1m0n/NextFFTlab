"""Exact binary-window search and a factored endpoint predictor."""
from math import comb, prod

from .binary_repair import binary_degree_coefficients
from .exact import P
from .predictor import window
from .query_polynomial import compile_query_polynomial


def narrowest_symmetric_window(m):
    """Return inclusive bounds and exact exceptional shift count for 1/(2m³)."""
    if not isinstance(m, int) or not 2 <= m <= 1024:
        raise ValueError("window search requires 2 <= m <= 1024")
    budget = (1 << m) // (2 * m**3)
    outside = 0
    lower = 0
    while lower < m - lower:
        wider_tail = outside + 2 * comb(m, lower)
        if wider_tail > budget or lower + 1 > m - lower - 1:
            break
        outside = wider_tail
        lower += 1
    return lower, m - lower, outside


def endpoint_shift_masks(m):
    """Smallest uniform shift set for the odd [1,m-1] exception pattern."""
    if not isinstance(m, int) or not 3 <= m <= 1024 or m % 2 == 0:
        raise ValueError("endpoint shifts require odd 3 <= m <= 1024")
    size = 2 * m**3
    if size > 1 << (m - 1):
        raise ValueError("the endpoint window exceeds the repair budget")
    # An endpoint occurs only at beta=k or beta=k xor all_ones.
    # Every representative below has a zero top bit, hence no complement in the set.
    return range(size)


def endpoint_predictor(query_signs):
    """The zero-shift polynomial on [1,m-1] for odd m over the base field."""
    q = tuple(query_signs)
    if len(q) < 3 or len(q) % 2 == 0:
        raise ValueError("endpoint factorization requires odd m >= 3")
    target = prod(q) % P
    plus = prod((1 + value) % P for value in q) % P
    minus = prod((value - 1) % P for value in q) % P
    return (target - (plus + minus) * pow(2, -1, P)) % P


def window_cost(m, bounds):
    """Report integer sizes as exponents without allocating the pencil or tensor."""
    u, v = bounds
    polynomial = compile_query_polynomial([0] * m, bounds=bounds)
    coefficients = binary_degree_coefficients(polynomial)
    degrees = [d for d, coefficient in enumerate(coefficients) if coefficient]
    degree = max(degrees, default=0)
    terms = sum(comb(m, d) for d in degrees)
    log2_b = (max(2, degree) - 1).bit_length()
    radix = 1 << log2_b
    bad = sum(comb(m, k) for k in range(m + 1) if not u <= k <= v)
    endpoint_form = m % 2 == 1 and bounds == (1, m - 1)
    # The factored representation contains products of length m even if
    # the leading degrees cancel. Use enough factors in every product.
    factored_log2_b = (max(2, m) - 1).bit_length()
    shell = m + 3 * factored_log2_b if endpoint_form else None
    return {
        "window": [u, v],
        "degree": degree,
        "paper_window_radix": 1 << (max(2, v - u) - 1).bit_length(),
        "degree_radix": radix,
        "expanded_terms": terms,
        "bad_shifts": bad,
        "total_shifts": 1 << m,
        "within_repair_fraction": bad * 2 * m**3 <= 1 << m,
        "expanded_log2_rows": m + log2_b * max(1, terms),
        "endpoint_factored_log2_rows_upper": shell,
        "endpoint_factored_cyclotomic_rank_log2": shell - 1 if endpoint_form else None,
        "endpoint_factored_root_field_degree_log2": max(0, shell - 23) if endpoint_form else None,
        "paper_reference_window": list(window(m)),
    }
