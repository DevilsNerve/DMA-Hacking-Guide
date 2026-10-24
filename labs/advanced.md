# Advanced observation lab

[Book contents](../README.MD#table-of-contents) · [First lab](README.md) · [Chapter 15](../chapters/15-strings-and-collections.md) · [Final investigation](../chapters/20-complete-investigation.md)

This lab supports Chapters 15–20. It adds a Unicode label, a collection of identified entities, semantic comparison, and deterministic replay. It uses a second invented format, `OBS2`, and leaves the original pointer-width lab unchanged.

These files are serialized teaching observations. They contain file offsets, not live process pointers, and cannot be opened as operating-system captures. No command accesses another process or a device.

## Quick start

Use Python 3.10 or newer from the repository root:

```sh
python labs/advanced_lab.py demo
```

Expected output:

```text
label='Pilot \U0001f9ed' generation=2 entities=3
ids=[10, 20, 40]
id=10 health=87.5 x=1 y=2
id=20 health=100 x=10 y=12
id=40 health=50 x=-1 y=3
generations=2->4
label_changed=no
added=[30] removed=[40]
changed=['10.health:87.5->60', '20.y:12->13']
```

The label is `Pilot 🧭`. Output uses an ASCII escape for the compass so a terminal's font or encoding does not determine whether the example runs. Generation 2 is the baseline; generation 4 contains the known state changes.

<a id="format"></a>
## OBS2 format reference

The image is at least 32 bytes and at most 4,096 bytes. Every integer and binary32 float is little-endian. Offsets are measured in bytes from the beginning of this file. There is no automatic relationship to a process virtual address.

| Header offset | Size | Field | Rule |
| --- | ---: | --- | --- |
| `0x00` | 4 | Magic | ASCII `OBS2` |
| `0x04` | 2 | Format version | `uint16`, exactly 2 |
| `0x06` | 2 | Header size | `uint16`, exactly 32 |
| `0x08` | 8 | Generation | `uint64`; ordered only within the declared replay session |
| `0x10` | 4 | Entity count | `uint32`, 0 through 64 |
| `0x14` | 4 | Name length | `uint32`, 0 through 64 UTF-16 code units |
| `0x18` | 4 | Name offset | `uint32` file offset |
| `0x1C` | 4 | Entity-array offset | `uint32` file offset |

Both payload offsets must lie between the end of the header and the end of the image, inclusive. Their requested lengths must fit. Nonempty name and entity ranges must not overlap. Empty payloads are allowed and their offsets must still satisfy the range rule. Unused gaps and trailing bytes are not interpreted.

The name has no terminator or required byte-order mark. Decode exactly `name_length * 2` bytes as UTF-16 little-endian using strict error handling. Empty text and supplementary characters are allowed; malformed surrogate sequences are rejected.

Each entity occupies sixteen bytes:

| Entity offset | Size | Field | Rule |
| --- | ---: | --- | --- |
| `0x00` | 4 | ID | Nonzero `uint32`, unique within this image |
| `0x04` | 4 | Health | Finite binary32, 0 through 100 |
| `0x08` | 4 | x coordinate | Finite binary32 |
| `0x0C` | 4 | y coordinate | Finite binary32 |

Entity order has no identity meaning. IDs are stable within the synthetic session used by these exercises. The format itself does not encode a session identifier; the fixture case and experiment record supply that context. Comparing unrelated real sessions would require additional identity evidence.

Generation is not the first lab's even/odd sequence protocol. Any `uint64` value is structurally valid. The replay policy separately requires nondecreasing accepted generations within one session and equal semantic state for repeated generations. It does not infer that numbering is consecutive.

<a id="comparison-lab"></a>
## Compare layout and state changes

```sh
python labs/advanced_lab.py create out/advanced/before.obs --case before
python labs/advanced_lab.py create out/advanced/relocated.obs --case relocated
python labs/advanced_lab.py create out/advanced/after.obs --case after
python labs/advanced_lab.py inspect out/advanced/before.obs
python labs/advanced_lab.py compare out/advanced/before.obs out/advanced/relocated.obs
python labs/advanced_lab.py compare out/advanced/before.obs out/advanced/after.obs
```

The baseline is 96 bytes. The relocated and later cases are each 112 bytes because they add sixteen bytes before the payload. Creation prints the actual SHA-256. It refuses to overwrite an existing file; add `--force` only when deliberately regenerating it.

The first comparison reports generation `2->2`, no label change, empty added/removed lists, and `changed=[]`. Payload relocation and reversed array order do not change the semantic view.

The second comparison reports the four lines at the end of the demo output. It matches by unique ID, sorts reported changes, and compares health/x/y numerically. Positive and negative zero compare equal. Inputs containing NaN or infinity are rejected before comparison.

Inspection and change reports use nine significant digits for binary32 fields. This preserves visible distinctions between adjacent finite values that a shorter display could round to the same text. It does not change the stored bytes or the exact numeric comparison policy.

Both images must decode successfully before any comparison output is printed. A missing or invalid second file must not look like an empty collection whose objects were all removed.

## Replay failures without waiting

```sh
python labs/advanced_lab.py replay
```

Expected output:

```text
  0 ms accepted
 10 ms duplicate
 20 ms unavailable
 30 ms invalid
 40 ms accepted
 50 ms regressed
 60 ms inconsistent
200 ms no-progress
```

The timestamps are supplied data, so this command does not sleep. The monitor preserves the last accepted state through failures. Its 100 ms progress budget is exceeded only when elapsed time is greater than 100 ms; exactly 100 ms remains within budget.

`no-progress` means that no higher generation has been accepted within the configured interval. It does not prove that a real source is broken or that an unchanged application value is stale. See [Chapter 18](../chapters/18-polling-and-replay.md) for the interpretation.

## Explore failure cases

The [tests](../tests/test_advanced_lab.py) construct malformed headers, excessive lengths, overlapping ranges, invalid Unicode, duplicate IDs, truncated arrays, and non-finite numbers. They also compare reordered records and replay conflicting generations.

```sh
python -m unittest discover -s tests -p test_advanced_lab.py -v
```

The command-line contract is success status 0, operational/input failure status 1, and argument-parser error status 2. A semantic comparison with no changes is a successful result. An invalid format is a failure, even if its filename ends in `.obs`.

The fixed-seed mutation cases are bounded experiments. Passing them is evidence about those cases, not an exhaustive proof of parser correctness or a performance benchmark.

<a id="detailed-walkthroughs"></a>
## Reproduce the detailed chapter calculations

The companion [deep-dive tool](deep_dive.py) uses only the Python standard library:

```sh
python labs/deep_dive.py sections
python labs/deep_dive.py precision
python labs/deep_dive.py trace
python labs/deep_dive.py evidence
```

`sections` checks the six complete-range requests in [Chapter 16](../chapters/16-modules-and-symbols.md#image-model). Its three rejected requests are expected demonstration outcomes, so the demonstration itself exits successfully:

```text
rva=0x1250 length=4 file=0x650
rva=0x13f8 length=8 file=0x7f8
rva=0x13f8 length=16 rejected: virtual range has no complete stored counterpart
rva=0x1450 length=4 rejected: virtual range has no complete stored counterpart
rva=0x2100 length=16 file=0x900
rva=0x3000 length=1 rejected: virtual range has no complete stored counterpart
```

The mapper is a restricted geometry model, not a PE parser. It requires 1–96 sections with nonempty, nonoverlapping virtual extents; integer metadata and requests fit the declared 32-bit address space, and all declared raw ranges must fit the file. It rejects empty requests. Header mapping, alignment, directory semantics, and loader transformations are outside the model.

`precision` shows the raw encodings and two display precisions for adjacent binary32 values:

```text
bytes=cdcccc3d decoded=0.10000000149011612 display=0.100000001
bytes=cecccc3d decoded=0.10000000894069672 display=0.100000009
1.health:0.100000001->0.100000009
```

`trace` prints every post-event monitor state:

```text
at_ms status accepted_generation last_observation_ms last_progress_ms
0 accepted 2 0 0
10 duplicate 2 10 0
20 unavailable 2 20 0
30 invalid 2 30 0
40 accepted 4 40 40
50 regressed 4 50 40
60 inconsistent 4 60 40
200 no-progress 4 200 40
```

`evidence` prints a JSON reference report containing fixture hashes, sizes, generations, storage IDs, comparison lines, and replay states with input hashes. It regenerates reference fixtures in memory; it does not read or verify earlier files on disk. No command writes an evidence file automatically or accesses a process or device. Retain actual file-creation and inspection outputs separately when completing the investigation.

The [focused tests](../tests/test_deep_dive.py) cover mapping boundaries, ambiguous metadata, truncated backing, width limits, replay state, and the reference artifact hashes. The [worked answers](../appendices/deep-dive-answers.md) explain all 24 chapter exercises.

## Complete the investigation

Follow [Chapter 20](../chapters/20-complete-investigation.md) to combine the files, comparison, replay, and tests into a report. Keep the supported claims at the synthetic-data level until you have independent evidence for a real acquisition source.

[Back to contents](../README.MD#table-of-contents)
