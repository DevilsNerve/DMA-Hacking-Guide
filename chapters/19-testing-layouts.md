# Chapter 19: Testing unfamiliar layouts

<!-- BOOK:NAV:START -->

[Previous: Polling and replay](18-polling-and-replay.md) · [Contents](../README.MD#table-of-contents) · [Next: A complete investigation](20-complete-investigation.md)

<!-- BOOK:NAV:END -->

**You will learn:** how to turn layout assumptions into tests, select informative malformed inputs, and use mutation experiments without claiming they prove more than they do.

**Before you start:** understand the `OBS2` layout and its validation order in [Chapter 15](15-strings-and-collections.md). Keep the [format reference](../labs/advanced.md#format) open while reading.

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

## Checkpoint

Your mutation test changes a byte and the parser still succeeds. Why is that not sufficient evidence of a validation bug? What additional fact would establish a bug?

[Check your answer](../appendices/answers.md#chapter-19).

<!-- BOOK:FOOT:START -->

[Previous: Polling and replay](18-polling-and-replay.md) · [Contents](../README.MD#table-of-contents) · [Next: A complete investigation](20-complete-investigation.md)

<!-- BOOK:FOOT:END -->
