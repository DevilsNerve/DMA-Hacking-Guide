# Chapter 17: Comparing captures

<!-- BOOK:NAV:START -->

[Previous: Modules, symbols, and build identity](16-modules-and-symbols.md) · [Contents](../README.MD#table-of-contents) · [Next: Polling and replay](18-polling-and-replay.md)

<!-- BOOK:NAV:END -->

**You will learn:** how to compare two observations by meaning, recognize changes caused only by layout, and avoid mistaking missing evidence for a removed object.

**Before you start:** understand the named collection in [Chapter 15](15-strings-and-collections.md). This chapter compares synthetic `OBS2` images, not entire operating-system captures.

## Start with a question you can answer

“What changed?” is too broad for a useful experiment. Try: “Between two complete observations from this test session, which entity IDs were added or removed, and which tracked fields changed?”

That question commits you to a scope, an identity rule, and a completeness requirement. It also avoids treating a different file layout as a different application state.

Our advanced lab provides three cases:

| Case | What it changes | Purpose |
| --- | --- | --- |
| `before` | Baseline generation 2 with IDs 10, 20, and 40 | Establish a known starting observation |
| `relocated` | Moves payload ranges and reverses array order | Demonstrate unchanged meaning despite different bytes |
| `after` | Generation 4; changes two fields, adds ID 30, removes ID 40 | Provide known semantic changes |

Create and compare them using the [advanced walkthrough](../labs/advanced.md#comparison-lab). The original baseline remains available even after the later cases are generated.

## Byte comparison answers a narrower question

A byte diff compares values at corresponding file positions. It is useful for finding where files differ, but the positions need not describe the same logical field after a layout change.

If a name moves sixteen bytes forward, many file positions change even though the decoded name is identical. If the entity array is reordered, the first record in one file may represent a different entity from the first record in the other.

Likewise, a file hash establishes equality or inequality of the complete byte sequences. Different hashes do not tell you whether health changed. Identical hashes do establish identical captured bytes, but not that a live source was current when those bytes were obtained.

<a id="semantic-comparison"></a>
## Compare a normalized view

Decode both images independently. Reject either one if its schema or ranges are invalid. Then build an ID-to-record mapping for each observation.

```text
before IDs: 10, 20, 40
after IDs:  20, 10, 30

shared IDs: 10, 20
added IDs:  30
removed IDs: 40
```

For the shared IDs, compare named fields instead of record positions. The fixture's known changes are:

```text
10.health: 87.5 -> 60
20.y: 12 -> 13
```

Sort the reported IDs and fields so output is deterministic. Preserve the capture generations as context, but do not report a generation increase as an entity-field change. The label is a separate observation-level field.

The `before` and `relocated` cases should produce no semantic changes. This is a useful negative control: it demonstrates that your comparison does not accidentally depend on array order or file position.

## Identity is an assumption to test

Unique IDs are part of the `OBS2` schema. The decoder rejects duplicates rather than letting the last record silently overwrite an earlier one in a dictionary.

In a real application, an ID may be unique only within one process lifetime, scene, or session. A restarted application can reuse ID 10 for an unrelated object. Bind comparisons to the appropriate lifetime or use a documented compound identity such as session plus object generation plus ID.

Names, positions, and pointers are often weaker identity candidates. A pointer can be reused, a name can be shared, and a position can change. If you cannot establish identity, report candidate correspondences and uncertainty rather than a definite update history.

## Missing is different from removed

Suppose the second read of the entity array fails halfway through. You cannot conclude that every unread entity was removed. The source did not supply a complete observation.

Our comparison accepts only complete successfully decoded images. A system designed for partial observations needs explicit per-object availability. Its output might say `not observed` or `unavailable`; it should reserve `removed` for evidence that supports removal under the collection's semantics.

Even a complete list might be a filtered view. If a tool lists only visible objects, disappearance can mean “outside this view” rather than destruction. Write down the list's meaning before interpreting its differences.

## Deeper detail: what counts as an equal float?

The fixtures use exactly representable values, so exact numeric comparison is appropriate for this exercise. Scientific or graphical measurements may require an absolute tolerance, a relative tolerance, or domain-specific rounding.

Choose the comparison rule before examining the result, and retain raw values. A large tolerance can hide a meaningful change; a tiny one can flood the report with insignificant noise. Also decide whether positive and negative zero should be distinguished. The lab's numeric comparison treats them as equal, while their bit patterns can differ.

NaN is rejected by the schema. This prevents the comparison from inheriting surprising NaN equality behavior. Another schema may permit NaN as a missing measurement, but then it needs an explicit rule for comparing missing measurements.

## A compact comparison record

Keep the two input hashes, format versions, session context, generation values, completeness status, identity rule, and field-comparison policy with the result. This lets someone reproduce the comparison without assuming that a screenshot contains all relevant evidence.

## Checkpoint

The byte diff changes at dozens of positions, but the ID-based comparison reports no changed fields. Give two explanations that do not require a parser bug. What evidence would distinguish them?

[Check your answer](../appendices/answers.md#chapter-17).

<!-- BOOK:FOOT:START -->

[Previous: Modules, symbols, and build identity](16-modules-and-symbols.md) · [Contents](../README.MD#table-of-contents) · [Next: Polling and replay](18-polling-and-replay.md)

<!-- BOOK:FOOT:END -->
