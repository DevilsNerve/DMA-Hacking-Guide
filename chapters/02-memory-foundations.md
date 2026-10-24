# Chapter 2: Memory foundations

<!-- BOOK:NAV:START -->

[Previous: Start here](01-start-here.md) · [Contents](../README.MD#table-of-contents) · [Next: Tools and your first lab](03-tools-and-lab.md)

<!-- BOOK:NAV:END -->

**You will learn:** how bytes become values, how addresses differ, and how to follow a pointer without confusing it with an offset.

**Before you start:** read [Chapter 1](01-start-here.md). You can run the examples below in a Python interpreter.

<a id="bytes"></a>
## Bytes, hexadecimal, and types

A byte contains eight bits and can represent 256 different bit patterns. Hexadecimal is a compact way to write those patterns: each hex digit represents four bits, so one byte needs two digits. The prefix `0x` says “read this number as hexadecimal.”

| Notation | Decimal value | Useful interpretation |
| --- | ---: | --- |
| `0x10` | 16 | Sixteen bytes, if used as a byte offset |
| `0x40` | 64 | The root-pointer slot in our lab |
| `0x100` | 256 | The record's location relative to the lab base |
| `0x1000` | 4096 | A common page size, not a universal one |

Bytes do not carry their own type labels. The four bytes `00 00 AF 42` represent `87.5` when decoded as a little-endian IEEE 754 binary32 float. Decode them as an unsigned integer and you get `1118765056` instead. Both decoders can execute successfully; only the format tells you which interpretation is appropriate.

```python
import struct

raw = bytes.fromhex("00 00 AF 42")
print(struct.unpack("<f", raw)[0])  # 87.5
print(struct.unpack("<I", raw)[0])  # 1118765056
```

The `<` selects little-endian byte order and standard field sizes. `f` means a four-byte float; `I` means a four-byte unsigned integer. Avoid native-layout defaults when decoding a documented external format. See Python's [struct reference](https://docs.python.org/3/library/struct.html).

Little-endian means the least significant byte comes first: the integer `0x12345678` is stored as `78 56 34 12`. It does not reverse bits within each byte.

<a id="addresses"></a>
## Give every address a context

An address is meaningful only within an address space. Write down that context when you record one.

| Kind | Meaning | Example notation |
| --- | --- | --- |
| Process virtual address | A location as seen in one process's address space | `PID 4120: VA 0x140000100` |
| CPU physical address | A location in the platform's physical address map | `PA 0x12345000` |
| Device or bus address | An address used by a device's DMA transaction | `IOVA 0x8000 in device domain A` |
| File offset | A byte position within a particular file | `capture.bin + 0x100` |

These numbers can differ for the same underlying data. Processes can reuse the same virtual address for unrelated memory. Device mappings can translate or restrict access. Physical address maps can contain holes or device regions. A file can omit pages or include headers.

Our synthetic image deliberately uses a simple rule:

```text
file_offset = virtual_address - image_base
```

That is the lab's format contract. It is not a general rule for process dumps, executable files, or physical memory captures.

## Follow the pointer one operation at a time

In the 64-bit lab, the base is `0x140000000`. The slot at base plus `0x40` contains an eight-byte pointer whose value is `0x140000100`. The health field is twelve bytes into the record.

```text
base                         0x140000000
address of root slot         base + 0x40       = 0x140000040
value read from root slot    read_u64(slot)    = 0x140000100
address of health            record + 0x0C     = 0x14000010C
value read from health       read_f32(address) = 87.5
```

Adding an offset and reading a pointer are different operations. `base + 0x40 + 0x0C` points inside the root-slot neighborhood. It does not follow the pointer to the record.

Target pointer width matters. An eight-byte reader must not decode a four-byte target pointer by borrowing the next four bytes. The reader's own architecture does not determine the target's pointer size.

## Layout, alignment, and lifetime

A structure's fields can include padding. A compiler may align an eight-byte field differently from a four-byte field. Managed objects can also include runtime headers and references with runtime-specific representations. Reconstruct a layout from evidence for that build; do not assume source-code field order gives you byte offsets.

The lab uses a packed, explicit wire format, including an intentionally unaligned pointer field at offset `0x14`. Python decodes bytes directly. Copying this layout into an ordinary C++ struct without a packing and serialization strategy would not establish the same format.

An address that was valid a moment ago can become invalid when an object is freed, moved, or replaced. Worse, the address might be reused for another object and still be readable. A successful read proves byte availability, not object identity.

## Deeper detail: arithmetic is part of validation

Before reading `count * element_size` bytes, bound the count and check the multiplication. Before adding a field offset to a pointer, check the address range. Fixed-width arithmetic can wrap; Python integers do not wrap automatically, but the target address space still has a maximum.

Reject a null pointer before dereferencing it. Distinguish a valid zero field from an unavailable field. A float can also be NaN or infinity; range checks should explicitly reject non-finite values when the schema requires a normal measurement.

## Checkpoint

The root slot contains `0x140000100`, and health is at record offset `0x0C`. Which address do you read, and how many bytes do you request? What changes for a 32-bit root pointer?

[Check your answer](../appendices/answers.md#chapter-02).

<!-- BOOK:FOOT:START -->

[Previous: Start here](01-start-here.md) · [Contents](../README.MD#table-of-contents) · [Next: Tools and your first lab](03-tools-and-lab.md)

<!-- BOOK:FOOT:END -->
