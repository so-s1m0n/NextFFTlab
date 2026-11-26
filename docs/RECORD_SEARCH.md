# Bounded search against the published H8 and H16 records

The annotated local tag `checkpoint/166-tests` preserves commit `6d77b7f`. The unmodified checkpoint passed all 166 tests again before the search. This experiment targets a common-scale H16 body with at most 53 scalar arithmetic operations, or an H8 body with at most 18 binary linear gates or 19 arithmetic operations. At H16, 53 body operations would give a leading arithmetic constant of 53/64 under repeated layers and one final rescaling, below 5/6.

## Comparison points

Alman and Rao's version 2, Sections 2.2 and 6.2, starts from a sparse-plus-rank-one decomposition of H8. Its recursive arithmetic saving depends on passing differently scaled inputs to the 8-point step and collecting powers of two at the leaves. Theorem 6.2 counts 30 operations at H8 and 77 at H16 for the full output, including the charged input multiplications. The asymptotic 23/24 leading constant describes that recursion. [Alman and Rao v2](https://arxiv.org/pdf/2211.06459).

Sussman's pinned README distinguishes the 19-binary-gate H8, the 3/4 multiply-add family, and the 5/6 arithmetic family. It identifies the <=53 arithmetic H16 body as an open search direction and gives 56 as its published comparison. The 3/4 family's lower gate count comes with additional scalar multiplications. The 5/6 family combines half-scale H8 layers and restores the accumulated scale at the end. Its H16 body comprises two half-scale H8 blocks and a textbook butterfly layer. [Pinned README and open direction](https://github.com/jacobalansussman/wht-fewer-operations/blob/bbb7f830d8c5612465a9922ace566750ce6d09d2/README.md#open-directions) · [Pinned search methodology](https://github.com/jacobalansussman/wht-fewer-operations/blob/bbb7f830d8c5612465a9922ace566750ce6d09d2/tools/circuits/search/README.md).

The driver reads the published straight-line programs from the pinned Git tree as data. It checks each input basis vector over rational numbers using exact fractions and checks each basis vector independently over F₉₉₈₂₄₄₃₅₃. For the field check, a final common rescaling recovers the ordinary Walsh matrix. The search operates over the rationals. A regression case adds P to one coefficient and verifies that the field accepts the equivalence while the rational verifier rejects it.

| Published seed | Binary gates | Add/sub | Constant multiplies in body | Body arithmetic | Body output | Restoration |
|---|---:|---:|---:|---:|---|---:|
| H8 19-gate witness | 19 | 19 | 12 | 31 | H8x | 0 |
| H8 5/6-series block | 19 | 19 | 1 | 20 | H8x/2 | 8 |
| H16 5/6-series layers | 54 | 54 | 2 | 56 | H16x/2 | 16 |
| H16 3/4-series exact | 52 | 52 | 32 | 84 | H16x | 0 |
| H16 3/4-series rescaled | 52 | 52 | 8 | 60 | H16x/4 | 16 |

Arithmetic charges each addition, subtraction, scalar multiplication and any separate unary negation. A binary gate has arbitrary scalar coefficients, with unary scaling folded into consumers or outputs under the gate count. The restoration column counts one multiplication per output when restoring this single block to scale one. A tensor chain can defer all its common scales. Structural wire depth includes unary stages and output restoration, and live-wire count assumes last-use slot reuse with outputs retained until completion.

## Methods and scope

| Method | Implemented search and limit | Scope of a negative result |
|---|---|---|
| Local replacement and CSE | Exact rational wire vectors, one-wire re-expression through earlier wires at coefficients ±1, ±2, ±1/2, and two-gate reassociation. Deduplicate equal vectors and prune unused wires. | Applies to tested neighborhoods and does not exhaust alternative topologies that require larger coordinated changes. |
| Beam and stochastic selection | Up to six retained states, eight rounds and 6,000 emitted neighbors per seed. One beam slot samples near-best discarded candidates with seed 20261126. Each seed has 120 s. | Safe ordering and reproducible random choices do not certify global optimality. |
| SMT scaling | Integer exponents in [−2,2] on internal wires and the common output scale, on the current fixed binary DAG. A distinct nonzero scale copy of a wire costs one multiplication and is shared by all consumers requiring it. Probe the target first when tighter. Each query sequence has 12 s per seed and a 768 MiB Z3 limit. | UNSAT only constrains the stated fixed DAG and exponent box. The solver does not select a new graph. UNKNOWN is retained separately. |
| Projective H8 exchange | Reorder the 19-gate seed's available directions using exact rank-two span checks with arbitrary rational coefficients. Test one helper deletion and two deletions plus one replacement. The replacement pool is formed from six small signed combinations of pairs of seed directions, with support at most four and primitive coefficients of magnitude at most two. Cap 512 replacements and 120 s. | Exhaustive only over those deletions and that pool. Every allowed wire direction may be reached in any topological order. |
| Live-wire scheduling | 256 seeded topological orders per DAG, then exact memoized feasibility under decreasing live-wire caps. The executed-operation set determines readiness and liveness. The exact phase has 100,000 states and 5 s per DAG. | The result concerns schedules of the same DAG with outputs retained and last-use reuse. It does not measure hardware registers. |
| Broader topology SMT or new low-rank decomposition | Left for a separate experiment. The published rank-one decomposition informs baseline choice, but varying it would require a new synthesis grammar. | This run gives no result for either global family. |

The method budget is 30 minutes and 1 GiB. The CLI applies the 1 GiB process cap before search. The run uses a Windows Job Object commit limit. POSIX uses `RLIMIT_AS` where available. Model and search limits above additionally bound each workload. [Windows process-limit semantics](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information).

## Results

| Seed | Local candidates | Best gates | Best add/sub | Best constant multiplies | Best scaled arithmetic | Output restore | Live-wire peak |
|---|---:|---:|---:|---:|---:|---:|---:|
| H8 19-gate witness | 2,207 | 19 | 19 | 1 | 20 | 8 | 13 |
| H8 5/6-series block | 2,086 | 19 | 19 | 1 | 20 | 8 | 13 |
| H16 5/6-series layers | 6,000 | 54 | 54 | 2 | 56 | 16 | 21 |
| H16 3/4-series rescaled | 6,000 | 52 | 52 | 8 | 60 | 16 | 17 |

The rows were checked on all 8 or 16 basis vectors in both domains. SMT recovered the published 20-operation half-scaled count from the unscaled 19-gate witness. The rescaled body uses H8/2 and matches the existing arithmetic benchmark. The best H16 body remains the pinned 56-operation circuit. The best H8 binary count remains 19. No arithmetic or gate record was found in the tested scopes.

For the fixed DAGs in the stated exponent box, Z3 returned UNSAT for zero scalar copies on the 19-gate H8, at most one on the 54-gate H16, and at most one on the 52-gate H16 family graph. The last test rules out 53 arithmetic operations in that particular model. Its follow-on request for at most seven scalar copies reached the timeout and remains UNKNOWN. The 54-gate topology already exceeds 53 before any scalar cost.

Projective closure exhausted all 11 single helper deletions and all 25,080 two-deletion/one-replacement exchanges over the 456 admitted new directions. There were 488,943 exact span checks and zero feasible 18-gate circuits in that neighborhood. It permits arbitrary rational pair coefficients within the allowed direction set. The 16,293 local rewrite candidates use the narrower dyadic coefficient list. These two negative results test different spaces.

The heuristic tried 256 topological orders per seed. The exact feasibility checks excluded peaks of 12 for the H8 half-scale DAG, 20 for the H16 5/6 layers, and 16 for the H16 3/4 rescaled DAG. Their attainable peaks under last-use reuse are therefore 13, 21 and 17 respectively. Binary and restored wire depth for these three circuits were 6/8, 7/9 and 8/11. None of the search passes reduced depth or peak on these witnesses.

The main run used Windows 11, Ryzen 7 5800X and CPython 3.13.3. Peak process working set was 66,011,136 bytes. The local passes took about 1.27, 1.30, 14.90 and 16.36 s, and H8 projective closure took 1.20 s. Solver and scheduling state counts, elapsed times and stop conditions are in the JSON record. The full local suite passed 172 tests in 24.73 s and the classical smoke benchmark exited successfully. The fixed-DAG solver test requires the optional Z3 package. No larger tensor lift or native port was started.

## Reproduce and resume

```sh
git clone --no-checkout https://github.com/jacobalansussman/wht-fewer-operations.git published-wht-reference
python -m pip install -e '.[dev]'
python -m pip install z3-solver==4.15.4.0
python -m nextfft_lab.bench_record_search --reference-repo published-wht-reference --out-dir results/record-circuits
python -m pytest -q
```

The reference clone can live outside the project. The driver pins the commit before reading any circuit and uses no upstream search code. The optional `--skip-smt` runs the non-SMT methods. Saved rational witnesses use string fractions with a common scale in the `nextfft-rational-circuit-v1` schema. Load with `RationalCircuit.from_dict`, then run `verify_rational` and `verify_field`. Unchanged best seeds are named by their exact source paths in the benchmark record.

The bounded run is closed. Continue only with a larger coordinated topology change that can plausibly remove binary gates from the 54-gate H16 layers or remove multiplication demand from a redesigned 52-gate DAG. The explored fixed-DAG and single-exchange neighborhoods give explicit baselines for that decision. [Raw results](../results/record-search.json) · [Rescaled H8 witness](../results/record-circuits/h8_19_gate.json).
