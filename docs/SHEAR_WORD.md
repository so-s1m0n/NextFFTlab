# Explicit tensor shear word: bounded source check

Source: [layers.tex, lem:shear and synchronization discussion](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/layers.tex#L18-L105).

The paper proves a uniform field bound using a bounded word in dimension four and tensoring it. This repository independently derives a two-coordinate word and checks its specialization over F_998244353. Let H = [[1,1],[1,-1]], U = [[1,1],[0,1]], and D(a,b) = diag(a,b). Direct multiplication gives

    H D(2,1) H D(3,-1) H = [[8,10],[0,6]],
    U = D(1/8,5/24) H D(2,1) H D(3,-1) H D(1,4/5).

The identity uses only inverses of 2, 3 and 5, so it holds in fields with other characteristics, including characteristic zero. The code implements the fixed finite field only. Tensoring j copies gives three full Walsh transforms H^(tensor j) separated by four tensor diagonals. Each diagonal entry depends on the population count of its index. Inversion uses conjugation by D(1,-1)^(tensor j).

Independent oracle: the upper subset zeta map sends x to y_i = sum_{k containing i} x_k, and inverse uses sign (-1)^(|k|-|i|). Check every basis at N=1,2,4,8,16,32,64 (127 columns per direction), seeded dense inputs at N=128,256,1024, operation counts and invalid sizes. The incoming 11 tests passed in an independent replay. A separate review multiplied all seven matrices over the rationals, then compared both algorithms with an independently written submask oracle on signed integer inputs at every supported power of two, including 512. The full incoming suite passed 283 tests with Z3. A new regression checks that invalid floats are rejected and that oversized iterators are consumed only through entry 1,025. Integer field representatives are reduced modulo the field prime.

    python -m pytest -q tests/test_shear_word.py

## Dense subset transforms

Let j be the universe size and N=2^j. Complementing both indices changes the implemented superset zeta transform into the subset zeta transform. The inverse is Möbius inversion in either convention. The classical in-place butterfly needs Nj/2 additions or subtractions. The word needs 3Nj Walsh additions/subtractions plus four diagonal passes (4N entry updates, including some unit scales). Its inverse uses six diagonal passes in total. These are mathematical operations or passes, excluding index work and coefficient setup. Multiplication by −1 can also be implemented as subtraction. They are separate from minimum binary linear gate counts and measured runtime. No wall-clock shear benchmark was run in this checkpoint.

If an exact Walsh implementation has gate cost T(N), each dense zeta or Möbius transform costs at most 3T(N)+O(N) gates through this word. With the paper's bound, this gives Oε(N j^(1/2+ε)) gates for every ε>0 over fields admitting the displayed identity. It improves the exponent over the dense classical butterfly for ε<1/2 when comparing arithmetic costs in the same field. This is a consequence for dense transforms in the exact model. To obtain a practical speedup, an executable backend must also pay for batching, output restoration and diagonal passes. Trimmed Möbius inversion already saves work when the relevant support closure is small, so its comparison is with a different workload. [Trimmed Möbius inversion](https://arxiv.org/abs/0802.2834)

## Ranked subset convolution

The disjoint convolution is h(S)=Σ_{A⊆S}f(A)g(S∖A). Björklund, Husfeldt, Kaski and Koivisto's method rank-slices the two operands, takes subset zeta transforms, multiplies rank polynomials pointwise, applies subset Möbius inversion to each retained rank and selects rank |S| at S. After inversion, each pair must have A∪B=S. The rank condition |A|+|B|=|S| then forces A∩B=∅. This known algorithm uses O(N j²) additions and multiplications. [Fourier meets Möbius, Section 2](https://arxiv.org/abs/cs/0611101)

| Stage | Classical cost | Cost if the Walsh backend saves gates |
|---|---|---|
| 2(j+1) forward zeta and j+1 inverse rank maps | O(N j²) additions/subtractions | O(j T(N)+Nj) field operations |
| N pointwise truncated rank-polynomial products | O(N j²) field operations by schoolbook | Unchanged by a faster Walsh backend. O(N M(j+1)) with a separate polynomial multiplication method of cost M. |
| Rank slicing, final selection and ordinary dense tables | O(Nj) entries or initialization work | The same capacity and data movement obligations. |

Thus replacing only the transforms improves one stage. With schoolbook rank products, the overall upper bound stays O(N j²). With a separate quasi-linear rank product algorithm, the combined bound becomes Oε(N j^(3/2+ε)+N M(j+1)); an exponent improvement follows, for example, if ε<1/2 and M(j+1)=O(j^(2−δ)) for some δ>0. For example, radix-two NTT gives M(j+1)=O(j log j) at sizes where the zero-padded length dividing |K^×| is supported. The fixed field supplies powers of two only through 2^23. A claim for arbitrary j needs an appropriate multiplication algorithm or field extension with its cost included. The accounting does not reduce the usual Θ(Nj) rank-table storage.

Walsh directly diagonalizes XOR convolution, which does not itself impose disjointness. Rank slicing can filter this variant too, since |A△B|=|A|+|B| holds exactly for disjoint A,B. Rank slicing followed by a Fourier convolution and cardinality filtering already appears in Stoian's cyclic FFT method, so the lab makes no novelty claim for that approach. No ranked convolution speedup or general semiring method was benchmarked. The executable evidence is the fixed-field zeta/Möbius component. [Stoian, Sections 2–3](https://arxiv.org/html/2404.18522v1)

This checkpoint leaves characteristics 2, 3 and 5, uniform field descent, disjoint-word synchronization and a saving Walsh implementation open. The next concrete dependency is a bounded saving template. [Recursion gate](RECURSION_GATE.md)
