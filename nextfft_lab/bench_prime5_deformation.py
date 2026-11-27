"""Matched benchmarks for width-four multiplication over truncated Gaussian jets."""

import argparse
from contextlib import contextmanager
from fractions import Fraction
import gc
import json
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter_ns
import tracemalloc

from .bench_optimization import peak_process_bytes
from .bench_repair import environment
from .prime5_deformation import Gaussian, WidthFourPlan, prime5_constants, schoolbook_product
from .research_budget import limit_process_memory

MAX_PROCESS_BYTES = 1024**3
MAX_SECONDS = 30 * 60
ORDERS = (1, 2, 3)
DEFAULT_SEED = 20261127
OPERATOR_NAMES = {
    "__add__": "add",
    "__sub__": "subtract",
    "__neg__": "negate",
    "__mul__": "multiply",
    "__truediv__": "divide",
}


def _coefficient(rng):
    """Seeded nonzero real and imaginary rational components."""
    real = Fraction(rng.choice((-1, 1)) * rng.randint(1, 13), rng.randint(2, 17))
    imag = Fraction(rng.choice((-1, 1)) * rng.randint(1, 13), rng.randint(2, 17))
    return Gaussian(real, imag)


def _inputs(rng, order, pairs):
    def tensor():
        return tuple(tuple(_coefficient(rng) for _ in range(order)) for _ in range(4))

    return tuple((tensor(), tensor()) for _ in range(pairs))


def _time(call):
    start = perf_counter_ns()
    value = call()
    return value, perf_counter_ns() - start


def _memory(call):
    gc.collect()
    tracemalloc.start()
    try:
        call()
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


def _summary(samples):
    return {"samples_ns": samples, "median_ns": median(samples)}


def _same(outputs, expected):
    return tuple(tuple(tuple(row) for row in item) for item in outputs) == expected


@contextmanager
def _observe_arithmetic():
    counts = {name: 0 for name in OPERATOR_NAMES.values()}
    bits = {"numerator": 0, "denominator": 0}
    originals = {}

    def observe(value):
        if isinstance(value, Gaussian):
            for coefficient in (value.real, value.imag):
                bits["numerator"] = max(bits["numerator"], abs(coefficient.numerator).bit_length())
                bits["denominator"] = max(bits["denominator"], coefficient.denominator.bit_length())

    def wrap(method, name):
        def instrumented(self, *args):
            counts[name] += 1
            observe(self)
            for arg in args:
                observe(arg)
            result = method(self, *args)
            observe(result)
            return result
        return instrumented

    def wrap_init(method):
        def instrumented(self, *args, **kwargs):
            method(self, *args, **kwargs)
            observe(self)
        return instrumented

    try:
        for attr, name in OPERATOR_NAMES.items():
            originals[attr] = getattr(Gaussian, attr)
            setattr(Gaussian, attr, wrap(originals[attr], name))
        originals["__init__"] = Gaussian.__init__
        Gaussian.__init__ = wrap_init(originals["__init__"])
        yield {"gaussian_method_calls": counts, "peak_fraction_bits": bits}, observe
    finally:
        for attr, method in originals.items():
            setattr(Gaussian, attr, method)


def _arithmetic(call, coefficients=()):
    with _observe_arithmetic() as (result, observe):
        for value in coefficients:
            observe(value)
        call()
    count = result["gaussian_method_calls"]
    result["rational_ops_inside_gaussian_methods"] = {
        "add_or_subtract": 2 * (count["add"] + count["subtract"] + count["multiply"])
        + 3 * count["divide"],
        "negate": 2 * count["negate"],
        "multiply": 4 * count["multiply"] + 6 * count["divide"],
        "divide": 2 * count["divide"],
    }
    return result


def _check_budget(start_ns):
    if perf_counter_ns() - start_ns >= MAX_SECONDS * 10**9:
        raise TimeoutError("prime-five deformation benchmark exceeded its elapsed-time budget")
    if peak_process_bytes() > MAX_PROCESS_BYTES:
        raise MemoryError("prime-five deformation benchmark exceeded its process-memory budget")


def _case(order, lam, cases, repeats, start_ns):
    def make_plan():
        return WidthFourPlan(lam, order)

    def direct():
        return tuple(schoolbook_product(left, right, lam, order) for left, right in cases)

    plan = make_plan()

    def split():
        return tuple(plan.multiply(left, right) for left, right in cases)

    expected = tuple(tuple(tuple(row) for row in item) for item in direct())
    if not _same(split(), expected):
        raise ArithmeticError("split plan and schoolbook disagree during warm-up")

    setup_samples = []
    for _ in range(repeats):
        _check_budget(start_ns)
        fresh_plan, elapsed = _time(make_plan)
        setup_samples.append(elapsed)
        del fresh_plan

    methods = (("schoolbook", direct), ("split_plan", split))
    samples = {name: [] for name, _ in methods}
    for trial in range(repeats):
        _check_budget(start_ns)
        for name, call in methods[::1 if trial % 2 == 0 else -1]:
            output, elapsed = _time(call)
            if not _same(output, expected):
                raise ArithmeticError(f"{name} disagrees with checked schoolbook outputs")
            samples[name].append(elapsed)

    input_coefficients = tuple(
        coefficient
        for pair in cases
        for tensor in pair
        for row in tensor
        for coefficient in row
    )
    measurements = {}
    for name, call in methods:
        _check_budget(start_ns)
        measurement = _summary(samples[name])
        measurement["median_ns_per_product"] = measurement["median_ns"] / len(cases)
        measurement["python_peak_bytes_per_batch"] = _memory(call)

        def one_product():
            left, right = cases[0]
            if name == "split_plan":
                return plan.multiply(left, right)
            return schoolbook_product(left, right, lam, order)

        measurement["arithmetic_first_product"] = _arithmetic(
            one_product,
            (lam, *(coefficient for tensor in cases[0] for row in tensor for coefficient in row)),
        )
        measurement["arithmetic_warm_batch"] = _arithmetic(call, (lam, *input_coefficients))
        measurements[name] = measurement

    setup = _summary(setup_samples)
    setup["python_peak_bytes"] = _memory(make_plan)
    setup["arithmetic"] = _arithmetic(make_plan, (lam,))
    return {
        "order": order,
        "lambda": {"real": str(lam.real), "imag": str(lam.imag)},
        "pairs_per_sample": len(cases),
        "verified_exact_pair_count": len(cases),
        "reusable_split_setup": setup,
        "methods": measurements,
    }


def run(*, repeats=20, pairs=8, seed=DEFAULT_SEED):
    if not 1 <= repeats <= 40 or not 1 <= pairs <= 32:
        raise ValueError("benchmark bounds are 1..40 repeats and 1..32 input pairs per order")
    start_ns = perf_counter_ns()
    rng = Random(seed)
    paper_lambda, _ = prime5_constants()
    inputs = {order: _inputs(rng, order, pairs) for order in ORDERS}
    cases = {
        name: [_case(order, lam, inputs[order], repeats, start_ns) for order in ORDERS]
        for name, lam in (("paper_lambda", paper_lambda), ("lambda_one_control", Gaussian(1)))
    }
    _check_budget(start_ns)
    return {
        "experiment": "width-four truncated-jet binomial multiplication",
        "algebra": "Q(i)[z,Y]/(z^r,Y^4-lambda)",
        "arithmetic_domain": "exact fractions in both Gaussian coordinates",
        "environment": environment(),
        "seed": seed,
        "repeats": repeats,
        "orders": list(ORDERS),
        "cases": cases,
        "conventions": {
            "inputs": "Both methods and both lambdas receive the same immutable input pairs by order.",
            "timing": "perf_counter_ns without tracing or counters. Both methods warm up once and alternate timed batch order. Exact output checks are outside the timed interval.",
            "setup": "Split plan construction only, measured separately. Dense schoolbook has no plan.",
            "python_peak_bytes": "Separate tracemalloc calls after GC, excluding already constructed inputs and the warm plan.",
            "gaussian_method_calls": "Literal Gaussian arithmetic method invocations, including any nested calls. They are not rational primitive-operation counts or binary linear gates.",
            "rational_ops_inside_gaussian_methods": "Derived from the formula in each Gaussian method. Excludes indexing, Fraction normalization and scalar setup outside those methods.",
            "peak_fraction_bits": "Maximum bit lengths of reduced numerators and denominators in real and imaginary coordinates of inputs, observed Gaussian operands/results, and Gaussian objects constructed during the measured call. Internal temporaries inside Fraction are excluded.",
            "comparison_scope": "Concrete-width quotient-algebra component only. No full Fourier transform timing.",
        },
        "budget": {"max_seconds": MAX_SECONDS, "max_process_bytes": MAX_PROCESS_BYTES},
        "peak_process_bytes": peak_process_bytes(),
        "elapsed_seconds": (perf_counter_ns() - start_ns) / 10**9,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/prime5-deformation.json"))
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--pairs", type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 40 or not 1 <= args.pairs <= 32:
        parser.error("benchmark bounds are 1..40 repeats and 1..32 input pairs per order")
    cap = limit_process_memory(MAX_PROCESS_BYTES)
    result = run(repeats=args.repeats, pairs=args.pairs)
    result["budget"]["memory_enforcement"] = cap
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded {len(ORDERS) * 2} matched cases in {args.output}")


if __name__ == "__main__":
    main()
