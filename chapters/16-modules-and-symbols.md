# Chapter 16: Modules, symbols, and build identity

<!-- BOOK:NAV:START -->

[Previous: Strings and collections](15-strings-and-collections.md) · [Contents](../README.MD#table-of-contents) · [Next: Comparing captures](17-comparing-captures.md)

<!-- BOOK:NAV:END -->

**You will learn:** how a loaded location relates to a file, what matching symbols contribute, and how to describe an address so another person can reproduce your lookup.

**Before you start:** review [offset types](04-offsets-and-signatures.md#offset-types). The arithmetic below uses an invented section table; it does not require opening a real executable.

## Three coordinates for one investigation

Suppose a debugger shows an instruction at virtual address `0x140001250`. The module is loaded at `0x140000000`. Subtracting the loaded base gives RVA `0x1250`.

That RVA is useful because it describes a location relative to this image. It does not yet tell you where to seek in the executable file. A loader maps file sections into memory, and their file positions can differ from their virtual positions.

Keep three labels in your notes:

```text
loaded VA:   0x140001250 in a specified process and module
image RVA:   0x1250 in a specified build
file offset: determined from that build's file layout
```

Microsoft's [PE specification](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format) defines the section fields and distinguishes loaded addresses from file positions. The exercise below applies those ideas to deliberately simple numbers.

<a id="section-example"></a>
## Work through a section mapping

Imagine one section with these properties:

| Property | Value |
| --- | --- |
| Start RVA | `0x1000` |
| Virtual size | `0x600` |
| Raw file offset | `0x400` |
| Raw file size | `0x400` |

For RVA `0x1250`, the displacement into the section is `0x250`. It falls inside both the declared virtual region and the raw file bytes, so the corresponding file offset is `0x400 + 0x250 = 0x650`.

For RVA `0x1450`, the displacement is `0x450`. It lies inside the declared virtual size but beyond the raw file size. In this example, there is no corresponding stored file byte to return. Do not continue the formula and accidentally read bytes belonging to the next file region.

This small Python calculation reproduces the first lookup:

```python
section_rva, virtual_size = 0x1000, 0x600
raw_offset, raw_size = 0x400, 0x400
rva = 0x1250
delta = rva - section_rva
if not (0 <= delta < virtual_size and delta < raw_size):
    raise ValueError("RVA is not backed by this section's file bytes")
print(hex(raw_offset + delta))  # 0x650
```

This is arithmetic for one declared section. It is not a PE parser. A general parser must handle headers, alignment rules, malformed or overlapping ranges, file bounds, and format-specific exceptions. It must also check the entire requested range, not only its first byte.

## Symbols add names and relationships

A symbol file can associate code or data locations with names and other debugging information. This can be far more informative than guessing what an anonymous address represents. The symbol information must match the module being examined; Microsoft's [debugging symbols guide](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/symbols) describes the relationship.

For your own program, preserve the exact binary, matching symbols, build configuration, and source revision together. Treat “the filename looks right” as a weak check. A rebuilt `Game.dll` can have the same name and different code.

Symbols also have limits. An optimized build may transform or remove local variables. A public symbol set may contain less information than a private one. A function name does not identify a particular live object, and a successful symbol lookup does not prove that the acquisition source supplied every requested byte.

## A repeatable module lookup

First establish the process lifetime and the module instance in that process. Then record the loaded base, image size, architecture, and exact build identity. Use the matching file or symbols to interpret the RVA. Finally, verify the bytes or application behavior relevant to your claim.

Do not retain a module base indefinitely. A process restart or module unload/reload can invalidate it. If you cache the lookup, bind the cache entry to that lifecycle context.

For a compact report, write:

```text
process context: my development player, run 2026-10-23-A
module: Example.dll, SHA-256 recorded in the experiment artifact
loaded base: 0x140000000
location: RVA 0x1250
file interpretation: raw offset 0x650 under the recorded section table
evidence: matching build artifacts and the bytes inspected
```

The example deliberately avoids a fabricated hash. A real record should contain the actual hash of the retained artifact.

## Deeper detail: loaded bytes can differ from file bytes

Relocations, runtime initialization, imports, and mutable data can make a loaded image differ from its original file. A byte difference is a finding to explain, not automatic proof of corruption.

Likewise, comparing hashes of a whole on-disk image with a whole loaded image is not generally a meaningful equality test. Identify which region you expect to be comparable and what transformations are permitted. The same principle will help with the relocated payload in [Chapter 17](17-comparing-captures.md).

A stored timestamp is also not a complete build identity. Preserve stronger artifact evidence and the toolchain context needed to interpret it. A hash identifies bytes; it does not supply missing symbols or establish that the bytes are trustworthy.

## Checkpoint

For the invented section above, what does RVA `0x1450` tell you? Why would returning raw file offset `0x850` be misleading?

[Check your answer](../appendices/answers.md#chapter-16).

<!-- BOOK:FOOT:START -->

[Previous: Strings and collections](15-strings-and-collections.md) · [Contents](../README.MD#table-of-contents) · [Next: Comparing captures](17-comparing-captures.md)

<!-- BOOK:FOOT:END -->
