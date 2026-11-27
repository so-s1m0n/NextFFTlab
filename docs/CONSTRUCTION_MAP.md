# Construction and evidence map

This map follows `openai/math@3344da59991ed94f9ba711217b29c1d760badfa6`. A bounded check compares an executable component with an independent oracle. A measurement applies to the implementation, arithmetic and inputs recorded in its data. The paper's binary linear gates, counted operations, logical workspace and elapsed time are separate. [Pinned manuscript][paper]

| Source and construction | Implementation | Verification | Evidence and scope | Open scope |
|---|---|---|---|---|
| [`thm:main`][intro] and [Lean comparator statements][lean] | The project records theorem statements and arithmetic hypotheses. | Main, Fourier and batched Fourier theorem correspondence. | Source inspection. [Lean correspondence](ROADMAP.md#lean-source-correspondence) | Local Lean compilation, transitive axioms and full proof validation. |
| [`lem:count-predict`][count] | [Integer-count oracle](../nextfft_lab/predictor.py) and [query-power polynomial](../nextfft_lab/query_polynomial.py). | [Window](../tests/test_predictor.py) and [polynomial](../tests/test_query_polynomial.py) tests. | Exact on the tested queries and shifts, including all pairs in the three-bit toy case. [Data](../results/gate1-components.json) | Predictor execution in a saving recursive template. |
| [`lem:matrix-root`][matrix] | [Explicit pencil](../nextfft_lab/matrix_pencil.py) and [implicit pencil](../nextfft_lab/implicit_pencil.py). The implicit layout is a local implementation experiment. | [Pencil/repair](../tests/test_binary_repair.py) and [implicit versus explicit](../tests/test_implicit_pencil.py) tests. | Small exact matrix-power checks and a separate one-shift comparison. [Data](../results/gate2-pencil.json) · [Implicit experiment](OPTIMIZATION.md) | Theorem-scale batched workspace and routing. |
| [`lem:hermite-repair` and `thm:repair`][hermite] | [Frequency repair](../nextfft_lab/spectral_repair.py) and [binary assembly](../nextfft_lab/binary_repair.py). | [Exact basis and exception tests](../tests/test_binary_repair.py). | Verified with nonzero exceptions in a toy window. [Data](../results/gate2-pencil.json) | Nonzero-exception repair inside the complete shared-routing construction. |
| [`thm:kernel`, `eq:kernel-routing-block` and `eq:kernel-template-saving`][kernel], [`prop:binary-template`][binary] | [Binary kernels](../nextfft_lab/binary_kernel.py), [shared routing](../nextfft_lab/binary_routing.py), [fixed template](../nextfft_lab/binary_template.py), [compact experiment](../nextfft_lab/compact_template.py). | [Kernel](../tests/test_binary_kernel.py), [routing](../tests/test_binary_routing.py), [template](../tests/test_binary_template.py) and [compact template](../tests/test_compact_template.py) tests. | The zero-exception template matched classical Walsh on the tested independent rows. Sparse routing and a smaller pencil improved the prototype. Classical Walsh remained faster in the matched run. [Data](../results/gate3-kernel.json) · [Ablations](OPTIMIZATION.md) | Strict axis-call saving, recursive construction and its stability claims. |
| [`up:newton-lemma` and `up:newton`][newton] | [Newton and Toeplitz plans](../nextfft_lab/geometric.py), using classical padded radix-2 NTT. | [Dense character basis, inverse and Toeplitz tests](../tests/test_geometric.py). | Exact evaluation and interpolation on the supported geometric nodes. [Data](../results/geometric-baseline.json) · [Derivation](GENERAL_LENGTH_RESEARCH.md#g1--executable-geometric-newton-factorization) | A saving transform backend and synchronized execution across many axes. |
| [`up:toeplitz`][toeplitz] | [Occupied Toeplitz, triangular and Newton words](../nextfft_lab/occupied.py). | [Independent block basis and dirty-workspace checks](../tests/test_occupied.py). | The word restores occupied auxiliary registers. Setup and actual backend calls remain part of the cost. [Data](../results/geometric-extensions.json) | Low-depth execution with reduced auxiliary transform cost. |
| [`up:fibers`][fibers] | [Serial borrowing on occupied tensors](../nextfft_lab/fiber_schedule.py). | [Dense tensor oracle and occupied-neighbor restoration](../tests/test_fiber_schedule.py). | Borrowing removes dedicated payload slots with the same backend transform count as dedicated scratch. It took longer in the matched Python measurements. [Slot counts and scope](OCCUPIED_FIBERS_A2.md) · [Data](../results/fiber-schedule-a2.json) | Full grouping and depth synchronization for many axes. |
| [`up:newton-lemma`][newton], [Bostan–Schost, Props. 3–5][bostan] | [Chirp and divided differences](../nextfft_lab/geometric_baselines.py), [Bostan–Schost comparator](../nextfft_lab/geometric_interpolation.py). The non-root grid product is a lab application. | [Geometric basis and dense tests](../tests/test_geometric_baselines.py), [interpolation and independent product checks](../tests/test_geometric_interpolation.py). | Matched non-root comparisons. The evaluate–multiply–interpolate path lost to ordinary convolution at the measured sizes. [Method](GEOMETRIC_INTERPOLATION_A1.md) · [Data](../results/geometric-interpolation-a1.json) | General multipoint interpolation and a matched application advantage. |
| [`up:grid`, `up:fourier` and `up:packing`][grids] | [Classical Good factorization](../nextfft_lab/geometric_packing.py), [quadratic two-row coordinates](../nextfft_lab/extension_coordinates.py), [multi-axis extension grids](../nextfft_lab/extension_research.py). | [Dense cyclic DFT oracle](../tests/test_geometric_packing.py), [auxiliary root and basis checks](../tests/test_extension_coordinates.py), [multi-axis and odd-batch checks](../tests/test_extension_research.py). | Verified supported auxiliary root orders and independent input coordinates under actual extension arithmetic. [Packing data](../results/geometric-packing.json) · [Extension methods](EXTENSION_RESEARCH.md) · [Extension data](../results/extension-research-a3-a4.json) | General auxiliary selection, efficient higher-degree descent and the full general-length Fourier theorem. |
| [`poly:eq:mixed-radix-packing`, part of `thm:conv`][packing] | [Base-field packing](../nextfft_lab/geometric_packing.py) and [quartic half-box packing](../nextfft_lab/extension_research.py). | [Basis-product carry checks](../tests/test_geometric_packing.py), [dense bilinear and operand-recovery oracles](../tests/test_extension_research.py). | Exact convolution in the tested layouts, including live extension coordinates and mixed-radix carries. [Packing data](../results/geometric-packing.json) · [Extension data](../results/extension-research-a3-a4.json) | General prime-grid choices, efficient jet arithmetic and the full formal convolution bound. |
| [`poly:lem:descent-prime`][prime], explicit `p=3` | [`cyclic3_product`](../nextfft_lab/rational_deformation.py) over the rationals. | [Cyclic product basis and dense rational oracle](../tests/test_rational_deformation.py). | The scalar and binomial split uses the paper's relation `Y² = −3`. [Derivation and checks](RATIONAL_DEFORMATION_A3.md) | General-prime restored-word cost. |
| [`poly:lem:descent-deform`][deform], width two | [`deformed_product`](../nextfft_lab/rational_deformation.py), using exact rational endpoint units, Walsh evaluation, jet multiplication and recovery. | [Dense binomial multiplication](../tests/test_rational_deformation.py), including full bilinear basis pairs for the listed configurations. | Verified one to three axes with short jets. [Derivation and checks](RATIONAL_DEFORMATION_A3.md) | General widths, synchronized execution and cost with coefficient growth. |
| [`poly:lem:descent-prime`][prime], `p=5` | [Exact Gaussian resolvents and DFT4 coordinate maps](../nextfft_lab/prime5_deformation.py). | [Cyclotomic eigenvectors and powers, five coordinate basis vectors, direct cyclic products](../tests/test_prime5_deformation.py). | Exact p=5 specialization with rational cyclic output. [Derivation and scope](PRIME5_DEFORMATION_A3.md) | Restored workspace word and arbitrary prime axes. |
| [`poly:lem:descent-deform`][deform], width four | [One-axis width-four deformation over Q(i)](../nextfft_lab/prime5_deformation.py). | [224 full bilinear jet basis pairs and seeded dense bivariate reduction](../tests/test_prime5_deformation.py). | Slower than direct schoolbook at r=1,2,3. [Method and scope](PRIME5_DEFORMATION_A3.md) · [Data](../results/prime5-deformation.json) | Multi-axis width-four deformation, efficient jet operations and a saving convolution. |
| [`up:newton-lemma`][newton], complex128 experiment | [Complex Newton plan](../nextfft_lab/complex_geometric.py) and [FFT/CZT comparisons](../nextfft_lab/bench_complex_geometric.py). | [Independent high-precision evaluator, grids and basis](../tests/test_complex_geometric.py). | The tested unrebalanced factors show severe forward error on some grids. [Numerical study](COMPLEX_GEOMETRIC_A5.md) · [Data](../results/complex-geometric-a5.json) | A stability hypothesis with matched accuracy checks. |
| [Alman–Rao][alman] and [Sussman's fixed circuits][sussman], separate WHT research | [Circuit synthesis and verification](../nextfft_lab/linear_circuit.py), [exact record-search driver](../nextfft_lab/bench_record_search.py). | [Circuit basis](../tests/test_linear_circuit.py) and [rational, finite-field and Z3 checks](../tests/test_record_search.py). | Known-circuit reproduction and bounded negative search results. [Circuit data](../results/circuit-search.json) · [Search bounds and evidence](RECORD_SEARCH.md) | An improvement to a published comparison under the same cost model. |

## Minimal checks

From the repository root with Python 3.10 or newer, install the test and research extras and choose the focused checks. [Dependencies and full regression commands](REPRODUCIBILITY.md)

```sh
python -m pip install -e '.[dev,research]'
python -m pytest -q tests/test_geometric.py tests/test_occupied.py tests/test_fiber_schedule.py
python -m pytest -q tests/test_geometric_interpolation.py tests/test_geometric_packing.py tests/test_extension_research.py
python -m pytest -q tests/test_rational_deformation.py tests/test_prime5_deformation.py tests/test_complex_geometric.py
```

This exact evaluation and interpolation example uses a geometric grid with ratio 3. The dense value calculation supplies an independent check.

```python
from nextfft_lab.exact import P
from nextfft_lab.geometric import NewtonPlan

coefficients = [2, 5, 7]
plan = NewtonPlan.build(3, 3)
expected = [sum(c * pow(3, i * j, P) for j, c in enumerate(coefficients)) % P for i in range(3)]
assert plan.apply(coefficients) == expected
assert plan.apply(expected, inverse=True) == coefficients
```

The following products have direct monomial checks. In the jet example, zY³ times Y reduces to λz. In the cyclic example, X⁴ times X reduces to one.

```python
from nextfft_lab.prime5_deformation import Gaussian, WidthFourPlan, cyclic5_product, prime5_constants

lam, _ = prime5_constants()
plan = WidthFourPlan(lam, 2)
assert plan.multiply([[0, 0], [0, 0], [0, 0], [0, 1]],
                     [[0, 0], [1, 0], [0, 0], [0, 0]]) == [
    [Gaussian(), lam], [Gaussian(), Gaussian()], [Gaussian(), Gaussian()], [Gaussian(), Gaussian()]
]
assert cyclic5_product([0, 0, 0, 0, 1], [0, 1, 0, 0, 0]) == [1, 0, 0, 0, 0]
```

Use a separate location for fresh benchmark output. [Geometric benchmark commands and saved raw samples](GENERAL_LENGTH_RESEARCH.md) · [Source and license notes](REPRODUCIBILITY.md#pinned-circuit-search-and-source-licenses)

[paper]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/paper.pdf
[intro]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/intro.tex
[lean]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/ComparatorChallenges/ExactFourier.lean
[count]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/repair.tex#L81-L124
[matrix]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/repair.tex#L128-L176
[hermite]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/repair.tex#L188-L269
[kernel]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/kernel.tex
[binary]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/binary.tex#L12
[newton]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/layers.tex#L106-L149
[toeplitz]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/layers.tex#L153-L219
[fibers]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/layers.tex#L222-L253
[grids]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/grids.tex#L11-L113
[packing]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/packing.tex#L37-L65
[prime]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/packing.tex#L214-L274
[deform]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/packing.tex#L293-L380
[bostan]: https://cs.uwaterloo.ca/~eschost/publications/BostanSchost.pdf#page=27
[alman]: https://arxiv.org/abs/2211.06459
[sussman]: https://github.com/jacobalansussman/wht-fewer-operations/tree/bbb7f830d8c5612465a9922ace566750ce6d09d2
