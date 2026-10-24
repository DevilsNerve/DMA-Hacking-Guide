# Chapter 18: Polling and replay

<!-- BOOK:NAV:START -->

[Previous: Comparing captures](17-comparing-captures.md) · [Contents](../README.MD#table-of-contents) · [Next: Testing unfamiliar layouts](19-testing-layouts.md)

<!-- BOOK:NAV:END -->

**You will learn:** how to represent reader state over time, separate several kinds of failure, and test a polling policy without depending on a live device.

**Before you start:** review [consistency](06-reading-memory.md#consistency) and [performance](12-performance.md). The advanced lab supplies a deterministic replay trace; it does not perform live polling.

## In this chapter

- [Outcome definitions](#state-transitions)
- [Trace every state update](#state-walkthrough)
- [Distinguish four clocks and ages](#observation-clocks)
- [Specify producer generations](#generation-contract)
- [Design a bounded live scheduler](#bounded-scheduler)
- [Test recovery and lifecycle transitions](#recovery-tests)
- [Practice exercises](#chapter-exercises)

## Every iteration needs an outcome

A loop that repeatedly prints the last decoded value can look healthy after acquisition has stopped working. Keep the last valid observation if it is useful, but label it as retained data. Do not refresh its acquisition timestamp when no new valid sample arrived.

Separate the reader's status from the value it last observed. A user should be able to distinguish “current request failed; last accepted health was 60” from “the current request successfully observed health 60.”

For this exercise, the producer contract is explicit: within one test session, a larger generation means a newer published observation, and a generation identifies one semantic state. The counter does not wrap during the session. These are fixture rules, not guarantees supplied automatically by DMA.

<a id="state-transitions"></a>
## Give each state a precise meaning

| Outcome | Meaning | What the monitor retains |
| --- | --- | --- |
| `accepted` | First valid sample or a higher generation | New valid state and time of observed progress |
| `duplicate` | Same generation and same semantic state | Existing state; no new progress timestamp |
| `unavailable` | Acquisition supplied no sample | Existing state, labeled with the failed request |
| `invalid` | Bytes arrived but violate the format | Existing state; invalid bytes do not become data |
| `regressed` | Generation is lower than the accepted one | Existing state; session identity needs investigation |
| `inconsistent` | Same generation now claims different semantic state | Existing state; the producer contract was violated |
| `no-progress` | A valid duplicate arrives after the progress budget | Existing state, with the lack of observed advancement |

The lab uses a 100 ms progress budget. That is a policy chosen for an exercise. An application whose state is expected to remain unchanged for minutes needs a different policy or an explicit heartbeat.

## Read the replay trace

Run:

```sh
python labs/advanced_lab.py replay
```

The trace contains these events:

| Observation time | Input | Expected outcome |
| --- | --- | --- |
| 0 ms | Valid generation 2 | `accepted` |
| 10 ms | Same observation | `duplicate` |
| 20 ms | No bytes available | `unavailable` |
| 30 ms | Unsupported format version | `invalid` |
| 40 ms | Valid generation 4 | `accepted` |
| 50 ms | Old generation 2 | `regressed` |
| 60 ms | Changed health still labeled generation 4 | `inconsistent` |
| 200 ms | Original generation 4 again | `no-progress` |

The last accepted progression occurred at 40 ms, so the final duplicate arrives 160 ms later. The monitor does not replace that timestamp with 50 or 60 ms when it sees a regression or inconsistency.

No actual delay occurs during replay. The timestamps are data. This makes the result repeatable and allows a test to cover an entire failure sequence quickly.

## Be careful with the word “fresh”

Observation age, time since observed progress, and age of the underlying application state are different measurements. The lab can calculate the first two from its replay history. It cannot establish when a real producer created bytes it has never communicated a trustworthy timestamp for.

Even a first sample can already be old. A new generation is evidence of advancement relative to earlier samples, not a universal proof that the source is synchronized with the application's present state.

For elapsed durations in one running program, use a suitable monotonic clock; Python documents this in its [time module](https://docs.python.org/3/library/time.html#time.monotonic). Cross-machine timing needs additional synchronization assumptions. The replay uses nondecreasing integer milliseconds and rejects a backwards observation time.

## Add live scheduling only after the policy works

Once the state machine is tested, a live loop can supply observations to it. Define a target interval, a request timeout supported by the backend, and a limit on retries. A timeout in your wrapper does not necessarily cancel an underlying native call; use the backend's actual cancellation or lifetime contract.

Decide what happens if one request takes longer than the interval. Starting overlapping requests without a limit can create a backlog when completions fall behind. Depending on the purpose, skip a missed interval, reduce sampling, or bound outstanding work. Preserve the decision in your measurements.

Likewise, cancellation should stop new work and then close resources according to the backend's rules. Do not close a handle while an unsupported concurrent operation is still using it.

## Deeper detail: restart is an explicit transition

A lower generation might indicate a producer restart, an out-of-order result, a stale cache, or the wrong session. The monitor cannot choose among those explanations from the counter alone.

When a new process or session is independently identified, create a fresh monitor or perform an explicit reset that records that identity change. Automatically accepting every lower counter as a restart would also accept stale observations as new ones.

The same-generation content check compares semantic records, so harmless changes in array order or padding do not produce an inconsistency. This connects the monitor to the normalization rules from [Chapter 17](17-comparing-captures.md).

<a id="state-walkthrough"></a>
## Trace every state update

The monitor stores three pieces of state: the last observation time, the last time it accepted a higher generation or its first valid sample, and the accepted snapshot. The progress budget is configuration, not another timestamp.

These fields answer different questions. `last_observation_ms` tells you when the caller most recently supplied an event, even if it supplied no bytes. `last_progress_ms` tells you when a valid first or higher generation was accepted. `accepted` holds the last accepted semantic state. None of them is automatically the producer's creation time.

Work through the fixture trace after each event:

| Time | Outcome | Accepted generation | Last observation time | Last progress time |
| ---: | --- | ---: | ---: | ---: |
| 0 | accepted | 2 | 0 | 0 |
| 10 | duplicate | 2 | 10 | 0 |
| 20 | unavailable | 2 | 20 | 0 |
| 30 | invalid | 2 | 30 | 0 |
| 40 | accepted | 4 | 40 | 40 |
| 50 | regressed | 4 | 50 | 40 |
| 60 | inconsistent | 4 | 60 | 40 |
| 200 | no-progress | 4 | 200 | 40 |

At 20 ms, the monitor has heard from the caller but has no new sample. Updating the observation timestamp is accurate; updating the progress timestamp would not be. At 30 ms, bytes arrived, but they do not form a supported observation. They also do not advance progress.

At 40 ms, generation 4 is accepted and becomes the retained state. At 50 ms, generation 2 is rejected as older under this session's ordering contract. At 60 ms, a different health value claims to belong to the already accepted generation 4. The monitor reports the conflict and preserves the earlier accepted state.

At 200 ms, the original generation 4 arrives again. The semantic content agrees with the retained state, but 160 ms have elapsed since accepted progression. With a 100 ms budget and a strict `elapsed > budget` rule, the result is `no-progress`.

### Validation order is observable behavior

The order of checks determines which outcome is reported when several concerns might apply. The lab's order is:

1. Reject an invalid observation time without mutating monitor state.
2. Record the valid observation time.
3. Report no supplied bytes as `unavailable`.
4. Decode supplied bytes; report format failure as `invalid`.
5. Accept the first valid sample or a higher generation.
6. Reject a lower generation as `regressed`.
7. Reject changed semantic content at the same generation as `inconsistent`.
8. Classify a valid unchanged duplicate by the progress budget.

For example, an invalid payload at 200 ms produces `invalid`, not `no-progress`. The reader can still derive that its retained state has not advanced for 160 ms, but the primary event outcome describes why the current sample was not accepted.

A user interface may display both facts: “current sample invalid; last accepted progression 160 ms ago.” The reference monitor returns one primary outcome per event and exposes the retained timestamps; it does not implement a complete alerting dashboard.

### An accepted state is not a mutable scratch buffer

The decoded snapshots and entities are immutable dataclasses in the lab. A rejected observation cannot partially update the accepted health value and then fail while decoding another field. The decoder produces a complete valid snapshot before the monitor considers replacing its retained state.

If you implement a mutable version, preserve this transactional behavior. Decode into a separate candidate, validate the candidate, and publish it as one accepted observation. Updating shared fields one by one during parsing can create a state that no input ever contained.

<a id="observation-clocks"></a>
## Distinguish four clocks and ages

Timing reports become misleading when one timestamp is used for several different events. Name the events you actually measure:

| Time | What it marks | Who can establish it |
| --- | --- | --- |
| Producer publication time | When the application published a state | The producer or a validated synchronization protocol |
| Request start time | When acquisition began | The reader's local clock |
| Request completion time | When the reader obtained the result | The reader's local clock |
| Acceptance time | When the consumer accepted a validated observation | The consumer's local clock |

A fifth useful timestamp is the latest accepted generation advance. It can differ from acceptance of a repeated sample if your system records both. The lab deliberately treats duplicates as non-advancing events.

From one local monotonic clock, you can calculate request duration and processing duration. You cannot subtract an unrelated producer clock and call the result exact source age without a clock relationship. Cross-machine clock offset, drift, and timestamp precision become part of that calculation.

### A simple timing example

Suppose a request starts at local time 100 ms, completes at 108 ms, and is accepted at 110 ms. Acquisition took 8 ms and local post-acquisition work took 2 ms. Those measurements do not tell you whether the returned state was published at 99 ms, 50 ms, or much earlier.

Now suppose the producer includes a timestamp on a synchronized clock with a known uncertainty of plus or minus 3 ms. Your estimate of source age should retain that uncertainty. Presenting a precise-looking age of `11.000 ms` without the clock caveat would imply more evidence than you have.

For a single-process exercise, supplied replay times avoid these complications. The times are integers and are validated as nonnegative and nondecreasing. NaN, floating-point values, booleans, and backwards times are rejected by the reference monitor rather than allowed to poison later arithmetic.

### A budget is a policy, not a physical fact

At exactly 100 ms after the last accepted progression, the lab still reports a duplicate within budget. At 101 ms, it reports no progress. This boundary should be tested explicitly; otherwise documentation and implementation can disagree over `>` versus `>=`.

The same state can be healthy in one application and concerning in another. A stationary diagnostic record might remain unchanged for hours. A producer contract promising a new heartbeat every 20 ms creates a different expectation. Attach the progress budget to that contract rather than calling every repeated value stale.

The monitor also does not wake up by itself. If no new event is supplied after time 40 ms, it will not spontaneously emit an outcome at 141 ms. A live application needing timeout alerts must schedule its own health assessment using the exposed timestamps or a separate timer policy. That is a separate behavior from classifying an arriving sample.

<a id="generation-contract"></a>
## Specify producer generations

The generation field helps only because the exercise supplies a meaning for it. Within one session, a larger generation means a newer published observation, and a repeated generation identifies the same semantic state. Numbering is not required to be consecutive.

Consequently, advancing from 2 to 4 proves advancement under this contract but not that exactly one or two updates were missed. The producer could reserve numbers, increment for unrelated events, or publish a subset of its internal updates.

A higher generation with unchanged tracked fields is still acceptable. It can represent a new publication of the same tracked state or changes outside the observed field set. Do not change the monitor to require a field difference unless the producer contract actually says every generation must alter those fields.

For repeated generations, the lab compares the normalized semantic view. Changed padding or entity order is harmless. Changed label or tracked entity values is a conflict. This makes the consistency check match the equality policy rather than the physical byte layout.

### Counter wrap and restart

The decoder can represent any `uint64` generation. The replay contract assumes the counter does not wrap inside the session. If the accepted value is the largest `uint64` and the next value is zero, the monitor reports a regression.

An explicit new-session transition can establish a new ordering domain. That transition requires independent evidence of a producer restart or session change. Resetting automatically whenever a lower value appears would also accept out-of-order or cached old data as a fresh session.

The producer may use a different protocol in a real system, such as a modular sequence number with a bounded reordering window. That requires a different ordering rule and tests. Do not borrow modular arithmetic merely to make a failed sample pass this simpler monitor.

<a id="bounded-scheduler"></a>
## Design a bounded live scheduler

Replay separates policy from acquisition. A live scheduler's job is to obtain observations and supply them to that policy without creating uncontrolled concurrency, backlog, or resource lifetimes.

Start with a single outstanding request if the backend's concurrency guarantees are unclear. Choose a desired start-to-start interval and define what happens when an operation overruns it. Waiting a full interval after every request finishes produces a different sampling schedule from targeting fixed start times.

For an invented 10 ms interval and a 15 ms request duration, those designs behave differently. A finish-then-wait loop starts roughly every 25 ms. A fixed-schedule design with one outstanding request must skip or account for missed starts because it cannot complete serial 15 ms work every 10 ms.

If the backend serializes requests, continuing to enqueue one every 10 ms produces a growing backlog. A backend that safely supports two concurrent 15 ms requests could sustain that cadence with overlapping work instead. Establish the actual concurrency contract, bound outstanding requests, and handle completion ordering; do not infer capacity from the desired schedule alone.

### Choose a backlog policy

| Purpose | Plausible policy | Tradeoff to record |
| --- | --- | --- |
| Show the latest known state | Keep the newest acceptable pending observation | Intermediate states can be discarded |
| Preserve every event in a bounded experiment | Queue with explicit capacity and overflow reporting | Latency rises under load; overflow must remain visible |
| Measure a fixed request corpus | Finish the corpus without pretending it is real-time | Throughput and freshness are different metrics |
| Sample at a target cadence | Skip missed intervals and record them | Fewer observations, with a clearer schedule |

No policy is universally correct. What matters is that the measurement and user-facing result match it. A queue that preserves every old sample may be appropriate for an audit trace and poor for a live status display.

### Timeouts must correspond to actual backend behavior

A wrapper timing out while a native read continues does not free the underlying handle for reuse or closure. Establish whether the backend supports cancellation, whether a timed-out operation can later complete, and who owns its buffers until then.

Keep request identity with each completion. If responses can arrive out of order, a completion for an older request should not overwrite a newer accepted state merely because it arrived last. The generation policy can detect some regressions, but request/session identity is still needed to attribute the result correctly.

Avoid an unlimited retry loop. Bound retries by count, elapsed time, or both, and retain the reasons. A repeated unsupported-format error is different from a temporary unavailable range; retrying it more often does not add layout support.

### Shutdown is part of the lifecycle

When stopping, stop scheduling new requests first. Then resolve or cancel outstanding work according to the backend contract, prevent late completions from publishing into a closed session, and close resources when their lifetimes permit it.

For a synchronous backend, this may be a simple serial sequence. For an asynchronous backend, ownership needs to be explicit. “Close everything in a finally block” is useful only if the close operations are safe while the relevant work is still running.

These are design obligations for a future live adapter. The replay helper intentionally performs no scheduling, sleeps, device reads, or cancellation. Its small scope lets you verify consumer policy before introducing those variables.

<a id="recovery-tests"></a>
## Test recovery and lifecycle transitions

An error-handling policy should show both rejection and recovery. A monitor that rejects every later sample after one failure is not a useful repair.

Test an unavailable event before the first valid sample: the accepted state should remain absent. Then supply a valid sample and confirm that it can be accepted. Test invalid bytes after a valid sample: the accepted state should remain intact. Then supply a valid higher generation and confirm that progress resumes.

For a same-generation conflict, inspect both the reported outcome and the retained value. A test that checks only the string `inconsistent` can miss an implementation that printed the right label after already overwriting the accepted health value.

For a backwards observation time, check that the call fails before changing any stored timestamp. If invalid time data partly mutates state, subsequent valid events can produce misleading ages even though the initial exception looked appropriate.

### Separate transport, schema, and policy failures

Use distinct test inputs for no sample, malformed sample, valid older sample, and valid conflicting sample. They exercise different branches:

```text
None                         -> acquisition supplied no observation
bytes with unsupported tag   -> supplied observation cannot be decoded
valid lower generation       -> decoded state violates ordering policy
valid same generation change -> decoded state violates generation identity
```

A single generic failure injection cannot prove all four behaviors. Conversely, do not invent different errors solely to make the interface complicated. Keep categories that change how the reader or operator should respond.

### Compare a status stream with a value stream

A value-only log might show generation 4 repeatedly and hide several acquisition failures. A status-only log might show failures without telling you which state remains available. Retain both when diagnosing a problem: the event outcome, accepted state identity, last observation time, and last progress time.

That combined trace is what supports the final investigation's conclusion. It explains why the monitor still holds the valid generation-4 observation and why its progress age is measured from 40 ms rather than from the most recent failed or duplicate request.

<a id="chapter-exercises"></a>
## Practice exercises

1. **Check the exact boundary.** A valid first sample is accepted at 10 ms with a 100 ms budget. What should an unchanged duplicate produce at 110 ms and at 111 ms?
2. **Separate acceptance from field change.** A valid higher generation contains identical tracked entity values. Should the reference monitor accept it? What does that acceptance prove?
3. **Handle a long request.** A scheduler targets 10 ms intervals, but requests take 15 ms. Name two bounded policies and explain the different observations they produce.
4. **Preserve the correct state.** After generation 4 is accepted, a same-generation conflict arrives and then a valid generation 5. What should be retained after each event?

[Worked solutions](../appendices/deep-dive-answers.md#chapter-18).

## Checkpoint

Why should a successful duplicate read leave the “last observed progress” timestamp unchanged? Why does exceeding the progress budget not prove that the source is broken?

[Check your answer](../appendices/answers.md#chapter-18).

<!-- BOOK:FOOT:START -->

[Previous: Comparing captures](17-comparing-captures.md) · [Contents](../README.MD#table-of-contents) · [Next: Testing unfamiliar layouts](19-testing-layouts.md)

<!-- BOOK:FOOT:END -->
