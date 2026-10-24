# Chapter 1: Start here

<!-- BOOK:NAV:START -->

[Contents](../README.MD#table-of-contents) · [Next: Memory foundations](02-memory-foundations.md)

<!-- BOOK:NAV:END -->

**You will learn:** what DMA contributes to memory analysis, which skills transfer between tools, and what counts as a useful first result.

**Before you start:** you only need to be comfortable opening a terminal and running a command. If hexadecimal notation is new, the next chapter explains it.

## A concrete question

Imagine a small program that displays a health value of `87.5`. You want a second tool to observe that value. Before choosing any hardware, you need answers to four questions:

1. Where is the value stored?
2. How is it represented as bytes?
3. Can your reader obtain those bytes from the right address space?
4. How will you tell that the observation is current and correct?

DMA can help with the third question. It does not automatically answer the other three. Much of this book is about those other questions, because they remain important whichever acquisition tool you use.

## What DMA actually means

Direct memory access lets a device transfer data to or from memory without the CPU copying each byte itself. Normal computers use DMA constantly: storage devices, network adapters, and graphics hardware all need efficient data movement.

The CPU and operating system can still configure the transfer, establish mappings, and handle completion. “Direct” describes a data-transfer mechanism; it does not mean that the device operates outside all system control. The [Linux DMA documentation](https://docs.kernel.org/core-api/dma-api-howto.html) explains the distinction between the addresses software uses and the addresses devices use.

For analysis, think of a pipeline:

```text
memory source -> acquisition -> address translation -> bytes -> decoder -> evidence
```

Each arrow can fail independently. A device can be connected while a particular memory range remains inaccessible. A read can succeed while your decoder uses the wrong field layout. A decoded number can be plausible while belonging to an unrelated object.

## Three ways to practice

| Route | What it teaches | What it cannot prove |
| --- | --- | --- |
| Synthetic byte image | Types, pointers, bounds, failures, repeatability | Operating-system translation or hardware behavior |
| Your own live program or captured image | Real object lifetime and process context | Compatibility with every acquisition device |
| Authorized hardware acquisition | Transport, platform mappings, latency, source availability | Correctness of your field interpretation by itself |

Start with the first route. It removes several variables at once. When something goes wrong, you can inspect the entire input and compare it with a known answer.

## How to read the book

The main text builds a working explanation. Sections marked **Deeper detail** deal with assumptions that matter when you build a tool. Checkpoints ask you to explain a result, rather than memorize terminology. Answers are linked at the end of each chapter.

You will see the same small record repeatedly: a root pointer, a health value, and a short list of item IDs. Keeping the example familiar lets us change one idea at a time. The layout is invented for teaching and is documented completely in the [lab reference](../labs/README.md#layout).

When a chapter discusses an external API, treat the linked upstream documentation as the authority for your installed version. A conceptual diagram is not an executable API, and a successful synthetic test is not a hardware test.

## Your first milestone

Run the demo, obtain `health=87.5`, then intentionally break the root pointer and explain the resulting error. That is already meaningful progress: you have a reader that can distinguish one valid record from one invalid record.

Later milestones add address-space awareness, lifecycle handling, consistency checks, and measurements. Speed becomes useful once the observations are trustworthy.

## Checkpoint

Your tool reads four bytes successfully and prints `100`. What evidence would establish that this is the current health value rather than an unrelated integer?

[Compare your reasoning with the answer](../appendices/answers.md#chapter-01).

<!-- BOOK:FOOT:START -->

[Contents](../README.MD#table-of-contents) · [Next: Memory foundations](02-memory-foundations.md)

<!-- BOOK:FOOT:END -->
