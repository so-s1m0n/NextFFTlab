# Independent Lean audit of the pinned Fourier statements

**Status.** The solution-module imports, theorem statements and proof entry points were inspected. Lean 4.34.1 was run on the pinned project sources for direct import resolution. Dependency setup hit the 1 GiB process-group memory limit before proof compilation. The solution's transitive axioms and Comparator verdict remain unverified.

## What to check

The pinned OpenAI/math revision is `3344da59991ed94f9ba711217b29c1d760badfa6`. Its toolchain is `leanprover/lean4:v4.34.1`. The Lake manifest locks 59 packages, including Mathlib at `d13f23b723b8a846827a245b89c10fc7d3f11612`. The upstream Lake configuration includes compatibility patches for pinned dependency checkouts. The local attempt used that configuration without edits to the proof sources. [Toolchain][toolchain] · [Dependency lock][manifest] · [Upstream build configuration][lakefile]

The selected [Comparator configuration][spec] compares challenge module `ComparatorChallenges.ExactFourier` against solution module `OAI.LinearAlgebra.FiniteFourier.Main`. It requests three theorem comparisons with an empty named-definition list and an axiom allowlist of `propext`, `Quot.sound` and `Classical.choice`. This is the permitted list. The actual list for each solution theorem needs a kernel-level check.

| Target | Definitions and assumptions | Proof correspondence |
|---|---|---|
| `OAI.ExactFourier.main_theorem` | Exact complex cyclic DFT in a scalar DAG charging additions, subtractions and individual scales. For each c>0 and cutoff N₀≥2, some n≥N₀ has size < cn log₂n. | `main_theorem := win_to_fourier finite_win` in `OAI.Computability.FourierCircuit.Main`. This is a subsequential saving from the earlier line of work. [Challenge][legacy-challenge] · [Solution][legacy] · [Upstream scope notes][scope] |
| `OAI.LinearAlgebra.FiniteFourier.fourierComplexity` | Finite abelian G, a field K, invertible group order at least two and a primitive root of order exp(G) in K. Forward character matrix and normalized inverse. Exact acyclic binary linear costs have the lower and upper exponents, and the lower bound applies to geometric-border feedback. | `fourierComplexityTheorem_of_estimates uniformFourierBorderLower uniformFourierUpper`. Its upper branch uses integral tensor bounds, convolution, grid and cyclic estimates. The lower branch uses companion and characteristic witnesses. [Challenge][single-challenge] · [Solution entry][main] · [Upper][upper] · [Lower][lower] |
| `OAI.LinearAlgebra.FiniteFourier.batchedFourierComplexity` | J≥1 blocks of common order n≥2 over an admissible common field, with separate direction and index equivalences. Direct sum. Binary gates may mix blocks. The robust lower bound uses a joint Zariski-closure error model with simultaneous global rank and entrywise support budgets. | The upper estimate sums per-block upper circuits. The lower estimate joins a bounded-order proof and a large-order spectral-plane argument over the algebraic closure. The exact direct-sum clause matches the November paper's `thm:main`. [Challenge][batch-challenge] · [Batched assembly][batch] · [Paper statement][paper] |

The challenge file contains `sorry` at lines 58, 246 and 311 as theorem placeholders. The solution entry point imports the actual proofs. A source scan of the solution module's import closure found 8,115 repository modules and 641 distinct external module references at the boundary. Lean's own direct source-dependency listing agreed on the five direct solution imports; the challenge directly imports Mathlib. The lexical solution scan reports only `admit` tokens in the reachable repository sources. Some are identifiers, for example a bound variable of the `rejectCallback` case. The graph records module imports, which can include declarations unused by the selected theorem. It leaves transitive theorem axioms and external source bodies unresolved. The three challenge placeholders therefore do not establish that the corresponding solution theorems use `sorryAx`. [Saved source inventory](../results/lean-fourier-source-audit.json) · [Exact proof entry][main] · [Identifier example][admit]

## Observed build attempt

- Environment was Ubuntu 24.04 x86-64 under WSL, one CPU quota and a 30-minute wall-clock limit. A systemd scope set `MemoryMax=1G` and `MemorySwapMax=0` for the entire process group.
- The official Linux toolchain archive was 580,432,872 bytes. Its SHA-256 was verified as `47bf4bbd78f70c2e9670598ab7124d92b6efb7330ff33e5fbb4030f6fd72e4e4`. Lean reported 4.34.1 (commit `5045d0056413266e57c625dcd7c365b10e377c52`) and Lake reported 5.0.0-src+5045d00. The fetched source matched the full revision above. [Release assets][release]
- The upstream `lake update` applied its compatibility patches and fetched Mathlib and other packages. The last Lake output warned that multiple dependency toolchains differed and that the root fixed toolchain was not updated. About 6 minutes 32 seconds after starting the scope, systemd reported a process killed by the OOM killer and the scope result `oom-kill`. This establishes the limit reached during this attempt. It does not identify the killed process or imply that a provisioned build would fail.
- The run stopped before the post-update lock check, cache download, proof build and `#print axioms`. Comparator, landrun and lean4export were absent at preflight. No comparison or formal proof pass is claimed. The Python/Z3 regression is a separate check of the lab code.

## Reproduce in an isolated Linux checkout

The source-only inventory requires Python and Git. The bounded attempt used an isolated sparse checkout. Install the official pinned Lean release or select it with Elan before running the build commands. Use dedicated storage for the toolchain, packages and compiled files. Keep the official source and its manifest unchanged.

```sh
git init openai-math
git -C openai-math remote add origin https://github.com/openai/math.git
git -C openai-math -c protocol.version=2 fetch --depth=1 --filter=blob:none origin 3344da59991ed94f9ba711217b29c1d760badfa6
git -C openai-math sparse-checkout set lean
git -C openai-math checkout --detach FETCH_HEAD
python /path/to/NextFFTlab/scripts/lean_fourier_sources.py openai-math

cd openai-math/lean
lean --version
lake --version
export LEAN_NUM_THREADS=1
lake update
git diff --exit-code HEAD -- lean-toolchain lake-manifest.json OAI ComparatorChallenges
lake exe cache get
lake build +OAI.LinearAlgebra.FiniteFourier.Main
lake env lean /path/to/NextFFTlab/scripts/ExactFourierAudit.lean
git diff --exit-code HEAD --
```

For the bounded Linux run, put the toolchain setup and build steps in a script and run it with `systemd-run --user --scope -p MemoryMax=1G -p MemorySwapMax=0 -p CPUQuota=100% timeout -k 15s 30m bash ./audit.sh`. File paths in the example are placeholders. Inspect any changed lock before continuing. A verified outcome needs each fully qualified solution name to resolve and its reported axiom set to be a subset of the configured list. A reported `sorryAx` fails this criterion. `#print axioms` inspects dependencies of the compiled declarations. Full statement equivalence and proof validation are a separate run with the upstream Comparator toolchain, after installing its documented prerequisites. [Probe](../scripts/ExactFourierAudit.lean) · [Upstream verifier setup][comparator]

```sh
lake env comparator ComparatorChallenges/ExactFourier.json
```

Resume formal verification on a provisioned environment or with compatible compiled dependencies, keeping the source and locks pinned. Record tool versions, build outcome, each theorem's observed axioms and the Comparator verdict separately.

[toolchain]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/lean-toolchain
[manifest]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/lake-manifest.json
[lakefile]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/lakefile.lean
[spec]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/ComparatorChallenges/ExactFourier.json
[legacy-challenge]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/ComparatorChallenges/ExactFourier.lean#L12-L58
[legacy]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/OAI/Computability/FourierCircuit/Main.lean#L224-L279
[scope]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/docs/130.md
[single-challenge]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/ComparatorChallenges/ExactFourier.lean#L205-L246
[batch-challenge]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/ComparatorChallenges/ExactFourier.lean#L250-L311
[main]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/OAI/LinearAlgebra/FiniteFourier/Main.lean
[upper]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/OAI/LinearAlgebra/FiniteFourier/CompanionUpper.lean
[lower]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/OAI/LinearAlgebra/FiniteFourier/CompanionStretch.lean
[batch]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/OAI/LinearAlgebra/FiniteFourier/BatchedTheorem.lean
[paper]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/intro.tex#L25-L47
[admit]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/OAI/Computability/BorderVNP/TeamSiteStop.lean#L88-L95
[release]: https://github.com/leanprover/lean4/releases/tag/v4.34.1
[comparator]: https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/lean/ComparatorChallenges/README.md
