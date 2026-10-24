# Chapter 18: Polling and replay

<!-- BOOK:NAV:START -->

[Previous: Comparing captures](17-comparing-captures.md) · [Contents](../README.MD#table-of-contents) · [Next: Testing unfamiliar layouts](19-testing-layouts.md)

<!-- BOOK:NAV:END -->

**You will learn:** how to represent reader state over time, separate several kinds of failure, and test a polling policy without depending on a live device.

**Before you start:** review [consistency](06-reading-memory.md#consistency) and [performance](12-performance.md). The advanced lab supplies a deterministic replay trace; it does not perform live polling.

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

Decide what happens if one request takes longer than the interval. Starting overlapping requests indefinitely creates a backlog. Depending on the purpose, skip a missed interval, reduce sampling, or bound outstanding work. Preserve the decision in your measurements.

Likewise, cancellation should stop new work and then close resources according to the backend's rules. Do not close a handle while an unsupported concurrent operation is still using it.

## Deeper detail: restart is an explicit transition

A lower generation might indicate a producer restart, an out-of-order result, a stale cache, or the wrong session. The monitor cannot choose among those explanations from the counter alone.

When a new process or session is independently identified, create a fresh monitor or perform an explicit reset that records that identity change. Automatically accepting every lower counter as a restart would also accept stale observations as new ones.

The same-generation content check compares semantic records, so harmless changes in array order or padding do not produce an inconsistency. This connects the monitor to the normalization rules from [Chapter 17](17-comparing-captures.md).

## Checkpoint

Why should a successful duplicate read leave the “last observed progress” timestamp unchanged? Why does exceeding the progress budget not prove that the source is broken?

[Check your answer](../appendices/answers.md#chapter-18).

<!-- BOOK:FOOT:START -->

[Previous: Comparing captures](17-comparing-captures.md) · [Contents](../README.MD#table-of-contents) · [Next: Testing unfamiliar layouts](19-testing-layouts.md)

<!-- BOOK:FOOT:END -->
