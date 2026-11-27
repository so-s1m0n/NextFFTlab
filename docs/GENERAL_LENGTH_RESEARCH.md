# General-length research: source verification and applications

## Purpose and scope

The first research cycle is archived in FINAL_REPORT.md. The aim now is to make the November 24, 2026 preprint inspectable and useful beyond WHT: executable lemma checks, clear applicability boundaries, and reproducible application experiments. A new record or a faster production FFT is not a required outcome. Do not resume the closed WHT search without a new structural argument.

Pinned source: [manuscript LaTeX](https://github.com/openai/math/tree/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build). This is a source-derived, independently coded component check, not independent validation of the complete theorem.

## G1 — executable geometric Newton factorization

Source: layers.tex, lem: up:newton-lemma / eq: up:newton (lines 106–149).
For distinct geometric nodes q^i, set H_i = product_{k=1}^i (1-q^k), c_i = (-1)^i q^{i(i-1)/2}, and T lower triangular Toeplitz with column 1/H_i. The paper's L = diag(H) T diag(c), Delta = diag(H_i c_i), hence V = diag(H) T diag(c/H) T^t diag(H). Inverse reverses the factors and replaces T by the Toeplitz matrix of the truncated reciprocal series.

Implementation: nextfft_lab/geometric.py, NewtonPlan and ToeplitzPlan. Field F_998244353, sizes 1..512, exact forward and interpolation. Toeplitz products are padded classical radix-2 NTT convolutions with cached kernel spectrum. This is a classical backend, not a saving recursive implementation. The reciprocal setup is quadratic; no complexity claim is made.

Verification: independent dense geometric character formula on every basis vector at sizes 1,4,7,8,16,17 for root nodes and 7,12 for q=3 (non-root nodes); compare cyclic inverse separately. 72 basis vectors across these cases (sum 1+4+7+8+16+17+7+12). Upper/lower Toeplitz direct oracle, reciprocal and rejection checks. tests/test_geometric.py.

## G2 — occupied workspace algebra [partial]

Source: layers.tex, up:toeplitz (lines 153–219). For normalized unit h, solve f(uX)=h(X)f(X) modulo X^n coefficientwise. With S multiplication by f and D diagonal u^i, T=D S D^-1 S^-1. Realize diag(S,S^-1) through the paper's three block shears and signed swap. Compose the commutator to obtain (Tx,z) for arbitrary scratch z. occupied_lower verifies this in sizes 2,5,8,16,31,64 using independent seeded nonzero scratch.

This only checks the algebra and scratch restoration. The padded Toeplitz backend allocates temporary arrays. It does NOT implement a bounded word with fully occupied registers, the four-update composition for R L J, or the synchronized fiber scheduler. Next test the full block map on every basis of the combined x,z input, implement the four-update composition with arbitrary nonzero intermediate registers, then implement the circulant shear and verify restoration of every scratch register. Count actual registers and transforms; stop if the practical cost is prohibitive.

## Matched measurement (G1)

Run: python -m nextfft_lab.bench_geometric --repeats 20
Raw samples and observed medians: results/geometric-baseline.json (20 samples per method and size). CPython 3.13.5, Linux x86_64, sandbox host, seed 20261127; one Python process, warm timings, 20 repeats, setup measured separately. Host CPU not recorded; no cross-machine claims. Local verification used the initial 58-test baseline plus 15 new cases (73 passed); full current repository suite is left to CI. Four length-b classical backend transforms per application; two cached kernel spectra built during setup.

| N | Padded b | Newton forward median | Classical radix2 median | Newton setup median |
|---:|---:|---:|---:|---:|
|16|32|120.572 us|13.097 us|92.386 us|
|64|128|523.240 us|49.261 us|458.524 us|
|256|512|2605.314 us|259.144 us|3514.008 us|
|512|1024|6412.407 us|655.572 us|11252.061 us|

No practical NTT speedup. The factorization is useful as an executable identity and a reusable fixed-kernel evaluation/interpolation path. Ordinary cyclic NTT is not its best application candidate; non-root geometric nodes are a separate workload. Do not claim an advantage there before comparing with Horner, chirp-based geometric evaluation (including odd/even and root conditions), and suitable fast multipoint evaluation implementations.

## Application research queue (all pending except G1/G2 checks)

| ID | Source anchor | Application and falsifiable next step |
|---|---|---|
| A1 | up:newton-lemma | Geometric multipoint evaluation/interpolation: compare against Horner and chirp-z style convolution on non-root grids, amortized setup and batches. Verify arbitrary distinct nodes only where geometric; no general multipoint claim. |
| A2 | up:toeplitz, up:fibers | Fixed-filter convolution/Toeplitz and synchronized NTT: implement full scratch restoration and fiber scheduling with independent input, compare workspace high-water mark, memory passes and wall time against batched classical kernels. |
| A3 | thm:conv, cor:toe (packing.tex) | Formal polynomial multiplication: implement small source-mapped packing/deformation or fixed multiplication by a unit. Compare schoolbook and optimized NTT including packing/extension and output recovery. Differentiate negacyclic, cyclic, linear convolution. |
| A4 | up:grid, up:packing (grids.tex) | General-length cyclic NTT: prove and verify small Good-factor/auxiliary-length/extension-coordinate identities, preserve independent fibers. Never claim sub-N-log-N without a real saving backend. |
| A5 | up:newton-lemma, up:grid | Complex FFT / chirp-z evaluation: first compare exact algebra with mpmath/high-precision oracles, quantify conditioning and forward/backward error; test roots and non-root grids. Compare FFTW/pocketfft and established chirp-z implementation. If unstable, record failure rather than presenting the finite-field algorithm as a numerical FFT. |
| A6 | A3/A4 prerequisites | Cryptographic polynomial arithmetic: benchmark public, non-secret vectors with the standardized transform conventions (ML-KEM's incomplete NTT differs from a full cyclic NTT); no production security or constant-time claims. |

Each track may proceed independently only as far as its mathematical dependencies are satisfied. Maintain the claim ledger in this file; archive raw outputs and distinguish classical baseline, source-derived identity, new experiment, and full theorem. No new product, GUI, or package dependency without a research requirement.
