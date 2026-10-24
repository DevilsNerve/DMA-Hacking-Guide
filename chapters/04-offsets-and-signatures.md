# Chapter 4: Offsets and signatures

<!-- BOOK:NAV:START -->

[Previous: Tools and your first lab](03-tools-and-lab.md) · [Contents](../README.MD#table-of-contents) · [Next: Acquisition](05-acquisition.md)

<!-- BOOK:NAV:END -->

**You will learn:** how to describe a location precisely, find candidate records, and distinguish a useful signature from a coincidental match.

**Before you start:** complete the valid and null-root cases in [Chapter 3](03-tools-and-lab.md).

<a id="offset-types"></a>
## “Offset” needs a reference point

An offset is a distance. It is incomplete without the thing you measure from.

| Name | Calculation | What must be known |
| --- | --- | --- |
| Field offset | `object_address + field_offset` | Correct object and layout |
| Module-relative address, often called RVA | `loaded_module_base + rva` | Correct module and build |
| File offset | `file_start + file_offset` | Correct file format |
| Relative instruction displacement | `reference_address + signed_displacement` | Instruction encoding and its reference point |

For PE images, an RVA is relative to the loaded image base; a file offset describes the on-disk layout. Section layout means they are not generally interchangeable. Microsoft's [PE specification](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format) defines the relevant terms.

A heap object's address minus a module base is just a subtraction. It does not become a stable module-relative locator because the arithmetic succeeds. Objects can be reallocated independently of modules.

## Build an offset record you can understand later

Instead of writing `health = 0x0C`, write:

```text
format: dma-book-fixture v1
root: read target-width pointer at image_base + 0x40
record identity: magic DMAL, version 1, size 32
health: float32 little-endian at record + 0x0C
valid values: finite, 0 through 100 inclusive
verified input: generated valid fixture, both pointer widths
```

This describes the whole route to the value. It also tells a future reader what must be rechecked after a change.

## Search for candidates

A byte signature is a pattern you search for. A wildcard accepts any byte at a particular position. In our fixture, this pattern looks for the magic, leaves the version bytes open, and requires the record size:

```text
44 4D 41 4C ?? ?? 20 00
 D  M  A  L       32
```

Run:

```sh
python labs/memory_lab.py scan out/first.bin --pattern "44 4D 41 4C ?? ?? 20 00"
```

The result is a candidate address. You must still decode and validate the record. In particular, a wildcarded version does not mean every version is supported.

Our scanner reports every match, including overlapping matches. It rejects an empty pattern and an all-wildcard pattern because neither provides a useful identity. Production tools should also bound pattern length, input size, scan scope, and result count.

## A candidate is not a conclusion

Use at least three kinds of evidence:

1. **Structural evidence:** the expected header, field widths, bounded counts, and pointer ranges are present.
2. **Behavioral evidence:** a controlled change in your program produces the expected change in the observed field.
3. **Lifecycle evidence:** restarting or recreating the object still resolves the correct record through a documented root.

If a signature matches two places, investigate both or report ambiguity. Selecting the first match makes results depend on scan order. If it matches nowhere after an update, report that the locator is stale; do not silently reuse yesterday's absolute address.

## Deeper detail: boundaries and instruction operands

When scanning in chunks, a pattern can start near the end of one chunk and finish in the next. Preserve the final `pattern_length - 1` bytes across **contiguous successfully read** chunks, then avoid duplicate reporting. Reset the overlap across an unreadable gap. Joining bytes from two separated ranges can invent a match that never existed in memory.

Finding an instruction is only the first step. For a relative operand, establish the operand's width, signedness, and architectural reference address. For example, a hypothetical four-byte signed displacement of `-0x20` relative to address `0x1010` resolves to `0x0FF0`. Reading it as an unsigned integer produces a different answer.

Do not generalize that example into “all pointers after signatures are four bytes.” Some instructions encode relative displacements; some data stores absolute pointers; other encodings work differently. Use the target architecture's instruction documentation or a suitable decoder.

## Revalidation after a build change

Keep the old locator with its old build identity. Create a new candidate record for the new build, repeat the controlled observations, and only then mark it supported. Hashes help identify inputs; they do not prove that your interpretation is correct.

## Checkpoint

A signature finds two identical headers. One candidate has health `87.5`; the other has health `100`. Why is “pick the realistic value” insufficient, and what experiment would help?

[Check your answer](../appendices/answers.md#chapter-04).

<!-- BOOK:FOOT:START -->

[Previous: Tools and your first lab](03-tools-and-lab.md) · [Contents](../README.MD#table-of-contents) · [Next: Acquisition](05-acquisition.md)

<!-- BOOK:FOOT:END -->
