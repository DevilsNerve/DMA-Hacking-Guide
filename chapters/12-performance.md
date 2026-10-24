# Chapter 12: Performance and freshness

<!-- BOOK:NAV:START -->

[Previous: Address translation](11-address-translation.md) · [Contents](../README.MD#table-of-contents) · [Next: Reproducibility and tool design](13-reproducibility.md)

<!-- BOOK:NAV:END -->

**You will learn:** how to measure useful work, when batching helps, and how a faster loop can still produce worse observations.

**Before you start:** understand [read consistency](06-reading-memory.md#consistency). Establish correctness on fixed inputs before benchmarking.

## Define the result you want sooner

“Reads per second” is incomplete. Are you counting API calls, requested bytes, returned bytes, decoded records, or distinct current application states? A loop that returns the same cached record a thousand times is different from one that observes a thousand new states.

Choose a primary metric, such as “valid observations of a specified record, with an acceptable age.” Record failure rate and freshness alongside latency. Otherwise an optimization can look successful simply because it skips difficult inputs.

<a id="measurement"></a>
## Design a comparison you can trust

Use the same input corpus, requests, decoder, and output validation for both configurations. Record source type, cache policy, batch sizes, tool versions, and hardware when relevant.

Measure several runs. Separate initialization from steady-state work. If you exclude a warm-up period, say so. Report median and tail latency, such as p95, plus sample count. A mean alone can hide occasional long stalls.

For a fixed image, verify that both versions return identical bytes or decoded results. For a live source, compare against a producer sequence and a documented sampling window; identical hashes are not expected when the input is changing.

## Know where the time goes

A simple model is:

```text
total time = fixed request overhead
           + transfer time
           + translation and metadata work
           + decoding
           + scheduling and output
```

Suppose each request has 0.5 ms of fixed overhead and moves a four-byte value almost instantly. One hundred serial requests spend roughly 50 ms on overhead. A supported batch can reduce the number of round trips. These are invented numbers illustrating the model, not device benchmarks.

Instrument stages before rewriting the whole tool. If formatting and console output dominate, a faster acquisition backend will barely change the total.

## Batch independent reads

Scatter/gather interfaces can request several discontiguous ranges together. They are most useful after you know the addresses. A pointer chain still has dependencies: you need the first pointer's value before you can determine the next address.

Batch by dependency level. Resolve roots, then independent headers, then independent payloads. Check each subrequest's status. One successful aggregate call does not necessarily establish success for every range.

Coalescing nearby reads can also help, but a larger request may cross an unavailable page. Preserve per-range availability and do not let one optional field silently invalidate unrelated results.

## Cache with a reason and an invalidation rule

| Candidate | Possible policy | Invalidation event |
| --- | --- | --- |
| Layout schema | Cache by exact supported build identity | Binary or configuration change |
| Module information | Cache within a verified process lifetime | Exit, restart, module load/unload |
| Object pointer | Keep briefly with identity checks | Generation or lifecycle change |
| Dynamic payload | Refresh according to freshness requirements | Age limit or producer update |

“No cache” is not a universal fix. A library can have separate caches for payload bytes, translation, and process metadata. Consult its current API and measure the layer you intend to change. A freshly fetched payload does not make an old object pointer valid.

## Deeper detail: backpressure and time

If the producer updates faster than you can consume, an unbounded queue makes observations progressively older. Decide whether to retain every sample, keep only the newest valid one, or reduce sampling. Document that decision because it changes the meaning of the output.

Use a monotonic clock for elapsed durations. Wall-clock timestamps are useful for records but can jump. Cross-machine age measurements require clock synchronization or an explicit uncertainty bound. Producer sequence numbers can reveal missed updates without pretending clocks are perfectly aligned.

External polling does not automatically provide CPU watchpoints. Event-driven observation requires a supported event source, such as instrumentation in your own application. Do not describe a fast poller as an interrupt-driven monitor.

## Checkpoint

Version B doubles calls per second, but its p95 observation age increases. Has it improved the tool? Which metric should decide?

[Check your answer](../appendices/answers.md#chapter-12).

<!-- BOOK:FOOT:START -->

[Previous: Address translation](11-address-translation.md) · [Contents](../README.MD#table-of-contents) · [Next: Reproducibility and tool design](13-reproducibility.md)

<!-- BOOK:FOOT:END -->
