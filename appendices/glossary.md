# Glossary

[Book contents](../README.MD#table-of-contents) · [Topic finder](../README.MD#topic-finder)

Read these as working definitions for the book. Platform documentation may use more specific terminology.

| Term | Meaning | Where to use it |
| --- | --- | --- |
| ABI | Application binary interface: rules governing binary-level representation and calling conventions | [Layouts](../chapters/02-memory-foundations.md) |
| Address space | The context in which an address identifies a location | [Address spaces](../chapters/02-memory-foundations.md#addresses) |
| Alignment | Placement of data at boundaries required or preferred by a representation | [Memory foundations](../chapters/02-memory-foundations.md) |
| AOT | Ahead-of-time compilation, performed before program execution | [Unity](../chapters/10-unity.md) |
| ASLR | Address space layout randomization; one reason loaded addresses can vary | [Offsets](../chapters/04-offsets-and-signatures.md) |
| Backpressure | A way to handle producers generating work faster than consumers can finish it | [Performance](../chapters/12-performance.md) |
| Binary32 | A 32-bit floating-point representation used for the lab's health field | [Bytes and types](../chapters/02-memory-foundations.md#bytes) |
| Build identity | Evidence distinguishing the exact application or module build being analyzed | [Reproducibility](../chapters/13-reproducibility.md) |
| Byte order | The ordering of bytes in a multi-byte value; also called endianness | [Bytes and types](../chapters/02-memory-foundations.md#bytes) |
| Cache | Previously obtained data reused to avoid another lookup or transfer | [Caching](../chapters/12-performance.md) |
| Code point | A value in Unicode's character-representation space | [Text length units](../chapters/15-strings-and-collections.md#text-units) |
| Code unit | A unit of an encoding, such as one 16-bit unit in UTF-16 | [Text length units](../chapters/15-strings-and-collections.md#text-units) |
| DMA | Direct memory access: a device data-transfer mechanism | [Start here](../chapters/01-start-here.md) |
| DTB | Directory table base; a name used for a translation-root context in some tooling | [Translation](../chapters/11-address-translation.md) |
| Exact read | An operation that supplies all requested bytes or reports failure | [Reliable reads](../chapters/06-reading-memory.md) |
| Field offset | Distance from the start of a specified object or record to a field | [Offset types](../chapters/04-offsets-and-signatures.md#offset-types) |
| File offset | Byte position within a specific file, starting from its beginning | [Address spaces](../chapters/02-memory-foundations.md#addresses) |
| Fixture | Controlled test input with known properties and expected behavior | [Lab](../labs/README.md) |
| FPGA | Field-programmable gate array, a configurable hardware device | [Equipment](../chapters/03-tools-and-lab.md#equipment) |
| Generation | A producer-defined identifier used to distinguish updates or object lifetimes | [Consistency](../chapters/06-reading-memory.md#consistency) |
| IOMMU | Input/output memory management unit; translates and restricts device access | [Protections](../chapters/08-protections-and-observability.md#iommu) |
| IOVA | I/O virtual address used within a device mapping context | [Translation](../chapters/11-address-translation.md) |
| IL2CPP | Unity's scripting backend that translates managed code through C++ to native code | [Unity](../chapters/10-unity.md) |
| Invariant | A condition that must hold for data to be valid under a schema or protocol | [Experiments](../chapters/07-controlled-experiments.md) |
| Little-endian | Byte order with the least significant byte first | [Bytes and types](../chapters/02-memory-foundations.md#bytes) |
| Module | A loaded executable image or library in a process context | [Offsets](../chapters/04-offsets-and-signatures.md) |
| Monotonic clock | A clock suitable for elapsed-time measurements because its readings do not go backwards | [Polling and replay](../chapters/18-polling-and-replay.md) |
| Mono | A runtime/backend used by supported Unity configurations | [Unity](../chapters/10-unity.md) |
| Null pointer | A pointer representation indicating no object, zero in this lab | [Pointer walk](../chapters/02-memory-foundations.md) |
| Page | A unit used by memory mapping; its size depends on the architecture and mapping | [Translation](../chapters/11-address-translation.md) |
| Physical address | An address in the platform's physical memory map | [Address spaces](../chapters/02-memory-foundations.md#addresses) |
| PID | Process identifier; meaningful within a system and lifetime context | [Acquisition](../chapters/05-acquisition.md) |
| Pointer | A value representing an address under a target's representation rules | [Memory foundations](../chapters/02-memory-foundations.md) |
| Pointer chain | A sequence of pointer reads and offset calculations | [Offsets](../chapters/04-offsets-and-signatures.md) |
| Replay | Feeding recorded or synthetic observations to a consumer in a defined order | [Replay states](../chapters/18-polling-and-replay.md#state-transitions) |
| RVA | Relative virtual address measured from an image's loaded base | [Offset types](../chapters/04-offsets-and-signatures.md#offset-types) |
| Scatter/gather | An interface for handling multiple discontiguous ranges in a batch | [Performance](../chapters/12-performance.md) |
| Schema | A documented set of layout and validation rules | [Reproducibility](../chapters/13-reproducibility.md) |
| Semantic comparison | Comparison of decoded meaning under an explicit identity and field policy | [Comparing captures](../chapters/17-comparing-captures.md#semantic-comparison) |
| Signature | A byte pattern used to locate candidates | [Signatures](../chapters/04-offsets-and-signatures.md) |
| Snapshot | A captured view whose consistency guarantees must be specified | [Consistency](../chapters/06-reading-memory.md#consistency) |
| Stale pointer | A retained pointer whose original object identity or validity no longer holds | [Troubleshooting](../chapters/09-troubleshooting.md) |
| Stride | Number of bytes from one element's start to the next element's start | [Collections](../chapters/15-strings-and-collections.md) |
| Symbol file | Build-specific debugging information relating names and other metadata to binary locations | [Modules and symbols](../chapters/16-modules-and-symbols.md) |
| Tearing | An observation combining parts of different updates | [Consistency](../chapters/06-reading-memory.md#consistency) |
| Virtual address | An address interpreted through a particular virtual-memory context | [Translation](../chapters/11-address-translation.md) |
| Wire format | An explicit byte representation independent of ordinary in-memory compiler layout | [Lab layout](../labs/README.md#layout) |
| WOW64 | Windows compatibility environment for running supported 32-bit applications on 64-bit Windows | [Pointer width](../chapters/02-memory-foundations.md) |

[Back to contents](../README.MD#table-of-contents)
