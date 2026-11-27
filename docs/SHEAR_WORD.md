# Explicit tensor shear word: bounded source check

Source: [layers.tex, lem:shear and synchronization discussion](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/layers.tex#L18-L105).

The paper reduces tensor shear layers to prime Fourier kernels, with uniform field bounds. Here an elementary explicit two-coordinate word verifies the reduction for the repository's fixed field F_998244353. Let H = [[1,1],[1,-1]], U = [[1,1],[0,1]], and D(a,b) = diag(a,b). Direct multiplication gives

    H D(2,1) H D(3,-1) H = [[8,10],[0,6]],
    U = D(1/8,5/24) H D(2,1) H D(3,-1) H D(1,4/5).

The identity uses only inverses of 2, 3 and 5, so it holds in fields with other characteristics, including characteristic zero. The code implements the fixed finite field only. Tensoring j copies gives three full Walsh transforms H^(tensor j) separated by four tensor diagonals. Each diagonal entry depends on the population count of its index. Inversion uses conjugation by D(1,-1)^(tensor j).

Independent oracle: the upper subset zeta map sends x to y_i = sum_{k containing i} x_k, and inverse uses sign (-1)^(|k|-|i|). Check every basis at N=1,2,4,8,16,32,64 (127 columns per direction), seeded dense inputs at N=128,256,1024, operation counts and invalid sizes. The focused suite passed 11 tests in 0.22 s using an isolated local copy of the new module and the existing field and classical Walsh routine. Full repository regression remains to CI.

    python -m pytest -q tests/test_shear_word.py

## Cost and application boundary

At N=2^j, the direct classical subset butterfly uses Nj/2 additions. Three classical Walsh calls use 3Nj additions/subtractions, plus four diagonal entry updates per input (4N, including unit coefficients). The inverse adds two conjugating diagonal passes. These are structural operation counts, not wall-clock timings. No new performance measurements were made. The classical word is not a speedup. If the paper's gate-saving Walsh backend existed as a usable implementation, a fixed number of such calls and O(N) diagonal operations would transfer its asymptotic exponent to the subset zeta transform, which also appears in combinatorial subset DP and inclusion-exclusion. This is a conditional application, not an independently demonstrated fast implementation or a novelty claim.

The characteristic 2, 3 and 5 cases, uniform field descent, the paper's fast kernel, general disjoint word synchronization and complete proof verification are outside this check. Do not substitute this fixed-field identity for the full lemma. A further priority is auditing the pinned Lean theorem and axioms, and separating the bounded verification checkpoint from unresolved fast recursion. Do not expand this identity to larger test sizes merely to accumulate tests.
