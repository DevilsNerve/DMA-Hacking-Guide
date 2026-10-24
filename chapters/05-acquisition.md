# Chapter 5: Acquisition

<!-- BOOK:NAV:START -->

[Previous: Offsets and signatures](04-offsets-and-signatures.md) · [Contents](../README.MD#table-of-contents) · [Next: Reading memory reliably](06-reading-memory.md)

<!-- BOOK:NAV:END -->

**You will learn:** how an acquisition stack fits together and how to establish a known-good baseline without confusing connection success with readable process memory.

**Before you start:** understand [address spaces](02-memory-foundations.md#addresses). Hardware is optional for this chapter.

<a id="layers"></a>
## Separate the layers

A useful analysis setup has distinct responsibilities:

```text
Analysis application       asks for a typed observation
Decoder                    interprets a specific byte layout
Process-memory view        resolves the process and virtual addresses
Acquisition library        obtains ranges from the selected source
Source                     file, supported live source, or DMA device
```

In the MemProcFS ecosystem, LeechCore supplies acquisition interfaces and MemProcFS supplies higher-level memory analysis, including process views for supported sources. Their supported sources and runtime requirements are documented separately in the [LeechCore wiki](https://github.com/ufrisk/LeechCore/wiki) and [MemProcFS wiki](https://github.com/ufrisk/MemProcFS/wiki).

A file source removes transport timing from the experiment. A live source adds change over time. A hardware source adds device, firmware, driver, topology, and platform-policy variables. Keep these distinctions in the experiment record.

## Start with a source you can describe

For the book's lab, use its own reader. The 512-byte fixture is not a supported operating-system capture and cannot provide MemProcFS with a kernel or process list.

For an actual capture, record its format, acquisition tool, timestamp, and hash. Confirm that the selected analysis tool supports that format and operating system. A raw physical image, crash dump, process minidump, and sparse capture are different inputs even if all have a `.dmp` or `.bin` extension.

For your own live program, begin with a small exported test value and an application-side log. Confirm its identity through a supported software observation path before adding a second acquisition route. This gives you a reference when the routes disagree.

## A hardware setup procedure that produces evidence

1. Identify the exact board, revision, documented firmware, target platform, and acquisition-computer operating system. Save the vendor's matching installation instructions.
2. Draw the physical topology. Label the endpoint that participates on the target bus and the interface that carries captured data to the analysis computer.
3. Follow the board's installation and power instructions. Do not assume a device supports hot-plugging because another connector does.
4. Install only the documented runtime and transport dependencies for that combination. Record versions and preserve a known working configuration.
5. Confirm device enumeration and source initialization before requesting a process view.
6. Check the supported physical ranges and platform protection state. Use documented RAM ranges; arbitrary physical addresses may refer to holes or device registers.
7. Request one small known value from your own test application. Check the address space, requested length, returned length, and decoded result.

An ordinary USB connection does not grant unrestricted access to a target's RAM. Some acquisition devices use USB as a transport while another interface participates in the target's memory-access path. The topology is what matters.

## Keep initialization separate from analysis

An initialization failure should say which layer failed. “No device,” “runtime dependency unavailable,” “unsupported capture,” and “process not found” require different responses.

Do not start a scan until the source and process identity are established. If several processes share a name, use an explicit PID and verify its identity. On a live system, a PID can later be reused; reacquire process and module information after lifecycle changes.

## Deeper detail: file and live observations differ

An immutable file gives repeatable bytes, but its acquisition might have spanned time. It is not automatically an atomic snapshot of the original machine. A live source can change during every step of a pointer walk. A process view can also depend on cached translation and metadata.

Document what the source guarantees. “The same file hash was used” is a reproducibility statement. “All records belonged to one application update” is a stronger consistency statement and needs separate evidence.

## Checkpoint

Your acquisition device initializes, but a process virtual read fails. Name three remaining layers that could explain the failure.

[Check your answer](../appendices/answers.md#chapter-05).

<!-- BOOK:FOOT:START -->

[Previous: Offsets and signatures](04-offsets-and-signatures.md) · [Contents](../README.MD#table-of-contents) · [Next: Reading memory reliably](06-reading-memory.md)

<!-- BOOK:FOOT:END -->
