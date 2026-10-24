# Worked exercises for Chapters 15–20

[Book contents](../README.MD#table-of-contents) · [Checkpoint answers](answers.md) · [Advanced lab](../labs/advanced.md)

These solutions explain the additional practice exercises at the end of each detailed chapter. Try the calculations and state transitions before reading the answers. The shorter chapter checkpoints retain their separate [answer appendix](answers.md).

- [Chapter 15: Strings and collections](#chapter-15)
- [Chapter 16: Modules and symbols](#chapter-16)
- [Chapter 17: Comparing captures](#chapter-17)
- [Chapter 18: Polling and replay](#chapter-18)
- [Chapter 19: Testing layouts](#chapter-19)
- [Chapter 20: Complete investigation](#chapter-20)

<a id="chapter-15"></a>
## Chapter 15: Strings and collections

### 1. Follow the byte ranges

Eight UTF-16 units occupy `8 * 2 = 16` bytes. The name interval is `[48, 64)`. Three sixteen-byte entities occupy 48 bytes, so the array interval is `[64, 112)`. They are adjacent and do not overlap.

The third entity has zero-based index 2. Its start is `64 + 2 * 16 = 96`. The y field is twelve bytes into the record, so its start is `96 + 12 = 108`, or `0x6C`. It occupies `[108, 112)`, ending exactly at the image boundary. No extra byte is required at offset 112 because the upper endpoint is excluded.

### 2. Choose the correct empty case

With a complete valid header, zero name units, zero entities, and both offsets equal to 32, the two requested ranges are `[32, 32)`. The offsets satisfy `header_size <= offset <= image_length`, and neither request consumes bytes. This is a valid empty observation.

Changing the array offset to zero violates the payload-offset rule even though the length remains zero. Empty does not mean “ignore every structural constraint.” The rule prevents header-relative or arbitrary out-of-range cursor values from acquiring a special undocumented meaning.

### 3. Separate identity from presentation

Keep the records separate. The declared identity is the entity ID within the session; a display name or normalized search key is not an alternative identity rule. Several entities can share a name, and normalization can intentionally make distinct text representations searchable together.

An interface may group search results for presentation while retaining each ID. A comparator must still match each record by the declared identity and report its fields independently. `OBS2` itself has one observation label rather than per-entity names; this question applies the same identity principle to a hypothetical richer schema.

### 4. Explain a successful bad read

Many arbitrary pairs of bytes form valid UTF-16 units. Therefore bytes borrowed from an entity array can decode as text without raising a Unicode error. Successful text decoding establishes only that the selected bytes satisfy that encoding's rules.

An `OBS2` observation must also have valid header fields, complete payload ranges, separate nonempty payloads, unique IDs, and valid numbers. A nonempty name overlapping the entity array violates the format independently of what the name bytes happen to decode into. Check structure before interpreting content.

### 5. Check a mixed label

Sixty-two copies of `A` plus one compass contain 63 code points, 64 UTF-16 units, and 128 UTF-16 bytes. The compass contributes one code point but two units. The label satisfies the 64-unit limit.

Sixty-three copies of `A` plus one compass contain 64 code points, 65 UTF-16 units, and 130 UTF-16 bytes. The label must be rejected despite having only 64 code points. A Python string-length check alone would enforce the wrong unit.

### 6. Finish a stream

The bytes `3e d8` form the high surrogate U+D83E. Before finalization, the decoder may buffer it and emit no text. At finalization, a strict decoder must reject the missing low surrogate rather than return a successful empty label.

If the contiguous bytes `ed dd` arrive before finalization, the complete pair decodes to the compass U+1F9ED. Buffering is justified by continuity of the encoded stream; it cannot repair an unavailable byte or join unrelated text fields.

### 7. Follow a different layout

The third entity starts at `32 + 2 * 16 = 64`. Its health begins four bytes later, at 68 or `0x44`, occupying `[68, 72)`. This field lies entirely within the declared array.

The name's later position is valid. The array ends at 80, exactly where the name starts, so the nonempty ranges are adjacent and do not overlap. `OBS2` does not require name-before-array ordering.

### 8. Explain an odd offset

The name occupies `[33, 49)` and the array `[49, 97)`. Both lie after the header, fit the 97-byte image, and are adjacent. The format does not impose an even or sixteen-byte-aligned payload start.

UTF-16 units begin at offsets 33, 35, 37, 39, 41, 43, 45, and 47. Each contains two bytes. Code-unit boundaries are relative to the string's declared start; imposing global even file offsets would reject this valid packed representation.

### 9. Stop a chain

A budget of 3 permits visits 0, 1, and 2, after which the next index is the end marker -1. The complete result is `[0, 1, 2]`.

A budget of 2 is exhausted before visiting node 2. The traversal must report that failure. Returning `[0, 1]` as a complete result would hide a known remaining dependency. A separate exploratory interface could display that prefix only with explicit incompleteness.

### 10. Separate sharing from a cycle

Two different paths can reach the same child in a graph that permits sharing without any path returning to an ancestor. A globally visited node can therefore mean “already processed through another branch,” not necessarily “cycle.”

Choose the algorithm according to the schema. A directed acyclic-graph traversal may distinguish active-path membership from completed nodes. The chapter's simpler chain has only one next edge per visited node, so encountering a previously visited index on that same chain identifies a cycle under its no-cycle contract.

### 11. Budget the hierarchy

There are `64 * 64 = 4,096` possible children. Each 64-unit UTF-16 label occupies 128 bytes, so the label bytes total `4,096 * 128 = 524,288`, or 512 KiB.

That excludes the child records, parent metadata, indices or pointers, request overhead, retries, and any derived output. Sixteen-byte child records alone add 65,536 bytes, or 64 KiB. Separate node, byte, depth, and request budgets capture costs that a per-label limit does not bound by itself.

### 12. Reject mixed metadata

The old capacity reserves `8 * 16 = 128` bytes. The new count asks for `9 * 16 = 144` bytes, sixteen beyond that allocation's extent. The mixed pointer/count pair describes neither complete published collection.

An adjacent readable range could let the byte request succeed, but readable bytes do not establish ownership, entity count, or a coherent publication. Even an old pointer paired with its old count still needs a lifetime guarantee if the old allocation can be released before the payload read.

[Return to Chapter 15](../chapters/15-strings-and-collections.md#chapter-exercises).

<a id="chapter-16"></a>
## Chapter 16: Modules and symbols

### 1. Check a boundary

The `data` section begins at RVA `0x2000`, with raw bytes beginning at file offset `0x800` and raw size `0x200`. For RVA `0x21F8`, the section-relative delta is `0x1F8`. Eight bytes remain in the stored extent.

Length 8 therefore maps to `0x800 + 0x1F8 = 0x9F8`, covering file interval `[0x9F8, 0xA00)`. Length 9 exceeds the raw extent by one byte and has no complete stored mapping. It remains within the section's declared virtual extent, which is why a start-address-only or virtual-only check is insufficient.

### 2. Separate two failures

A declared raw range ending at `0xA00` cannot fit a file only `0x900` bytes long. That is inconsistent metadata relative to the retained file, which the restricted mapper rejects before serving requests.

A valid section with a virtual-only tail is different: its declared stored bytes are all present, but the requested virtual bytes are not represented in the file. The first case suggests truncation or invalid metadata; the second can be an intentional property of the declared model. Neither permits silently returning zero-filled file evidence.

### 3. Follow the lifecycle

The former loaded module instance is gone. Its load context, runtime addresses, and resolved live locations must not be reused merely because the new module has the same name and base. Establish the new instance's build identity and resolve its own layout and symbols.

Immutable information about the old binary, such as its retained file's section table, can remain cached under that exact artifact identity. It is still useful for analyzing the old artifact. It cannot be relabeled as metadata for the new build without evidence that the applicable artifact is the same.

### 4. Assess the symbol claim

You can say that the tool displayed a name from the symbol data it loaded. You cannot yet say that the name correctly identifies the selected module's address or layout.

First identify the actual module build and verify the applicable binary/symbol match metadata. Then check the tool's supported load result and resolve the name again in that verified context. A familiar name is a useful clue, not an independent proof of the match.

[Return to Chapter 16](../chapters/16-modules-and-symbols.md#chapter-exercises).

<a id="chapter-17"></a>
## Chapter 17: Comparing captures

### 1. Choose an equality rule

Whole-file byte comparison reports a difference; the expected SHA-256 digest also changes for the altered fixture. A selected byte-range comparison reports a difference only if the selected range includes the changed padding.

Decoded records and the lab's normalized semantic view remain equal because they exclude unused padding. A claim about the whole application's meaning would require its own schema and context. Do not extend the lab's narrow equality result to fields it never observed.

### 2. Handle partial data

Report that ID 40's membership is unknown from the incomplete observation, or that the required comparison is unavailable. Preserve the missing-range evidence. “Not observed” is not equivalent to “removed” when the observation could not cover the relevant collection.

The current `OBS2` command takes the simpler all-or-nothing route: an unavailable required range makes decoding fail and prevents any normal comparison report. A future partial-data format would need explicit per-range or per-record availability semantics.

### 3. Evaluate a tolerance

With relative tolerance 0 and absolute tolerance 1, closeness reduces to `abs(a - b) <= 1`. The differences are 0.75, 0.75, and 1.5, so the results are true, true, and false.

This relation is not transitive. Connecting records through pairs of close neighbors can place endpoints in one group even though those endpoints are not close. A grouping algorithm needs a separately specified rule, such as distance from a chosen representative or a maximum group diameter; pairwise tolerance alone does not define an equivalence relation.

### 4. Read the displayed change

Retain the original field bytes, the decoding schema, sufficiently precise decoded values, and the chosen equality policy. Nine significant digits distinguish finite binary32 values in the lab's display, including the two adjacent values used in the chapter.

Different bytes need not imply unequal numerical values: positive and negative zero are the important counterexample. Conversely, identical short printed text does not imply equal numbers. Decide whether the question is bit equality, numeric equality, or application-level tolerance, then evaluate the retained evidence under that rule.

[Return to Chapter 17](../chapters/17-comparing-captures.md#chapter-exercises).

<a id="chapter-18"></a>
## Chapter 18: Polling and replay

### 1. Check the exact boundary

The progress time is 10 ms. At 110 ms the elapsed interval is exactly 100 ms, so the unchanged valid sample is `duplicate`. At 111 ms the interval is 101 ms, so it is `no-progress`.

Neither duplicate resets the progress time. Both update the last-observation time. The policy tests whether elapsed time is greater than the budget, not greater than or equal to it.

### 2. Separate acceptance from field change

The monitor accepts a valid higher generation and updates its progress time even if all tracked values are identical. The declared producer contract gives the higher generation its meaning as advancement.

Acceptance establishes that a valid newer generation was observed within this session's policy. It does not prove that health or position changed, that every intermediate update was seen, or that the observation is only a particular number of milliseconds old at the producer.

### 3. Handle a long request

One bounded policy allows one in-flight request and skips missed nominal ticks. For a 10 ms cadence with a request running from 0 to 15 ms, the next request can begin at the next future nominal tick, 20 ms. The missed 10 ms request is recorded as skipped rather than queued indefinitely.

Another policy waits 10 ms after each completion. With a request from 0 to 15 ms, the next starts at 25 ms. This gives at least the requested rest interval but does not maintain a 10 ms start cadence.

Both avoid overlapping requests and an unbounded backlog. They observe different times and should be described accordingly. A bounded queue is another possible policy, but it needs an explicit overflow and ordering rule.

### 4. Preserve the correct state

After the same-generation conflict, retain the accepted generation-4 snapshot and its original progress time. Update the last-observation time and return `inconsistent`. Do not replace selected fields from the conflicting candidate.

When the valid generation-5 input arrives, accept the entire new snapshot and set the progress time to that event's timestamp. This assumes the same declared session and a valid nondecreasing observation clock. An independently established restart would require an explicit new-session transition instead.

[Return to Chapter 18](../chapters/18-polling-and-replay.md#chapter-exercises).

<a id="chapter-19"></a>
## Chapter 19: Testing layouts

### 1. Expose the shared unit error

Construct a literal 36-byte image with a valid 32-byte header, zero entities, name offset 32, array offset 36, and name-unit count 2. The four name bytes are `3e d8 ed dd`, which encode one compass symbol as a surrogate pair.

The documented unit count requires four bytes and must decode to `\U0001f9ed`. An implementation treating the count as a byte count reads only the high surrogate's two bytes and fails strict decoding. Assert the known literal text and header field values independently of the serializer. The encoder/decoder pair cannot hide their shared unit mistake behind this manually specified input.

### 2. Interpret a successful padding mutation

This is valid behavior if the changed byte is genuinely unused padding and all other invariants still hold. The raw file differs and its expected hash changes, while the semantic state remains equal under the declared exclusions.

To establish a validation bug, show that the successful decode accepted a violated requirement, such as an overlapping active payload or duplicate ID. A changed byte alone is not such a requirement violation.

### 3. Check retained state

Save the accepted snapshot and progress time before the conflict. After `observe` returns `inconsistent`, assert that both remain unchanged. Also confirm that the last-observation time advances to the conflict's valid timestamp.

The status assertion protects classification; the retained-state assertions protect subsequent behavior. Without both, a later duplicate or comparison might operate on an incorrectly replaced snapshot even though the earlier status looked correct.

### 4. Check the whole CLI contract

The printed removal claim is unsupported because both inputs were not successfully validated. A caller or human could retain that text as a result while overlooking the nonzero status.

Require status 1, empty normal-result output, and a useful diagnostic on standard error. Validate both files before emitting the comparison. Retain the failing input for diagnosis instead of substituting an empty collection.

[Return to Chapter 19](../chapters/19-testing-layouts.md#chapter-exercises).

<a id="chapter-20"></a>
## Chapter 20: A complete investigation

### 1. Derive the health offsets

In `before`, the array begins at 48 and ID 10 is in slot 0: `48 + 0 * 16 + 4 = 52`, or `0x34`. In `after`, the array begins at 64 and ID 10 is in slot 1: `64 + 1 * 16 + 4 = 84`, or `0x54`.

The same file offset can refer to a different logical field after relocation and reordering. Offset 52 in `after` is inside the name; offset 84 in `before` is ID 40's health. Follow each file's structure and then match identity.

### 2. Handle the invalid later input

No entity-change claim is justified from that attempted pair: health changes, coordinate changes, additions, and removals all require a valid later observation under this comparator's contract. You can still describe the valid baseline and report the later input's validation failure.

Retain both actual files, their hashes, the decoder/version context, the command, its status, and its diagnostic. The reference generator's expected later values cannot substitute for bytes that were not successfully observed in the attempted comparison.

### 3. Calculate the progress age

The observed progress age is `200 - 40 = 160 ms`. This exceeds the 100 ms budget, so the valid repeated generation-4 sample yields `no-progress`.

The 60 ms event was a conflicting same-generation candidate. It updated the last-observation time but neither the accepted snapshot nor the progress time. Resetting progress on that event would reward a rejected observation and hide the absence of accepted advancement.

### 4. Identify the remaining live evidence

One plausible result is not a complete acquisition validation. Establish the actual source and session identity, address/translation context, complete-read behavior, schema match, consistency during producer changes, and behavior through unavailability and restart. Verify timeout, cancellation, and cleanup using the actual backend's contract.

Compare live values with your own producer-side evidence and measure timing under a stated clock model. Record the exact device/backend/platform configuration. Keep the synthetic parser and replay results as supporting component tests; add separate evidence for each new live claim rather than relabeling the existing fixture results.

[Return to Chapter 20](../chapters/20-complete-investigation.md#chapter-exercises) · [Back to contents](../README.MD#table-of-contents).
