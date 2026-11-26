# Implementation roadmap / acceptance gates

## Source snapshot

Primary source pinned to openai/math commit 3344da59991ed94f9ba711217b29c1d760badfa6.
[Manuscript directory](https://github.com/openai/math/tree/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026).
Actual LaTeX is in build/; no PDF extraction is needed. Upstream README, main.tex, intro.tex, repair.tex, kernel.tex and section labels of layers.tex/packing.tex/binary.tex were inspected. Full proof and Lean build are not yet audited.

| Source | Implementation role |
|---|---|
| intro.tex, thm:main | Binary linear-gate model and field conditions |
| repair.tex, lem:count-predict (81), lem:matrix-root (128), lem:hermite-repair (188), thm:repair (35) | Predictor, affine-linear matrix pencil, exact sparse error recovery |
| kernel.tex, thm:kernel (15), eq:kernel-routing-block (97), eq:kernel-pencil-cost (261), eq:kernel-template-saving (294) | Prime tensor power, shared queries and endpoint conversions, batch recursion |
| binary.tex, prop:binary-template (12) | Walsh–Hadamard specialization and stability (inspect in full) |
| layers.tex, lem:shear, up:newton-lemma, up:toeplitz, up:fibers | Axis synchronization and workspace |
| grids.tex, packing.tex, thm:conv | All lengths and polynomial multiplication (audit full dependencies) |
| lean/OAI/LinearAlgebra/FiniteFourier/Main.lean, BatchedTheorem.lean; lean/docs/130.md | Formal statements, scope, pinned toolchain |

Theorem counts a gate forming au+bv with arbitrary field coefficients, not processor cycles. Kernel proof uses constants depending on chosen radix and exponent, large batch widths, row-matrix coefficients, cyclotomic extension, and fixed template routing. Asymptotic existence alone does not supply a feasible crossover size. Do not hide enormous constants. Binary prime tensor transform is Walsh–Hadamard, not cyclic NTT.

## Gate 0 — baseline [done]

Classical direct DFT, radix-2 NTT, Bluestein, convolution, NumPy/SciPy benchmark. Local 58 tests passed; GitHub Actions run 45812334289 succeeded on initial commit. Benchmark is a smoke baseline only.

## Gate 1 — pinned proof audit and scalar predictor [executable criteria passed; Lean build deferred]

- [x] Locate exact primary LaTeX source and theorem labels.
- [x] Implement integer-count scalar oracle for lem:count-predict, using generalized integer binomial coefficients before reduction modulo the field. Exhaustive 3-bit toy window: 48 exact in-window cases, 16 outside (not the theorem's general window). Test general window for radices 2,7,17 at selected counts. Local suite: 64 passed.
- [ ] Compile upstream Lean with pinned toolchain; record theorem names, axioms and precise correspondence; distinguish formal lower and upper bounds and any nonformal practical cost claims. If build impractical, report the reason.
- [x] Implement binary tensor transform baseline (direct sign character matrix and independent iterative Walsh–Hadamard); add exact oracle and basis tests.
- [x] Derive indicator polynomial in query powers without reading integer count in the executable pencil; compare evaluation against scalar oracle. Record term counts, degree, and setup costs.
Acceptance: source-mapped formulas, verified domains, independent exact tests, explicit open assumptions. No speed claim.

### Gate 1 evidence (2026-11-26)

- The parameter domain is the fixed field F_998244353 with prime query radix in {2, 7, 17}. Each positive T coefficient is an affine form from the indicator in `lem:count-predict`. The executable stores these forms and multiplies truncated series. Each query appears at most once in a monomial, so degree is bounded by min(D,m) and the expanded support by Σ_{d≤min(D,m)} binom(m,d)(ell−1)^d. This is a support bound, with cancellations possible. The toy window (1,2) has exactly three nonzero terms and degree 1 for every binary shift.
- Tests compare the independent sign matrix with butterflies on basis, random and unsupported lengths. Query tests compare the truncated series evaluator against the integer-count oracle on all 64 toy query/shift pairs, including outside the window, degenerate windows, and sampled general windows. An affine test also evaluates off the root-of-unity grid.
- Windows x86-64, CPython 3.13, Ryzen 7 5800X, single-threaded component code. `python -m pytest -q` reported 90 passed and the existing `python -m nextfft_lab.bench --max-power 7 --repeats 2` smoke exited successfully. Run `python -m nextfft_lab.bench_repair --repeats 20` for raw timing, operation counts and separately traced Python allocation peaks. [Recorded samples](../results/gate1-components.json).
- At length 128 the direct and iterative Walsh medians were 1.285 ms and 0.0628 ms with 11,064 and 5,352 tracked bytes respectively. At m=128, ell=2 one query polynomial took 0.2033 ms to compile and 0.7599 ms to evaluate at the median. The polynomial evaluator is a component experiment. Paper gate counts and process RSS require separate measurement.

### Lean source correspondence

- [Pinned toolchain](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/lean-toolchain) specifies `leanprover/lean4:v4.34.1`. The Mathlib revision is `d13f23b723b8a846827a245b89c10fc7d3f11612` in the [Lake lock file](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/lake-manifest.json).
- The [Comparator spec](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/ComparatorChallenges/ExactFourier.json) lists `OAI.ExactFourier.main_theorem`, `OAI.LinearAlgebra.FiniteFourier.fourierComplexity` and `OAI.LinearAlgebra.FiniteFourier.batchedFourierComplexity`. The first directly states `thm:main`. The second combines the upper and geometric-feedback lower estimates and includes the normalized inverse. The third states the same exact bounds across mixed batched blocks and a stronger robust lower bound in the joint error model. [Statements](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/ComparatorChallenges/ExactFourier.lean).
- The batched upper estimate assembles per-block upper circuits via `batchFourier_upper`. The batched lower estimate joins bounded orders with the large-order spectral-plane argument. The Comparator axiom allowlist is `propext`, `Quot.sound`, `Classical.choice`. Actual transitive axioms and kernel verification remain unmeasured. These statements quantify over admissible fields and exact binary linear gates, with no guarantees about floating point, wall-clock time, memory or an engineering crossover. [Single theorem assembly](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/OAI/LinearAlgebra/FiniteFourier/Main.lean) · [Batched theorem assembly](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/OAI/LinearAlgebra/FiniteFourier/BatchedTheorem.lean).
- No Lean, Lake or Elan executable was present on PATH. The upstream Windows v4.34.1 release headers reported a 589,007,020-byte tar.zst or 850,624,573-byte ZIP before Mathlib and the remaining locked dependencies. The upstream Comparator instructions also require Comparator, landrun and lean4export. Local compilation and `#print axioms` are deferred pending a provisioned verifier and measured build budget. A source check was run here. [Release](https://github.com/leanprover/lean4/releases/tag/v4.34.1) · [Verifier setup](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/ComparatorChallenges/README.md).

## Gate 2 — actual pencil and repair

- Construct affine factors and matrix root L from repair.tex lem:matrix-root; verify L^b=pI over suitable fields for small symbolic/numeric examples. Track b^h row count, actual root availability, extension rank and memory before allocation. Use sparse operations; refuse huge allocation with diagnostics. All rows are independent inputs, not duplicated copies.
- Implement Hermite repair with Vandermonde H, known exceptional indices J per frequency, recover e_J, compute D_z by polynomial division without dividing by p-z at zero, lift with H^T. First verify frequency-local algebra, then full row program using only check-row spectral conversions; no per-row oracle conversion hidden in fast path. Handle s=0, multiple errors, characteristic, singular nodes and empty cases.
- Test toy 3-bit window and multi-frequency data, changing exceptional sets. Separately test actual theorem window and applicable size bound; toy cases do not establish its claimed rate.
Acceptance: independently computed product matches on all rows, actual conversion counts and predictor applications recorded; no claim of full kernel yet.

## Gate 3 — prime tensor kernel

- Derive commuting Q_j and monomial phase/permutation relation from kernel.tex; verify for small eligible digit/axis configurations.
- Implement shared pencil routing, label/rectangle decomposition and endpoint conversions; prove and test the indexing/permutation identity. Record actual calls per row, not just abstract pencil stages.
- Enumerate constructible finite-template parameters (m,A,W,sigma, extension rank, memory/setup). Demonstrate the actual strict saving sigma/W < A^theta at a specified theta > 1/2 or report the smallest tested feasible configuration and blocker. Distinguish analytic existence from a numeric certificate.
- Implement recursion and batch padding, with explicit fallback for bounded k; test basis, random, multi-batch and inverse. Verify against classical Walsh baseline.
Acceptance: actual source-mapped prime tensor construction end to end, supported domains and finite cost accounting. A fallback-only implementation fails this gate.

## Gate 4 — practical viability and applications

- If Gate 3 works, port the hot path to compiled Rust/C++ and compare same-domain optimized WHT first, then NTT/FFT only after source-mapped general-length construction. Benchmark cold/warm setup, wall time, peak memory, operation counts, batch throughput, size scaling, hardware, raw samples and variation.
- Derive general lengths via layers.tex/grids.tex and polynomial convolution via packing.tex; test independently. Check extension arithmetic cost, inverse normalization, and precision before complex FFT/GPU.
- First application candidate: exact modular polynomial multiplication; compare end-to-end convolution with optimized classical NTT for same modulus, lengths and outputs. If no viable construction, publish bounded negative results and investigate which components are reusable.

## Decision rules (project targets, not theorem guarantees)

- Reproduction milestone: Gate 3 correct on at least one nontrivial configuration with the actual new path exercised and independently checked; general-length reproduction is a separate extension.
- Research success: reproducible correctness/parameter and cost evidence, including negative findings. If blocked before complete reproduction, label it partial research, not completion.
- Practical GO: compiled same-domain backend >=1.2x faster than a tuned baseline on at least three consecutive realistic input sizes with identical exact output, median over >=20 repeats and memory <=2x baseline; report all sizes and cold/warm setup separately. Repeat on another machine if available. This threshold is provisional; justify any change before gathering evaluation data.
- Stop or pivot: if the actual template exceeds the local budget (default 1 GiB estimated working memory per experiment or 60 seconds per case), report parameters and estimates, try a bounded component optimization, do not blindly allocate. A budget failure is not a mathematical impossibility result.
- Application GO: measurable end-to-end improvement for a real workload, not just gate count. No premature GUI, package publishing, GPU port or unrelated feature expansion.

## Next task for Codex

Implement the bounded Gate 2 pencil and spectral repair. Keep the full local Lean build listed separately until it has observed evidence.
