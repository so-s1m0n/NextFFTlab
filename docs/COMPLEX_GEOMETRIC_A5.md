# A5 — complex geometric Newton evaluation

**Verified in a bounded domain and measured.** The source identity is the geometric Newton factorization in [pinned layers.tex, lem: up:newton-lemma](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/layers.tex#L106-L149). This is a separate complex128 experiment. The finite-field claims and occupied-workspace claims are unaffected.

## Hypothesis and method

For n distinct nodes q^j, the paper's factorization gives V = diag(H) T diag(c/H) T^t diag(H), where H_i = product(1 - q^k) for k from 1 to i, c_i = (-1)^i q^(i(i-1)/2), and T has subdiagonal coefficients 1/H_i. The upper operation uses a transpose, without conjugation. Reversing the factors uses the truncated reciprocal of the Toeplitz column. We tested whether these operations retain useful numerical accuracy over short complex128 grids.

The forward plan evaluates each of the two triangular Toeplitz factors by either direct convolution or a zero-padded FFT. The FFT plan caches one kernel spectrum and uses four transforms per application. Interpolation uses a quadratic reciprocal-series recurrence and direct convolution. The lab implementation accepts one row with at most 128 entries. Its backend allocates temporary arrays.

Decimal Horner evaluation with 100 decimal digits serves as an independent reference. It uses independent complex multiplication and a Taylor series for the ideal q, then rounds outputs once. A second reference treats the supplied complex128 q as exact, using Decimal conversion from its floating components. This separates input-parameter rounding from evaluation error. For interpolation, the input values are rounded samples from the reference for the rounded-q grid. The coefficient error relative to the original row therefore includes amplification of input rounding. The residual measures ||Va-y||₂/(||V||₂||a||₂+||y||₂). A small residual on a poorly conditioned grid does not imply accurate coefficients.

The comparison uses SciPy's one-worker FFT for the full-circle grid, CZT with its default grid or an explicit q, and ZoomFFT on unit-circle grids. On arcs and spirals, the step is q = radius·exp(-2πi·turns/n). The CZT parameter is w=q when the starting point is 1. [SciPy CZT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.CZT.html) · [SciPy ZoomFFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ZoomFFT.html)

## Observed negative result

All methods use the same seeded complex coefficient row per length. The grid sweep covers lengths 8, 32, 64, and 128. The largest explicit matrix has 16,384 complex128 entries, or 256 KiB before linear-algebra work buffers. The run used CPython 3.13.3 on Windows AMD64, NumPy 2.5.5, SciPy 1.18.1, seed 20261127, one FFT worker and five warm timings. The archive includes initial setup and warm samples. CPU model, peak process memory and backend thread counts outside the FFT calls were not measured.

| Grid | n | Newton direct relative error | Newton FFT relative error | Established baseline relative error |
|---|---:|---:|---:|---:|
| DFT | 64 | 5.87e-2 | 1.49 | 1.51e-16 FFT |
| DFT | 128 | 1.63e15 | 7.53e17 | 2.17e-16 FFT |
| Unit arc, 0.08 turns | 32 | 2.22e-13 | 6.18e31 | 5.59e-16 ZoomFFT |
| Spiral, 0.65 turns, step radius 1.002 | 64 | 1.91e5 | 6.93e5 | 1.05e-13 CZT |

Errors in the table are relative L2 errors against the ideal grid. The spiral's rounded-q error with CZT is 1.02e-14, so the row also shows the distinction between parameter representation and algorithmic error. At DFT length 64, the dense rounded-grid condition estimate is approximately 1, and parameter rounding accounts for 4.67e-14 relative error. The large Newton error on that grid therefore cannot be explained by conditioning of the full evaluation map or by parameter rounding alone. The intermediate Toeplitz/diagonal factors amplify numerical error. On the 32-point arc, the column's largest magnitude is about 1.13e22, which helps explain leakage from the FFT convolution into small target coefficients. At length 32 on that same arc, interpolation has coefficient error about 5.39e25 and residual about 4.86e-15. Very large condition estimates from complex128 SVD are qualitative once the smallest singular value falls below its effective resolution.

For the full-circle length 64 case, the direct and FFT-backed Newton warm medians were 17.0 and 43.7 µs, compared with 4.1 µs for the established FFT. These short local timings do not support a speedup claim. The unrebalanced complex128 factorization is **rejected as an FFT/CZT replacement for these cases**. The experiment does not establish a numerical lower bound for other factorizations, scaling, arithmetic, or implementations.

## Reproduction

```sh
python -m pytest -q tests/test_complex_geometric.py
python -m nextfft_lab.bench_complex_geometric --repeats 5 --out results/complex-geometric-a5.json
```

The focused suite passed 12 cases, including all basis columns at size eight on two small grids, the interpolation checks, reference-grid orientation, and a set of invalid inputs. [Raw measurements](../results/complex-geometric-a5.json)
