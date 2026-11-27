# A3 — Prime five and characteristic-zero quotient multiplication

## Source and acceptance criteria

The first hypothesis was that the prime-axis split in the paper can be instantiated for p=5 with exact arithmetic in Q(i), and that a single width-four deformation recovers nonconstant jets. Acceptance required all five forward coordinate basis images to agree with independent cyclotomic reduction, inversion on that basis, all bilinear basis pairs at r=1,2,3 and seeded dense inputs to match direct multiplication. The comparator for rational cyclic inputs is direct convolution modulo X^5−1. [Pinned prime-axis lemma][prime] · [Pinned deformation lemma][deform]

The application hypothesis was that reusing a plan for multiplication of truncated power series with coefficients in Q(i)[Y]/(Y^4−λ) might amortize the deformation overhead. Direct truncated schoolbook multiplication with a single binomial reduction is the comparator. Continue performance work only if the split route matches exactly and improves warm time or uses fewer Gaussian multiplications without increasing traced allocations on the paper-derived case. The fixed scope is one width-four axis, r=1,2,3, 20 repeated batches of eight seeded pairs per case and λ=1 as an already-split control. Each hypothesis has a 30-minute, 1 GiB budget. The benchmark bounds batch/repetition counts and enforces a 1 GiB process commit limit on Windows. The exact implementation uses Python standard-library arithmetic. The implementation was written in this repository, with the pinned source cited for the identities. No upstream code was copied.

## Prime-axis coordinates

Take g=2 and ω=i. The nonzero residues in powers of g are (1,2,4,3). With Φ₅(X)=1+X+X²+X³+X⁴, the resolvents are γⱼ=Σₜ i^(−jt)X^(g^t mod 5) modulo Φ₅. The permutation X→X² has eigenvalues i^j on these vectors. Reduction of the powers of γ=γ₁ gives

- γ^j=κⱼγⱼ for j=1,2,3, with κ=(1,−1+2i,3+4i).
- γ⁴=λ=−15−20i. In fact λ=−(2+i)^3(2−i), so the Gaussian valuation at 2−i is one and λ has no fourth root in Q(i).

For input v_*+Σₜ vₜX^(g^t), write wⱼ=Σₜ i^(jt)vₜ. The CRT map returns the scalar s=v_*+w₀, the constant binomial coefficient c=v_*−w₀/4, and the three coefficients wⱼ/(4κⱼ). For the inverse, w₀=4(s−c)/5, v_*=s−w₀, and inverse DFT4 recovers the other inputs in residue order. This is the paper's existing coordinate formula specialized to p=5. The implementation derives its constants by exact polynomial reduction and computes with rational pairs. For rational cyclic multiplication it also checks that every returned imaginary part vanishes. [Implementation](../nextfft_lab/prime5_deformation.py) · [Independent oracles](../tests/test_prime5_deformation.py)

## Width-four deformation and verification

Use f(t)=1+(λ−1)t. For degree j in Y, undo the t=1 endpoint with (1+((λ−1)/λ)z)^(−j/4), take the degree-<r lift with z=t−1, then apply f(t)^(j/4) at zero. The two forward DFT4s and one inverse DFT4 act on jets of length H=2r+1. Four pointwise jet products use schoolbook arithmetic. After inverting the zero scaling, the coefficient of t^(2r) must vanish because reduction modulo Y^4−f(t) introduces at most one factor of degree one. Shift back to t=1 and apply its endpoint unit to recover the product modulo z^r. [Pinned deformation lemma][deform]

The independent tests first multiply in the ordinary bivariate polynomial ring and then reduce by the monic binomial and truncate. They check 224 bilinear jet basis pairs, 12 seeded dense jet cases across three values of λ, and 25 rational cyclic basis pairs plus eight seeded rational products. The benchmark checks a further 48 matched pairs. The earlier p=3 path was independently reviewed against the pinned source and checked with a separate dense oracle on 45 rational binomial and 23 cyclic inputs.

With Z3 installed, the complete local suite passed all 272 tests (the 263-test checkpoint plus nine new tests). Both construction-map examples ran successfully.

## Measured application and continuation decision

Same-domain CPython 3.13.3, Windows 11, one thread. Each warm product time below is the median batch time divided by eight. Setup applies only to the reusable split plan. The bit pairs are the maximum reduced numerator/denominator lengths of observed Gaussian coordinates in the warm batch. Memory is a separate tracemalloc peak over each batch including its outputs, excluding the input arrays and existing split plan. [Raw samples, CPU, seed and counters](../results/prime5-deformation.json)

| λ | r | Setup μs | Direct / split μs | Direct / split Gaussian multiplications | Direct / split coefficient bits | Direct / split traced bytes |
|---|---:|---:|---:|---:|---|---:|
| −15−20i | 1 | 228.3 | 163.8 / 1172.2 | 19 / 121 | 33/27 · 45/37 | 18,244 / 29,660 |
| −15−20i | 2 | 533.7 | 445.6 / 3108.7 | 54 / 315 | 36/31 · 75/56 | 29,072 / 46,588 |
| −15−20i | 3 | 860.2 | 854.9 / 5994.9 | 105 / 597 | 42/35 · 101/72 | 39,720 / 63,600 |
| 1 | 1 | 222.8 | 148.1 / 1083.2 | 16 / 121 | 30/30 · 38/36 | 18,112 / 27,088 |
| 1 | 2 | 521.7 | 412.0 / 2659.2 | 48 / 315 | 34/31 · 46/40 | 28,472 / 43,468 |
| 1 | 3 | 927.4 | 806.4 / 5016.5 | 96 / 597 | 38/35 · 49/44 | 38,796 / 59,480 |

Direct multiplication uses 16r(r+1)/2 Gaussian coefficient multiplications, plus 3r for a binomial reduction factor λ≠1. In the split route, the four pointwise products alone use 4H(H+1)/2. The remaining multiplications include endpoint factors, shifts and DFT scalings. Timings and arithmetic counts come from separate runs. The raw data separate addition, subtraction, negation and division and give the rational operations inside each Gaussian method, excluding Fraction normalization and scalar setup outside those methods. The full benchmark used approximately 29.9 MiB peak process working set, which includes interpreter and process allocations.

The exactness hypothesis passed. The performance hypothesis failed even with precomputation excluded from warm time. With λ=−15−20i the split method took about seven times as long. Increasing the jet length from r to 2r+1 contributes work already at the pointwise products, while endpoint scaling, Taylor shifts and larger rational coefficients add costs. The λ=1 control also lost when forced through the same split-plan schedule. It does not measure a specialized DFT that takes advantage of the block being split at the original endpoint. Treat these as bounded lab measurements. Arbitrary prime axes, synchronized restored-workspace circuits and the theorem's recursion and formal convolution bound remain open. A future experiment would need a specific structural change that removes endpoint scaling work, reduces bit growth or changes the jet multiplication cost model before revisiting performance.

## Reproduce

Run in the repository root with Python 3.10 or newer. Generate fresh samples at a new output path.

```sh
python -m pip install -e '.[dev,research]'
python -m pytest -q tests/test_rational_deformation.py tests/test_prime5_deformation.py
python -m nextfft_lab.bench_prime5_deformation --output prime5-local.json
```

[Construction map and runnable examples](CONSTRUCTION_MAP.md) · [Active research ledger](GENERAL_LENGTH_RESEARCH.md) · [Repository license](../LICENSE) · [Pinned upstream license][upstream-license]

[prime]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/packing.tex#L214-L274
[deform]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/packing.tex#L293-L380
[upstream-license]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/LICENSE
