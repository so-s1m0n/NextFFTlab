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

## Gate 1 — pinned proof audit and scalar predictor [partial]

- [x] Locate exact primary LaTeX source and theorem labels.
- [x] Implement integer-count scalar oracle for lem:count-predict, using generalized integer binomial coefficients before reduction modulo the field. Exhaustive 3-bit toy window: 48 exact in-window cases, 16 outside (not the theorem's general window). Test general window for radices 2,7,17 at selected counts. Local suite: 64 passed.
- [ ] Compile upstream Lean with pinned toolchain; record theorem names, axioms and precise correspondence; distinguish formal lower and upper bounds and any nonformal practical cost claims. If build impractical, report the reason.
- [ ] Implement binary tensor transform baseline (direct sign character matrix and independent iterative Walsh–Hadamard); add exact oracle and basis tests.
- [ ] Derive indicator polynomial in query powers without reading integer count in the executable pencil; compare evaluation against scalar oracle. Record term counts, degree, and setup costs.
Acceptance: source-mapped formulas, verified domains, independent exact tests, explicit open assumptions. No speed claim.

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

Complete Gate 1 beginning with the Walsh–Hadamard baseline and query-power polynomial, then Gate 2. Use source labels, test and commit each bounded milestone. Update this ledger from observed results, not predictions.
