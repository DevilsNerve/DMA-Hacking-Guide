# Chapter 17: Comparing captures

<!-- BOOK:NAV:START -->

[Previous: Modules, symbols, and build identity](16-modules-and-symbols.md) · [Contents](../README.MD#table-of-contents) · [Next: Polling and replay](18-polling-and-replay.md)

<!-- BOOK:NAV:END -->

**You will learn:** how to compare two observations by meaning, recognize changes caused only by layout, and avoid mistaking missing evidence for a removed object.

**Before you start:** understand the named collection in [Chapter 15](15-strings-and-collections.md). This chapter compares synthetic `OBS2` images, not entire operating-system captures.

## In this chapter

- [Basic semantic comparison](#semantic-comparison)
- [Choose the level of equality](#equality-levels)
- [Trace the relocated fixture by hand](#relocation-walk)
- [Specify a numerical comparison policy](#numeric-policy)
- [Account for identity and incomplete observations](#comparison-contract)
- [Design a convincing change experiment](#change-experiment)
- [Practice exercises](#chapter-exercises)

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

Likewise, different hashes establish that the complete byte sequences differ, but do not tell you whether health changed. Matching cryptographic hashes are strong practical integrity evidence, not a mathematical proof of byte equality: collisions are possible. When both files are available and exact equality is the question, compare their bytes directly. Neither matching bytes nor matching hashes establish that a live source was current when those bytes were obtained.

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

The three main fixtures use exactly representable values, so exact numeric comparison is appropriate for this exercise. Scientific or graphical measurements may require an absolute tolerance, a relative tolerance, or domain-specific rounding.

Choose the comparison rule before examining the result, and retain raw values. A large tolerance can hide a meaningful change; a tiny one can flood the report with insignificant noise. Also decide whether positive and negative zero should be distinguished. The lab's numeric comparison treats them as equal, while their bit patterns can differ.

NaN is rejected by the schema. This prevents the comparison from inheriting surprising NaN equality behavior. Another schema may permit NaN as a missing measurement, but then it needs an explicit rule for comparing missing measurements.

## A compact comparison record

Keep the two input hashes, format versions, session context, generation values, completeness status, identity rule, and field-comparison policy with the result. This lets someone reproduce the comparison without assuming that a screenshot contains all relevant evidence.

<a id="equality-levels"></a>
## Choose the level of equality

Before computing a difference, decide what equality would mean. Several different questions can be valid, but they require different representations.

| Level | Equality means | A difference can tell you |
| --- | --- | --- |
| Complete file | Every stored byte matches | Something about the representation changed |
| Selected byte range | Corresponding bytes in a defined region match | That region differs under the chosen alignment |
| Decoded record | All interpreted fields and structure match | The schema's decoded representation changed |
| Normalized entity state | The same IDs have equal tracked values, regardless of storage order | A tracked logical value or membership changed |
| Application meaning | The difference matters under the application's rules | A domain-specific conclusion, requiring additional context |

Do not use the last label for a result that only established the first. A byte mismatch in padding can be real but irrelevant to tracked state. Conversely, an unchanged file can be an old capture repeatedly returned by a stale source.

The lab's `Snapshot` object preserves storage order. Consequently, the baseline and relocated snapshots are not identical as ordered collections. `semantic_view` deliberately sorts by unique entity ID and compares the label and entity values. This is a policy choice that removes one known irrelevant distinction.

### Define normalization narrowly

Normalization should remove only distinctions your question has declared irrelevant. Sorting entities by stable ID is appropriate here because order has no meaning in `OBS2`. Sorting a queue whose order determines processing priority would destroy relevant information.

Similarly, trimming spaces from labels or rounding coordinates before comparison would change the question. If you need a display-friendly representation, keep it separate from the values used to establish equality. A report can show a rounded summary while retaining precise values and the exact comparison policy.

The lab preserves decoded labels exactly. It does not case-fold them, apply Unicode normalization, or merge records by name. Those decisions keep the negative control focused on storage relocation and order rather than quietly adding a broader text-equivalence policy.

### Record what was excluded

The semantic view excludes payload offsets, unused gaps, file length, and entity order. It retains label, entity ID, health, x, and y. Generation values appear as comparison context rather than as entity-field changes.

Write those exclusions in the report. Otherwise “no changes” can be read as “the two files are equal” or “the entire application state is unchanged,” neither of which is the claim this comparator makes.

<a id="relocation-walk"></a>
## Trace the relocated fixture by hand

The baseline has a 32-byte header, a 16-byte name, and 48 bytes of entities. In the relocated case, sixteen unused bytes are inserted after the header and the entity order is reversed.

| Property | Baseline | Relocated |
| --- | --- | --- |
| File length | 96 | 112 |
| Generation | 2 | 2 |
| Name interval | `[32, 48)` | `[48, 64)` |
| Array interval | `[48, 96)` | `[64, 112)` |
| Storage order of IDs | 10, 20, 40 | 40, 20, 10 |

At file offset 48, the baseline begins entity 10. At that same position, the relocated image begins the name. A byte-by-byte comparison at fixed offsets is now comparing different logical regions. The mismatch is expected; it is not evidence that entity 10 became text.

The header explains how to realign the interpretation. Decode each name from its own declared range. Decode each array using its own start and count. Build a mapping from ID to record. Once you compare the corresponding entities, all tracked values agree.

This is also why a single guessed “shift everything by sixteen bytes” rule is insufficient. The name and array moved, but the header did not. The entity array also reversed. A correct decoder follows the declared structure instead of applying one global shift to unrelated fields.

### Build the join explicitly

For two complete observations, let `old_ids` and `new_ids` be the sets of decoded IDs. Then:

```text
shared = old_ids intersect new_ids
added = new_ids minus old_ids
removed = old_ids minus new_ids
```

For each shared ID, compare the fields selected by the schema. Do not compare the first old record with the first new record unless order is itself the declared identity rule. Reject duplicates before building maps; otherwise a dictionary assignment can silently erase conflicting evidence.

In the baseline-to-after comparison, IDs 10 and 20 are shared, 30 is added, and 40 is removed. ID 10's health changes while its coordinates stay equal. ID 20's y coordinate changes while its health and x coordinate stay equal. Reporting the unchanged fields is optional, but checking them is part of establishing the narrow change claim.

### Reverse comparison is useful but has a different reading

The comparator can compare `after` to `before`. The added and removed sets reverse, and field transitions reverse. That is a valid comparison operation. It does not mean time ran backward.

The current comparison function does not enforce chronological order; it reports the supplied generations. The replay monitor adds temporal policy separately. Keeping those responsibilities distinct allows the same semantic comparator to support regression analysis, baseline restoration checks, or an intentionally reversed investigation.

<a id="numeric-policy"></a>
## Specify a numerical comparison policy

A floating-point field has a stored representation, a decoded numerical value, and a chosen display format. Those three layers can disagree about whether something “looks the same.”

The binary32 encoding closest to decimal `0.1` is `cd cc cc 3d` in little-endian order. Decoded into Python's usual wider float representation, it prints as `0.10000000149011612` with sufficient digits. The adjacent higher binary32 encoding, `ce cc cc 3d`, becomes `0.10000000894069672`.

Both can print as `0.1` under a short display format even though the raw bytes and numeric values differ. This is why the lab now uses nine significant digits for displayed binary32 fields. The corresponding change is visible as:

```text
1.health:0.100000001->0.100000009
```

The displayed decimals are still concise representations, not the full exact decimal expansion. Nine significant digits suffice to distinguish and round-trip finite binary32 values through an appropriate decimal-to-binary32 conversion. Retaining raw bytes remains useful when bit-level identity is the question. Python's [floating-point tutorial](https://docs.python.org/3/tutorial/floatingpoint.html) explains why decimal input and binary storage need separate treatment.

### Exact comparison

Exact numeric comparison is appropriate when the schema and question require it, as in this fixture. It reports any unequal decoded finite value. It treats positive and negative zero as equal because their numeric values compare equal, even though their sign bits differ.

If the sign of zero matters to your application, compare an additional bit-level representation or define a different field policy. Do not silently switch between numeric and raw-byte equality depending on which result looks more convenient.

### Tolerance-based comparison

For a measured quantity, you may want to ignore differences smaller than a declared threshold. A common symmetric rule is:

```text
abs(a - b) <= max(abs_tol, rel_tol * max(abs(a), abs(b)))
```

An absolute tolerance sets a floor in the field's units. A relative tolerance scales with magnitude. Near zero, a relative tolerance alone can reject differences that a domain-specific absolute tolerance would regard as insignificant. Python documents this approach in [`math.isclose`](https://docs.python.org/3/library/math.html#math.isclose).

Choose tolerances from the measurement's meaning, not from a desire to make a test pass. A coordinate tolerance of 0.01 means something only after you know the coordinate units and the application's required precision. Do not apply the same tolerance to an ID, count, or generation counter; those are discrete identity or control fields.

Approximate equality can also be nontransitive. With an absolute tolerance of 1, 0 can be close to 0.75 and 0.75 close to 1.5, while 0 is not close to 1.5. Therefore a tolerance comparator is not automatically a valid equivalence relation for grouping or deduplicating records.

### Missing and non-finite measurements

`OBS2` rejects NaN and infinity before comparison. A different format might permit a missing-value marker. If so, define whether two missing values count as equal, how missing-to-present transitions are reported, and whether missing values participate in statistics.

Do not turn a failed read into NaN or zero unless the result schema explicitly identifies it as unavailable. Otherwise later tolerance logic can make an acquisition failure look like an ordinary small measurement change.

<a id="comparison-contract"></a>
## Account for identity and incomplete observations

Before using a set difference as a removal list, establish the scope of both sets. Are they all objects in a session, only objects near a camera, or only records whose pages were available? The same set operation can answer very different questions depending on that scope.

A complete decode means the bytes required by the schema were available and valid. It does not prove that the producer included every real-world object. In this lab, completeness of the collection is part of the synthetic producer contract. In a live system, you need evidence about the producer's selection rules too.

### Use a coverage ledger for partial sources

A system that intentionally supports partial observations can retain a coverage ledger: which collections or ranges were requested, which were supplied, and which could not be interpreted. A missing ID in a covered complete collection has a different meaning from a missing ID in an unread range.

For example, suppose the old collection contains IDs 10, 20, and 40. The new source supplies valid records for 10 and 20 but cannot read the range that may contain 40. The supported result is that 40's current membership is unknown. It is not evidence that 40 was removed.

The current `OBS2` comparison deliberately rejects incomplete input instead of implementing that richer ledger. This keeps the exercise's meaning clear. If you extend it, add explicit availability states to the output schema before accepting partial data; simply catching a read error and continuing is not enough.

### Bind identity to a session

An integer ID can be unique in one capture and still be reused across sessions. Comparing ID 10 from a restarted producer with ID 10 from the old producer may compare unrelated objects. A useful identity can include a source session, object generation, and local ID, but the exact components must come from the application contract.

Do not manufacture a session match from similar names or coordinates. If session continuity is unknown, retain both observations and label any match as a hypothesis. You can still compare file layouts or aggregate statistics without claiming object continuity.

### Schema changes need a migration rule

Suppose a later format changes health from a float fraction to an integer percentage or changes coordinates from meters to centimeters. The same field name no longer guarantees comparable values.

Require compatible schemas or an explicit conversion that records the source and destination units, rounding, and information loss. Keep the original values. If an older schema lacks a field, mark it unavailable for comparison rather than filling it with zero and reporting a change.

The advanced lab accepts only version 2. It does not guess a decoder for a newer version. That refusal is preferable to producing a convincing but unsupported cross-version report.

<a id="change-experiment"></a>
## Design a convincing change experiment

Use both positive and negative controls. The `relocated` case is a negative control for semantic change: representation changes, meaning stays equal under the schema. The `after` case is a positive control: known entity fields and membership change.

For your own application, create a small matrix before collecting data:

| Experiment | Controlled input | Expected observation |
| --- | --- | --- |
| Change only health | Application-side health command | One identified health field changes |
| Move one object | Known coordinate update | Specified coordinate fields change |
| Reorder storage | Producer rebuilds the same collection | ID-based state stays equal |
| Recreate an object | Documented lifecycle action | Identity or generation changes under the declared rules |
| Change a display label | Rename through the application | Label changes without merging object identities |
| Interrupt observation | Deliberately unavailable sample | Failure or unknown state, not a fabricated removal |

Run the baseline more than once when the application can change independently. A single before/after pair cannot establish causation if other state also changed during the interval. Retain application-side evidence of the action, the acquisition window, and the observation generations.

For a slowly updating value, record enough time to distinguish “the change was not observed yet” from “the candidate is unrelated.” For a rapidly changing value, a wider observation window may include several valid states. Avoid forcing a one-to-one correspondence that the timing evidence does not support.

### Follow one unexpected difference

Suppose the tool reports a health change even though only storage order was reversed. First verify that both images decode. Then inspect the mapping keys: was the comparison keyed by ID or by array position? Check whether duplicate IDs were rejected before the map was created. Finally, inspect whether a presentation step rounded or converted values before comparison.

This sequence tests the comparison pipeline itself. Re-running the acquisition would not repair a positional join over already valid fixed images.

### Keep a claim ledger

A useful claim ledger pairs each conclusion with its evidence and limits:

| Claim | Evidence | Limit |
| --- | --- | --- |
| Stored representation changed | Different retained bytes or hashes | Does not identify the changed meaning |
| Tracked state stayed equal after relocation | Two valid decodes and the declared semantic comparator | Covers only tracked fields and the stated identity scope |
| ID 10 health changed | Exact decoded values matched by ID | Requires session continuity and the field policy |
| ID 40 left the observed collection | Complete compatible observations and set difference | Does not alone prove object destruction |
| Reader progress stalled | Ordered generation observations | Requires a progress policy and timing context |

This prevents the final report from overstating what a technically correct diff established.

<a id="chapter-exercises"></a>
## Practice exercises

1. **Choose an equality rule.** Two captures differ only in unused padding. Which equality levels should report a difference, and which should not under the lab's policy?
2. **Handle partial data.** The new source cannot read the range that might contain ID 40. What should replace the confident statement “ID 40 was removed”?
3. **Evaluate a tolerance.** With absolute tolerance 1 and relative tolerance 0, compare the pairs `(0, 0.75)`, `(0.75, 1.5)`, and `(0, 1.5)`. Why does this matter for grouping records?
4. **Read the displayed change.** Two binary32 values print as `0.1` at low precision, but their bytes differ. What information should a diagnostic report retain before calling them equal?

[Worked solutions](../appendices/deep-dive-answers.md#chapter-17).

## Checkpoint

The byte diff changes at dozens of positions, but the ID-based comparison reports no changed fields. Give two explanations that do not require a parser bug. What evidence would distinguish them?

[Check your answer](../appendices/answers.md#chapter-17).

<!-- BOOK:FOOT:START -->

[Previous: Modules, symbols, and build identity](16-modules-and-symbols.md) · [Contents](../README.MD#table-of-contents) · [Next: Polling and replay](18-polling-and-replay.md)

<!-- BOOK:FOOT:END -->
