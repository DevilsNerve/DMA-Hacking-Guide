# Chapter 8: Protections and observability

<!-- BOOK:NAV:START -->

[Previous: Controlled experiments](07-controlled-experiments.md) · [Contents](../README.MD#table-of-contents) · [Next: Troubleshooting](09-troubleshooting.md)

<!-- BOOK:NAV:END -->

**You will learn:** why DMA access is scoped by a platform, why different protections should not be conflated, and how to describe visibility without unsupported guarantees.

**Before you start:** understand the [acquisition layers](05-acquisition.md#layers).

<a id="iommu"></a>
## The device's view is a mapping

An IOMMU translates and restricts device memory accesses. A device can be assigned a domain containing selected mappings. The addresses it uses need not be the CPU's physical addresses, and the mapped range need not include all RAM.

Windows Kernel DMA Protection uses platform support and DMA remapping to limit access from supported external peripherals. Its behavior depends on system support and device/driver configuration. Microsoft's [Kernel DMA Protection documentation](https://learn.microsoft.com/en-us/windows/security/hardware-security/kernel-dma-protection-for-thunderbolt) explains supported configurations and how to inspect the state, including through System Information.

A blocked read can be the expected result of the platform's configuration. Record that result and continue with a supported source or the offline lab. Changing unrelated security settings is not a useful first diagnostic.

## Separate the protections

| Mechanism | What it concerns | Common misunderstanding |
| --- | --- | --- |
| Process access rights | Whether a software reader can obtain/use a process handle | Assuming read-only access needs every process permission |
| CPU virtual-page permissions | CPU access to a mapped page | Assuming they define a device's DMA mappings |
| IOMMU mappings | Device access to permitted memory ranges | Assuming every attached device sees all physical memory |
| Source availability | What the capture or device can actually supply | Treating missing bytes as readable zeros |
| Application invariants | Which combinations of state are meaningful | Assuming writable bytes imply a valid state change |

For Windows software readers, guard pages have special semantics and should not be treated as ordinary readable buffers. Consult the [memory protection definitions](https://learn.microsoft.com/en-us/windows/win32/memory/memory-protection-constants) when implementing region classification. A region map is still a point-in-time observation; the read itself must handle change.

## “External” is not a visibility guarantee

A device can be enumerated. Firmware and drivers have identities and behavior. Memory changes can affect application state. Platform components can observe faults, topology, or other signals. The fact that a reader does not inject a user-mode library does not establish that the whole setup is invisible.

Similarly, changing an identifier or varying polling intervals does not demonstrate undetectability. A claim about visibility needs a defined observer, a specific measurement, and a described environment. “No warning appeared” is much weaker than “this component did not record this particular event during this test.”

The earlier guide presented several stealth claims without this evidence. This edition replaces them with a measurable question: what does the system expose, what did your experiment observe, and what remains unknown?

## Collect diagnostics that help

For your own lab, record device enumeration, runtime versions, source initialization, supported ranges, process identity, and read failures. Avoid dumping unrelated memory into logs just to prove that a connection works.

If you maintain the target application, its own telemetry can reveal missed updates and inconsistent reads much more directly than guessing from the reader alone. This is especially useful when comparing a file-backed baseline with a live source.

## Deeper detail: a threat model is a set of questions

For a defensive platform review, ask which devices are trusted, which ranges they can access, when mappings exist, and what changes across boot, lock, sleep, and resume. Test documented policy with a controlled workload and retain the exact platform state. Avoid generalizing a result from one machine to another with different firmware or topology.

This also improves ordinary engineering. It turns “DMA does not work” into a specific finding such as “source initialization succeeds, but the configured device mapping does not supply the requested range.”

## Checkpoint

A software process read succeeds while a device read of what you believe is the same location fails. Does that prove the device is faulty? What context is missing?

[Check your answer](../appendices/answers.md#chapter-08).

<!-- BOOK:FOOT:START -->

[Previous: Controlled experiments](07-controlled-experiments.md) · [Contents](../README.MD#table-of-contents) · [Next: Troubleshooting](09-troubleshooting.md)

<!-- BOOK:FOOT:END -->
