# DMA Hacking Guide

## Learn memory analysis, one reliable observation at a time

You have an address, a handful of bytes, and a value that looks almost right. How do you tell whether you found the right object—or just something that happens to look convincing?

This book teaches you to answer that question. Start with bytes and pointers, work through a small reproducible lab, then connect those skills to DMA acquisition, Unity, and larger analysis tools. You can complete the first exercises with Python and an ordinary computer. Hardware comes later.

The examples use synthetic data and programs you control. The practical goal is to understand and verify memory observations in your own development, research, or authorized analysis environment.

**New here?** Read [Chapter 1](chapters/01-start-here.md), then try the [15-minute lab](labs/README.md#first-run). **Already comfortable with pointers?** Jump to [the advanced reading path](#advanced-path) or use the [topic finder](#topic-finder).

<a id="contents"></a>
## Table of contents

<!-- BOOK:CONTENTS:START -->

| Chapter | What you will learn |
| --- | --- |
| [1. Start here](chapters/01-start-here.md) | What DMA does, what you will learn, and where to begin. |
| [2. Memory foundations](chapters/02-memory-foundations.md) | Bytes, types, pointers, address spaces, and object lifetime. |
| [3. Tools and your first lab](chapters/03-tools-and-lab.md) | A useful setup and a first result without hardware. |
| [4. Offsets and signatures](chapters/04-offsets-and-signatures.md) | Find, describe, and validate locations without guessing. |
| [5. Acquisition](chapters/05-acquisition.md) | Connect the source, transport, translation, and analysis layers. |
| [6. Reading memory reliably](chapters/06-reading-memory.md) | Exact reads, bounded decoding, and consistency. |
| [7. Controlled experiments](chapters/07-controlled-experiments.md) | Change known inputs and distinguish observation from causation. |
| [8. Protections and observability](chapters/08-protections-and-observability.md) | IOMMUs, permissions, and the limits of visibility claims. |
| [9. Troubleshooting](chapters/09-troubleshooting.md) | Work from a symptom to the smallest discriminating check. |
| [10. Unity in practice](chapters/10-unity.md) | Mono, IL2CPP, managed objects, and your own instrumented build. |
| [11. Address translation](chapters/11-address-translation.md) | Page tables, page boundaries, and missing pages. |
| [12. Performance and freshness](chapters/12-performance.md) | Batching, caches, latency distributions, and useful throughput. |
| [13. Reproducibility and tool design](chapters/13-reproducibility.md) | Versioned layouts, evidence records, and dependable exports. |
| [14. Build a trustworthy reader](chapters/14-capstone.md) | An end-to-end project with measurable acceptance criteria. |
| [15. Strings and collections](chapters/15-strings-and-collections.md) | Decode text and variable-length records with explicit units and bounds. |
| [16. Modules, symbols, and build identity](chapters/16-modules-and-symbols.md) | Relate loaded addresses, file bytes, symbols, and exact builds. |
| [17. Comparing captures](chapters/17-comparing-captures.md) | Separate layout changes from meaningful changes in application state. |
| [18. Polling and replay](chapters/18-polling-and-replay.md) | Handle duplicates, failures, generation changes, and observation age. |
| [19. Testing unfamiliar layouts](chapters/19-testing-layouts.md) | Challenge a decoder with boundaries, mutations, and independent evidence. |
| [20. A complete investigation](chapters/20-complete-investigation.md) | Turn several captures and a replay trace into a defensible conclusion. |

<!-- BOOK:CONTENTS:END -->

### Appendices and practical material

- [Runnable labs and expected output](labs/README.md)
- [Advanced lab for Chapters 15–20](labs/advanced.md)
- [Glossary](appendices/glossary.md)
- [Checkpoint answers](appendices/answers.md)
- [Worked exercises for Chapters 15–20](appendices/deep-dive-answers.md)
- [Sources and further reading](appendices/resources.md)
- [Corrections to the earlier guide](appendices/corrections.md)
- [Experiment record template](templates/experiment.md)
- [Contributing and checking the book](CONTRIBUTING.md)

## Choose your reading path

### First time working with memory

Read Chapters [1](chapters/01-start-here.md), [2](chapters/02-memory-foundations.md), and [3](chapters/03-tools-and-lab.md), then run the lab. Return to [Chapter 4](chapters/04-offsets-and-signatures.md) once you can explain why a pointer is different from the value it points to. There is no need to understand page tables on your first day.

### Comfortable programming, new to DMA

Read [acquisition](chapters/05-acquisition.md), [reliable reads](chapters/06-reading-memory.md), and [protections](chapters/08-protections-and-observability.md). Complete the lab's failure cases before connecting an acquisition source. Your first milestone is a correct, repeatable observation—not a fast polling loop.

<a id="advanced-path"></a>
### Building or reviewing an analysis tool

Use [Unity layouts](chapters/10-unity.md), [translation](chapters/11-address-translation.md), [performance](chapters/12-performance.md), and [reproducibility](chapters/13-reproducibility.md) as reference chapters. The [capstone](chapters/14-capstone.md) gives you acceptance criteria for a reader that survives malformed data and changing layouts.

### Continue beyond the first capstone

Chapters [15](chapters/15-strings-and-collections.md) through [20](chapters/20-complete-investigation.md) take you from one record to a small investigation: decode a named collection, distinguish module and file locations, compare captures by identity, replay failures, and test the assumptions behind your conclusion. Follow the [advanced lab](labs/advanced.md) alongside these chapters. It uses ordinary Python and synthetic observations, so you can reproduce the results without a device.

Each of these chapters includes a local contents list, detailed calculations, failure analysis, and exercises with [worked solutions](appendices/deep-dive-answers.md). Chapter 15 includes twelve exercises and a [strings and collections casebook](labs/advanced.md#strings-and-collections); Chapters 16–20 each add four. The [calculation tools](labs/advanced.md#detailed-walkthroughs) reproduce section mapping, numeric precision, replay state, and the final evidence report.

<a id="topic-finder"></a>
## Find a specific answer

| If you are wondering… | Read… |
| --- | --- |
| “What does `0x` mean?” | [Hex, bytes, and endianness](chapters/02-memory-foundations.md#bytes) |
| “Which kind of address is this?” | [Address spaces](chapters/02-memory-foundations.md#addresses) |
| “Why did my offset stop working?” | [What an offset means](chapters/04-offsets-and-signatures.md#offset-types) |
| “Do I need to buy a board?” | [Choose the smallest useful setup](chapters/03-tools-and-lab.md#equipment) |
| “How do MemProcFS and LeechCore fit together?” | [Acquisition layers](chapters/05-acquisition.md#layers) |
| “Why do I keep reading zero?” | [Troubleshooting by symptom](chapters/09-troubleshooting.md#symptoms) |
| “Can one read contain two different moments?” | [Consistency](chapters/06-reading-memory.md#consistency) |
| “Does IL2CPP preserve C# object layouts?” | [Unity's managed and native sides](chapters/10-unity.md#layouts) |
| “Why doesn't DMA imply unrestricted access?” | [IOMMU and platform protections](chapters/08-protections-and-observability.md#iommu) |
| “How do I measure improvements?” | [Benchmark design](chapters/12-performance.md#measurement) |
| “Does a string length count bytes or characters?” | [Text length units](chapters/15-strings-and-collections.md#text-units) |
| “How do I find an RVA in a file?” | [Section mapping example](chapters/16-modules-and-symbols.md#section-example) |
| “Did the data change, or just its position?” | [Semantic comparison](chapters/17-comparing-captures.md#semantic-comparison) |
| “What should a reader do when a sample fails?” | [Replay state transitions](chapters/18-polling-and-replay.md#state-transitions) |
| “How do I challenge my decoder?” | [Mutation experiments](chapters/19-testing-layouts.md#mutations) |
| “What does a finished investigation look like?” | [Worked investigation](chapters/20-complete-investigation.md#investigation) |

## Run the book's examples

Install Python 3.10 or newer. From the repository root:

```sh
python labs/memory_lab.py demo
python labs/advanced_lab.py demo
python -m unittest discover -s tests -v
python tools/book.py check
```

On systems where Python is named `python3`, substitute `python3`. On Windows, `py -3` is another common launcher. The examples use the standard library; they require no administrator access, drivers, memory dumps, or DMA hardware.

The lab is a deliberately invented byte format. It is **not** a Windows memory dump, a Unity object layout, or proof of hardware compatibility. The book labels those boundaries at the point where they matter.

## Scope and editions

This edition concentrates on reading and interpreting memory, with controlled state changes in your own fixtures or development builds. It includes the reasoning needed to evaluate acquisition results; it does not promise universal offsets, transparent access through platform protections, or an undetectable device.

Technical references were reviewed on **2026-10-23**. Examples tied to external tools are identified separately from the locally executable labs. See the [source notes](appendices/resources.md) for version-sensitive topics and the [corrections](appendices/corrections.md) for changes from the earlier overview.

## Older chapter bookmarks

The original README contained the whole guide. These landing points preserve its chapter headings while the contents above lead directly to the expanded chapters.

<a id="chapter-1-introduction-to-direct-memory-access-dma"></a>
### Original Chapter 1: Introduction to DMA

Continue to [Chapter 1: Start here](chapters/01-start-here.md).

<a id="chapter-2-preliminary-knowledge"></a>
### Original Chapter 2: Preliminary knowledge

Continue to [Chapter 2: Memory foundations](chapters/02-memory-foundations.md).

<a id="chapter-3-required-tools--equipment"></a>
<a id="chapter-3-required-tools-and-equipment"></a>
### Original Chapter 3: Tools and equipment

Continue to [Chapter 3: Tools and your first lab](chapters/03-tools-and-lab.md).

<a id="chapter-4-identifying-offsets"></a>
### Original Chapter 4: Identifying offsets

Continue to [Chapter 4: Offsets and signatures](chapters/04-offsets-and-signatures.md).

<a id="chapter-5-setting-up-dma"></a>
### Original Chapter 5: Setting up DMA

Continue to [Chapter 5: Acquisition](chapters/05-acquisition.md).

<a id="chapter-6-extracting-game-data-via-dma"></a>
### Original Chapter 6: Extracting data

Continue to [Chapter 6: Reading memory reliably](chapters/06-reading-memory.md).

<a id="chapter-7-modifying-game-data-via-dma"></a>
### Original Chapter 7: Modifying data

Continue to [Chapter 7: Controlled experiments](chapters/07-controlled-experiments.md).

<a id="chapter-8-maintaining-stealth-in-dma-operations"></a>
### Original Chapter 8: Observability

Continue to [Chapter 8: Protections and observability](chapters/08-protections-and-observability.md). The earlier stealth claims are addressed in the [corrections](appendices/corrections.md).

<a id="chapter-9-challenges--pitfalls-in-dma-hacking"></a>
<a id="chapter-9-challenges-and-pitfalls-in-dma-hacking"></a>
### Original Chapter 9: Challenges and pitfalls

Continue to [Chapter 9: Troubleshooting](chapters/09-troubleshooting.md).

<a id="chapter-10-miscellaneous-considerations--advanced-topics-in-dma-hacking"></a>
<a id="chapter-10-miscellaneous-considerations-and-advanced-topics-in-dma-hacking"></a>
### Original Chapter 10: Advanced topics

Continue to [Chapter 10: Unity](chapters/10-unity.md), then [address translation](chapters/11-address-translation.md), [performance](chapters/12-performance.md), and [reproducibility](chapters/13-reproducibility.md).

[Back to contents](#table-of-contents)
