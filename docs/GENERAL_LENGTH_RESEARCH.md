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

### A4 — extension-coordinate packing checkpoint [bounded verification]

Source: grids.tex, up:packing (returning to the base field), combined with up:newton-lemma. See [pinned source](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/grids.tex#L88-L112).

The independent reference uses E = F_p[t]/(t^2-3), p=998244353. Euler's criterion verifies 3 is a nonsquare. With i a primitive fourth root in the base field, z=(-1+i*t)/2 is a primitive third root. Multiplying z by the base-field primitive root of order b/3 gives an auxiliary root of order b in {6,12,24,48}; no such b-th root exists in F_p. Pack the two independent inputs as x+t*y. Base-defined Newton diagonal and triangular Toeplitz factors preserve the coordinatewise target transform, even though the auxiliary cyclic convolutions actually use E-valued roots and coefficients. The basis 1,t is related by an invertible base-field change of coordinates to 1,w for the chosen auxiliary root w. This checks the coordinate principle, not the paper's exact asymptotic parameter schedule.

Implementation: nextfft_lab/extension_coordinates.py. Tests check exact auxiliary root orders, dense extension DFT inversion, all 106 basis vectors of the combined two-row input across seven lengths (2,3,4,7,8,13,16), independent seeded rows, restoration by interpolation, and unsupported inputs. Forward output uses an independent direct base-field geometric formula. Local focused suite: 12 passed; full current suite requires CI.

Run: python -m pytest -q tests/test_extension_coordinates.py

Limitations: dense quadratic extension DFT; six auxiliary transforms per application (including repeated kernel setup), ordinary base-field NewtonPlan setup, temporary arrays, no occupied-register word, no performance claim. Each extension register is two base-field coordinates, so packing two rows does not compress arbitrary input information. This is an actual extension-field execution, not a componentwise base-field transform masquerading as extension arithmetic. General extension degrees, grouped-axis capacity, incomplete final batches, efficient descent, and the saving backend remain open.

Next: A2 fiber scheduling with arbitrary occupied adjacent fibers; then batch padding and multiple axes for A4. For A1 compare interpolation with an established fast geometric interpolation method before claiming an application advantage. Keep A5's bounded negative result; no further complex optimization without a stability hypothesis.

### Next-cycle checkpoint from PR #3 at 8432fab

The 12 extension-coordinate tests at the incoming commit were independently reviewed and replayed. Root orders, two-row basis results and the field-coordinate scope agree with the pinned source. The full incoming suite with Z3 passed 232 tests. Integer residues and integer lengths are the supported interface.

| Track | Status and evidence |
|---|---|
| A2, occupied neighbors | The serial group kernel of `up:fibers` now operates on an occupied tensor. At 8×8 it needs zero dedicated payload slots rather than 40 with dedicated scratch, with 3,072 NTT calls in either path. The borrowed path took 169.6 ms versus 85.8 ms with dedicated scratch. All basis vectors matched a dense tensor calculation. [Implementation, actual slot traffic and limits](OCCUPIED_FIBERS_A2.md) |
| A1, fast interpolation | Bostan–Schost's two-convolution interpolation now provides a matched fast comparator over F_998244353. At n=128 the setup was 0.887 ms versus 1.556 ms for the paper-derived prototype, and four-input reuse took about 5.36 ms in both paths. The non-root evaluate–multiply–interpolate application matched schoolbook and NTT and took about 7.79 ms versus 1.71 ms for ordinary convolution at 128 coefficients per operand. [Method, verification and measurements](GEOMETRIC_INTERPOLATION_A1.md) |
| A4, multi-axis extension coordinates | Actual quadratic-field Fourier kernels process up to three axes, preserving each independent grid. Odd batch widths exercise the padded zero coordinate. The 3×4, width-five case used 37,512 counted base multiplications versus 4,840 for separate base-field calls. [Extension checks and raw data](EXTENSION_RESEARCH.md) |
| A3, extension-coordinate packing | The half-box experiment performs multiplication in a quartic extension with quadratic subfield Fourier roots, then gathers mixed-radix carries. All bilinear basis pairs at the tested sizes agree with ordinary convolution. At n=16 warm packed multiplication took about 0.884 ms versus 0.103 ms for classical linear NTT. [Extension checks and raw data](EXTENSION_RESEARCH.md) |
| A5, complex arithmetic | The earlier bounded negative result is retained as the decision for the tested implementation. Resume only with a specific numerical-stability hypothesis. [Archived result](COMPLEX_GEOMETRIC_A5.md) |

The current checks establish exactness for the supported sizes. Low-depth synchronized word construction, practical base-field descent for larger extension degrees, and the source's prime-grid and deformation machinery remain open. Priority goes to a structurally different cost model before expanding the exhaustive cases.

Regression with Z3 after integration passed all 255 tests in 50.68 s. The classical benchmark smoke produced 35 rows. Reproduction commands and raw samples are in each track report.

### A3 — characteristic-zero deformation checkpoint

The separate characteristic-zero path in `packing.tex` is now checked for p=3 over Q and width-two binomial blocks with one to three axes and jet length one to three. Exact rational endpoint scaling, lifting, Walsh evaluation, pointwise jet products, inverse evaluation and polynomial recovery agree with independent dense binomial multiplication; 104 full bilinear basis pairs plus 9 cyclic basis pairs, seeded rational inputs and rejected invalid cases. The eight focused tests and all 263 tests at 71348d5 passed on the research environment with Z3. An independent review also verified 45 seeded binomial products and 23 cyclic products with a separate dense oracle. No performance measurement is claimed for the width-two checkpoint. [Source mapping, reproduction and limits](RATIONAL_DEFORMATION_A3.md). The prime-five follow-up appears below.

### A3 — prime-five axis and width-four quotient product [verified and measured]

The p=5 specialization of `poly:lem:descent-prime` uses Q(i), g=2 and λ=−15−20i. The width-four case of `poly:lem:descent-deform` agrees with direct quotient multiplication on all 224 bilinear jet basis pairs for r=1,2,3 and seeded dense inputs. The rational cyclic-five wrapper agrees on all 25 cyclic basis pairs and seeded inputs. The exactness hypothesis passed. The precomputed deformation took about seven times as long as direct schoolbook for the paper-derived λ, with more Gaussian multiplications, larger observed coefficient bit lengths and higher traced allocation peaks. The λ=1 control also lost. [Hypotheses, limits and commands](PRIME5_DEFORMATION_A3.md) · [Raw data](../results/prime5-deformation.json)

Keep this implementation as a correctness example. Resume characteristic-zero performance work when a concrete change eliminates endpoint stages, bounds coefficient growth or changes the jet-product cost model. Arbitrary prime-axis inverse words, prime-grid selection and the saving recursion remain open. The complex128 result remains closed pending a new stability hypothesis. [Unified construction map and runnable checks](CONSTRUCTION_MAP.md)

### Shear-layer reduction checkpoint

Added an explicit fixed-field word for U^(tensor j) from three classical Walsh transforms and four tensor diagonals, with independent subset zeta/Moebius oracles. 11 focused local tests passed. This gives a concrete conditional application of a future saving Walsh backend to subset transforms, but the present backend uses six times the direct butterfly's addition count plus diagonal updates. No speed claim; full uniform-field lemma and synchronized saving circuits remain open. [Derivation, tests and boundaries](SHEAR_WORD.md).
