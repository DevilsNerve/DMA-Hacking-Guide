# Chapter 19: Testing unfamiliar layouts

<!-- BOOK:NAV:START -->

[Previous: Polling and replay](18-polling-and-replay.md) · [Contents](../README.MD#table-of-contents) · [Next: A complete investigation](20-complete-investigation.md)

<!-- BOOK:NAV:END -->

**You will learn:** how to turn layout assumptions into tests, select informative malformed inputs, and use mutation experiments without claiming they prove more than they do.

**Before you start:** understand the `OBS2` layout and its validation order in [Chapter 15](15-strings-and-collections.md). Keep the [format reference](../labs/advanced.md#format) open while reading.

## In this chapter

- [Turn the format into a test matrix](#test-matrix).
- [Construct independent expected answers](#independent-oracles).
- [Design informative mutations](#mutation-design).
- [Test comparisons and temporal behavior](#behavioral-properties).
- [Diagnose and minimize a failure](#failure-triage).
- [Verify the command-line boundary](#cli-contract).
- [Work the review exercises](#chapter-exercises).

## Start with the assumptions you could get wrong

A parser can accept a valid fixture while still making dangerous or misleading assumptions. Perhaps it trusts an unbounded count. Perhaps it reads the name from inside the header. Perhaps a duplicate entity ID disappears when records are placed in a dictionary.

Write down the conditions required for one successful decode. Each condition should have a valid example, a boundary example, and, where possible, a nearby counterexample.

| Assumption | Useful counterexample | Expected result |
| --- | --- | --- |
| Header is complete | Input one byte shorter than the header | Reject before decoding fields |
| Version is supported | Correct magic with version 3 | Report unsupported version |
| Name length uses code units | Valid supplementary character | Decode the complete surrogate pair |
| Text is well formed | Isolated UTF-16 surrogate | Reject malformed text |
| Array is bounded | Count 65 when the limit is 64 | Reject before reading elements |
| Payloads are separate | Name overlaps the entity array | Reject the invalid layout |
| IDs are unique | Two valid records with ID 10 | Reject ambiguous identity |
| Floats are meaningful | NaN or infinity in a tracked field | Reject the invalid observation |
| Collection is complete | Remove one byte from the final element | Report an unavailable range |

These tests are justified by the format contract. They should not reject a valid representation simply because you did not think to generate it in the first fixture.

## Test the edge, not just a dramatic failure

If the entity limit is 64, test 0, 1, 64, and 65. A count of four billion demonstrates one bad input, but it can miss an off-by-one error at the actual boundary.

If an image ends exactly after its final entity, that image should pass. Removing one byte should fail. Adding unrelated padding can remain valid if the format allows it. If zero entities are allowed, confirm that the parser handles an empty array without inventing a required record.

Do the same for strings. Test empty text, plain ASCII, a supplementary character, the maximum code-unit count, and an input just beyond the maximum. A test based on code-point count alone can miss the UTF-16 unit boundary.

## Preserve an independent expected answer

A serializer and parser can share the same error. If the serializer writes a field to the wrong offset and the parser reads the same wrong offset, a round trip still succeeds.

Keep at least one independently specified byte sequence or literal field slice alongside round-trip tests. In this lab, a fixed header prefix and the documented name bytes provide such checks. Also compare the decoded entity values with explicit expected values, not only with another invocation of the same parser.

For unfamiliar real layouts, seek a second evidence source: matching symbols, producer-side instrumentation, or a separately implemented parser. Agreement is useful only to the extent that the methods do not share the same unsupported assumption.

<a id="mutations"></a>
## Use mutations to find unexpected behavior

Take a valid image, choose one or more byte positions, and change them. Then feed the changed image to the decoder under fixed resource limits.

The desired outcomes are either a valid decoded observation or the decoder's documented input error. An uncaught indexing error, an unbounded allocation, or a hang is a bug. A mutated input that still decodes is not automatically a bug: the mutation may have changed padding or produced another valid field value.

The supplied [advanced tests](../tests/test_advanced_lab.py) use a fixed random seed for mutation and arbitrary-byte cases. This makes a failure reproducible. It is a small deterministic corpus, not exhaustive fuzzing or evidence that every possible input is handled correctly.

```sh
python -m unittest discover -s tests -p test_advanced_lab.py -v
```

When a case fails, retain the original input, changed input, seed, mutation position, and exception. Reduce the case until the smallest change still exposes the bug. Add that minimized case as a named regression test so it remains useful even if the random generator changes later.

## Test the consumer as well as the parser

Valid decoded records can still be mishandled. The comparison must ignore array order, detect field changes by ID, and distinguish additions from missing input. The replay monitor must preserve its last accepted state through invalid samples and must reject same-generation conflicting content.

These are behavioral tests. They protect the meaning of the output, not just the mechanics of turning bytes into objects.

Also exercise command-line boundaries: absent files, truncated files, incompatible formats, and an existing output path. A friendly tool should provide a useful error and a nonzero exit status. A failed parse should not leave a normal-looking success report on standard output.

## Deeper detail: properties and their limits

Good properties for this specific format include “reordering uniquely identified entities does not change their semantic comparison” and “relocating nonoverlapping payloads without changing contents preserves the decoded state.”

Avoid properties that merely repeat the implementation, such as “the parser returns whatever its private helper returns.” A property should express a requirement independently enough to catch a plausible mistake.

Nor should you overgeneralize a property. Truncating an image always changes its bytes, but it only makes the image invalid when required data is removed. Removing optional trailing padding may leave a valid image. That distinction is precisely what a format-aware test should capture.

<a id="test-matrix"></a>
## Turn the format into a test matrix

A test matrix connects each requirement to evidence. It is more useful than a list of functions that happen to execute. Start with the public contract, then choose cases that would distinguish a correct implementation from a plausible incorrect one.

For example, “the parser accepts three entities” cannot distinguish an implementation that ignores the count and always reads three records. Add empty, single-record, and maximum-count cases. Now the reader has to respect the field rather than the original demonstration's accident of size.

| Requirement | Small valid case | Exact boundary | Nearby invalid case |
| --- | --- | --- | --- |
| Image length is 32–4,096 bytes | Empty label and collection in 32 bytes | Valid payload with trailing padding to 4,096 | 31 or 4,097 bytes |
| Header has version 2 and size 32 | Reference header | All supported fields present | Version 3 or header size 31 |
| Name length counts UTF-16 units | One ASCII letter, one unit | 64 ASCII letters or 32 compass symbols | 65 ASCII letters or 33 compass symbols |
| Collection count is at most 64 | One uniquely identified record | 64 records | Count field says 65 |
| Whole requested range is available | Payload ends before the file ends | Final byte ends exactly at the file limit | Required range extends one byte beyond it |
| Nonempty payloads do not overlap | Adjacent name and array | Name end equals array start | Name end exceeds array start by a valid field-sized mutation |
| Entity IDs are nonzero and unique | IDs 1 and 2 | Maximum nonzero `uint32` remains representable | ID 0 or repeated ID 1 |
| Health is finite and within 0–100 | 50 | 0 and 100 | Negative value, value above 100, or NaN |

The maximum text cases show why one boundary can need multiple representations. Thirty-two compass symbols are 32 code points but 64 UTF-16 code units. A validator based on the wrong unit might pass all-ASCII cases while accepting oversized supplementary text.

### Keep other requirements valid

To test the count limit, put 65 in the count field of an otherwise ordinary image. The decoder checks the count before attempting array access, so the intended result is the count-limit error. To test a truncated range, keep the count legal and remove required data instead.

This distinction matters when diagnosing a regression. An image can violate several rules, but the parser usually reports the first failed check. A test that changes both version and range cannot establish which check rejected it unless it asserts the intended diagnostic and the validation order is part of the contract.

For a focused boundary test, change one relevant fact. For a robustness test, multiple simultaneous faults can be useful. Label the test according to its purpose so a future maintainer does not “repair” a multi-fault experiment into something else.

### Separate format limits from fixture-generator limits

The decoder accepts images up to 4,096 bytes. The fixture encoder permits only 0–256 bytes of deliberately inserted padding. These are different interfaces with different purposes. The encoder's smaller convenience limit does not reduce the decoder's declared image limit.

To construct a valid 4,096-byte image, append unused bytes to a valid small image until it reaches that length. The existing payload offsets remain valid. Append one more byte and the image-size rule must reject it. This challenges the decoder without requiring the fixture generator to support every valid storage arrangement.

Likewise, a serializer may always put the name before the array, but the format allows either ordering when ranges are valid and separate. A complete test strategy should eventually include a valid array-before-name fixture. Do not accidentally turn a generator preference into a format requirement.

<a id="independent-oracles"></a>
## Construct an answer independently

An **oracle** is the evidence that tells a test what the correct answer is. It can be a manually derived byte sequence, a known producer-side value, or another implementation with sufficiently independent assumptions. Calling the function under test twice is not an independent oracle.

The baseline header provides a compact example. Its first eight bytes are:

```text
4f 42 53 32 02 00 20 00
```

Read these without using the fixture encoder: four ASCII bytes spell `OBS2`; `02 00` is little-endian version 2; `20 00` is little-endian header size 32. If a refactor accidentally uses big-endian integers for both encoding and decoding, an encode/decode round trip can pass, but this literal prefix check will fail.

The first entity gives a second independent check:

```text
0a 00 00 00 | 00 00 af 42 | 00 00 80 3f | 00 00 00 40
ID 10      | health 87.5 | x 1          | y 2
```

Check the actual decoded fields against those four expected values. Also check where the record occurs: baseline offset 48, not an offset obtained by asking the same encoder where it wrote the record. The [advanced tests](../tests/test_advanced_lab.py) retain these literal slices.

### Use round trips for the right question

Round trips remain valuable. They test whether supported values survive serialization and parsing according to the chosen representation. Their limitation is shared implementation error, not uselessness.

For binary32 fields, account for quantization. A Python float supplied to the encoder may not be exactly representable as binary32. After packing and decoding, compare against the expected binary32 value, rather than demanding that every arbitrary wider input survive unchanged. The decimal value `0.1` is the obvious example from [Chapter 17](17-comparing-captures.md#numeric-policy).

For text, specify whether the round trip preserves the exact code-point sequence or a normalized form. `OBS2` preserves the sequence. A test should not normalize its expected string merely because two forms appear similar on screen.

### Turn a presentation bug into a regression test

Consider these two valid binary32 encodings: `cdcccc3d` and `cecccc3d`. The comparator correctly detects unequal values. However, a six-significant-digit display renders both as `0.1`, producing an apparently self-contradictory change report.

A useful regression test decodes the two literal encodings, confirms that the values differ, and requires this visible transition:

```text
1.health:0.100000001->0.100000009
```

The test should also cover ordinary inspection output, because fixing the comparator alone would leave an inspector displaying the same ambiguity. The updated lab uses nine significant digits in both places. Run the byte-to-display demonstration with:

```sh
python labs/deep_dive.py precision
```

This is a behavioral requirement: distinct supported binary32 values must remain distinguishable in the diagnostic output. It does not require any particular private formatting helper or class structure.

<a id="mutation-design"></a>
## Design mutations that reach useful code

Purely random files often fail at the magic or length check. That exercises rejection at the front door, but tells you little about string decoding or record iteration. Start some experiments from valid fixtures so mutations can reach deeper layers.

For `OBS2`, divide the input into the fixed header, name bytes, entity records, and unused space. Choose a mutation family deliberately:

| Family | Example | What it challenges |
| --- | --- | --- |
| Header mutation | Change the name offset to 31 | Payloads cannot borrow header bytes |
| Range mutation | Keep count 3, remove the final byte | Complete array availability |
| Unicode mutation | Replace the name with an isolated high surrogate and adjust its count | Strict decoding after range validation |
| Identity mutation | Copy ID 10 into a second record | Duplicate detection before map construction |
| Numeric mutation | Put infinity in x | Non-finite rejection outside the health range rule |
| Valid transformation | Move the name and update its offset | Acceptance of a different valid layout |
| Ignored-space mutation | Change only trailing padding | Excluded bytes do not affect semantic values |

Some mutations must update related fields to remain informative. If you lengthen a name but leave its count unchanged, you may merely add ignored bytes. If you change a text count to include an extra unit, the array might now overlap the name. Decide which invariant you mean to test and inspect the resulting ranges.

### What the supplied deterministic corpus does

The advanced suite currently makes 512 mutated baseline images using seed `19020`, changing one to four randomly selected positions in each case. Selection can revisit the same position or write the byte already present; this is a bounded mutation experiment, not a promise of 512 unique malformed files.

It also tries 128 arbitrary byte strings using seed `19021`. Each decode must either return a valid result or raise the documented `DecodeError`. Unexpected exceptions propagate and fail the test. Successful mutated decodes are checked for the format's ID, count, text, finite-number, and health invariants.

Retain the actual failing bytes when a failure occurs. A seed is useful, but the generated sequence also depends on the generator logic and environment. The smallest self-contained reproduction is usually a byte fixture plus its expected result, with the seed and original case index as supplementary context.

### Bound work as well as input size

The decoder's image-size, name-length, and entity-count limits constrain its work. The section example similarly caps metadata at 96 sections before sorting or examining ranges. These limits are explicit choices in the teaching tools, not measurements of the largest practical real capture.

In a future parser with compressed content or linked traversal, a small input can still imply substantial work. Bound expanded bytes, visited nodes, nesting depth, or total requests as appropriate. A test that merely checks the source file's length would not cover those separate costs.

Use a separate process and an external time budget when testing code that might hang. Catching an exception inside the same process does not stop an infinite loop. The command-line tests use subprocess timeouts; the existing in-process mutation loops rely on the decoder's small, explicitly bounded operations.

<a id="behavioral-properties"></a>
## Test comparison and history as public behavior

The consumer can violate the investigation's meaning even when every input record decodes correctly. Write properties around the promised behavior rather than duplicating the implementation's loops.

Useful comparison properties include identity, permutation invariance, and deliberate reversal. Comparing a snapshot to itself produces no additions, removals, or field changes. Reordering distinct-ID records preserves its semantic view. Reversing a valid comparison exchanges additions and removals and reverses field transitions, without claiming chronological order.

Each property has a boundary. Reordering records is harmless only because the schema declares their order irrelevant. Sorting a sequence of timestamped events would erase history. Reversal is valid for the stateless comparator; the replay monitor can still reject an older generation. Apply the property at the correct interface.

### Build a stateful counterexample

Suppose a monitor resets its progress time on every successful decode. A test containing only increasing generations passes. A test containing one valid sample followed by duplicates at 100 and 101 ms exposes the error: the second duplicate must become `no-progress`, measured from the original acceptance.

Now add invalid and conflicting samples between those times. The accepted snapshot and progress time must remain unchanged. Inspect those fields, not just the returned status. A buggy monitor could correctly return `inconsistent` while having already overwritten the accepted content.

Use the [full state trace](18-polling-and-replay.md#state-walkthrough) as a concrete oracle. The helper prints all state after each input:

```sh
python labs/deep_dive.py trace
```

At 60 ms the accepted generation is still 4 and the progress time is still 40 ms. At 200 ms those values remain 4 and 40. Only the last-observation time advances to the current event time.

### Include rejected clock input

A decreasing timestamp is a caller error, not an unavailable source. Reject it before changing any monitor state. Tests should also try negative values, noninteger values, NaN, and booleans. In Python, booleans behave like integers in many contexts, but the replay contract explicitly excludes them as times and budgets.

For a real asynchronous backend, additional tests would need to simulate delayed completion, cancellation, source closure, and process restart. Those are outside this synchronous replay implementation. Keep them on the acquisition adapter's acceptance list rather than claiming that a synthetic trace already proves them.

<a id="failure-triage"></a>
## Diagnose the failure before changing code

A failed command is not always a failed decoder. Read the exit status and the first relevant diagnostic before deciding what to repair.

| Observation | Likely investigation layer | First useful action |
| --- | --- | --- |
| Python cannot open the script | Working directory or path | Confirm the repository root and exact filename |
| Test module cannot import the lab | Test invocation/environment | Use the documented discovery command |
| Documented malformed input raises `DecodeError` | Expected input rejection | Check whether the test expected that error |
| A valid boundary input is rejected | Format implementation or fixture construction | Hand-check its extents and invariants |
| Unexpected `IndexError` or `struct.error` escapes | Missing validation or error conversion | Retain bytes and locate the first unchecked read |
| Compare succeeds but hides a difference | Output contract | Inspect raw values and formatting separately |
| Local link checker fails | Documentation navigation | Repair the exact file or fragment destination |

Do not make a test pass by changing `except DecodeError` into `except Exception`. That would classify programming errors, such as an accidental attribute lookup, as normal input rejection. Similarly, zero-filling a short record can hide the missing-data condition the test was designed to expose.

### Minimize while preserving the cause

When a mutation exposes a bug, first save the original failing image. Then remove unrelated changes one at a time and rerun the focused test. Keep each simplification only if the same failure remains. A smaller image that now fails at the magic check is not a minimized reproduction of a duplicate-ID bug.

Record the relevant offsets and expected rule. For example: “A 96-byte valid baseline, with the second entity's ID at offset 64 changed to 10, must reject duplicate identity.” That description is easier to review than an unexplained hex blob, but keep the blob or construction code as the exact artifact.

Add the reproduction as a named test before broadening the fix. After the focused test passes, run the surrounding suite to check related behavior. There is no benefit in repeatedly rerunning an unchanged suite after it has passed unless another change or unresolved concern justifies it.

<a id="cli-contract"></a>
## Verify the command-line boundary

The command line is the interface many readers will actually use. Its behavior deserves tests that reflect their workflow: create fixtures, inspect them, compare them, and handle a missing or invalid input.

The lab uses status 0 for success, 1 for an operational or input failure, and 2 for an argument-parser error. A comparison with no differences is still successful. A rejected image is a failure even when the exception was handled politely.

A useful failed-comparison test supplies one valid file and one invalid file, then asserts both status 1 and empty standard output. Diagnostics belong on standard error. Otherwise a script could retain a normal-looking partial report and overlook the final error. Both inputs must validate before comparison output begins.

Also confirm that refusing an existing output path preserves its bytes. Merely asserting a nonzero status misses a tool that truncates the destination before discovering the conflict. Use paths with spaces and non-ASCII characters so shell assumptions do not silently narrow the supported workflow.

Python's [`unittest` assertion documentation](https://docs.python.org/3/library/unittest.html#unittest.TestCase.assertRaises) describes assertions for expected failures. Choose the narrow exception or output condition that expresses the requirement; avoid tying tests to incidental internal call sequences.

### Read the final result honestly

Passing the suite means the tested implementation satisfied these executable cases in the recorded environment. It does not prove all layouts are supported, that every malformed input is safe, or that a device can capture a coherent live process. A test count summarizes activity, while named invariants and retained failures explain confidence.

Your handoff should identify the test command, exit status, environment, and relevant limits. Keep documentation checks separate from parser tests: correct fragments do not prove correct decoding, and correct decoding does not make a broken chapter link usable.

<a id="chapter-exercises"></a>
## Practice exercises

1. An encoder and decoder both interpret the name count as bytes. Their round-trip test passes. Construct a small independent test that exposes the shared error.
2. A mutation changes a trailing padding byte and decoding succeeds with the same semantic state. Is this a bug? What should the file hash do?
3. A monitor returns `inconsistent` for a same-generation conflict, but stores the conflicting snapshot. Which additional assertion detects the problem?
4. A failed CLI comparison returns status 1 after printing `removed=[10, 20, 40]`. Explain why checking only the exit status is insufficient and state the expected output contract.

[Worked solutions](../appendices/deep-dive-answers.md#chapter-19).

## Checkpoint

Your mutation test changes a byte and the parser still succeeds. Why is that not sufficient evidence of a validation bug? What additional fact would establish a bug?

[Check your answer](../appendices/answers.md#chapter-19).

<!-- BOOK:FOOT:START -->

[Previous: Polling and replay](18-polling-and-replay.md) · [Contents](../README.MD#table-of-contents) · [Next: A complete investigation](20-complete-investigation.md)

<!-- BOOK:FOOT:END -->
