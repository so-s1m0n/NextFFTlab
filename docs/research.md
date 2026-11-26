# Research plan and claim ledger

## Sources

- OpenAI, *The logarithmic exponent of finite Fourier transforms*, 2026-11-24: https://github.com/openai/math/tree/main/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026
- Indexed manuscript revision (source commit): https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/paper.pdf
- Release history: https://github.com/openai/math/blob/main/history.md
- Community overview and formalization links: https://mathcommunity.github.io/oai-math-revised/papers/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/
- Related independent certificate work, not peer reviewed: https://airr.science/papers/ARR-2026-1BXNNHNTEA8DAB2R/versions/v1/

## Claim ledger (initial snapshot, 2026-11-26)

| Claim | Status |
|---|---|
| Preprint reports N(log N)^(1/2+o(1)) binary linear-gate complexity for finite abelian Fourier transforms over qualifying fields | Reported in abstract; not independently proved here |
| Required field contains appropriate roots of unity and N is invertible | Reported assumptions |
| Lean statements cover forward/inverse and batched linear-gate bounds | Source mapping recorded in ROADMAP.md; local compilation and dependency axioms pending |
| Classical exact finite-field baselines agree on tested inputs | Tested here |
| Bluestein identity yields exact results at selected lengths | Tested here; classical identity only |
| Matrix-root predictor and Hermite repair compute the binary query product | Verified for a toy window with repairs and a theorem window with zero exceptions |
| Fixed binary template with shared routing reproduces exact Walsh output | Verified at A=8, f=1, W=512 with zero exceptional rows |
| Saving template and recursive construction | No bounded scheduled candidate passed the strict saving condition |
| Practical speedup | Fixed Python template was slower than classical same-domain Walsh at its one tested batch size |

Gate 1 maps the main Lean statements and the count predictor to pinned sources. The full proof and local Lean compilation remain open. The pinned manuscript maps the predictor, matrix root and Hermite repair to bounded binary implementations. The first theorem-scale case with nonzero exceptions exceeds the current budget, including under the factored predictor estimate. Never infer a formula merely from an abstract.

## Milestones and acceptance gates

1. Source audit: obtain pinned LaTeX and Lean; record hashes, theorem locations, definitions, parameters, hypotheses, and axioms. Run Lean using the upstream pinned toolchain. Compare actual statements with manuscript. Document discrepancies.
2. Exact component prototypes: parity-sign count prediction, spectral repair, associated linear maps and chirp specialization as applicable. For each, exhaustively test small instances, including edge conditions, and compare with independently computed oracles. Record operation counts, coefficient bit lengths and failures. Do not substitute heuristics for proof obligations.
3. End-to-end exact construction: implement the actual recursion and full repair for eligible fields and transform lengths. Compare to direct DFT at small N and radix-2 NTT when applicable. Test basis vectors (which characterize a fixed linear map), randomized vectors, inverse and convolution. Reject unsupported inputs explicitly.
4. Cost model: separate binary linear gates (under the paper definition), modular arithmetic, coefficient generation, indexing, preprocessing, peak memory and actual runtime. Count setup both cold and amortized. Do not fit the theoretical exponent from a few tiny inputs.
5. Performance: compare equivalent domains, precision, sizes, thread counts and batches; use optimized compiled NTT or FFTW/pocketfft/cuFFT as appropriate. Pin CPU affinity when possible, record CPU model and software versions, randomize benchmark order, use repetitions and distributions. Report median, variability, memory, error, crossover and negative results. Python timings are only smoke tests.
6. Application: start with exact polynomial multiplication; profile realistic workloads and isolate transform contribution. Then consider image convolution or signal processing only after numerical stability and complex arithmetic portability are demonstrated.

## Suggested experiment record

Commit SHA; source theorem/lemma; field and primitive root; input length and seed; arithmetic domain; implementation/backend/version; operation model; setup time; transform time; raw samples; peak memory; oracle; result/error; hardware/OS/thread configuration; limitations.

## Non-goals

Do not claim the mathematical proof is independently validated merely because tests pass. Do not claim speedups from asymptotic complexity alone. Do not mix finite-field exact arithmetic with complex floating point as equivalent measurements.
