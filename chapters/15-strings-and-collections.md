# Chapter 15: Strings and collections

<!-- BOOK:NAV:START -->

[Previous: Build a trustworthy reader](14-capstone.md) · [Contents](../README.MD#table-of-contents) · [Next: Modules, symbols, and build identity](16-modules-and-symbols.md)

<!-- BOOK:NAV:END -->

**You will learn:** how to read text without guessing its length, how to walk a collection with a bounded cost, and how to distinguish a format rule from a convenient assumption.

**Before you start:** complete the first [capstone](14-capstone.md), or be comfortable with exact reads, field offsets, and count limits. The [advanced lab](../labs/advanced.md) supplies the new examples.

## In this chapter

Read the opening sections for the basic model, then use these detailed references as you work:

- [Walk through every byte of an observation](#byte-walkthrough)
- [Compare six text representations](#text-casebook)
- [Choose a text-decoding contract](#unicode-decisions)
- [Decode text across chunk boundaries](#streamed-text)
- [Prove a variable-length range fits](#range-proof)
- [Resolve boundary and overlap cases](#range-casebook)
- [Handle arrays, lists, and linked structures](#collection-layouts)
- [Decode alternative valid storage layouts](#storage-layouts)
- [Walk an index chain with explicit limits](#bounded-traversal)
- [Budget nested collections](#nested-budgets)
- [Separate live lifetime from stored layout](#live-collections)
- [Review a collection replacement timeline](#replacement-timeline)
- [Diagnose three malformed observations](#diagnostic-lab)
- [Run the complete decoder casebook](#decoder-casebook)
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

<a id="text-casebook"></a>
## Compare six text representations

The compass example is a useful starting point, but one string cannot expose every unit mistake. Compare these small values before writing a generic text helper. Escapes in the table identify the exact code points independently of a terminal's font.

| Text | Code points | UTF-16 units | UTF-16 bytes | UTF-8 bytes | UTF-16 little-endian hex |
| --- | ---: | ---: | ---: | ---: | --- |
| `A` | 1 | 1 | 2 | 1 | `41 00` |
| `\u00E9` | 1 | 1 | 2 | 2 | `e9 00` |
| `e\u0301` | 2 | 2 | 4 | 3 | `65 00 01 03` |
| `\U0001F9ED` | 1 | 2 | 4 | 4 | `3e d8 ed dd` |
| `A\x00B` | 3 | 3 | 6 | 3 | `41 00 00 00 42 00` |
| `\uFEFFA` | 2 | 2 | 4 | 4 | `ff fe 41 00` |

The last row means U+FEFF followed by `A`; it is not one code point named FEFFA. The table describes Python strings and their explicitly selected encodings. It does not treat a leading U+FEFF as an external header or strip an embedded NUL.

Reproduce these values with:

```sh
python labs/collections_lab.py text
```

The [companion source](../labs/collections_lab.py) prints each exact escaped string, all four lengths, and the encoded bytes. This is a local calculation over synthetic text. It does not inspect a managed-runtime string object or assume a particular C++ string class layout.

### Storage units do not count displayed characters

The precomposed accent and the combining sequence can appear alike even though their code-point and byte counts differ. A user-facing cursor or truncation feature may need grapheme-cluster boundaries rather than individual code points. Unicode's [text-segmentation specification](https://unicode.org/reports/tr29/) defines default grapheme-cluster rules; rendering and application tailoring are separate concerns.

For the binary decoder, use the unit declared by the schema. For a display preview, choose and name the presentation rule separately. A limit of 64 UTF-16 units is a storage limit. It is not automatically a promise of 64 visible characters, screen columns, or cursor movements.

Do not derive byte size from a rendered label's width. Combining marks, supplementary characters, control characters, and font choices make that unreliable. Retain a byte length, code-unit count, and decoded string as distinct quantities when they serve different purposes.

### Test a mixed-text boundary

The name limit is 64 UTF-16 units. These four examples show how the same limit applies to different representations:

| Label construction | Code points | UTF-16 units | Expected result |
| --- | ---: | ---: | --- |
| 64 copies of `A` | 64 | 64 | Accept |
| 32 compass symbols | 32 | 64 | Accept |
| 62 copies of `A`, then one compass | 63 | 64 | Accept |
| 63 copies of `A`, then one compass | 64 | 65 | Reject name length |

A `len(text) <= 64` check would accept the fourth Python string, but it does not satisfy the format's unit budget. Compute the encoded unit count when serializing, and validate the declared count before reading when decoding.

Do not shorten an invalid input by dropping the last code unit and calling it the original observation. That can split a surrogate pair and, even when it does not, changes the input. A producer-side UI may deliberately create a shortened new label, but that is a separate transformation with its own rules.

### Strict decoding cannot discover the intended byte order

The little-endian compass bytes `3e d8 ed dd` form units `0xD83E` and `0xDDED`. Interpreting the same bytes as big-endian instead yields U+3ED8 and U+EDDD. Those units can decode without a surrogate error, but they do not represent the intended compass.

This is a stronger counterexample than merely obtaining a decode exception. “The decoder accepted it” does not establish that you selected the correct encoding. The field's declared encoding and byte order must come from the supported schema or independent producer evidence.

Likewise, try reading the embedded-NUL row as a C-style terminated string. It would appear to end after `A`, while the counted `OBS2` text includes `B`. Preserve the declared length convention through adapters and exports so that a valid observation is not silently shortened downstream.

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

<a id="streamed-text"></a>
## Decode text across chunk boundaries

A complete counted range is easiest to decode after all required bytes have been obtained. A larger source may instead supply contiguous chunks. The chunk boundary is an acquisition detail; it is not automatically a code-unit or character boundary.

Split the compass's four bytes into `3e`, `d8 ed`, and `dd`. The first chunk contains half a UTF-16 unit. After the second, you have a complete high surrogate plus half the low surrogate. Only after the third chunk do you have the complete encoded code point.

An incremental decoder can retain this incomplete state. The final lines from `python labs/collections_lab.py text` are:

```text
chunk=3e text=''
chunk=d8ed text=''
chunk=dd text='\U0001f9ed'
final text=''
```

Empty text after a chunk means the decoder has not emitted a complete character yet. It does not mean the original label is empty, and it does not permit discarding the buffered bytes. At end of input, the finalization step must detect any incomplete remaining sequence. Python documents this stateful contract in its [incremental-decoder API](https://docs.python.org/3/library/codecs.html#incrementaldecoder-objects).

### Finalization is a validation step

If the stream ends after `3e d8`, a high surrogate remains without a low surrogate. If it ends after `3e`, even the first unit is incomplete. A strict finalization must fail in either case. Silently dropping buffered bytes would turn truncation into apparently successful text.

Keep one decoder instance per continuous encoded text stream. Reusing its buffered state for another label can join unrelated bytes. Resetting it after every chunk loses valid cross-chunk sequences. Both mistakes come from treating transport chunks as if they were complete text fields.

The `OBS2` parser does not need this streaming machinery: its label is bounded to 128 bytes, and it decodes a complete validated byte slice. The companion demonstration teaches the additional state needed if you later introduce streaming. Do not add buffering complexity to a small immutable input without a reason.

### Missing bytes are not a chunk boundary

Suppose the source provides the first byte and last two bytes but cannot supply the intervening byte. Appending the available pieces and passing them to a decoder would create a byte sequence that was never observed contiguously.

Preserve the unavailable range and fail the complete-field read. An incremental decoder can bridge chunk boundaries only when the chunks are consecutive parts of the same encoded stream. It cannot reconstruct missing input or establish that two separate live reads came from one coherent publication.

For a terminated UTF-16 string, also align the terminator search to units relative to the declared string start. A zero byte is not a two-byte terminator. At an odd file offset, valid two-byte units still start at that odd offset and every two bytes afterward; global even file addresses are not the alignment rule.

### Keep raw, decoded, and searchable values separate

A useful text result can retain the source byte range, encoding, declared units, strict decode status, original decoded text, and an optional derived search key. The search key should record the transformation that produced it.

For example, NFC normalization can bring the two accent representations into a common canonical form. Compatibility normalization can make additional changes, such as converting the single ligature U+FB01 into `fi`. Choose a form according to the search requirement and preserve the original text. The [normalization specification](https://unicode.org/reports/tr15/) distinguishes those equivalences.

Neither normalization nor a replacement-character preview repairs unavailable bytes. Neither should redefine numeric entity identity. When exporting to JSON, escaped Unicode can represent the same string; when displaying in a terminal, escaped controls can preserve otherwise invisible distinctions. Record transformations without confusing presentation with a new source observation.

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

<a id="range-casebook"></a>
## Resolve boundary and overlap cases

Practice range checks independently of text decoding. For a 96-byte image, a 32-byte header, and a sixteen-byte entity stride, the following array requests illustrate the format's policy. Assume the other fields satisfy their own rules.

| Array offset | Count | Requested interval | Range result |
| ---: | ---: | --- | --- |
| 32 | 0 | `[32, 32)` | Valid empty range |
| 96 | 0 | `[96, 96)` | Valid empty range at image end |
| 97 | 0 | Outside image | Reject the offset |
| 31 | 0 | Inside fixed header | Reject the offset |
| 48 | 3 | `[48, 96)` | Valid exact fit |
| 49 | 3 | `[49, 97)` | Reject one missing byte |
| 48 | 4 | `[48, 112)` | Reject incomplete array |
| `0xFFFFFFFF` | 0 | Outside image | Reject despite zero count |

Notice that offset 49 fails here because the range extends past byte 96, not because 49 is odd. This packed file format has no alignment requirement for payload starts. With enough bytes and nonoverlapping ranges, an odd start is valid.

### Use the actual overlap predicate

For two nonempty half-open intervals `[a, a+n)` and `[b, b+m)`, overlap exists when:

```text
max(a, b) < min(a + n, b + m)
```

Adjacent intervals have equal endpoints at the meeting point, so the strict inequality is false. The `OBS2` decoder first establishes bounded extents and applies this relationship only when both lengths are nonzero.

For a name in `[32, 48)`, an array beginning at 48 is adjacent and valid. An array beginning at 47 overlaps one byte. An empty name positioned at 48 consumes no bytes and does not overlap an array starting there, although its offset must still satisfy the payload-offset rule.

This overlap restriction belongs to `OBS2`. A different object model can deliberately alias buffers or refer to shared strings. Reusing this predicate as a universal “memory validity” rule would reject legitimate shared storage. First state which regions must be disjoint under the actual schema.

### Bound before multiplying

For a fixed-width implementation, consider a malicious count of `0x10000000` and stride 16. Their mathematical product is `0x100000000`, one beyond the largest `uint32`. Unchecked 32-bit multiplication can wrap it to zero and make an incomplete array look like a harmless empty request.

The teaching decoder rejects counts above 64 before multiplying. That limits entity payloads to `64 * 16 = 1,024` bytes. The name cap similarly limits text to 128 bytes. Their maximum active payload plus the 32-byte header is 1,184 bytes, while the separate 4,096-byte image cap also permits unused gaps and trailing bytes.

Those limits answer different questions. The image cap bounds supplied input; field limits bound supported work and representation; range checks prove the requested data is actually present. None should silently replace the others when porting the parser.

### Respect validation order

The decoder validates overall image length, header identity/version/size, count and name-unit budgets, payload extents, overlap, strict text, and entity fields. An input with count 65 and a malformed name will fail the count limit before reaching text decoding.

Use one primary defect per diagnostic exercise when you want to establish a particular check. Multiple faults are useful for robustness tests, but the first reported error does not prove that later validators ran. A clear failure matrix records the intended failing invariant rather than merely asserting that some exception occurred.

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

<a id="storage-layouts"></a>
## Decode alternative valid storage layouts

A decoder should follow the format, not the fixture generator's favorite ordering. The normal encoder writes the name before the entity array. The `OBS2` schema permits another ordering as long as the header points to complete, nonoverlapping payloads.

The companion constructs four representations of the same tracked state:

```sh
python labs/collections_lab.py layouts
```

```text
baseline bytes=96 name=32 array=48 equal=true
array-first bytes=96 name=80 array=32 equal=true
unaligned bytes=97 name=33 array=49 equal=true
reordered bytes=112 name=48 array=64 equal=true
```

Here, `equal=true` means equality under the lab's semantic view: exact decoded label and entity values matched in ID order. It does not mean identical file bytes, identical array storage order, or equality of properties outside the schema.

### Array before name

The array-first case stores its three records in `[32, 80)` and its sixteen-byte label in `[80, 96)`. The first record begins immediately after the header. The header says name offset 80 and array offset 32.

Nothing in the format requires `name_offset < array_offset`. An implementation that always treats the name's end as the array start would fail this valid layout. Follow each declared range independently, then enforce their actual relationship.

The third record's health starts at `32 + 2 * 16 + 4 = 68`, or `0x44`. This differs from the baseline third health offset `0x54`. The same field calculation works because it uses the declared array start and stride rather than a remembered absolute offset.

### Unaligned payloads

One padding byte moves the name to offset 33 and the array to offset 49. The name occupies `[33, 49)` and the array `[49, 97)`. Both ranges fit, are adjacent, and decode to the same values.

The file format permits this. A native structure access strategy might impose stronger alignment requirements, but those are implementation concerns to solve without inventing a new file-format restriction. Read bytes and decode the explicitly specified fields rather than assuming that a cast to a host-language object is valid.

This example also clarifies UTF-16 alignment: the first unit begins at offset 33, the next at 35, and so on. Each unit still contains two bytes. “Aligned to a code-unit boundary” means relative to this payload's start, not necessarily an even absolute file offset.

### Three collection representations that need different reads

Do not generalize the inline `OBS2` array into every native collection. Consider three separate hypothetical schemas for three entities:

| Representation | Initial storage | Additional interpretation |
| --- | --- | --- |
| Inline sixteen-byte records | 48 bytes contain all three records | Decode fields at each sixteen-byte stride |
| Array of three eight-byte pointers | 24 bytes contain three target addresses | Validate and read each referenced record under its own lifetime |
| Separate arrays for IDs and fields | Each array has its own address and field stride | Establish their count, correspondence, and shared snapshot contract |

In the pointer-array case, reading 24 bytes does not obtain the records themselves. In the separate-array case, a valid health array is insufficient if the corresponding ID array came from another generation. The logical phrase “three entities” does not specify physical representation or consistency.

Likewise, a source-language string can use inline small-string storage, a pointer/length pair, or a managed object whose fields depend on runtime and build. Establish that representation from the supported ABI, symbols, or controlled producer evidence. There is no universal “string offset” derivable merely from the language name.

<a id="bounded-traversal"></a>
## Walk an index chain with explicit limits

A packed array has direct element arithmetic. A linked structure adds a dependency at every node: the next location comes from the current node. To make that behavior executable without inventing live-pointer guarantees, the companion includes a separate immutable index-table exercise.

The table stores one next index per slot. Valid indices are `0` through `len(table) - 1`. The value `-1` is the only end marker. Cycles are forbidden in this exercise, the table is limited to 1,024 entries, and the caller supplies a visit budget from 0 through 1,024. This is not an additional `OBS2` payload layout.

For the table `(1, 2, -1)` and start index 0:

| Step | Current index | Recorded visit | Next index |
| ---: | ---: | --- | ---: |
| 1 | 0 | `[0]` | 1 |
| 2 | 1 | `[0, 1]` | 2 |
| 3 | 2 | `[0, 1, 2]` | -1 |
| Stop | -1 | Return the complete order | No further read |

A budget of 3 permits this chain. A budget of 2 must report exhaustion before visiting index 2; it must not return `[0, 1]` labeled as the complete chain. An empty table with start `-1` and budget 0 is valid because no node is requested.

### Validate before indexing

The traversal checks the current value's integer type, handles the documented sentinel, verifies its range, checks for a repeated index, and checks the visit budget before accessing the table entry. The order makes each next-index read conditional on valid context.

This matters in languages where a negative index can have another meaning. Python's `table[-1]` selects the last element; the exercise's sentinel must therefore be recognized before indexing. Other negative values are invalid, not alternate ways to address the table. Booleans are also rejected as indices despite Python's integer relationship.

For table `(3, -1)` starting at 0, the first node leads to index 3, which is outside the two-entry table. The failure is an invalid link. Reading whatever happens to lie after the table would not be a valid traversal strategy.

For table `(1, 0)`, the path is `0 -> 1 -> 0`. Encountering 0 a second time identifies a cycle in this single chain. A larger node budget does not make that cycle valid; the structure's termination contract forbids it.

### Run success and failure paths

```sh
python labs/collections_lab.py traversal
```

```text
PASS chain order=[0, 1, 2]
PASS empty order=[]
PASS cycle cycle at index 0
PASS invalid-link index out of range: 3
PASS budget visit budget exhausted
checks=5 passed=5 failed=0
```

Each failed traversal is a successful demonstration when its diagnostic matches the expected rule. The demonstration returns status 0 when all five expectations hold. The reusable `walk_chain` function raises `TraversalError` for a rejected input and never returns a partial order as a complete result.

### Do not confuse shared nodes with cycles in other structures

The visited-set rule above applies to one chain. A graph can legitimately let two parents reference the same child without containing a cycle. A graph traversal must distinguish a node already processed through another branch from a node encountered again on the active path, according to the graph's declared rules.

Similarly, a circular list may intentionally terminate when traversal returns to its sentinel. Rejecting every repeated address would be wrong for that structure. Document the sentinel, allowed sharing, cycle policy, and output multiplicity before choosing the algorithm.

For live pointers, add address-space validation and object lifetime to these index checks. The same address can be reused for a different allocation. A set of previously seen integers alone cannot establish that the objects remained stable during a live walk.

<a id="nested-budgets"></a>
## Budget nested collections

A limit on each individual collection does not necessarily bound a whole operation to a useful size. Imagine a different schema containing 64 parents, each with 64 children. That permits 4,096 child visits. If every child has a 64-unit UTF-16 label, the label payload alone can occupy `4,096 * 128 = 524,288` bytes, or 512 KiB.

If each child also has a sixteen-byte record, those records add 65,536 bytes, or 64 KiB. This is already 576 KiB before parent metadata, lookup tables, unavailable reads, or retry overhead. This calculation describes a hypothetical nested format; one `OBS2` image does not encode that hierarchy.

Define budgets at the operation level as well as the field level:

| Budget | What it limits | Why a local count is insufficient |
| --- | --- | --- |
| Total node visits | Traversal work across the hierarchy | Many individually small lists can accumulate |
| Total requested bytes | Acquisition and retained payload volume | Strings and indirect buffers vary in size |
| Nesting depth | Recursive descent and stack growth | A chain can be deep without having broad child lists |
| Request count | Source operations, including failed attempts | Tiny or repeatedly unavailable reads can dominate |
| Retry count or elapsed budget | Repeated attempts to obtain consistency | A changing producer can prevent completion indefinitely |

Charge work according to the contract. If the byte budget measures requested bytes, a failed source request still consumed that request allowance. If the node budget measures visits rather than unique objects, revisiting a shared node consumes work even when its identity was previously seen.

Caching can reduce repeated reads, but it needs a lifetime and version key. A cached string from the same immutable image can be reused under that image's identity. Reusing it across live collection replacements without source evidence can return old display text with a new entity record.

When a budget is exhausted, report the unfinished scope. A complete-snapshot consumer should reject that incomplete observation. An exploratory interface may show a bounded prefix if it labels the prefix and never treats unseen children as absent. The output's completeness status must survive beyond the traversal function.

<a id="live-collections"></a>
## Separate live lifetime from stored layout

The synthetic image is immutable while it is decoded. A live list can change between the header read and the payload read. Knowing the correct offsets does not solve that timing problem.

Imagine a live header initially containing pointer A and count 3. The producer grows the collection, installs pointer B and count 4, and frees A. A reader might observe A before the change and count 4 afterward. All arithmetic can be correct while the resulting request describes no valid collection state.

If you control the producer, use an explicit publication and lifetime protocol. An immutable published buffer retained until readers finish is one design. A generation protocol combined with appropriate memory ordering and retention can be another. A plain integer counter does not by itself stop an allocation from disappearing while a reader copies it.

If you do not have such a protocol, describe your observations as best effort and test for inconsistency. Re-reading the header can detect some changes, but matching pointer and count values do not prove stability: an allocation can be replaced and its address reused between observations. This is why identity and generation belong in the analysis where available.

For a bounded retry strategy, record how many attempts were made and why each was rejected. An eventual success supports the accepted attempt; it does not erase the fact that earlier attempts were inconsistent. Returning a mixture of fields from different attempts is especially misleading. Treat the accepted observation as one unit.

The current `OBS2` decoder has no live producer, pointer-retention protocol, or thread synchronization implementation. Its generation field identifies a stored observation for comparison and replay. Keeping that boundary explicit prevents a useful file parser from being mistaken for a verified concurrent-memory reader.

<a id="replacement-timeline"></a>
## Review a collection replacement timeline

Consider a hypothetical native collection header with a buffer pointer, logical count, capacity, and publication generation. These are illustrative fields, not offsets copied from a particular runtime. Each element occupies sixteen bytes.

At first, the header describes pointer `0x2000`, count 3, capacity 8, and generation 10. The active records occupy `[0x2000, 0x2030)`, while the allocation reserves `[0x2000, 0x2080)`. Five capacity slots do not belong to the current logical collection.

The producer grows the collection to count 9, allocates capacity 16 at `0x3000`, publishes generation 12, and eventually releases the old allocation. The new active range is `[0x3000, 0x3090)`; reserved storage ends at `0x3100`.

### Identify a mixed observation

| Time | Producer action | Reader action | Consequence |
| --- | --- | --- | --- |
| t0 | Old header is current | Reads pointer `0x2000` | Has part of generation-10 context |
| t1 | Installs the new header | Reads count 9 | Combines a new count with an old pointer |
| t2 | Old storage may be released | Requests 144 bytes from `0x2000` | Request does not describe either published collection |

The old allocation reserved only 128 bytes. A mixed count of 9 asks for 144, exceeding it by sixteen. A source might report unavailability, or the following address range might happen to be readable. Successful acquisition in the latter case still would not establish a valid nine-element collection.

Even copying the old pointer and old count together is not enough if the old allocation can disappear before its payload is copied. Bounds establish arithmetic consistency; a retention protocol establishes whether those bytes still belong to the intended object.

### Define what an acceptance protocol must establish

For a producer you control, one option is to publish immutable buffers and retain them until the supported reader protocol permits release. Another design may use generations and retries together with the required memory-ordering and lifetime rules. The specific protocol must cover both the header and referenced data.

A useful review asks when publication becomes visible, what metadata identifies it, how a reader detects replacement, and when old storage may be freed. It also asks what the acquisition route guarantees about freshness and ordering. A counter copied from a cache cannot automatically prove that the referenced payload belongs to that same publication.

The synthetic `OBS2` image avoids these live races by supplying immutable bytes. Its generation field supports the comparison and replay exercises, but it is not itself an implementation of buffer retention. Preserve that distinction when reusing the file decoder in a live application.

### Keep one candidate per attempt

When an attempt fails consistency validation, discard that candidate as a complete observation. Do not retain its name, fetch the array again under a later generation, and combine them without an explicit cross-generation rule.

For example, attempt one might observe label `old` and then fail the array read. Attempt two might observe label `new` with a valid array. The accepted snapshot should come from the supported coherent attempt, not from a mixture chosen because each individual field looked valid.

Record the number and reason of rejected attempts. If the retry budget ends, report that no complete observation was established. A last-known valid snapshot can remain available to a user interface, but its identity and age should remain attached to it. [Chapter 18](18-polling-and-replay.md#state-walkthrough) shows that separation in deterministic replay.

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

<a id="decoder-casebook"></a>
## Run the complete decoder casebook

The companion packages the chapter's valid alternatives and malformed examples into a reproducible acceptance matrix:

```sh
python labs/collections_lab.py cases
```

Expected final line:

```text
checks=25 passed=25 failed=0
```

Each row shows whether the input was accepted or rejected and the actual result or diagnostic. The matrix contains empty inputs, empty-offset violations, exact and incomplete ranges, alternate layouts, overlaps, excessive counts, malformed surrogate sequences, partial units, duplicate or zero IDs, non-finite fields, mixed-text limits, embedded NUL, and a leading U+FEFF.

An expected rejection counts as a passed check. An unexpected acceptance or incorrect diagnostic makes the demonstration return status 1. This is a demonstration command that evaluates expectations; direct inspection of a malformed file still returns failure as described in the [advanced lab](../labs/advanced.md).

### Diagnose malformed Unicode at the right layer

The isolated high-surrogate case contains complete bytes `00 d8` for one unit. The range is available, but that unit cannot complete a well-formed UTF-16 string by itself. The isolated low-surrogate case uses `00 dc` and fails for the corresponding structural reason.

The high-surrogate-followed-by-ASCII case contains `00 d8 41 00`. Both units are available, but the second is not a low surrogate. The reversed compass pair `ed dd 3e d8` also fails. These are text errors after successful byte-range validation.

By contrast, the partial-unit case declares one unit but supplies only byte `3e`. The parser rejects the required two-byte range before attempting text decoding. Keep this distinction in a diagnostic report: unavailable encoded data and available malformed text require different investigations.

### Validate the collection after validating the text

A valid label does not make entity records valid. The duplicate-ID case overwrites the second entity's ID at offset 64 with 10, duplicating the first record. The zero-ID case overwrites the first ID with zero. Both violate the identity rule before any comparison map should be constructed.

The non-finite cases use literal binary32 encodings for NaN in health and positive infinity in x. The schema rejects both. Health also has a separate 0–100 bound, while coordinates have no additional range restriction in this invented format. Do not infer a universal coordinate range from the sample values.

Retain the original input and expected rule if a case behaves unexpectedly. Identify whether a change affected construction, range validation, text interpretation, entity validation, or presentation. The broader testing methodology is developed in [Chapter 19](19-testing-layouts.md#failure-triage).

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
5. **Check a mixed label.** Compare 62 copies of `A` plus one compass with 63 copies of `A` plus one compass. Give the code-point, UTF-16-unit, and byte counts, then apply the name limit.
6. **Finish a stream.** A strict incremental decoder receives `3e d8` and then reaches end of input. Should it return an empty successful label, a compass, or a failure? What if the missing low-surrogate bytes arrive before finalization?
7. **Follow a different layout.** The three entity records occupy `[32, 80)` and the name occupies `[80, 96)`. Where is the third entity's health? Does the name's position make the layout invalid?
8. **Explain an odd offset.** The name starts at 33, occupies sixteen bytes, and the three-record array starts at 49 in a 97-byte image. Are the payload ranges valid, and where do UTF-16 units begin?
9. **Stop a chain.** For links `(1, 2, -1)` starting at 0, compare visit budgets 2 and 3. Explain why returning a two-node prefix as complete would be wrong.
10. **Separate sharing from a cycle.** Two parents in a graph reference the same child. Why is “already visited” not sufficient to declare a cycle under every graph schema?
11. **Budget the hierarchy.** In the hypothetical 64-by-64 hierarchy, calculate maximum child-label bytes when each label uses 64 UTF-16 units. What work remains outside that figure?
12. **Reject mixed metadata.** The old allocation at `0x2000` has capacity 8 and stride 16, but a mixed read uses the new count 9. Calculate the requested and reserved byte counts and explain why a successful byte read would not establish a valid collection.

[Worked solutions](../appendices/deep-dive-answers.md#chapter-15).

## Checkpoint

A header says a UTF-16 name has length 8. Why can neither “read eight bytes” nor “show eight visible characters” be assumed correct?

[Check your answer](../appendices/answers.md#chapter-15).

<!-- BOOK:FOOT:START -->

[Previous: Build a trustworthy reader](14-capstone.md) · [Contents](../README.MD#table-of-contents) · [Next: Modules, symbols, and build identity](16-modules-and-symbols.md)

<!-- BOOK:FOOT:END -->
