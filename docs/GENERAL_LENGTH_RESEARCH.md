# General-length research: source verification and applications

## Purpose and scope

The first research cycle is archived in FINAL_REPORT.md. The aim now is to make the November 24, 2026 preprint inspectable and useful beyond WHT: executable lemma checks, clear applicability boundaries, and reproducible application experiments. A new record or a faster production FFT is not a required outcome. Do not resume the closed WHT search without a new structural argument.

Pinned source: [manuscript LaTeX](https://github.com/openai/math/tree/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build). This is a source-derived, independently coded component check, not independent validation of the complete theorem.

## G1 — executable geometric Newton factorization

Source: layers.tex, lem: up:newton-lemma / eq: up:newton (lines 106–149).
For distinct geometric nodes q^i, set H_i = product_{k=1}^i (1-q^k), c_i = (-1)^i q^{i(i-1)/2}, and T lower triangular Toeplitz with column 1/H_i. The paper's L = diag(H) T diag(c), Delta = diag(H_i c_i), hence V = diag(H) T diag(c/H) T^t diag(H). Inverse reverses the factors and replaces T by the Toeplitz matrix of the truncated reciprocal series.

Implementation: nextfft_lab/geometric.py, NewtonPlan and ToeplitzPlan. Field F_998244353, sizes 1..512, exact forward and interpolation. Toeplitz products are padded classical radix-2 NTT convolutions with cached kernel spectrum. This is a classical backend, not a saving recursive implementation. The reciprocal setup is quadratic; no complexity claim is made.

Verification: independent dense geometric character formula on every basis vector at sizes 1,4,7,8,16,17 for root nodes and 7,12 for q=3 (non-root nodes); compare cyclic inverse separately. 72 basis vectors across these cases (sum 1+4+7+8+16+17+7+12). Upper/lower Toeplitz direct oracle, reciprocal and rejection checks. tests/test_geometric.py.

## G2 — occupied workspace algebra [PR #3 starting point]

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

## Application research queue (initial plan)

| ID | Source anchor | Application and falsifiable next step |
|---|---|---|
| A1 | up:newton-lemma | Geometric multipoint evaluation/interpolation: compare against Horner and chirp-z style convolution on non-root grids, amortized setup and batches. Verify arbitrary distinct nodes only where geometric; no general multipoint claim. |
| A2 | up:toeplitz, up:fibers | Fixed-filter convolution/Toeplitz and synchronized NTT: implement full scratch restoration and fiber scheduling with independent input, compare workspace high-water mark, memory passes and wall time against batched classical kernels. |
| A3 | thm:conv, cor:toe (packing.tex) | Formal polynomial multiplication: implement small source-mapped packing/deformation or fixed multiplication by a unit. Compare schoolbook and optimized NTT including packing/extension and output recovery. Differentiate negacyclic, cyclic, linear convolution. |
| A4 | up:grid, up:packing (grids.tex) | General-length cyclic NTT: prove and verify small Good-factor/auxiliary-length/extension-coordinate identities, preserve independent fibers. Never claim sub-N-log-N without a real saving backend. |
| A5 | up:newton-lemma, up:grid | Complex FFT / chirp-z evaluation: first compare exact algebra with mpmath/high-precision oracles, quantify conditioning and forward/backward error; test roots and non-root grids. Compare FFTW/pocketfft and established chirp-z implementation. If unstable, record failure rather than presenting the finite-field algorithm as a numerical FFT. |
| A6 | A3/A4 prerequisites | Cryptographic polynomial arithmetic: benchmark public, non-secret vectors with the standardized transform conventions (ML-KEM's incomplete NTT differs from a full cyclic NTT); no production security or constant-time claims. |

Each track may proceed independently only as far as its mathematical dependencies are satisfied. Maintain the claim ledger in this file; archive raw outputs and distinguish classical baseline, source-derived identity, new experiment, and full theorem. No new product, GUI, or package dependency without a research requirement.

## Continuation checkpoint (2026-11-27)

### G2 — occupied register word [verified in a bounded domain]

`nextfft_lab/occupied.py` implements both four-update identities, first for LJ and then for RLJ. Each circulant shear transforms two already occupied b-register blocks, adds the diagonal-spectrum product in place and applies the inverse transforms. The padded length b is the least power of two at least 2a. The execution uses one caller-owned buffer of 2a+2b canonical residue registers, plus scalar temporaries and read-only coefficient tables. The plan setup allocates coefficient arrays separately and uses a quadratic recurrence. The 2a+2b combined basis tests cover a two-sided Toeplitz shear, lower/upper triangular factors and the Newton word. Inverse Newton is checked on the independent forward-image basis and the identity on auxiliary slots. Seeded dirty registers are checked separately. [Source, up:toeplitz](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/layers.tex#L153-L219)

A Toeplitz shear uses 16 classical length-b NTTs, a triangular factor uses 96 and a Newton application uses 192. Scalar updates, bit reversal, plan storage and setup are additional. The n=32 word with 192 data registers took 17.824 ms per sample including reset of the existing input slots. The ordinary padded Newton implementation took 0.343 ms with reused setup on the same input. The restoration identity works and this replacement is expensive. A2 remains open for borrowing occupied fibers in groups and measuring the scheduling cost. [Raw timings and traced Python peaks](../results/geometric-extensions.json)

### A1 — non-root geometric evaluation and interpolation [verified and measured]

With q=3, compare Horner evaluation and classical divided differences with the paper's Newton factorization. A separate chirp baseline uses q^(ij)=q^(C(i+j,2)-C(i,2)-C(j,2)). After reversing the scaled input its selected convolution interval has no circular aliasing at a padded length of at least 2n−1. This avoids a square-root assumption on q. Basis and random tests include odd and even lengths and compare evaluations with a dense character oracle. The interpolation baseline is quadratic and computes inverses per difference.

At n=128 the batch-of-four forward medians were 5.169 ms for Newton, 2.765 ms for the chirp and 3.781 ms for Horner. The independently implemented divided-difference interpolation took 30.125 ms against 5.232 ms for Newton on the same values. Newton setup was 1.543 ms and chirp setup 0.557 ms. Newton uses four padded NTTs per forward application and two cached spectra across forward/inverse setup. The chirp needs two transforms per application and one cached spectrum. These measurements support a bounded interpolation comparison against the chosen quadratic baseline. Faster interpolation comparators and rectangular grids are open. [Evidence](../results/geometric-extensions.json)

### A3/A4 — small packing and coprime-axis checks [verified and measured]

`packed_product` verifies the mixed-radix map in `poly:eq:mixed-radix-packing` at extension degree e=1. It uses padded z-exponents, cyclic NTT along X and schoolbook products of truncated jets at each frequency. Gather adds all coordinates with the same original integer index, including mixed-radix carries. Both operands' bases and seeded vectors are compared against dense linear convolution. At n=32 the packed path took 0.652 ms and ordinary linear NTT convolution 0.208 ms, including setup. Per case, packing uses 4 ceil(r/2)−1 length-N classical transforms and direct pointwise jet arithmetic. Root extensions, prime-grid selection and deformation remain open. [Source, packing.tex](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/packing.tex)

`good_factor` verifies Good's prime-factor identity for coprime lengths a,b with ab dividing p−1. Input indices use CRT representatives j₁b·b⁻¹ mod a and j₂a·a⁻¹ mod b in the two summands. Outputs read the axis frequencies k·b⁻¹ mod a and k·a⁻¹ mod b. Axis kernels use classical radix-2 or dense DFT, with inversion normalized on each axis. Complete basis checks compare both directions with the dense cyclic DFT. At n=28 the measured Good factorization took 0.091 ms, Bluestein 0.237 ms and dense DFT 0.261 ms. The comparison covers the listed eligible sizes and does not instantiate extension-coordinate packing or the paper's general-length circuit. [Source, grids.tex](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/grids.tex) · [Packing and factorization data](../results/geometric-packing.json)

### A5 — complex FFT / CZT [measured, tested implementation rejected as replacement]

The separate complex128 experiment isolates parameter rounding with a 100-digit Decimal oracle. At DFT length 64 the whole-map condition estimate was about 1, while the FFT-backed Newton error was about 1.49 and SciPy FFT about 1.51e−16. The measured instability is associated with the factorization's intermediate scaling. The result applies to the tested implementation and grids. [Experiment](COMPLEX_GEOMETRIC_A5.md) · [Raw data](../results/complex-geometric-a5.json)

### Reproduction and next bounded gate

The finite-field benchmarks below used seven warm samples per method, seed 20261127, Windows 11 x86-64, Ryzen 7 5800X, CPython 3.13.3 and a single algorithm thread. The largest exact geometric batch measured was four rows of length 128. Setup and application are separated when reused. Traced peaks describe Python allocations rather than process RSS. The full regression with Z3 passed all 220 tests, and the classical benchmark smoke produced 35 rows.

```sh
python -m pip install -e '.[dev,research]'
python -m pytest -q -rs
python -m nextfft_lab.bench_geometric_extensions --repeats 7
python -m nextfft_lab.bench_geometric_packing
python -m nextfft_lab.bench_complex_geometric
```

G2's next dependency is A2 fiber scheduling with arbitrary occupied neighboring data. Beyond the bounded A3/A4 identities, the next source gate is independent coefficient-coordinate verification over a small extension field before testing any claimed general-length savings.
