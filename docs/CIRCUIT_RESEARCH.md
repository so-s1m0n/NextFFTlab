# Exact Walsh circuit research

PR #1 is preserved by the local annotated tag `checkpoint/pr-1` at `dd120eb`. The research branch starts from that commit. The explicit predictor/repair template is a fixed evidence baseline. Its simple scaling experiments are closed. This branch studies exact Walsh–Hadamard over F₉₉₈₂₄₄₃₅₃ with practical matrix sizes.

## Limits of the predictor/repair construction

| Constraint | What follows mathematically | What belongs to the construction or implementation |
|---|---|---|
| 6,750 shifts | Fix m=15, the endpoint predictor for [1,14], all 2¹⁵ query tuples, disjoint independent rows assigned to a shift, and a worst-case repair fraction 1/(2m³). A tuple k makes exactly the pair {k, k⊕(2¹⁵−1)} exceptional. Both endpoint errors are nonzero in the chosen field. Write r(C) for the live row mass assigned to a complement pair. Each r(C)≤R/6,750 and the sum over pairs is R. There must be at least 6,750 occupied pairs, hence at least that many distinct shifts. One equal-width shift per pair achieves equality. | The argument also permits unequal block widths under the same row assignment. It does not constrain other predictors, a different repair budget, or shared encodings with a different error rank. It uses the full set of query tuples, attainable in the source binary layout by setting auxiliary coordinates to zero and choosing each distinguished frequency pair independently. |
| Pencil | If an affine d×d matrix L satisfies the formal polynomial identity Lᵇ=pI with p≠0, then deg p≤b and b·deg(det L)=d·deg p. The degree-13 endpoint polynomial therefore forces 16 to divide d when b=16. | Three products give 4,096 lanes per shift in the tensor-root construction. The divisibility argument does not show that this is minimal, and does not apply directly to an identity verified only on the sign cube. |
| Independent inputs | Rank of Hₙ⊗I_R is nR over the chosen field. If the circuit encodes independent inputs into fewer than nR scalar coordinates and discards the rest, exact reconstruction for all inputs is impossible. | Streaming and structured reindexing can reduce simultaneous storage. A smaller lane or shift count must describe a different batching or representation rather than copies of fewer inputs. The endpoint tensor-root design with 6,750 shifts uses R=27,648,000 rows per label. |
| Axes | For the given binary Hamming Gram relation, any realization of the same matrix by a nondegenerate pairing needs dimension at least its rank. Each selected orthogonal pair needs at least two dimensions. | The source allocation A=2(m+D−1) and 2^(Af) entries per explicit row are layout properties. At m=15 even the weaker A≥30 requires 4 GiB for one packed row at f=1. The named Hamming-label family with q≥2 has D≥2 and A≥32. The 1 GiB experiment cap is a lab constraint. |
| Field extension | Root order and pairwise unit node differences must hold in the coefficient algebra used by the identities. | The proof's universal cyclotomic rank is not a mandatory runtime multiplier over this base field. b=16 divides P−1, and R<P allows distinct base-field Vandermonde nodes for the bounded formula. |
| Repair | For a known support of s arbitrary independent errors, a linear syndrome with fewer than s scalars cannot distinguish all s error values. | Dense Vandermonde checks/lifts, 4s conversions and the four predictor applications are costs of this implementation of the binary Hermite construction. Structured syndromes or a smaller error rank would change the accounting and require a new proof. |

Source anchors are `lem:count-predict`, `lem:matrix-root`, `lem:hermite-repair` and `eq:kernel-routing-block`. [Pinned OpenAI manuscript](https://github.com/openai/math/tree/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build) · [PR #1 experiments](OPTIMIZATION.md).

## Independent research tracks

| Track | Mathematical basis and expected cost | Entry requirement and failure condition |
|---|---|---|
| Small circuit synthesis | Represent every wire as an n-vector over the field. For a bounded gate budget, constrain coefficients and earlier-wire choices, then match the output basis coefficients. General bounded SAT/SMT has a combinatorial topology space. This branch runs exhaustive algebraic synthesis in a restricted rank-one grammar. | Keep the exact verifier independent of the search. The 7- and 22-gate witnesses beat folklore butterflies and reach known counts. End this grammar at n=8, since its best witness trails the published 19-gate circuit. A future solver run should target a stronger baseline with explicit coefficient and topology budgets. |
| Low-dimensional pencil | Search representations of the polynomial root identities in a smaller matrix algebra. A dense d-lane stage costs O(d²) row combinations before address volume. Sparse representations are needed alongside smaller d. | For b=16 and the formal degree-13 identity, the smallest eligible d is 16. Verify a candidate symbolically or state a weaker verified domain explicitly. A determinant representation alone is insufficient. Eliminate candidates whose evaluation or field descent consumes the lane savings. |
| Predictor and repair | Analyze the rank of the correction at each frequency, or design predictors with different exceptional support. Classical erasure syndromes motivate sparse repairs. Dense correction cost scales as O(sRM+s²M) per label for M entries per row. | A candidate must give an exact decoding argument for independent inputs and account for all transforms, checks and reindexing. Lowering a mean error rate with no uniform guarantee, or hiding full-row transforms in the predictor, fails. |
| Auxiliary axes | Change the Gram relation or rectangle construction. For the existing full Hamming-label family with even alphabet q and length L, the rank is exactly D=L(q−2)+2. Reducing D by one divides explicit binary row volume by 4^f at fixed m and f. | The current family already uses its exact rank. A different relation must preserve the free-rectangle orthogonality and weighted label-identity decomposition. Reducing D at the cost of more charged calls or row mixing only counts if total cost improves. |
| Tensor lift | A block of size b=2ᵗ with g binary gates, repeated over disjoint bit groups, costs g(N/b)⌊log₂N/t⌋ + N(log₂N mod t) binary gates. A common scale per block can be deferred to the outputs. Fixed blocks retain O(N log N). | Recheck every basis vector at bounded sizes. Compare true additions, constant multiplications, dependency depth and time after lifting. A smaller gate count permits this study to proceed to lifting. It does not pass the paper's predictor/repair recursion condition. |

The Gram rank formula follows by subtracting the baseline row from each row with one label coordinate changed. Coordinate i spans the q−1-dimensional even-parity subspace of functions on its alphabet. For even q each such subspace contains the constant function. The sum of these coordinate spaces has dimension 1+L(q−2), since a sum of one-coordinate functions vanishes only when each term is constant. The baseline row contributes one more dimension because its coordinate indicators have odd parity. The implementation computes this rank without forming the Gram matrix. Tests compare it to independent elimination on small label sets.

Prior art consulted includes [Fuhs and Schneider-Kamp's GF(2) SAT synthesis](https://titan.dcs.bbk.ac.uk/~carsten/papers/SAT10-slp.pdf), [Childs on generalized Clifford algebras](https://www.tandfonline.com/doi/abs/10.1080/03081087808817206), [Reed and Solomon's polynomial codes](https://sites.math.rutgers.edu/~zeilberg/akherim/reed.pdf), [Alman on rigidity and Kronecker powers](https://arxiv.org/abs/2102.11992) and [Alman on finite-field lookup tables](https://arxiv.org/abs/2211.04643). The XOR synthesis model does not transfer directly to this odd-characteristic field. The lookup-table and bounded-depth models use different cost measures.

## Bounded synthesis and measurements

The synthesis writes T=Σᵢ₌₁ⁿ⁻¹xᵢ and D=x₀−T. For k≠0, output k is D+2Σxᵢ over the nonzero indices with parity(k & i)=0. The search pairs all but one variable in T, optionally precomputes a subset of D+2xᵢ anchors, then chooses each output's cheapest route using the selected anchors, matched pairs and singleton variables. These restrictions define the exhausted grammar. There is no unrestricted optimality claim.

Limits were set before the run. Synthesis visits at most 13,440 configurations and stops after 10 s per search. The benchmark's traced Python allocation budget is 16 MiB per measurement, checked after the measurement. Circuit construction is capped at 512 inputs and 8,192 operations, and no search frontier is materialized. Verification checks every basis vector against the independent parity formula and tests seeded inputs against the iterative Walsh implementation.

| Search | Configurations | Best gates | Add/sub | Scalar multiplies | Search median | Search allocation peak |
|---|---:|---:|---:|---:|---:|---:|
| H4 | 24 | 7 | 7 | 3 | 0.067 ms | 7,264 B |
| H8 | 13,440 | 22 | 22 | 14 | 49.27 ms | 852,744 B |

H4's count is known from the multiply/add literature. H8's 22-gate result uses the same rank-one parity decomposition as Alman and Rao's approach, though the code searches a restricted family of schedules. Sussman's published 19-gate H8 identity serves as a stronger comparison. It is encoded separately using the shared half-scale center and a deferred output scale. These are existing results, including the arithmetic benefit from lifting the half-scale circuit. [Coppersmith, Feig and Linzer](https://research.ibm.com/publications/hadamard-transforms-on-multiplyadd-architectures) · [Alman and Rao, Section 2.2](https://arxiv.org/pdf/2211.06459) · [Sussman, pinned comparison and circuit](https://github.com/jacobalansussman/wht-fewer-operations/tree/bbb7f830d8c5612465a9922ace566750ce6d09d2#the-8-point-circuit).

| Size and circuit | Binary gates | Add/sub | Scalar multiplies | Binary depth | SSA evaluator median |
|---|---:|---:|---:|---:|---:|
| H8 butterflies | 24 | 24 | 0 | 3 | 7.85 µs |
| H8 synthesized | 22 | 22 | 14 | 8 | 5.00 µs |
| H8 published | 19 | 19 | 9 | 6 | 4.80 µs |
| H64 butterflies | 384 | 384 | 0 | 6 | 70.25 µs |
| H64 published lift | 304 | 304 | 80 | 12 | 65.85 µs |
| H512 butterflies | 4,608 | 4,608 | 0 | 9 | 849.80 µs |
| H512 published lift | 3,648 | 3,648 | 704 | 18 | 741.15 µs |

At H512 the lift costs 4,352 adds/subtracts plus constant multiplies counted together, versus 4,608 for butterflies. The existing iterative Walsh evaluator took 343.75 µs at H512, ahead of either generic circuit evaluator. A gate maps to one two-input linear combination with arbitrary coefficients. Unary scaling can be inlined into consumer coefficients or output scale in that model. Actual constant multiplications, unary negations and modular reductions are tracked separately. Depth measures the wire graph, while the last-use peak assumes immediate slot reuse. The evaluator retains the full wire list, whose Python allocation peak is measured separately.

Reproduce on the repository root after installing the baseline development dependencies.

```sh
python -m nextfft_lab.bench_circuit --repeats 20 --out-dir results/circuits
python -m pytest -q
```

The bench prints JSON. Saved circuits use the `nextfft-linear-circuit-v1` schema. Pass the parsed JSON to `LinearCircuit.from_dict`, then use `evaluate` or `verify_walsh`. Each operation stores [a,u,b,v] for a·u+b·v. Outputs are [wire,scale] in natural binary frequency order. The recorded run used Windows 11, Ryzen 7 5800X, CPython 3.13.3, one algorithm thread and seed 20261126. Times are medians after warmup and allocation peaks use a separate `tracemalloc` pass. Search timings use three samples. The complete suite passed 166 tests in 23.25 s, and the classical smoke benchmark exited successfully. [Raw data](../results/circuit-search.json) · [Circuit JSON files](../results/circuits).

### Continuation decision

The finite gate threshold was reached and the next step of tensor-lifting was completed on the known H8 circuit. The restricted synthesis reached 22 gates, above the published 19-gate bound. Scaling the same grammar or the explicit predictor/repair template is closed. A new synthesis run should target 18 gates or fewer at H8, a better small-block arithmetic total that survives output scaling, or a separate candidate that lowers the predictor's input burden and improves total cost. The current timing and depth data leave a practical runtime crossover open.
