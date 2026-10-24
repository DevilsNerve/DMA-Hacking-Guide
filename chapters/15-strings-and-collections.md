# Chapter 15: Strings and collections

<!-- BOOK:NAV:START -->

[Previous: Build a trustworthy reader](14-capstone.md) · [Contents](../README.MD#table-of-contents) · [Next: Modules, symbols, and build identity](16-modules-and-symbols.md)

<!-- BOOK:NAV:END -->

**You will learn:** how to read text without guessing its length, how to walk a collection with a bounded cost, and how to distinguish a format rule from a convenient assumption.

**Before you start:** complete the first [capstone](14-capstone.md), or be comfortable with exact reads, field offsets, and count limits. The [advanced lab](../labs/advanced.md) supplies the new examples.

## In this chapter

Read the opening sections for the basic model, then use these detailed references as you work:

- [Walk through every byte of an observation](#byte-walkthrough)
- [Choose a text-decoding contract](#unicode-decisions)
- [Prove a variable-length range fits](#range-proof)
- [Handle arrays, lists, and linked structures](#collection-layouts)
- [Separate live lifetime from stored layout](#live-collections)
- [Diagnose three malformed observations](#diagnostic-lab)
- [Practice exercises and worked answers](#chapter-exercises)

## Move beyond one scalar

A health field needs a fixed number of bytes. A player name and an inventory require more information: an encoding, a length convention, a location, and rules for the elements. Getting the pointer right is only the beginning.

Imagine an observation named `Pilot 🧭` containing three entity records. Our second lab stores that observation in a documented file format called `OBS2`. It uses file offsets instead of process pointers. This keeps the text and collection problems reproducible while making the address context explicit. It is a separate format from the first lab, not a real Unity layout.

<a id="text-units"></a>
## Ask what the length measures

The same text can have several useful lengths:

| Measurement for `Pilot 🧭` | Value | Why it differs |
| --- | ---: | --- |
| Unicode code points | 7 | Six basic characters plus the compass |
| UTF-16 code units | 8 | The compass uses a pair of 16-bit units |
| UTF-16 little-endian bytes | 16 | Each code unit occupies two bytes |
| UTF-8 bytes | 10 | The compass occupies four bytes in UTF-8 |

Do not replace “code unit” with “visible character” in a schema. A displayed character can contain multiple code points. Python's [Unicode HOWTO](https://docs.python.org/3/howto/unicode.html) explains the distinction between text and encoded bytes.

Run this self-contained example:

```python
text = "Pilot \U0001f9ed"
encoded = text.encode("utf-16-le")
print(len(text), len(encoded) // 2, len(encoded))
print(encoded.decode("utf-16-le", errors="strict") == text)
```

Expected output is `7 8 16`, followed by `True`. The escape is the compass character; it also lets you type the example without an emoji keyboard.

## Decode the exact range

Our header stores a UTF-16 code-unit count. The reader first checks that the count is at most 64, calculates `count * 2`, verifies that range lies inside the image, then decodes exactly those bytes as UTF-16 little-endian.

There is no terminator in this format. Searching for a zero byte would be wrong: the ordinary letter `P` already contains one in UTF-16 little-endian (`50 00`). A format with a two-byte terminator needs a search aligned to code-unit boundaries and a documented maximum length.

A strict decoder rejects an isolated surrogate or a truncated code unit. Replacing malformed input with a replacement character can be useful for a best-effort preview, but it changes the observation. If you offer that preview, retain the failure status and original bytes separately. The lab rejects malformed text.

## Read a collection in a deliberate order

An `OBS2` entity occupies sixteen bytes: a nonzero `uint32` ID, a binary32 health value, and two binary32 coordinates. The header gives a count and a file offset for the array.

The decoder follows this order:

1. Verify the fixed header and supported format version.
2. Check the count against the format's limit of 64 entities.
3. Calculate the array's byte length using the documented sixteen-byte stride.
4. Verify that the whole array exists and does not overlap the name or header.
5. Decode each record and validate its values.
6. Reject duplicate IDs because later comparison relies on unique identity.

In a native collection, capacity and count may be different fields. Capacity describes storage, while count identifies logically present elements. Reading every capacity slot can decode unused or stale entries. Here, the format has only a count, so there is no implied spare capacity.

## Two kinds of bounds

An address-range check prevents reading outside the supplied image. A work limit prevents a technically in-range input from asking your program to do unreasonable work. Both matter.

For example, a large capture may contain room for millions of records. A tool intended to inspect a small diagnostic table should still have an explicit element budget. A linked structure needs a node budget and cycle handling; a nested structure also needs a depth budget. A bounded string length does not bound the total cost of thousands of strings.

## Deeper detail: identity and display text

Use the entity ID as the comparison key in this lab. Names are display data: two objects can share a name, and one object can change its name. Likewise, array position is storage order, not identity.

Unicode normalization can make visually equivalent text easier to search, but normalized text is a derived view. Preserve the original decoded value when byte identity matters. Do not normalize a binary identifier or silently use normalized display names as unique keys.

The lab also rejects overlapping active payload ranges. That is a rule of `OBS2`, not a universal rule for memory: real structures can legitimately share storage or reference the same object. Validation should enforce the actual schema rather than assumptions copied from another format.

## Try it

```sh
python labs/advanced_lab.py demo
```

Read the [layout table](../labs/advanced.md#format) and locate the name length, name offset, count, and array offset. Explain which values use bytes and which use elements. Then inspect the malformed-string test in the [test suite](../tests/test_advanced_lab.py).

<a id="byte-walkthrough"></a>
## Walk through every byte of an observation

Start with the `before` fixture. Its first 32 bytes are the header:

```text
file offset  bytes
0000         4f 42 53 32 02 00 20 00 02 00 00 00 00 00 00 00
0010         03 00 00 00 08 00 00 00 20 00 00 00 30 00 00 00
```

The offsets at the left are hexadecimal file positions. Do not read `0010` as decimal ten; it means sixteen bytes from the start. Split the bytes by the schema, not by how the viewer happens to wrap its lines:

| Range, end excluded | Raw bytes | Interpretation |
| --- | --- | --- |
| `[0x00, 0x04)` | `4f 42 53 32` | Four identity bytes spelling `OBS2` |
| `[0x04, 0x06)` | `02 00` | Version 2 |
| `[0x06, 0x08)` | `20 00` | Header size `0x20`, or 32 |
| `[0x08, 0x10)` | `02 00 00 00 00 00 00 00` | Generation 2, stored in eight bytes |
| `[0x10, 0x14)` | `03 00 00 00` | Three entity records |
| `[0x14, 0x18)` | `08 00 00 00` | Eight UTF-16 code units |
| `[0x18, 0x1C)` | `20 00 00 00` | Name begins at file offset 32 |
| `[0x1C, 0x20)` | `30 00 00 00` | Entity array begins at file offset 48 |

The interval notation `[start, end)` includes `start` and excludes `end`. Its size is exactly `end - start`. Using this convention avoids asking whether “ends at 48” means byte 48 exists in the name or the next region starts there.

The name occupies `8 * 2 = 16` bytes, so its interval is `[32, 48)`. The entity array occupies `3 * 16 = 48` bytes, so its interval is `[48, 96)`. The ranges touch at 48 but do not overlap. The image length is exactly 96, so the final requested byte is at offset 95.

The name bytes are:

```text
50 00 69 00 6c 00 6f 00 74 00 20 00 3e d8 ed dd
```

The first six two-byte units describe `P`, `i`, `l`, `o`, `t`, and a space. The final four bytes form a surrogate pair. Interpreted as little-endian units, they are `0xD83E` and `0xDDED`, which together represent the compass at `U+1F9ED`.

For this example, the supplementary code point minus `0x10000` is `0xF9ED`. Split that value into its upper and lower ten bits: `0x3E` and `0x1ED`. Adding the high- and low-surrogate bases gives `0xD83E` and `0xDDED`. This arithmetic explains why one code point needs two units here; a single high surrogate is not a complete encoded character. The formal encoding rules are in the [Unicode core specification](https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/).

The first entity starts at file offset `0x30`:

```text
0a 00 00 00  00 00 af 42  00 00 80 3f  00 00 00 40
ID 10        health 87.5  x 1.0        y 2.0
```

Its health is at `0x30 + 0x04 = 0x34`. The second entity's health is at `0x30 + 1 * 0x10 + 0x04 = 0x44`. The third entity's health is at `0x54`. The multiplication belongs to the array stride; the final addition belongs to the field within one element.

An off-by-one index of 3 would select an imaginary fourth entity at offset `0x60`, exactly where the valid file ends. The fact that this address is a clean multiple of sixteen does not make the record present.

<a id="unicode-decisions"></a>
## Choose a text-decoding contract

Before writing a string helper, write its contract in plain language. For `OBS2`, that contract is: “Read a bounded number of UTF-16 little-endian code units from a file range, decode strictly, preserve the resulting string, and do not search for a terminator.” Each clause prevents a different mistake.

### Encoding and byte order are separate choices

An encoding label such as `utf-16-le` fixes little-endian ordering. A generic `utf-16` decoder can have different byte-order-mark behavior. Do not let a convenience default decide how a binary format is interpreted. If the format specifies a byte-order mark, define whether it belongs to the payload and whether its bytes count toward the length.

The lab requires no byte-order mark and uses the explicit little-endian decoder. If a producer puts the code point `U+FEFF` at the start of the counted text, this decoder preserves it as part of the string; it does not silently discard it as an out-of-band header. That is an observable consequence of the chosen contract.

### Terminated and counted strings fail differently

For a counted string, an excessive count or missing final byte is a range failure. A complete byte range can then fail text decoding. These are useful separate diagnoses: the source may be incomplete, or it may contain invalid text under the declared encoding.

For a terminated string, you additionally need a search policy. Define the terminator width, code-unit alignment, and maximum search length. If reading in chunks, preserve an incomplete code unit between chunks and handle an unavailable next range explicitly. Reaching the search budget without finding the terminator is not the same as finding an empty string.

The `OBS2` label may contain an embedded NUL because its schema uses a count. A terminal, a C-string API, or an export format may treat that character specially. Keep decoding and presentation separate: the decoder preserves valid data; a display layer can escape control characters without pretending they were absent.

### Malformed text needs an explicit result

An isolated high surrogate, an isolated low surrogate, and a high surrogate followed by an unrelated unit are distinct malformed sequences. The fixture parser reports a controlled decode error for these cases. It does not reinterpret the bytes as UTF-8 or Latin-1 merely because that alternate decoder would accept them.

If an exploratory viewer offers a replacement-character preview, label the preview and retain the original failure. Otherwise two different malformed inputs may collapse to the same displayed string and appear identical. A preview answers “what can be shown,” while a strict decode answers “does this payload satisfy the declared format?”

### Display equality is not identity

The strings `\u00E9` and `e\u0301` can look alike while containing different code-point sequences. Unicode normalization provides defined transformations for certain equivalences. It is not a general correction for arbitrary malformed text, and compatibility normalization can erase distinctions that some applications care about. Consult [Unicode normalization](https://unicode.org/reports/tr15/) when choosing a policy.

For this book's comparison, labels are compared exactly after strict decoding. If you add a normalized search index, store it as a derived field. Preserve the original value and name the normalization form. Keep entity identity tied to the integer ID and session contract rather than to whichever display spelling happens to be convenient.

<a id="range-proof"></a>
## Prove a variable-length range fits

Suppose `available` is the image length, `offset` is a payload position, `count` is an element count, and `stride` is the byte size of one element. A robust check should establish all of the following before slicing or allocating:

1. The fields have the expected integer representation and the format version is supported.
2. The count is within the application's work budget.
3. The offset is at or after the end of the fixed header and at or before the image end.
4. The requested bytes fit in the remaining range.
5. Active ranges obey any nonoverlap rule of this format.

In fixed-width arithmetic, checking `offset + count * stride <= available` is insufficient if an intermediate operation can wrap. After establishing a positive stride and a valid offset, a useful equivalent bound is `count <= (available - offset) // stride`. Multiply only after the bound succeeds. In languages with signed integers, reject negative values before converting them to an unsigned type.

Python's arbitrary-size integers avoid that particular wraparound, but they do not make unbounded allocation or iteration acceptable. The lab caps entity count at 64 and image size at 4,096 bytes before decoding the array.

Consider a 96-byte image and an array offset of 48. There are 48 bytes left. With a stride of 16, at most three complete elements fit. A declared count of four is invalid even though the first three records can be decoded. Returning those three as a complete four-element observation would hide missing evidence.

Zero-length ranges deserve an explicit rule. `OBS2` still requires their offsets to lie between the end of the header and the end of the image. Thus a zero-count array at offset 96 is valid, while a zero-count array at offset `0xFFFFFFFF` is invalid. Another format could choose a different empty-pointer convention; the lesson is to specify it rather than rely on incidental slicing behavior.

<a id="collection-layouts"></a>
## Handle arrays, lists, and linked structures

A collection's source-language name does not determine its external layout. “List” can mean a contiguous allocation, a header pointing to an allocation, a chain of nodes, or an application-specific index structure. First identify the representation, then choose a traversal.

### Contiguous records

For a packed array, element `i` begins at `array_start + i * stride`. Validate `i < count`; using `i <= count` admits one nonexistent element. Read the complete bounded array when that makes sense for the source, then decode each record from the captured bytes. This can reduce transport calls, but it does not make a live source atomic.

The stride can exceed the sum of the fields you currently understand. Unknown fields or padding may occupy the remainder. Do not compress the stride because your decoder consumes only twelve of a sixteen-byte record. Record the full layout extent separately from the subset of fields you expose.

Conversely, do not assume every field is inline. A record may contain a pointer or an index into another table. That introduces another lookup, its own bounds, and potentially another lifetime. Document the dependency chain so the reader does not accidentally batch an address before the pointer needed to compute it has been read.

### Count and capacity

For a collection with count 3 and capacity 8, three elements are logically present. The remaining storage is not evidence of five additional objects. It may contain uninitialized bytes, old values, or reserved slots. If the format requires `count <= capacity`, validate that invariant; if capacity is itself unavailable, do not invent it from the allocation's apparent size.

When a collection grows, the allocation may move while the owning header stays put. A cached element pointer can therefore become stale even though the header address still resolves. A useful live test forces growth across a capacity boundary instead of changing only existing values.

### Linked and indexed structures

A linked traversal should keep a visited set, a node budget, and a termination rule. A null link may terminate one structure; a sentinel node may terminate another. A repeated address can signal a cycle, but some circular lists are intentional. The decoder must know whether that cycle is permitted and when to stop following it.

An index-based structure replaces pointer validation with index validation. If a record stores an index into a table of length `n`, check the index against `n` before computing the slot. A special “none” index must be interpreted according to the schema rather than treated as a large ordinary index.

For nested structures, track a total work budget as well as a per-list limit. Sixty-four parents each containing sixty-four children already produce 4,096 child visits. Add strings, retries, and repeated shared objects, and a seemingly small local limit can still produce a large operation.

<a id="live-collections"></a>
## Separate live lifetime from stored layout

The synthetic image is immutable while it is decoded. A live list can change between the header read and the payload read. Knowing the correct offsets does not solve that timing problem.

Imagine a live header initially containing pointer A and count 3. The producer grows the collection, installs pointer B and count 4, and frees A. A reader might observe A before the change and count 4 afterward. All arithmetic can be correct while the resulting request describes no valid collection state.

If you control the producer, use an explicit publication and lifetime protocol. An immutable published buffer retained until readers finish is one design. A generation protocol combined with appropriate memory ordering and retention can be another. A plain integer counter does not by itself stop an allocation from disappearing while a reader copies it.

If you do not have such a protocol, describe your observations as best effort and test for inconsistency. Re-reading the header can detect some changes, but matching pointer and count values do not prove stability: an allocation can be replaced and its address reused between observations. This is why identity and generation belong in the analysis where available.

For a bounded retry strategy, record how many attempts were made and why each was rejected. An eventual success supports the accepted attempt; it does not erase the fact that earlier attempts were inconsistent. Returning a mixture of fields from different attempts is especially misleading. Treat the accepted observation as one unit.

The current `OBS2` decoder has no live producer, pointer-retention protocol, or thread synchronization implementation. Its generation field identifies a stored observation for comparison and replay. Keeping that boundary explicit prevents a useful file parser from being mistaken for a verified concurrent-memory reader.

<a id="diagnostic-lab"></a>
## Diagnose three malformed observations

### Case A: the name looks cut in half

You read eight bytes because the header says length 8. The result looks like `Pilo`. The raw range is available and its bytes decode successfully. This is a unit error, not a transport failure: the declared length counts UTF-16 units, so the required byte length is sixteen.

Check the schema before changing error handling. Then verify the decoded text and its raw byte range. A replacement-character setting would not repair the original mistake because the shortened range can still be well-formed text.

### Case B: the name points into the array

The header's name offset is changed to 48 while the array still begins at 48. Both ranges can fit inside the image, and the first entity's bytes may even decode as some Unicode string. The observation is still invalid because `OBS2` forbids overlap between nonempty payloads.

This case demonstrates why bounds checks and structural validation are separate. “Inside the file” does not mean “belongs to the expected field.” Check the intended relationships among ranges before assigning meaning to their bytes.

### Case C: the final entity is missing one byte

The header still declares three entities, but the file is truncated from 96 bytes to 95. The first two records and most of the third are present. The exact array read must fail; the parser must not pad the missing byte or silently reduce the count to two.

If a separate exploratory viewer chooses to show the first two records, label that view incomplete and keep it out of the complete-snapshot comparison path. The missing byte is evidence about availability, not a license to redefine the schema.

## A decoder review you can perform on paper

Trace each untrusted header field to the operation it controls. The name-unit count controls a multiplication and a decode length. The entity count controls a multiplication and loop bound. The two offsets control slices. The generation controls later ordering but not range validity. The version determines whether any of those interpretations are supported.

For each field, ask: what is its representation, what bound is checked before use, and what error remains visible if the check fails? This exercise is often faster than reading the entire parser line by line without a question in mind.

Finally, inspect the output boundary. The lab stores decoded text as Unicode, escapes it for console display, and preserves numeric IDs. That keeps a terminal's capabilities from deciding whether the underlying observation is valid. A future JSON or CSV exporter should likewise define its encoding and escaping rather than relying on a machine's default locale.

<a id="chapter-exercises"></a>
## Practice exercises

1. **Follow the byte ranges.** For a 112-byte relocated fixture, the name starts at 48, has eight UTF-16 units, and the array starts at 64 with three sixteen-byte entities. Write both intervals and the file offset of the third entity's y field.
2. **Choose the correct empty case.** A 32-byte image contains an empty name and zero entities. Both payload offsets are 32. Does the layout satisfy the range rules? What changes if the array offset is zero?
3. **Separate identity from presentation.** Two entity records have different IDs but the same display name. A search index normalizes both names to the same text. Should the comparison merge the entities?
4. **Explain a successful bad read.** Why can a string read from an array's bytes pass the text decoder while still being an invalid `OBS2` observation?

[Worked solutions](../appendices/deep-dive-answers.md#chapter-15).

## Checkpoint

A header says a UTF-16 name has length 8. Why can neither “read eight bytes” nor “show eight visible characters” be assumed correct?

[Check your answer](../appendices/answers.md#chapter-15).

<!-- BOOK:FOOT:START -->

[Previous: Build a trustworthy reader](14-capstone.md) · [Contents](../README.MD#table-of-contents) · [Next: Modules, symbols, and build identity](16-modules-and-symbols.md)

<!-- BOOK:FOOT:END -->
