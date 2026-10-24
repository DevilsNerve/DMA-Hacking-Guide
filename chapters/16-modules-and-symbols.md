# Chapter 16: Modules, symbols, and build identity

<!-- BOOK:NAV:START -->

[Previous: Strings and collections](15-strings-and-collections.md) · [Contents](../README.MD#table-of-contents) · [Next: Comparing captures](17-comparing-captures.md)

<!-- BOOK:NAV:END -->

**You will learn:** how a loaded location relates to a file, what matching symbols contribute, and how to describe an address so another person can reproduce your lookup.

**Before you start:** review [offset types](04-offsets-and-signatures.md#offset-types). The arithmetic below uses an invented section table; it does not require opening a real executable.

## In this chapter

- [Single-section mapping example](#section-example)
- [Map a complete request across an image model](#image-model)
- [Track address width and module lifetime](#module-context)
- [Establish a symbol match](#symbol-evidence)
- [Investigate a wrong-module result](#module-diagnosis)
- [Review a module-aware reader](#module-review)
- [Practice exercises](#chapter-exercises)

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

<a id="image-model"></a>
## Map a complete request across an image model

The single-section calculation is a useful beginning. A tool must also decide which section applies, whether the entire request fits, and whether the corresponding file bytes are present.

For the rest of this exercise, use an invented 4,096-byte file with this section table. Every interval excludes its upper endpoint:

| Section | RVA interval | File interval | Interpretation in this exercise |
| --- | --- | --- | --- |
| `code` | `[0x1000, 0x1600)` | `[0x400, 0x800)` | First `0x400` bytes are stored; remaining virtual bytes have no file counterpart |
| `data` | `[0x2000, 0x2300)` | `[0x800, 0xA00)` | First `0x200` bytes are stored |
| `state` | `[0x3000, 0x3100)` | Empty | Virtual-only region in the declared model |

This model intentionally omits PE header mapping, loader alignment, and directory-specific interpretation. It is a small geometry exercise. The names are labels; the intervals and backing rules determine the result. Actual section-field semantics are documented in [IMAGE_SECTION_HEADER](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-image_section_header).

### Work through six requests

| Request | Result | Reason |
| --- | --- | --- |
| RVA `0x1250`, length 4 | File offset `0x650`, length 4 | Fits within both declared extents of `code` |
| RVA `0x13F8`, length 8 | File offset `0x7F8`, length 8 | Ends exactly at the raw-data boundary |
| RVA `0x13F8`, length 16 | No complete file mapping | Eight bytes would extend beyond the stored `code` bytes |
| RVA `0x1450`, length 4 | No stored counterpart | Virtual range exists, raw range does not cover it |
| RVA `0x2100`, length 16 | File offset `0x900`, length 16 | Fits the `data` section |
| RVA `0x3000`, length 1 | No stored counterpart | `state` has no raw payload in this model |

Notice the third request. Its first byte has a valid file mapping, but the whole request does not. An implementation that validates only the start address would return a misleading contiguous file slice containing bytes from another region.

There are at least four distinct failures worth reporting: no section contains the requested virtual interval; a virtual interval lacks stored bytes; the section metadata itself is ambiguous; or the file is shorter than the declared raw range. Combining all four into “bad address” loses information needed to investigate the problem.

### A precise algorithm for this restricted model

Treat the metadata as untrusted input even when it came from a familiar-looking header. Bound the number of section records before allocating a list. Validate nonnegative extents and the address-width limits. Reject overlapping declared virtual intervals, because this exercise deliberately requires one unambiguous containing section.

For a positive-length request, locate a section that contains the complete virtual interval. Calculate `delta = request_rva - section_rva`. Require `delta < raw_size` and `length <= raw_size - delta`. Only then compute `raw_offset + delta`, and check the complete resulting range against the actual file length.

Use subtraction-based bounds or checked arithmetic in a fixed-width language. A malformed size should never wrap an end address to a small apparently valid number. Zero-length requests should have a documented policy; the exercise's mapper rejects them because it is intended to identify actual stored bytes, not to validate cursor positions.

The executable version is available through:

```sh
python labs/deep_dive.py sections
```

It uses the table above and reports the accepted and rejected requests. Passing this exercise validates that restricted mapping algorithm. It does not establish that the program can parse arbitrary PE files.

### Why an operating-system helper still needs context

An API name containing “virtual address” does not necessarily mean a remote process address. For example, `ImageRvaToVa` operates on an image mapped as a file and returns a location in that mapping. Its arguments and lifetime belong to the caller's mapped file view. Read the [API contract](https://learn.microsoft.com/en-us/windows/win32/api/dbghelp/nf-dbghelp-imagervatova) before treating its result as an address to send to another acquisition interface.

This distinction applies beyond Windows. A pointer into your parser's local buffer, a virtual address in the target process, and an offset in the retained file can all be represented by integers. Give them separate names or types so that crossing the boundary requires an explicit conversion.

<a id="module-context"></a>
## Track address width and module lifetime

Suppose the same supported build is loaded in two runs:

| Run | Loaded base | RVA | Resulting process VA |
| --- | --- | --- | --- |
| A | `0x140000000` | `0x1250` | `0x140001250` |
| B | `0x180000000` | `0x1250` | `0x180001250` |

The RVA can remain meaningful for that build while the absolute address changes. The file mapping can also remain `0x650` in both runs because it describes the retained artifact, not either process's chosen load address.

Do not truncate the resulting address to 32 bits. The low 32 bits of `0x140001250` are `0x40001250`, which is a different location. At the same time, do not conclude that every field in a 64-bit executable is eight bytes wide. File formats can store fixed-width offsets and sizes even when runtime pointers are wider. Read each field according to its declared representation.

A module-relative location also needs a module identity. A process can contain several similarly named libraries from different directories or versions. An unqualified name lookup that returns the first match turns enumeration order into a hidden input. Record the selected instance and report ambiguity when you cannot establish the intended one.

### Define a useful cache key

A cache entry for a loaded module should be bound to the source session, process lifetime, module instance, and build identity that justified it. A filename alone is not enough. Neither is a PID, because a later process can reuse that number.

Separate the data you cache. A file's section table can be cached by exact file identity. A process load base belongs to that process/module lifetime. A symbol resolution belongs to its matched symbol/module pair. Combining them into one undocumented “module cache” makes invalidation difficult to reason about.

When a process exits, reject further observations associated with that lifetime. When a module unloads, invalidate that module instance. If your acquisition source cannot observe those events directly, define a refresh and revalidation policy and state its limits. A periodically refreshed list is an observation strategy, not proof that no unload happened between checks.

### Preserve uncertainty instead of guessing

If you have a complete file but only partial live module metadata, you can still describe file-level findings. If you have a live base but cannot establish the exact build, you can still record the raw bytes and context. What you should avoid is silently promoting incomplete evidence into a fully identified module-relative claim.

This habit makes the eventual repair smaller. Instead of replacing a correct decoder because an absolute address went stale, you can identify the failed lifecycle assumption and reacquire the module context.

<a id="symbol-evidence"></a>
## Establish a symbol match

Think of symbol loading as another evidence chain. You need to know which module instance you selected, which binary build it represents, which symbol artifact matches that build, and what information that artifact actually contains.

For relevant PDB formats, matching involves identifiers such as a GUID or signature together with age. The applicable values depend on the symbol format; they are not interchangeable with a human-readable filename. The identification parameters in [SymFindFileInPath](https://learn.microsoft.com/en-us/windows/win32/api/dbghelp/nf-dbghelp-symfindfileinpath) illustrate why symbol lookup needs more than a name.

You do not need to implement a symbol server to learn this lesson. For your own development build, retain the binary and its symbols from the same build operation. Record their hashes and the debugger's matching result. If you later rebuild the source, treat the new outputs as a new artifact set even when the filenames are unchanged.

### Four statements that should stay separate

| Statement | Evidence required |
| --- | --- |
| “I found a file named `Example.pdb`.” | A filesystem or symbol-store lookup |
| “These symbols match this module.” | Matching metadata and a successful supported symbol-load check |
| “This address resolves to a named location.” | A resolution in the matched module context |
| “This live field has the expected meaning.” | Layout and runtime observation evidence for that field |

The first statement does not establish the second, and the third does not establish the fourth. A convincing function name can make an incorrect context harder to notice, so preserve the module identity alongside the resolved name in reports.

### Public symbols and private type information

Symbol sets differ in what they expose. Public names can help identify functions while omitting local variables or detailed type information that a private set contains. Optimized code can further complicate source-level expectations. Microsoft's [public and private symbols documentation](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/public-and-private-symbols) describes the distinction.

If a type layout is unavailable, say so. A nearby function name is not a substitute for a field offset. If a debugger cannot show a local variable at a particular instruction, do not infer that the bytes must therefore be stored at an old stack offset. The compiler may have changed where or whether the value exists.

The practical response is to choose an observation that your evidence supports. For a program you own, a development build with appropriate symbols or an explicit diagnostic snapshot can provide a stronger reference than repeatedly guessing from optimized output.

### A symbol-loading record

A useful record contains the selected module path or instance identifier, loaded base, binary hash, symbol artifact identity, search path policy, and the outcome reported by the debugger. Preserve mismatches as mismatches; do not describe a forced or approximate symbol interpretation as a verified match.

Avoid mixing diagnostic state between targets. A symbol result cached for one binary should not survive into another binary merely because both export a function with the same name. The names can match while the code and layout differ.

<a id="module-diagnosis"></a>
## Investigate a wrong-module result

Consider a development tool that worked yesterday. Today it still finds `Example.dll`, resolves an RVA, and reads four bytes successfully, but the decoded value is implausible.

Work through the investigation in this order:

1. **Verify the selected process.** Confirm that it belongs to the intended run rather than an older or parallel instance.
2. **Verify the selected module instance.** Compare path, loaded range, architecture, and any recorded instance metadata.
3. **Verify build identity.** Compare the retained artifact with the expected build. An unchanged filename is insufficient.
4. **Recompute the location.** Show the loaded-base-plus-RVA arithmetic without truncation or unintended signed conversion.
5. **Verify the requested range.** Check that the complete read belongs to the intended image region and is actually available.
6. **Revisit interpretation.** Only after the location context is established should you reconsider the field type or layout.

This order is useful because it separates a stale locator from a bad decoder. Changing the decoder first can make the number look plausible while preserving the real error.

### A deliberately misleading example

Run A loads build X at `0x140000000`; run B loads build Y at the same base. Your tool sees the familiar base and reuses RVA `0x1250` from X. The arithmetic is correct, the read is successful, and the number can even look realistic. The missing fact is that Y has not been verified to use the same location for the same purpose.

Now consider the reverse: run B loads the same build X at `0x180000000`. A tool that retains the old absolute address fails even though its build-specific RVA remains appropriate. These examples require different repairs—layout revalidation in the first case, lifecycle-aware base resolution in the second.

### When file and loaded bytes disagree

First identify the exact compared ranges and their coordinate systems. Then determine whether the region is expected to change during loading or execution. Preserve the raw difference before interpreting it.

A useful report says, for example, “These twelve bytes differ between the retained artifact's mapped region and this live observation; the comparison has not yet accounted for runtime transformations.” It should not jump directly to “the binary was modified” without explaining what equality was expected to mean.

For controlled experiments, choose a region whose expected behavior you understand. A file-backed constant in your own build can be easier to reason about than a mutable import table or an actively updated state structure. The important step is defining the expectation before observing the mismatch.

<a id="module-review"></a>
## Review a module-aware reader

Trace a requested value through five conversions: process selection, module selection, build-specific location resolution, source read, and typed decode. Each stage should either return enough context for the next stage or report why it could not establish that context.

For the restricted section mapper, review these cases explicitly:

| Case | Required behavior |
| --- | --- |
| Request ends exactly at a stored boundary | Accept if the complete interval fits |
| Request crosses that boundary by one byte | Reject the complete mapping |
| Section claims raw bytes beyond the file | Reject inconsistent metadata |
| Two declared virtual ranges overlap | Reject ambiguity under the exercise's model |
| RVA falls in a gap | Report no containing section |
| Address arithmetic exceeds its declared width | Reject rather than wrap |
| A virtual-only region is requested | Report no stored counterpart |

For a live adapter, add lifecycle cases: the process disappears, a module unloads, another module shares the name, or a newly observed build has no supported locator. Those tests require an actual adapter and controlled target; the file-geometry exercise alone does not cover them.

The result should retain both a machine-usable location and a human-readable explanation. “RVA `0x1250` in the recorded build, read from base `0x180000000` in run B” is more useful than a bare address or an unexplained symbol name.

<a id="chapter-exercises"></a>
## Practice exercises

1. **Check a boundary.** In the `data` section, does RVA `0x21F8` with length 8 have a file mapping? What about length 9? Give the file offset for the valid case.
2. **Separate two failures.** A file is only `0x900` bytes long, but its declared `data` raw range ends at `0xA00`. Is this the same failure as a request into the virtual-only tail of an otherwise valid section?
3. **Follow the lifecycle.** A module unloads and another build with the same name loads at the same base. Which cached facts remain reusable, and which need fresh evidence?
4. **Assess the symbol claim.** A debugger shows a familiar function name after symbols were loaded without a verified match. What can you safely claim, and what should you check next?

[Worked solutions](../appendices/deep-dive-answers.md#chapter-16).

## Checkpoint

For the invented section above, what does RVA `0x1450` tell you? Why would returning raw file offset `0x850` be misleading?

[Check your answer](../appendices/answers.md#chapter-16).

<!-- BOOK:FOOT:START -->

[Previous: Strings and collections](15-strings-and-collections.md) · [Contents](../README.MD#table-of-contents) · [Next: Comparing captures](17-comparing-captures.md)

<!-- BOOK:FOOT:END -->
