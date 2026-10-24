# Chapter 13: Reproducibility and tool design

<!-- BOOK:NAV:START -->

[Previous: Performance and freshness](12-performance.md) · [Contents](../README.MD#table-of-contents) · [Next: Build a trustworthy reader](14-capstone.md)

<!-- BOOK:NAV:END -->

**You will learn:** how to preserve the meaning of a result across tool changes, application updates, and handoffs to another person.

**Before you start:** complete at least one [controlled experiment](07-controlled-experiments.md).

## Record the claim, not just the number

“Health is 87.5” omits most of the information needed to evaluate it. A useful record identifies the input, process or synthetic context, layout, observation time, acquisition policy, and validation result.

```json
{
  "schema": "dma-book-observation-v1",
  "source": "synthetic-fixture-v1",
  "pointer_bits": 64,
  "image_base": "0x140000000",
  "record_address": "0x140000100",
  "sequence": 2,
  "status": "valid",
  "health": 87.5,
  "items": [10, 20, 30]
}
```

This is an example record format, not the lab CLI's output schema. Addresses are strings here to avoid precision loss in consumers that represent JSON numbers with limited integer precision. Specify your encoding instead of assuming every downstream tool handles a 64-bit address identically.

## Give unsupported layouts an explicit outcome

Keep a layout registry keyed by the evidence that actually controls representation: format version for a fixture, or build identity, architecture, and runtime information for an application. Include field sizes, endianness, root resolution, validation rules, and test evidence.

An unknown build should produce “unsupported layout” until verified. Guessing a nearby version may return plausible data and be harder to diagnose than an immediate failure.

Separate locator confidence from decode confidence. You can know that a record is internally valid while remaining uncertain which application instance it represents.

## Use interfaces that preserve the distinctions

A small tool can have four layers:

```text
source adapter -> exact byte reader -> versioned decoder -> result publisher
```

The adapter understands the source. The reader enforces availability. The decoder understands one layout. The publisher handles formatting and files. Tests can then replace the source without rewriting the decoder.

Keep addresses, lengths, and target pointer widths explicit in interfaces. Avoid passing an unlabeled integer that sometimes means a file offset and sometimes means a process virtual address.

## Publish complete results

If a required field fails, do not publish a normal-looking successful record with a default value. Either fail that observation or use an explicit per-field status in a schema that supports partial results.

For file exports, write a complete temporary file, close it, and use the platform's supported replacement mechanism where appropriate. Decide how existing files are handled. A failed run should not silently destroy the last good result. Keep input and output paths distinct.

These are design requirements, not a claim that every rename is an atomic transaction across filesystems. If you publish several related files, define how readers recognize a complete generation.

## Build a useful test corpus

Include known-good examples and failures that challenge assumptions:

- Both target pointer widths and an address above 4 GiB.
- Null and out-of-range pointers, truncated records, and oversized counts.
- Unknown versions, malformed identity bytes, and invalid float values.
- Inconsistent sequence fields and multiple signature matches.
- Matches crossing scan boundaries and explicit unreadable gaps in any region-aware backend.
- Process exit, module replacement, and stale-cache behavior when you add a live backend.

The supplied suite covers the synthetic cases relevant to its implementation. Live lifecycle and hardware cases require their own environment and evidence.

## Deeper detail: evidence levels

Use precise language in reports:

| Evidence | A claim it supports |
| --- | --- |
| Parser test on a fixture | This decoder handled these bytes as expected |
| Runtime API check | This installed API accepted this call in this environment |
| Supported capture replay | This source and process view decoded this capture |
| Live observation of your application | This setup observed this application state during this run |
| Hardware run | This specific device/platform combination supplied these observations |

None of these automatically establishes the next row. The distinction is useful when reviewing changes: a decoder fix may need only fixture tests, while a transport change needs transport evidence.

## Checkpoint

A new decoder passes every fixture but has not been tried on your live acquisition setup. What should the release note claim?

[Check your answer](../appendices/answers.md#chapter-13).

<!-- BOOK:FOOT:START -->

[Previous: Performance and freshness](12-performance.md) · [Contents](../README.MD#table-of-contents) · [Next: Build a trustworthy reader](14-capstone.md)

<!-- BOOK:FOOT:END -->
