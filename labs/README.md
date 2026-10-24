# Memory lab

[Book contents](../README.MD#table-of-contents) · [Foundations](../chapters/02-memory-foundations.md) · [Capstone](../chapters/14-capstone.md)

This lab gives you a complete byte layout and a known answer. It runs locally without reading another process, installing dependencies, or accessing hardware. The fixture is deliberately **not a real OS capture or Unity layout**.

<a id="first-run"></a>
## Your first 15 minutes

Use Python 3.10 or newer. Open a terminal in the repository root—the directory containing `README.MD` and `book.json`. The commands below use `python`; substitute `python3` on systems that use that name, or `py -3` on Windows if that is your installed launcher.

```sh
python --version
python labs/memory_lab.py demo
```

Expected demo output:

```text
pointer_bits=64 base=0x140000000
record=0x140000100 sequence=2
health=87.5 items=[10, 20, 30]
signature_matches=['0x140000100']
```

The base belongs to the lab's invented address space. No process with that address needs to exist on your machine.

Create a persistent fixture, decode it, and search for its header:

```sh
python labs/memory_lab.py create out/first.bin
python labs/memory_lab.py inspect out/first.bin
python labs/memory_lab.py scan out/first.bin --pattern "44 4D 41 4C ?? ?? 20 00"
```

`inspect` prints the first three demo lines. `scan` prints the signature line. All three commands should succeed. `create` refuses to replace an existing file; use a new filename or add `--force` when you deliberately want to regenerate it.

Now run the 32-bit variant:

```sh
python labs/memory_lab.py demo --bits 32
```

Its base is `0x400000` and its record is `0x400100`. Health and items remain unchanged. Use the matching `--bits 32` option for both creation and inspection of a 32-bit file.

<a id="layout"></a>
## The complete fixture format

All integers and floats use little-endian encoding. A valid image is 512 bytes. The default base is `0x140000000` for 64-bit pointers or `0x00400000` for 32-bit pointers. The byte image uses the simple mapping `file_offset = address - base`.

| Image offset | Size | Meaning |
| --- | ---: | --- |
| `0x40` | 4 or 8 | Target-width root pointer containing `base + 0x100` |
| `0x100` | 32 | Record described below |
| `0x180` | 6 | Three `uint16` item IDs: 10, 20, 30 |

| Record offset | Size | Field | Valid baseline |
| --- | ---: | --- | --- |
| `0x00` | 4 | Magic bytes | ASCII `DMAL` |
| `0x04` | 2 | Version, `uint16` | 1 |
| `0x06` | 2 | Record byte size, `uint16` | 32 |
| `0x08` | 4 | Beginning sequence, `uint32` | 2 |
| `0x0C` | 4 | Health, binary32 | 87.5 |
| `0x10` | 4 | Item count, `uint32` | 3 |
| `0x14` | 4 or 8 | Item pointer | `base + 0x180` |
| `0x18` | 4, in 32-bit format only | Reserved padding | Zero in generated fixtures; ignored by decoder |
| `0x1C` | 4 | Ending sequence, `uint32` | 2 |

The pointer at `0x14` is intentionally unaligned. This is an explicit byte format, not a native C++ or C# structure layout. Both sequence markers must be equal and even. Health must be finite and within 0 through 100. Counts are bounded to 16 items; a zero count does not dereference the item pointer.

The parser limits images to 1 MiB. The scanner accepts patterns of 1–128 bytes, rejects all-wildcard patterns, and limits results to 1,024 matches. It scans one contiguous available image, not a collection of memory regions. Region gaps and real page translation belong to a future source adapter.

<a id="failure-lab"></a>
## Learn from deliberate failures

Create one fixture with a single injected fault, then inspect it:

```sh
python labs/memory_lab.py create out/bad.bin --fault null-root
python labs/memory_lab.py inspect out/bad.bin
```

Expected: `error: null root pointer` on standard error and exit status 1. In a POSIX shell, run `echo $?` immediately after inspection to see the status. In PowerShell, use `$LASTEXITCODE` immediately afterward.

Use a different output path for each case, or add `--force` to `create` when reusing `out/bad.bin`.

| `--fault` value | What changes | Expected error contains |
| --- | --- | --- |
| `null-root` | Root pointer becomes zero | `null root pointer` |
| `bad-magic` | Record identity bytes change | `record magic mismatch` |
| `bad-version` | Version becomes 2 | `unsupported record version` |
| `bad-size` | Declared record size becomes 64 | `record size mismatch` |
| `bad-count` | Count exceeds 16 | `item count exceeds limit` |
| `odd-sequence` | Both markers become 3 | `inconsistent sequence` |
| `mismatched-sequence` | Ending marker becomes 4 | `inconsistent sequence` |
| `nan-health` | Health becomes NaN | `invalid health` |
| `dangling-items` | Array pointer leaves the image | `unavailable range` |
| `truncated` | Only the first item remains available | `unavailable range` |

These errors are successful demonstrations of the reader's checks. No bytes are fabricated to make a malformed record look complete. Sequence checking here validates static fixture bytes; it does not prove a live concurrent-read protocol.

## Scanner exercises

Vary the chunk size without changing the expected match:

```sh
python labs/memory_lab.py scan out/first.bin --chunk-size 7
python labs/memory_lab.py scan out/first.bin --chunk-size 256
```

Try a pattern absent from the input: `--pattern "FE ED FA CE"`. Expect `signature_matches=[]` and status 0: the scan completed and found no match. A caller requiring exactly one locator must enforce that additional condition.

Try `--pattern "?? ??"`. Expect status 1 because the pattern contains no fixed byte. Invalid command syntax, such as `--bits 16`, is handled by the argument parser with status 2.

## Run the checks

```sh
python -m unittest discover -s tests -v
python tools/book.py check
```

The tests exercise valid decoding, malformed data, target-width handling, scanner boundaries, and the command-line contract. The book checker validates local links and generated chapter navigation. Neither substitutes for a real capture, Unity build, or hardware test.

## Explain what you learned

Before moving on, explain why the signature match is a candidate, why the root slot is not the record, and why a failed read must not become a zero-valued field. Then complete the [capstone](../chapters/14-capstone.md) or return to [offsets and signatures](../chapters/04-offsets-and-signatures.md).

For Chapters 15–20, continue to the [advanced observation lab](advanced.md). It introduces a separate format for Unicode text, identified collections, capture comparison, and replay. Keep this first lab as the smaller baseline for pointer-width and exact-read behavior.

[Back to contents](../README.MD#table-of-contents)
