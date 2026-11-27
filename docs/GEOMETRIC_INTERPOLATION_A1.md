# A1 — Bostan–Schost comparison

This bounded experiment compares interpolation on the distinct nodes `1, q, …, q^(n−1)` over `F_998244353`. The existing chirp plan supplies evaluation. The interpolation comparator follows the Newton interpolation of Proposition 3 and the Newton-to-monomial conversion of Proposition 4, combined in Proposition 5. [Bostan–Schost, 2005](https://cs.uwaterloo.ca/~eschost/publications/BostanSchost.pdf#page=27)

Let `H_i = product(1-q^j, j=1..i)` and `t_i = q^(i(i−1)/2)`. Scale the samples by `(−1)^i/H_i`, then multiply the resulting series by the kernel `t_i/H_i` to order n. The result contains Newton coefficients scaled by `t_i`. Scale these by `H_i/t_i` and apply the upper triangular Toeplitz matrix whose diagonal at offset d is `(−1)^d t_d/H_d`. Finally scale by `1/H_i` to obtain monomial coefficients. This upper factor follows from the q-binomial coefficients of the Newton basis products.

The plan builds the field coefficients with linear recurrences and two field inversions. It caches two padded NTT spectra and runs four classical NTTs per application. The paper-derived Newton plan already uses two convolutions per inverse application, with a quadratic reciprocal-series setup in this repository. The comparison therefore distinguishes the cost of preparing the kernels from their nearly identical application costs. The same `ToeplitzPlan` supplies both backends. This study evaluates a known fast method with a matched backend.

Independent tests interpolate every sample-space basis vector for n in {1,7,8,16,17}, including non-root grids and exact-order roots. They compare coefficients with classical divided differences and re-evaluate at the nodes using the dense character formula. The polynomial application evaluates each padded operand on a shared non-root grid, multiplies samples, and recovers monomial coefficients by interpolation. Its outputs agree with both schoolbook convolution and the repository's classical linear NTT product. Its reused setup still requires two chirp evaluations and the two-convolution interpolation, whereas ordinary linear NTT convolution needs three NTTs in total. Applicability is restricted to square distinct geometric grids with nonzero q and lengths of at most 512. The experiment uses finite-field residues and leaves out erasure patterns on arbitrary node subsets.

Run `python -m pytest -q tests/test_geometric_interpolation.py` and `python -m nextfft_lab.bench_geometric_interpolation`. The latter emits seed, environment, raw samples and traced Python allocation peaks. It measures separate setup, plan construction plus one interpolation, and reused batches of width 1, 4 and 16. Each comparison uses the same inputs. The application compares reused and cold geometric setup with classical linear NTT convolution. [Raw samples](../results/geometric-interpolation-a1.json)

## Measurements

Seven warm samples per method used Windows 11 x86-64, Ryzen 7 5800X, CPython 3.13.3, seed 20261127 and one algorithm thread. The table reports microseconds, with both columns ordered as paper Newton / Bostan–Schost.

| Grid length | Setup | Setup plus one | One with reused setup | Reused batch of 4 | Reused batch of 16 |
|---:|---:|---:|---:|---:|---:|
| 8 | 62.5 / 47.6 | 148.1 / 132.2 | 84.1 / 81.8 | 331.0 / 323.4 | 1268.2 / 1186.4 |
| 32 | 252.2 / 161.0 | 1039.7 / 814.4 | 308.0 / 310.7 | 1269.4 / 1295.6 | 4616.8 / 4638.6 |
| 128 | 1556.3 / 887.1 | 2948.7 / 2089.9 | 1366.0 / 1363.1 | 5370.1 / 5358.4 | 20979.3 / 21103.3 |
| 512 | 26283.5 / 3988.6 | 23731.3 / 18511.4 | 7489.0 / 11995.5 | 47742.0 / 46006.7 | 174019.9 / 181622.5 |

These medians are from separate timing passes. Short runs and machine load produced variability, especially at length 512. Setup was consistently lower in the comparator, while warm application had no consistent winner. At length 128 the independent quadratic method took 7491.0 µs for one input. The largest recorded traced Python allocation peak for the Bostan–Schost warm cases was 527,564 bytes with length 512 and batch width 16. This is a Python allocation measure rather than process working set.

At length 128 per operand, the polynomial application took 7.787 ms with reused setup and 16.056 ms with cold setup. Classical linear NTT convolution took 1.714 ms. All tested products agreed exactly, and the non-root grid path was slower at all three measured sizes. The experiment was bounded to grids of length 512 and avoids external dependencies. [Raw samples](../results/geometric-interpolation-a1.json)
