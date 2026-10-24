# Chapter 3: Tools and your first lab

<!-- BOOK:NAV:START -->

[Previous: Memory foundations](02-memory-foundations.md) · [Contents](../README.MD#table-of-contents) · [Next: Offsets and signatures](04-offsets-and-signatures.md)

<!-- BOOK:NAV:END -->

**You will learn:** which tools answer which questions, and how to produce a repeatable result before introducing hardware.

**Before you start:** understand the pointer walk in [Chapter 2](02-memory-foundations.md).

<a id="equipment"></a>
## Choose the smallest useful setup

For the supplied exercises, you need Python 3.10 or newer, a text editor, and this repository. You do not need a commercial game, administrator privileges, a debugger, or a DMA board.

For your own application, add its source, build settings, and debug symbols. These often provide stronger evidence than a scanner. A debugger tells you about live objects and instructions; a hex viewer tells you about bytes; a profiler tells you about allocations and timing. Use each tool for the question it can answer.

| Question | Useful tool or artifact |
| --- | --- |
| What bytes are in this file? | Hex viewer or a short bounded reader |
| What did my application intend to store? | Source code and an application-side log |
| Which module contains this instruction? | Module map and symbols for that build |
| What is my Unity build configuration? | Editor version, scripting backend, architecture, build log |
| Can an acquisition source supply this range? | Source diagnostics and exact-length read results |
| Are observations current? | A producer-side sequence number and timestamps |

If you later evaluate hardware, first identify the bus topology, supported host systems, documented firmware, transport interface, and platform DMA policy. A connector shape or an advertised bandwidth number does not establish compatibility. Prefer a documented supported combination over a product name copied from an old guide.

## Run the first example

From the repository root:

```sh
python labs/memory_lab.py demo
```

Expected output:

```text
pointer_bits=64 base=0x140000000
record=0x140000100 sequence=2
health=87.5 items=[10, 20, 30]
signature_matches=['0x140000100']
```

The command creates bytes in memory and reads them through the same parser used for file inputs. It does not attach to another process. If Python is not found, try the launcher described in the [lab instructions](../labs/README.md#first-run).

Now create a file you can inspect and rerun:

```sh
python labs/memory_lab.py create out/first.bin
python labs/memory_lab.py inspect out/first.bin
```

The file contains 512 bytes. The parser knows the image base and layout because this is a format we designed. When you analyze a different format, those assumptions must come from that format's documentation or your own verified schema.

## Make it fail on purpose

```sh
python labs/memory_lab.py create out/null-root.bin --fault null-root
python labs/memory_lab.py inspect out/null-root.bin
```

The second command should report `null root pointer` and exit unsuccessfully. That is the desired result. A reader that prints health zero after failing to obtain the root would turn missing evidence into misleading data.

Try the [other fault cases](../labs/README.md#failure-lab) after this one. Predict the error before running the command. This gives you a useful mental model of the parser's validation order.

## Keep a small notebook

Record the command, input hash, layout version, expected result, and observed result. The [experiment template](../templates/experiment.md) is intentionally short. You should be able to give it to someone else and have them reproduce the same observation.

Keep generated files in `out/`, which the repository ignores. Do not mix captured private data with teaching fixtures. If a later experiment needs real captures, store them separately with access appropriate to their contents.

## Deeper detail: choose tools by evidence quality

Decompilers reconstruct a useful approximation of a compiled program; they do not recover every original source decision. Symbols must match the binary. An acquisition library can expose process and module views only if it can interpret the source correctly. A UI showing a process name is one observation, not proof that every page belonging to that process is available.

When two tools disagree, first compare their inputs, address spaces, timestamps, and cache policies. Looking at the same hexadecimal number does not guarantee they are looking at the same bytes.

## Checkpoint

The demo works, but a hardware source cannot open. Which parts of your project have been validated, and which have not?

[Check your answer](../appendices/answers.md#chapter-03).

<!-- BOOK:FOOT:START -->

[Previous: Memory foundations](02-memory-foundations.md) · [Contents](../README.MD#table-of-contents) · [Next: Offsets and signatures](04-offsets-and-signatures.md)

<!-- BOOK:FOOT:END -->
