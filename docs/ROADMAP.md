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
- No Lean, Lake or Elan executable was present on PATH. The upstream Windows v4.34.1 release headers reported a 589,007,020-byte tar.zst or 850,624,573-byte ZIP before Mathlib and the remaining locked dependencies. The upstream Comparator instructions also require Comparator, landrun and lean4export. Local compilation and `#print axioms` are deferred pending a provisioned verifier and measured build budget. The source statements and declared axiom allowlist were inspected. [Release](https://github.com/leanprover/lean4/releases/tag/v4.34.1) · [Verifier setup](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/ComparatorChallenges/README.md).

## Gate 2 — actual pencil and repair [bounded components verified]

- Construct affine factors and matrix root L from repair.tex lem:matrix-root; verify L^b=pI over suitable fields for small symbolic/numeric examples. Track b^h row count, actual root availability, extension rank and memory before allocation. Use sparse operations; refuse huge allocation with diagnostics. All rows are independent inputs, not duplicated copies.
- Implement Hermite repair with Vandermonde H, known exceptional indices J per frequency, recover e_J, compute D_z by polynomial division without dividing by p-z at zero, lift with H^T. First verify frequency-local algebra, then full row program using only check-row spectral conversions; no per-row oracle conversion hidden in fast path. Handle s=0, multiple errors, characteristic, singular nodes and empty cases.
- Test toy 3-bit window and multi-frequency data, changing exceptional sets. Separately test actual theorem window and applicable size bound; toy cases do not establish its claimed rate.
Acceptance: independently computed product matches on all rows, actual conversion counts and predictor applications recorded; no claim of full kernel yet.

### Gate 2 evidence (2026-11-26)

- [Source](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/repair.tex). `lem:matrix-root` gives cyclic shifts with prefix phases, with each column represented as affine sparse transitions. Tested L^b=pI on all basis columns for b=2,4,8 and off-grid field values. Root orders must divide p−1. The bounded cases use extension rank 1 and distinct base-field nodes 0,…,W−1 as permitted by `lem:hermite-repair`. The theorem's universal construction instead chooses cyclotomic nodes.
- The binary quotient for `lem:hermite-repair` is D_z(y)=−(y+2z)/2. The program decodes with the first |J| Vandermonde checks, applies the transpose inverse for lifting and performs exactly 2s forward and 2s inverse conversions. Per-frequency operators only see check rows. Pencil applications are XOR index shifts and row combinations. Tests include multiple exceptions, changing and empty sets, a node with p=z, and singular nodes. The complete toy batch is compared to the independent coordinate permutation on all 512 basis vectors and seeded independent random rows.
- Toy m=3, [1,2] uses b=2, W=64 and s=16. The test observed 4 predictor calls and 32 forward plus 32 inverse row conversions. It uses 8 pencil stages, 12,288 pencil multiply-accumulates, and 32,768 check/lift multiply-accumulates. Its exception fraction is 1/4. The theorem's 1/(2m³) bound applies to its own window.
- The paper's m=2 window [−2,4] uses b=8 and W=32 with s=0. All 128 basis vectors and a random batch pass with no conversions. This case exercises matrix-root evaluation and the theorem window.
- The first binary theorem window with exceptions is m=60, [1,59], with exactly 2 bad shifts out of 2^60 per frequency. The expanded representation over F_998244353 has 576,460,752,303,423,487 nonzero terms per shift and b=64. Its log₂ W is 3,458,764,513,820,540,982. At m=128 the corresponding values are in the raw data. Those are counts for this expansion, and the cyclotomic rank estimate applies to the proof's universal node construction.
- A bounded algebraic alternative at m=60 replaces the expanded predictor by the target monomial plus its two corrections. The multilinear indicator of query point s is ∏(1+s_j q_j)/2, so each correction is one product of affine forms. Equality on the sign cube characterizes the multilinear polynomial because 2 is invertible. This yields W ≤ 2^78 with b=64 using at most three products. Even one 32-bit value per required shift costs 4 EiB at m=60. The 4,096-row local limit rejects these cases before matrix allocation. The bound applies to the paper's explicit all-shifts construction as implemented here.
- On the Gate 1 host, 20 repetitions gave 4.5324 ms median setup, 5.02875 ms median reused execution and 201,748 bytes of traced execution allocations for the toy. Direct XOR permutation took 0.00415 ms and 8,296 traced bytes. The m=2 theorem-window case took 0.20595 ms reused, with 16,960 traced bytes. Python tracing omits process RSS. These comparisons are for the query-product component. Walsh transforms of the whole input and the shared routing remain separate.
- `python -m pytest -q` reported 104 passed and the classical benchmark smoke exited successfully. Run `python -m nextfft_lab.bench_pencil --repeats 20`. [Raw samples and component counts](../results/gate2-pencil.json).

## Gate 3 — prime tensor kernel [fixed template verified; saving and recursion open]

- Derive commuting Q_j and monomial phase/permutation relation from kernel.tex; verify for small eligible digit/axis configurations.
- Implement shared pencil routing, label/rectangle decomposition and endpoint conversions; prove and test the indexing/permutation identity. Record actual calls per row, not just abstract pencil stages.
- Enumerate constructible finite-template parameters (m,A,W,sigma, extension rank, memory/setup). Demonstrate the actual strict saving sigma/W < A^theta at a specified theta > 1/2 or report the smallest tested feasible configuration and blocker. Distinguish analytic existence from a numeric certificate.
- Implement recursion and batch padding, with explicit fallback for bounded k; test basis, random, multi-batch and inverse. Verify against classical Walsh baseline.
Acceptance: actual source-mapped prime tensor construction end to end, supported domains and finite cost accounting. A fallback-only implementation fails this gate.

### Gate 3 evidence (2026-11-26)

- `kernel.tex`, “The product of queries”, gives one factor with kernel (−1)^((x−s)(t−y))/2 per selected binary pair. The product visits each distinguished pair once and each auxiliary pair an odd number of times. The input and output sign diagonals, output half exchange and factor 2^(df) recover the unnormalized Walsh matrix. Tests compare the spectral query multipliers and commutativity, all 64 basis columns of the smallest monomial identity, and seeded arrays with auxiliary axes and two-column layouts. [Pinned kernel source](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/kernel.tex).
- `eq:kernel-routing-block`: over F_998244353, the charged rectangles expand p(Δ) in the match-binomial basis. The free rectangles partition odd distances by the first differing bit. Their weights cancel the off-diagonal transfers and their Gram pairings vanish. Tests check all label entries for six label sets up to 64 labels. For L=q=2 the Gram space has two orthogonal directions given by label parity. Each free rectangle is a singleton transfer. One auxiliary pair transform at its source and one at its destination serve all three queries. The intervening axis exchange and cross-row mixing implement each transfer. Tests compare arbitrary cross-row matrices with an independent per-label pencil application and observe 80 pair kernels for two rows per label in a single stage.
- The materialized binary template connects the paper-window matrix root, all 16 pencil stages, shared routing and the input/output monomial maps at m=3, L=q=2, D=2, A=8, f=1. All 512 independently seeded arrays of 256 entries agree with iterative Walsh–Hadamard. A separate inverse basis test checks all four labels and normalization. The concentration window is [−4,7] and has no exceptions. Hermite repair with nonzero exceptions remains verified in the Gate 2 toy component.
- The routed schedule uses 163,840 one-axis-call equivalents, or 320 per batch row, compared with A=8 for successive classical axis transforms. One selected pair kernel represents two axis calls mathematically. The implementation executes that kernel directly using modular arithmetic. Across 40 schedule estimates for m in {3,5,7,9,11}, L=2…6, q in {2,4,8}, and at most 64 labels, 11 fit the 1 GiB input-only estimate. No estimated schedule satisfies σ/W < A^(3/4). The estimates enumerate the charged common transforms and free endpoint incidences in this schedule, with no cross-rectangle caching. They do not bound every possible schedule or disprove the asymptotic result.
- Windows 11 x86-64, CPython 3.13, Ryzen 7 5800X, one active algorithm thread. Three materialized repetitions gave 7.684 s median application and 73.36 ms median for independent classical Walsh on the same batch. Cold template setup took 1.397 ms. A separate direct CPython process reached a 55,705,600-byte peak working set, including inputs, the reference result and the interpreter. Both paths used exact field arithmetic. This is a bounded Python comparison. No compiled-baseline practical GO or crossover was established.
- The first odd m with a nontrivial paper window is 63, with window [1,62]. The source layout has A=2(m+D−1)≥126, so a single explicit f=1 row already requires at least 2^128 bytes at four bytes per entry. This is separate from the row count, coefficient extension and routing storage. The local template cannot supply a strict saving or the padding recurrence. The next unverified milestones are a feasible saving template, recursive packing and a complete finite Fourier backend. `prop:binary-template` assumes that saving and provides a perturbation bound for a normalized construction. These finite-field tests make no numerical stability claim. [Pinned binary proposition](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/binary.tex).
- `python -m pytest -q` reported 121 passed at the original checkpoint and again at publication review. The classical benchmark smoke exited successfully at the original checkpoint. [Reproduction and memory methodology](../README.md#reproduce-the-recorded-benchmarks). [Raw samples](../results/gate3-kernel.json).

### Follow-up optimization checkpoint

Exact symmetric windows, a factored m=15 one-shift pencil and a sparse A=8 template are implemented. The optimized template uses 24 axis calls per row and remains above the recursion threshold. The m=15 window admits two exceptional shifts, yet even one dense source-layout row exceeds the local budget. [Derivations, ablations, raw data and continuation criteria](OPTIMIZATION.md).

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

## Circuit research checkpoint

The direct-reproduction and optimization work is preserved at `checkpoint/pr-1`. Scaling the explicit layout is closed for this research line. Bounded synthesis found 7- and 22-gate circuits at sizes 4 and 8. The known 19-gate H8 block was lifted through 512 points and checked on each basis vector. Structural constraints, operation counts, wall-clock comparisons and the next entry criteria are recorded in the circuit research note. [Circuit research](CIRCUIT_RESEARCH.md).

### Published-record search checkpoint

The 166-test baseline is tagged `checkpoint/166-tests`. Local substitution, dyadic scale SMT, projective H8 exchanges and schedule feasibility checks were completed under explicit limits. The best retained counts match the published comparison points. [Search scope and reproduction](RECORD_SEARCH.md).

## Next task for Codex

Use the exact rational verifier for a coordinated topology change beyond the explored H8 and H16 neighborhoods. A candidate must beat the published gate or scaled-arithmetic comparison before large lifts or native ports. Resume the predictor/repair line only for a structural alternative that reduces batch or address requirements and gives a verifiable saving with full independence and repair. Lean verification and general-length reproduction remain open.
