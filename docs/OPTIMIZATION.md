# Exact windows and sparse binary templates

Experiments use F₉₉₈₂₄₄₃₅₃. The source anchors are `lem:count-predict`, `lem:matrix-root`, `lem:hermite-repair` and `eq:kernel-routing-block`. Exact-window search, implicit tensor strides and rectangle endpoint reuse are lab experiments. [Pinned proof source](https://github.com/openai/math/tree/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build).

## Exact symmetric windows

With balanced binary shifts, C(m,k) shifts have Hamming count k at every frequency. The outside count for [u,m−u] is B(u)=2Σₖ₌₀ᵘ⁻¹ C(m,k). The repair budget requires 2m³B(u)≤2ᵐ. The implementation increases u until the next symmetric window fails, so the returned interval is the narrowest such interval.

| m=15 interval | Outside shifts of 32,768 | Meets the size bound |
|---|---:|---|
| [0,15] | 0 | Yes |
| [1,14] | 2 | Yes |
| [2,13] | 32 | No |
| [3,12] | 242 | No |

The allowed integer count is 4. The minimum predictor degree for [1,14] is 13. To see this, average a multilinear predictor over permutations. This preserves degree and the required values because 15! is invertible in the field. Each averaged degree-d monomial is a polynomial in Hamming weight of degree at most d. The thirteenth forward difference of the alternating sequence on 14 consecutive integers is a nonzero signed power of 2.

Write qᵢ=(−1)ᵏⁱ and z=∏qᵢ. For odd m at zero shift,

```text
P(q) = z − (∏(qᵢ+1) + ∏(qᵢ−1))/2.
```

The correction vanishes when both signs occur. At the two endpoints it gives the same corrections ±2^(m−1) as the source interpolation. Odd symmetry and cancellation of the top-degree term leave all odd degrees up to m−2. For shift β, substitute (−1)^βⁱqᵢ and multiply by (−1)^Σβ. Tests cover all 16 Hamming counts for m=15 and the entire five-bit cube.

At m=15, the 16,383 expanded terms at b=16 give log₂R=15+4·16,383=65,547. Here R=2ᵐbʰ is the number of independent input rows per label with h product terms. The three affine products give 4,096 lanes per shift and R=2²⁷ per label, with s=8,192 exceptional rows per frequency. The original window [−6,21] has zero exceptions and a one-term degree-15 predictor. The narrower window trades degree and interpolation width for extra terms and repair.

With M=2^(Af) elements per row, A=2(m+D−1)≥30 at m=15. Even the minimum A means 4 GiB per packed 32-bit row at f=1, or at least 2⁵⁹ input bytes per label for the three-product bound. This exceeds the 1 GiB experiment cap before workspace or outputs. The exception bound alone leaves the call-saving criterion open.

A reduced shift set tightens this bound for the endpoint predictor. A frequency k is exceptional for β=k or its bitwise complement. Choose 6,750 distinct masks with top bit zero, one at most per complement pair. Then at most one selected shift is bad anywhere, so the worst fraction is exactly 1/6,750. Any nonempty uniform shift set must have at least one exception at some k, which makes 6,750 shifts minimal for this endpoint pattern under the same fraction cap. The test checks all 32,768 masks. This lowers R from 134,217,728 to 27,648,000 and s from 8,192 to 4,096. It preserves independent input lanes. It still requires 4 GiB per dense row at the minimum axis count. These are exact combinatorial counts, with no tensor allocation.

## Parameter costs

V=q^L is the label count and e is the coordinate rank of the coefficient algebra. The expanded batch is W=RVe, with at least 4WM packed input bytes.

| Parameter | Model and evidence |
|---|---|
| Query count m | Balanced shifts require 2ᵐ blocks. An ordinary query touches one distinguished and D−1 auxiliary pairs per column. The exact-window sweep spans m=3…128. |
| Axis count A | A+2 quadruples M at f=1. At m=3, one query took 0.018, 0.132, 0.914 and 4.262 ms at A=6,8,10,12 respectively, with auxiliary axes increasing as well. At fixed A=10, changing (m,D) from (3,3) to (5,1) reduced touched pairs from three to one and the median from 0.914 to 0.302 ms. |
| Degree and radix | A power of two b must accommodate every affine product in the chosen representation. The zero-exception m=3 predictor has one degree-three monomial, so b falls from 16 to 4. The degree-13 m=15 formula uses three products of length 15 and still takes b=16. |
| Pencil dimension | bʰ lanes per shift. An explicit root stores h transitions per lane with affine coefficients. The implicit implementation stores hb factors and b phases, with two live lane vectors. It visits hb transitions per lane over a complete power. |
| Width W | The compact zero-exception template supports 128 independent rows across four labels as its minimum. The ablation repeats whole shift sets to keep W=512. All input lanes are independent. |
| Routing | Charged rectangles evaluate both kernels only for active source columns. Free rectangles reuse one source auxiliary transform across destination edges and delay each destination transform until after summing. Sparse metadata and fused permutation indexing reduce row handling. |
| Hermite repair | For s>0, four predictor applications and 4s row conversions cost 4sA axis calls per label. Dense checks/lifts take 4sRM MACs, and table solves/lifts at most 2s²M. A synthetic 24×8 experiment took 1.278 ms at s=1 and 1.510 ms at s=8 including four synthetic predictor calls. One such call took 0.146–0.243 ms across the positive-check cases. |
| Extension rank e | Packed coefficients take 4e bytes. General schoolbook negacyclic products use e² base multiplications, and monomial roots can use signed permutations. Rank 1 to 32 measured 0.85–75.65 μs. Coordinate expansion multiplies both batch width and axis calls by e and adds coefficient work. |

The extension sweep uses F[Y]/(Yᵉ+1), which can split over the base field. For R=2²⁷, the proof's universal cyclotomic rank is 2²⁶. If the same nodes are retained over the chosen finite field, primitive 2²⁷-th roots first occur at extension degree 16 because v₂(P−1)=23 and the order modulo 2²⁷ is 2^(27−23). Hermite repair also permits arbitrary distinct nodes. R<P and 16 divides P−1, so the bounded formula can use base-field nodes and a base-field pencil root. Batch and tensor sizes remain prohibitive.

## Matched measurements

The m=15 scalar pencil powers agree with the factored polynomial on all 4,096 inputs of one shift at each tested tuple. The implicit evaluator pre-evaluates each affine factor once per query tuple and generates the phase-weighted cyclic transitions when needed. Both paths use the same field, tuple and input. Peak below is per-call Python allocation.

| Method | Setup | Setup peak | Application | Application peak |
|---|---:|---:|---:|---:|
| Materialized transitions | 16.05 ms | 3,929,512 B | 213.77 ms | 362,128 B |
| Implicit strides | 0.0568 ms | 11,336 B | 46.36 ms | 330,576 B |

This scalar measurement leaves the all-shifts batch, label schedule and full addresswise operator unimplemented at m=15.

The next table uses the same 512 independent length-256 inputs and three timed runs per implementation. The working-set peak includes the interpreter, inputs and reference output.

| Path | Stages | Axis calls | Cross-row MACs | Median | Process peak |
|---|---:|---:|---:|---:|---:|
| Published template | 16 | 163,840 | 3,276,800 | 7.718 s | 49.9 MiB |
| Sparse routing only | 16 | 12,288 | 3,276,800 | 0.829 s | 44.2 MiB |
| Sparse routing and degree-sized pencil | 4 | 12,288 | 1,703,936 | 0.679 s | 48.8 MiB |
| Classical Walsh | — | 4,096 | — | 0.0772 s | 39.6 MiB |

One pair kernel is two axis-call equivalents. The compact path executes 6,144 such kernels with 2,752,512 additions/subtractions and 3,145,728 multiplications under the four-point block count. Including cross-row MACs, 786,432 charged gathers, 393,216 free output accumulations and the phase maps gives about 5.64M additions/subtractions and 6.42M multiplies. The classical transform core uses 1,048,576 additions/subtractions. Modular reduction, coefficient setup and address indexing contribute to runtime separately. Sparse routing reduces calls. The shorter root reduces repeated row mixes at fixed batch width. Small process-peak differences include allocator effects.

## Reproduction and decision

```sh
python -m nextfft_lab.bench_optimization --variant components --repeats 20
python -m nextfft_lab.bench_optimization --variant baseline --repeats 3
python -m nextfft_lab.bench_optimization --variant routing-only --repeats 3
python -m nextfft_lab.bench_optimization --variant compact --repeats 3
python -m nextfft_lab.bench_optimization --variant classical --repeats 3
```

The baseline rerun passed 121 tests. The updated suite passed 143 tests in 22.66 s and the classical CPU smoke command exited successfully. The seed is 20261126 for each benchmark invocation.

The host was Windows 11 x86-64, Ryzen 7 5800X, CPython 3.13.3, one algorithm thread. Each template variant runs in a separate process. Windows peaks use `GetProcessMemoryInfo.PeakWorkingSetSize`. Linux and macOS use `getrusage(RUSAGE_SELF).ru_maxrss` converted to bytes. Component timings and `tracemalloc` peaks come from separate calls. [Components](../results/optimization-components.json) · [Published template](../results/optimization-baseline.json) · [Sparse routing](../results/optimization-routing-only.json) · [Compact](../results/optimization-compact.json) · [Classical](../results/optimization-classical.json).

The compact template uses 24 axis calls per row at A=8, so it cannot satisfy σ/W<A^θ for any 1/2<θ≤1. Classical Walsh wins the same-workload comparison. A hybrid dispatcher would select classical for every currently measured case, so no hybrid backend was added. Stop scaling the explicit all-shifts layout. Continue a candidate when it reduces the all-shifts or dense-address requirement under the resource cap and gives a checkable strict call saving. Then verify independent inputs, shared routing and full repair before recursive packing or compiled evaluation. Lean compilation and general-length Fourier reproduction remain open.
