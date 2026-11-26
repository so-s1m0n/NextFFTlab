"""Run the bounded search on pinned published SLPs without executing upstream code."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import subprocess

from .bench_optimization import peak_process_bytes
from .bench_repair import environment
from .circuit_rewrites import COEFFICIENTS, MAX_BEAM, MAX_NEIGHBORS, MAX_ROUNDS, WALL_SECONDS, search_rewrites
from .circuit_scaling import search_wire_scales
from .circuit_schedule import reduce_live_wires
from .projective_search import projective_exchange
from .schedule_exact import improve_schedule_exact
from .research_budget import limit_process_memory
from .rational_circuit import parse_slp

REFERENCE = "bbb7f830d8c5612465a9922ace566750ce6d09d2"
PREFIX = "tools/circuits/programs/"
CASES = {
    "h8_19_gate": ("h8_19gates.txt", 8, Fraction(1), "gates"),
    "h8_20_scaled": ("generated/O_unit8_20ops_factor_half.txt", 8, Fraction(1, 2), "arithmetic"),
    "h16_56_layers": ("generated/O_layers8_16_factor.txt", 16, Fraction(1, 2), "arithmetic"),
    "h16_60_family": ("generated/O_family_16_factor.txt", 16, Fraction(1, 4), "arithmetic"),
}
FAMILY_G = ("h16_52gates.txt", 16, Fraction(1), "gates")


def _load(repo, spec):
    path, size, scale, _ = spec
    source = subprocess.run(
        ["git", "-C", str(repo), "show", f"{REFERENCE}:{PREFIX}{path}"],
        capture_output=True, text=True, encoding="utf-8", check=True, timeout=10,
    ).stdout
    circuit = parse_slp(source, size, scale)
    _confirm(circuit)
    return circuit


def _confirm(circuit):
    if not circuit.verify_rational() or not circuit.verify_field():
        raise ArithmeticError("circuit fails exact basis verification")


def run(repo, output_dir, skip_smt):
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "environment": environment(),
        "reference": REFERENCE,
        "excluded_from_search": {
            "published_h16_52_gate_exact": _load(repo, FAMILY_G).cost(),
            "alman_rao_theorem_6_2_exact_arithmetic_h8_h16": [30, 77],
        },
        "budget": {
            "max_process_bytes": 1024**3,
            "method_max_seconds": 1800,
            "rewrite_seconds_per_seed": WALL_SECONDS,
            "rewrite_neighbors_per_seed": MAX_NEIGHBORS,
            "rewrite_rounds": MAX_ROUNDS,
            "rewrite_beam": MAX_BEAM,
            "rewrite_coefficients": [str(x) for x in COEFFICIENTS],
        },
        "cases": {},
    }
    for name, spec in CASES.items():
        seed = _load(repo, spec)
        best, rewrite_log = search_rewrites(seed, spec[3])
        _confirm(best)
        if skip_smt:
            scaled, scaling_log = best, {"state": "not_requested"}
        else:
            try:
                scaled, scaling_log = search_wire_scales(best, 53 if best.inputs == 16 else 19)
            except ValueError as error:
                scaled, scaling_log = best, {"state": "outside_fixed_dyadic_model", "reason": str(error)}
            _confirm(scaled)
        scheduled, schedule_log = reduce_live_wires(scaled)
        _confirm(scheduled)
        exact_schedule, exact_log = improve_schedule_exact(scheduled)
        _confirm(exact_schedule)
        if output_dir is not None and exact_schedule != seed:
            (output_dir / f"{name}.json").write_text(
                json.dumps(exact_schedule.to_dict(), indent=2) + "\n", encoding="utf-8"
            )
        counts = exact_schedule.cost()
        reached = {
            "primary_h16_scaled_53": scaled.inputs == 16 and counts["scaled_arithmetic"] <= 53,
            "secondary_h8_18_gates": scaled.inputs == 8 and counts["gates"] <= 18,
            "secondary_h8_scaled_19": scaled.inputs == 8 and counts["scaled_arithmetic"] <= 19,
        }
        record["cases"][name] = {
            "reference_path": PREFIX + spec[0], "seed": seed.cost(),
            "rewritten": best.cost(), "after_smt": scaled.cost(), "after_schedule": counts,
            "rewrites": rewrite_log, "scaling": scaling_log,
            "schedule": schedule_log, "exact_schedule": exact_log, "target_met": reached,
            "verified_rational_basis_columns": seed.inputs, "verified_field_basis_columns": seed.inputs,
        }
        if peak_process_bytes() > record["budget"]["max_process_bytes"]:
            raise MemoryError("benchmark exceeded the peak process budget")
    witness, projective_log = projective_exchange(_load(repo, CASES["h8_19_gate"]))
    if witness is not None:
        _confirm(witness)
        projective_log["witness"] = witness.cost()
        if output_dir is not None:
            (output_dir / "h8_projective.json").write_text(
                json.dumps(witness.to_dict(), indent=2) + chr(10), encoding="utf-8")
    record["projective_h8"] = projective_log
    record["peak_process_bytes"] = peak_process_bytes()
    if record["peak_process_bytes"] > record["budget"]["max_process_bytes"]:
        raise MemoryError("benchmark exceeded the peak process budget")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-repo", required=True, type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--skip-smt", action="store_true")
    args = parser.parse_args()
    budget = limit_process_memory(1024**3)
    result = run(args.reference_repo, args.out_dir, args.skip_smt)
    result["budget"]["memory_enforcement"] = budget
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
