"""Benchmark endpoint identities and count a bounded binary routing schedule."""
import argparse
import json
from random import Random
from time import perf_counter_ns

from .bench_pencil import theorem_window_estimate
from .bench_repair import environment, measure
from .binary_kernel import binary_endpoint, binary_query, binary_rank, binary_rectangles
from .binary_template import compile_binary_square_template
from .exact import P
from .walsh import walsh


def schedule_estimate(m, length, alphabet, gram, rectangles, repair):
    dimension = binary_rank(gram)
    axes = 2 * (m + dimension - 1)
    labels = alphabet**length
    charged = sum(rect.charged for rect in rectangles)
    free_endpoint_calls = 0
    for rect in rectangles:
        if rect.charged:
            continue
        span = binary_rank(gram[index] for index in rect.destinations)
        free_endpoint_calls += (
            2 * span * len(rect.sources) + 2 * (dimension - span) * len(rect.destinations)
        )
    one_pencil_per_label_set = 2 * dimension * m * charged + free_endpoint_calls
    if repair["exception_shifts"]:
        raise ValueError("this estimate enumerates zero-exception schedules only")
    calls_per_label_set = repair["radix"] * one_pencil_per_label_set
    pre_extension_rows = (1 << repair["log2_batch_width"]) * labels
    return {
        "m": m,
        "label_length": length,
        "alphabet": alphabet,
        "gram_dimension": dimension,
        "axes": axes,
        "charged_rectangles": charged,
        "free_rectangles": len(rectangles) - charged,
        "batch_rows": pre_extension_rows,
        "minimum_input_bytes_f1_base_field": 4 * pre_extension_rows * (1 << axes),
        "axis_calls_per_batch_row_fraction": [calls_per_label_set, labels],
        "scheduled_calls_below_a_to_three_quarters": calls_per_label_set**4 < axes**3 * labels**4,
    }


def run(repeats):
    rng = Random(20261126)
    m, auxiliary, columns = 3, 1, 1
    size = 256
    row = [rng.randrange(P) for _ in range(size)]

    def unrouted_product():
        current = binary_endpoint(row, m, auxiliary, columns)
        for j in range(m):
            current = binary_query(current, m, auxiliary, columns, j)
        return binary_endpoint(current, m, auxiliary, columns, output=True)

    assert unrouted_product() == walsh(row)
    candidates = []
    for m_candidate in range(3, 12, 2):
        repair = theorem_window_estimate(m_candidate)
        for length in range(2, 7):
            for alphabet in (2, 4, 8):
                if alphabet**length <= 64:
                    gram, rectangles = binary_rectangles(length, alphabet)
                    candidates.append(schedule_estimate(m_candidate, length, alphabet,
                                                        gram, rectangles, repair))
    return {
        "environment": environment(),
        "seed": 20261126,
        "prime": P,
        "repeats": repeats,
        "component": {
            "m": m,
            "auxiliary": auxiliary,
            "columns": columns,
            "entries": size,
            "unrouted_product": measure(unrouted_product, repeats),
            "classical_walsh": measure(lambda: walsh(row), repeats),
            "local_pair_butterfly_applications": m * (1 + auxiliary) * columns * size // 4,
        },
        "schedule_estimates": candidates,
    }


def measure_template(repeats):
    rng = Random(20261126)
    start = perf_counter_ns()
    plan = compile_binary_square_template()
    setup = perf_counter_ns() - start
    labels = [[[rng.randrange(P) for _ in range(256)] for _ in range(plan.rows_per_label)]
              for _ in range(4)]
    baseline = []
    for _ in range(repeats):
        start = perf_counter_ns()
        expected = [[walsh(row) for row in block] for block in labels]
        baseline.append(perf_counter_ns() - start)
    samples = []
    for _ in range(repeats):
        start = perf_counter_ns()
        output = plan.apply(labels)
        samples.append(perf_counter_ns() - start)
        assert output == expected
        del output
    return {
        "cold_setup_ns": setup,
        "reused_apply_samples_ns": samples,
        "classical_walsh_samples_ns": baseline,
        "rows": 4 * plan.rows_per_label,
        "entries_per_row": 256,
        "pencil_stages": plan.stages,
        "axis_calls": 80 * plan.rows_per_label * plan.stages,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--template-repeats", type=int, default=0)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    if not 0 <= args.template_repeats <= 3:
        parser.error("template repeats must be between zero and three")
    result = run(args.repeats)
    if args.template_repeats:
        result["materialized_template"] = measure_template(args.template_repeats)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
