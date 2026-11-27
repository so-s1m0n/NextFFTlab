# A2 — borrowing occupied tensor fibers

**Verified in a bounded domain and measured.** This experiment implements the occupied-neighbor step of `up:fibers` by reusing the bounded `up:toeplitz` Newton word from the preceding checkpoint. [Pinned layers.tex](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/layers.tex#L222-L253)

For an axis of length a, its word has R=2a+2b logical slots. The scheduler groups complementary fibers into sets of m to 2m−1, where m=ceil(R/a). When processing a target in a group, logical block zero addresses that target. Later blocks cycle through distinct neighboring fibers in the group. The coordinate within each block addresses one entry of that fiber. Since R≤ma, all live logical slots map to distinct tensor slots. The occupied word acts as T⊕I on those slots, so a later target can borrow a fiber whose transformed output is already present. The scheduler executes groups and axes serially. The bound is 512 tensor entries and 128 word applications, with a capacity check before a plan is accepted. The order-of-depth synchronization and partition of many axes into blocks in the paper remain outside this check.

The tensor contains canonical integer residues in [0,P), with P=998244353. The borrowed-word contract preserves these integers exactly. The underlying modular arithmetic can canonicalize other representatives. The tests compare all 64 basis vectors of an 8×8 tensor with a direct product of character entries. The inverse is tested on that independently computed image basis. A (13,4) case creates groups of six and seven fibers and checks after *each* word that all non-target slots match their original nonzero contents, including previously transformed neighbors. An independent reviewer also checked a (7,5,2) tensor with axis order (1,0) against separate direct reference calculations.

## Matched measurements

The borrowed and dedicated paths use the same axis word. The dedicated path addresses the target in place and reuses separate dirty scratch. An ordinary Newton comparator allocates its own temporary arrays inside each call. The input copy is included equally in application timings, and immutable plan setup is measured separately. The benchmark intercepts the transform entry points on a separate counted pass. Counts exclude setup transforms. Reads and writes count logical Python payload and scratch slot operations, with ordinary Newton's internal temporary-array traffic outside that instrumentation. They do not measure physical cache traffic. The dimension and word caps bound the payload well below 1 GiB.

| Shape and method | Dedicated extra payload slots | NTT calls | Payload reads / writes | Scratch reads / writes | Median |
|---|---:|---:|---:|---:|---:|
| 8×8, borrowed | 0 | 3,072 | 303,232 / 281,728 | 0 / 0 | 169.582 ms |
| 8×8, dedicated | 40 | 3,072 | 5,760 / 3,712 | 297,472 / 278,016 | 85.775 ms |
| 8×8, ordinary | temporary arrays | 64 | 128 / 128 | unmeasured | 1.319 ms |
| 13×4, borrowed | 0 | 2,496 | 98,228 / 89,492 | 0 / 0 | 59.375 ms |
| 13×4, dedicated | 20 | 2,496 | 2,340 / 1,508 | 95,888 / 87,984 | 31.705 ms |
| 13×4, ordinary | temporary arrays | 52 | 52 / 52 | unmeasured | 0.934 ms |

Borrowing moves the scratch traffic to adjacent payload slots and eliminates the dedicated register buffer. Both occupied paths perform the same total slot accesses and the same number of NTTs. Borrowing additionally maps each logical address through the group rotation. This is consistent with its measured runtime penalty in this Python implementation. The NTT count, coefficient storage and temporary scalar objects are separate from the zero additional payload-register result.

```sh
python -m pytest -q tests/test_fiber_schedule.py
python -m nextfft_lab.bench_fiber_schedule
```

The archive records five warm samples per method, seed 20261127, setup timings, Python allocation peaks and the single-thread Windows measurement environment. [Raw data](../results/fiber-schedule-a2.json)
