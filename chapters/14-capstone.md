# Chapter 14: Build a trustworthy reader

<!-- BOOK:NAV:START -->

[Previous: Reproducibility and tool design](13-reproducibility.md) · [Contents](../README.MD#table-of-contents) · [Practice labs](../labs/README.md)

<!-- BOOK:NAV:END -->

**You will build:** a small analysis workflow that returns correct observations, explains failures, and can be reproduced by someone else.

**Before you start:** complete the [lab walkthrough](../labs/README.md). Use earlier chapters as references rather than trying to memorize them.

## The project brief

Your reader receives a byte image and its declared address context. It resolves a root, decodes one supported record layout, validates every field it consumes, and reports the observation. Unsupported or incomplete data produces an explicit failure.

The repository includes a reference implementation. First run it unchanged. Then implement a second decoder in a language you know, or extend the Python implementation with a new format version while retaining support for the original.

Keep the original fixtures as a fixed baseline. A format change should be visible through a version or a separately identified schema; do not quietly reinterpret existing bytes.

## Stage 1: explain one valid result

Create the default image and inspect it. Annotate the path from the root slot to health and the item list. Identify every read width and address calculation.

**Done when:** another reader can use your notes and the layout table to predict the output without running your code.

## Stage 2: support both pointer widths

Generate a 32-bit fixture and inspect it with the matching options:

```sh
python labs/memory_lab.py create out/fixture32.bin --bits 32
python labs/memory_lab.py inspect out/fixture32.bin --bits 32
```

Then try a mismatched pointer width. Notice whether the failure occurs during root decoding or later validation. A mismatch must not be presented as a successful meaningful observation merely because some bytes can be decoded.

**Done when:** valid 32-bit and 64-bit examples pass and the high 64-bit address is preserved without truncation.

## Stage 3: make failures useful

Run all supported fault variants. For each, record the expected failing invariant, actual error, and exit status. Add a new malformed example that your own implementation originally accepted.

**Done when:** failures identify the relevant boundary and no failure is silently converted to health zero or an empty item list.

## Stage 4: challenge the locator

Use the scanner on a known image. Create separate in-memory test inputs with zero, one, and two matches. Place a match across a chunk boundary. Try a wildcard and an overlapping match.

**Done when:** the scanner reports all matches accurately and the caller treats ambiguity explicitly. If you add region scanning, add an unreadable gap case too.

## Stage 5: write the handoff

Complete the [experiment record](../templates/experiment.md). Include exact commands, input identity, layout assumptions, observed results, and limitations. Ask yourself whether a fresh checkout on another computer has everything needed to reproduce the synthetic result.

**Done when:** the automated checks pass and the written explanation agrees with the implementation.

## Optional extension: use your own application

Add an adapter for a supported observation route to a program you control. Keep the decoder contract separate from acquisition. Give the producer a known state transition and a lifecycle event such as object replacement. Compare the observed state with application-side evidence.

Document what the new source guarantees about consistency and what it cannot supply. A process-memory adapter needs process identity and region handling. A capture adapter needs format and availability rules. A hardware adapter needs device/platform evidence. They are separate projects, not configuration switches that automatically prove one another.

## Optional extension: investigate performance

Use [Chapter 12](12-performance.md) to compare individual reads with a supported batch implementation. Keep output validation and failure accounting identical. Explain whether the change improves useful observation latency, throughput, or freshness.

## Review your finished work

| Question | Evidence to attach |
| --- | --- |
| Is the location meaningful? | Address context and root-resolution description |
| Is the layout supported? | Version/build identity and field schema |
| Are reads complete? | Exact-length behavior and truncation tests |
| Are results internally valid? | Bounds, identity, and sequence checks |
| Can a second person repeat it? | Commands, input hashes, expected output |
| Are claims appropriately scoped? | Separate fixture, API, live, and hardware evidence |

The useful habit to carry forward is simple: when a value looks right, ask what would make it wrong—and build an experiment that can tell the difference.

## Checkpoint

Which additional evidence would you need before describing your capstone as a working hardware DMA reader?

[Check your answer](../appendices/answers.md#chapter-14).

<!-- BOOK:FOOT:START -->

[Previous: Reproducibility and tool design](13-reproducibility.md) · [Contents](../README.MD#table-of-contents) · [Practice labs](../labs/README.md)

<!-- BOOK:FOOT:END -->
