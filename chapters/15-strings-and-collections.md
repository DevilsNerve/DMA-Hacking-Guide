# Chapter 15: Strings and collections

<!-- BOOK:NAV:START -->

[Previous: Build a trustworthy reader](14-capstone.md) · [Contents](../README.MD#table-of-contents) · [Next: Modules, symbols, and build identity](16-modules-and-symbols.md)

<!-- BOOK:NAV:END -->

**You will learn:** how to read text without guessing its length, how to walk a collection with a bounded cost, and how to distinguish a format rule from a convenient assumption.

**Before you start:** complete the first [capstone](14-capstone.md), or be comfortable with exact reads, field offsets, and count limits. The [advanced lab](../labs/advanced.md) supplies the new examples.

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

## Checkpoint

A header says a UTF-16 name has length 8. Why can neither “read eight bytes” nor “show eight visible characters” be assumed correct?

[Check your answer](../appendices/answers.md#chapter-15).

<!-- BOOK:FOOT:START -->

[Previous: Build a trustworthy reader](14-capstone.md) · [Contents](../README.MD#table-of-contents) · [Next: Modules, symbols, and build identity](16-modules-and-symbols.md)

<!-- BOOK:FOOT:END -->
