# Gate for a saving recursive Fourier implementation

## What the paper establishes

For J independent Fourier blocks of common order N≥2, the paper bounds the exact acyclic binary linear gate count between cJN√log₂N and Cε JN(1+log₂N)^(1/2+ε) for every ε>0. A gate forms au+bv with arbitrary field scalars. N must be invertible in the common field and the field must contain a primitive root of each group exponent. The upper bound at ε=0 remains open. Over odd characteristic, the prime tensor transform for ℓ=2 is Walsh–Hadamard on (Z/2)^k. The cyclic transform of length 2^k has different root requirements. [Main theorem and field hypotheses][intro]

The prime tensor proof builds a fixed batch program for any θ>1/2 (take θ≤1 to target a strict improvement over the classical exponent). Fix ℓ, choose 0<η<min(1,θ−1/2), then choose L with (ℓ−1)/(L−⌊L/ℓ⌋)<η. Choose large m≡1 mod ℓ and a power of two q within a factor of two of m^(1/(L−⌊L/ℓ⌋)). With Gram rank D the row has A=2(m+D−1) axes. The routing, predictor and repair estimates give normalized calls o(A^θ). Cyclotomic coordinate expansion multiplies the call count and independent input width by the same extension rank. This supplies a finite template in the exact model. The proof's asymptotic choices do not provide practical sizes or crossover times. [Tensor template and estimates][kernel]

## What a recursive implementation must show

A candidate must give fixed A, independent row count W and axis-call count σ such that its exact template works at all f≥1 and σ/W<A^θ. One call applies the ℓ^f transform along a single axis of one ℓ^(Af)-entry work row, over all its fibers. The count includes all required spectral conversions. Outside these calls, row mixing, signed reindexing and other fixed template passes must have bounded work per entry. Common spectator coordinates multiply all volumes equally. [Template layout and saving equation][saving] · [Binary column operations][binary]

The recursion uses a padding parameter r chosen so b=(σ/W)(1+W/ℓ^r)<A^θ. For k digits, set f=⌊(k−r)/A⌋ when positive and s=k−Af. There are ℓ^s independent rows, and the padded-to-live row factor is at most 1+W/ℓ^r because r≤s<r+A. The last batch uses dummy zero rows whose outputs are discarded. The bounded last s digit transforms can run directly. Work normalized by ℓ^k obeys T(k)≤C+bT(f), since b/A^θ<1. Small k uses direct base cases. Padding increases the call multiplier, so it cannot rescue a template with σ/W≥A^θ. [Recurrence and addressing][saving]

The real-arithmetic stability result in the binary proposition assumes that saving template and a normalized even-k recursion with gate-local relative errors. It bounds the Euclidean operator error by Cu(1+k)^B for u≤c(1+k)^−B. The lab's finite-field equalities and the separate complex Newton measurements address different questions. [Normalized binary proposition][binary] · [Archived complex experiment](COMPLEX_GEOMETRIC_A5.md)

## Current evidence and missing links

| Checkpoint | What was established | What the recursion still needs |
|---|---|---|
| Fixed binary layout | m=3, L=q=2, D=2, A=8, f=1. Exact on the measured batch of 512 independent length-256 rows. The paper's window [−4,7] includes all realizable counts, so the batch has zero exceptions. | A valid all-f template with strict call saving. End-to-end routing with nonzero exceptions and all repair conversions charged. |
| Compact fixed layout | Sparse routing and smaller pencil reduced the matched prototype from 7.718 s to 0.679 s. Classical Walsh took 0.0772 s. The compact program has σ=12,288 at W=512, so σ/W=24 versus A=8. | For 1/2<θ≤1, 24>8^θ before padding. Wall-clock improvement over the old prototype and passing the repair fraction do not enter this inequality. |
| Nonzero repair components | Exact Hermite checks and lifts on bounded toy cases. With s errors in at most R/(2m³) row slots, the paper charges up to ℓ+2 pencil applications and 2s full-row conversions in each direction. | Joint routing, predictor and repair with independent rows in a candidate that still saves after the conversions, cross-row moves and coefficient descent. |
| m=15 narrow window | Lab window [1,14] has two endpoint exceptions per frequency over all 2^15 shifts. The source's own m=15 interval [−6,21] has none. Keeping only 6,750 shifts is minimal for the endpoint predictor, disjoint independent row allocation and fixed worst-case fraction, with every query tuple included. | This minimum does not bound other predictors or encodings. The three-product tensor root uses 4,096 lanes per shift and 27,648,000 rows per label. Even one explicit packed binary row at f=1 takes at least 4 GiB from A≥30 before labels, workspace or outputs. |
| First source window with exceptions | For odd binary m, the paper's window first excludes realizable counts at m=63, giving [1,62]. The source layout has A≥126. A packed four-byte row at f=1 would take at least 2^128 bytes. | These bytes describe the explicit layout under the stated representation. They do not rule out a different indexing, batching or circuit structure. |

[Fixed-template timings and raw samples](OPTIMIZATION.md) · [6,750-shift assumptions and constraints](CIRCUIT_RESEARCH.md) · [Pinned predictor and Hermite repair][repair]

The gate remains open. Revisit the template only with a concrete structural change that lowers axis, address or batch cost and a plausible strict saving after padding and repair. First require a symbolic resource bound under the 1 GiB experiment limit, an exact independent-input oracle and call accounting, then verify the recursive scheduler. The shear, occupied-fiber and packing experiments provide components for later stages. Their bounded identities leave this gate unchanged. [Construction and evidence map](CONSTRUCTION_MAP.md)

[intro]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/intro.tex#L19-L47
[kernel]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/kernel.tex#L231-L295
[saving]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/kernel.tex#L294-L335
[binary]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/binary.tex#L12-L68
[repair]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/repair.tex
