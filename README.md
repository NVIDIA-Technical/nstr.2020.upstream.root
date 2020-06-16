# nstr-scratch

![CUDA](https://img.shields.io/badge/CUDA-11.0%20%7C%2011.1-76B900?logo=nvidia&logoColor=white)
![arch](https://img.shields.io/badge/arch-sm__70%20%7C%20sm__75%20%7C%20sm__80%20%7C%20sm__86-555555)
![build](https://img.shields.io/badge/build-make-informational)
![license](https://img.shields.io/badge/license-MIT-blue)

Scratch space for GPU work: warp-level primitives, memory-hierarchy experiments, Ampere-era features (TF32,
`cp.async`, `wmma`), a counter-based Monte Carlo sampler, and Nsight Compute recipes. Written to understand the
hardware, not to beat CUB, Thrust or cuBLAS. Several kernels are deliberately naive so the profiler has something
to say.

> **Status:** sketches. Some compile clean on 11.0 and 11.1, some are mid-refactor, and a couple are wrong on purpose
> (marked `// INTENTIONALLY BROKEN: see NOTES.md`). Read before you `make all`.

---

## Contents

```
nstr-scratch/
├── Makefile                 per-arch -gencode matrix, debug/lineinfo toggles
├── common/
│   ├── check.cuh            CUDA_CHECK / CU_CHECK macros, last-error sync in debug builds
│   ├── timer.cuh            cudaEvent-based timer, warmup + N reps, median
│   └── bw.cuh               effective-bandwidth helpers (bytes moved / elapsed)
├── warp/
│   ├── shfl_reduce.cu       butterfly reduction, __shfl_xor_sync, full vs __activemask() masks
│   ├── ballot_compact.cu    stream compaction: __ballot_sync + __popc + exclusive offset per warp
│   ├── match_any.cu         __match_any_sync (sm_70+) for warp-aggregated atomics
│   ├── cg_tiles.cu          cooperative_groups::tiled_partition<16/8/4> reductions
│   └── NOTES.md             independent thread scheduling (Volta+) and why implicit warp-sync code broke
├── mem/
│   ├── coalesce.cu          stride sweep 1..32, float / float2 / float4 vector loads
│   ├── smem_banks.cu        32x32 transpose tile, padded (33) vs unpadded, 4B vs 8B bank mode
│   ├── ldg_vs_ld.cu         __ldg / const __restrict__ read-only path vs plain loads
│   ├── l2_persist.cu        sm_80: cudaAccessPolicyWindow, persisting L2 carve-out
│   └── pinned_vs_pageable.md
├── ampere/
│   ├── cp_async.cu          global→shared with __pipeline_memcpy_async, double-buffered tiles
│   ├── tf32_gemm.cu         wmma 16x16x8 TF32 fragments, fp32 accumulate; vs FP32 SGEMM tile
│   ├── bf16_wmma.cu         __nv_bfloat16 fragments, 16x16x16
│   ├── async_barrier.cu     cuda::barrier (libcu++) arrive/wait split phases
│   └── NOTES.md             what changed from Turing, in the order it confused us
├── grid/
│   ├── coop_reduce.cu       single-kernel reduction with cooperative launch + grid.sync()
│   └── persistent.cu        persistent-threads work queue, atomicAdd ticket dispenser
├── mc/
│   ├── paths.cu             Monte Carlo path sampler: Philox4x32-10, one path per thread
│   ├── reduce.cuh           per-block partials, second-pass reduction
│   └── README.md
├── sched/
│   └── fair_share.py        toy weighted work-queue scheduler; starvation and fairness tests
├── prof/
│   ├── ncu.md               Nsight Compute sections we actually use, and how to read them
│   ├── nsys.md              Nsight Systems timeline recipes (copy/compute overlap, streams)
│   └── roofline.md          arithmetic intensity, where each kernel here should sit
└── reading/
    └── list.md
```

## Requirements

| | Minimum | Tested |
|---|---|---|
| CUDA toolkit | 11.0 | 11.0, 11.1 |
| Driver | 450.x | 455.x |
| GPU | sm_70 (Volta) | sm_75, sm_80, sm_86 |
| Host compiler | gcc 7 | gcc 9.3 |
| Python (sched/, plots) | 3.7 | 3.8 |

`ampere/` needs sm_80 or sm_86. `warp/match_any.cu` needs sm_70+. Everything else builds back to sm_70; nothing
here targets Pascal and nothing will.

## Build

```bash
make                    # default: -gencode for sm_75, sm_80, sm_86
make ARCH=sm_80         # single arch
make DEBUG=1            # -G -O0, synchronous error checks after every launch
make LINEINFO=1         # -lineinfo for source-level Nsight Compute
make ampere/tf32_gemm   # one target
```

Flags the Makefile passes by default:

```make
NVCCFLAGS = -O3 -std=c++17 --expt-relaxed-constexpr -Xptxas -v \
            -gencode arch=compute_75,code=sm_75 \
            -gencode arch=compute_80,code=sm_80 \
            -gencode arch=compute_86,code=[sm_86,compute_86]
```

`-Xptxas -v` stays on: register count and spill bytes per kernel are the first thing to look at, and it's cheaper
than opening the profiler.

## Running

Every binary takes the problem size first, then optional reps:

```bash
./bin/coalesce 268435456 50          # 1 GiB of float, 50 timed reps after 5 warmups
./bin/smem_banks 8192 8192
./bin/tf32_gemm 4096 4096 4096
NVIDIA_TF32_OVERRIDE=0 ./bin/tf32_gemm 4096 4096 4096   # force-disable TF32 for the comparison path
```

Output is one CSV line per configuration (`kernel,size,reps,median_ms,gbps_or_tflops`) so it pipes straight into
`prof/plot.py`.

No results table in this README. Effective bandwidth and TFLOPS depend on the board, clocks, driver and ECC
setting; run them and compare against your own card's datasheet peak. For orientation, the published peaks we
divide by are DRAM bandwidth (e.g. A100 40GB: 1,555 GB/s; RTX 3090: 936 GB/s) and the dense TF32 / FP32 rates on
the vendor spec sheets.

## Notes worth reading first

### warp/: independent thread scheduling

Since Volta, threads in a warp can diverge and reconverge independently. Pre-Volta code that relied on implicit
warp-synchronous execution (no `__syncwarp()`, bare `__shfl` without `_sync`) can silently produce wrong results.
`warp/NOTES.md` walks through the two bugs we hit:

1. a reduction using `__activemask()` inside a branch, which returns *whichever lanes happen to be converged*,
   not the lanes you meant;
2. a shared-memory warp reduction missing `__syncwarp()` between steps, which passes on sm_61 and fails on sm_75.

Rule we ended up with: compute the mask *before* divergence, pass it explicitly, never use `__activemask()` for
correctness.

### mem/: the two experiments everyone should run once

- **Stride sweep.** Effective bandwidth vs stride for 4B loads. Expect roughly 1/stride once you pass 8 (32B
  sectors), then flat. `float4` loads at stride 1 should land within a few percent of the device's achievable peak.
- **Transpose tile.** 32x32 `float` tile in shared memory. Unpadded: 32-way bank conflicts on the column read.
  Padded to 33: none. Nsight Compute's `l1tex__data_bank_conflicts_pipe_lsu_mem_shared_op_ld.sum` makes it obvious.

`l2_persist.cu` uses the sm_80 access-policy window to pin a hot lookup table in L2 while streaming a larger
buffer past it. Set the carve-out with `cudaDeviceSetLimit(cudaLimitPersistingL2CacheSize, ...)` first or the
window does nothing.

### ampere/: TF32, cp.async, barriers

- **TF32** keeps FP32's 8-bit exponent with a 10-bit mantissa; tensor cores take FP32 inputs, round to TF32,
  accumulate in FP32. `tf32_gemm.cu` checks max relative error against a double-precision reference so you can see
  what you trade.
- **`cp.async`** copies global → shared without staging through registers, so a block can issue the next tile's
  loads while computing on the current one. `cp_async.cu` double-buffers with `__pipeline_commit()` /
  `__pipeline_wait_prior(1)`.
- **`cuda::barrier`** splits arrive and wait, so producers don't stall on consumers. Needs libcu++ from the 11.x
  toolkit.

### grid/: cooperative launch

`coop_reduce.cu` launches with `cudaLaunchCooperativeKernel` and calls `this_grid().sync()`. The grid must be
fully co-resident: size it with `cudaOccupancyMaxActiveBlocksPerMultiprocessor × SM count`, or the launch fails
with `cudaErrorCooperativeLaunchTooLarge`. Don't use it under MPS without checking.

### mc/: counter-based sampling

`paths.cu` gives each thread one path and derives every random number from `(seed, path_id, step)` through
Philox4x32-10 (cuRAND device API, `curand_init(seed, path_id, 0, &state)`). Paths are reproducible and independent
of launch geometry, which matters when you compare a GPU run against a CPU reference. Per-block partial sums go to
global memory; a second tiny kernel reduces them.

It started as a side quest: one of us also works on **NVIDIA Strategy** ($NSTR), an independent Solana project,
and wanted to see what batched risk sweeps of its reinflow model would look like on a GPU. Short answer so far: the
model is light enough that a CPU handles it, and no GPU is provisioned for it. The kernel stayed because it's a
clean small example of Philox plus a two-pass reduction.

### sched/: weighted fair share

`fair_share.py` is a toy scheduler: jobs arrive in classes, each tick splits capacity by weight, idle capacity is
redistributed, and a test asserts no class starves over 10k ticks. It has nothing to do with CUDA; it's here
because the same "split capacity across classes once per tick" shape kept showing up (it's also roughly how NVIDIA
Strategy's design notes describe splitting fees across buckets, which is where the idea went next).

## Profiling recipes

```bash
# full section set, one kernel, source-level
ncu --set full --import-source yes -k tf32_gemm_kernel -o prof/tf32 ./bin/tf32_gemm 4096 4096 4096

# just memory throughput and bank conflicts
ncu --section MemoryWorkloadAnalysis --section SourceCounters ./bin/smem_banks 8192 8192

# timeline: copy/compute overlap across streams
nsys profile -t cuda,nvtx -o prof/streams ./bin/coalesce 268435456 10
```

`prof/ncu.md` lists the metrics we actually read (`sm__throughput.avg.pct_of_peak_sustained_elapsed`,
`dram__throughput...`, `smsp__warp_issue_stalled_*`) and what each stall reason usually means in these kernels.

## Known issues

- `ampere/bf16_wmma.cu` fragment layout assumption is wrong for `col_major` B; output is transposed. Tracked in
  NOTES, not fixed yet.
- `grid/persistent.cu` has no backoff; under heavy contention the ticket `atomicAdd` dominates. Fine for a demo of
  the pattern, not for anything real.
- On WSL2 the cooperative launch path is untested.
