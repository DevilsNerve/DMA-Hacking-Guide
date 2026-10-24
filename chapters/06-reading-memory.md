# Chapter 6: Reading memory reliably

<!-- BOOK:NAV:START -->

[Previous: Acquisition](05-acquisition.md) · [Contents](../README.MD#table-of-contents) · [Next: Controlled experiments](07-controlled-experiments.md)

<!-- BOOK:NAV:END -->

**You will learn:** the contract a reader should provide, how to handle partial reads, and why a group of individually valid fields can still form an invalid observation.

**Before you start:** work through the lab's root-pointer example and read [acquisition](05-acquisition.md).

## Make the reader's promise explicit

A useful primitive is `read_exact(address, size)`: return exactly the requested bytes or report a failure. It should never silently substitute zeros for missing data.

Before the request, validate the address range and a reasonable size limit. After the request, verify the actual length. Preserve enough context in errors to identify the failed range without logging unrelated memory contents.

The supplied [lab reader](../labs/memory_lab.py) enforces this contract against a bounded byte image. It then performs a separate decoding step. The separation lets the same decoder design be evaluated independently from a future acquisition backend.

Windows `ReadProcessMemory` uses a process handle with the appropriate access rights and reports transfer results through its return value and byte-count output. The [API contract](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-readprocessmemory) should guide a Windows backend; do not infer success from a preinitialized output buffer.

## Recognize the MemProcFS API boundary

The following is an **integration sketch**, not part of the executable synthetic lab. It requires a supported capture, an installed compatible MemProcFS Python environment, and a PID and virtual address independently identified in that capture. Replace every placeholder before using it.

```python
import memprocfs

capture_path = "PATH_TO_YOUR_SUPPORTED_CAPTURE"
pid = 1234                 # Replace with a verified PID from this capture.
address = 0x12340000        # Replace with a verified process virtual address.
size = 4

vmm = memprocfs.Vmm(["-device", capture_path])
try:
    process = vmm.process(pid)
    data = process.memory.read(address, size)
    if len(data) != size:
        raise RuntimeError(f"short read: expected {size}, received {len(data)}")
    print(data.hex(" "))
finally:
    vmm.close()
```

The [base API](https://github.com/ufrisk/MemProcFS/wiki/API_Python_Base) describes initialization and cleanup; the [process API](https://github.com/ufrisk/MemProcFS/wiki/API_Python_Process) describes virtual reads. Physical reads use a different object. Confirm flags and failure behavior against your installed version. Do not enable failure-padding options when exact availability is part of your evidence.

This sketch has no hardware acceptance claim. Its purpose is to show where the exact-read contract belongs when you connect a real source.

## Validate before following the next pointer

The lab reads the root slot, rejects null, checks the record header, checks the sequence fields, validates health and count, then reads the item array. The count is bounded before it controls a read length.

For linked structures, also maintain a visited-address set, a maximum node count, and a maximum depth. A cycle can be a valid feature of some formats, but your traversal still needs a termination rule. For strings, specify encoding and maximum bytes or code units; a missing terminator must not create an unlimited read.

Treat “unavailable,” “invalid,” and “valid value zero” as different outcomes. This distinction should survive all the way to your output format.

<a id="consistency"></a>
## Multiple reads can describe different moments

Suppose your program replaces a list:

```text
reader observes old pointer
writer installs new pointer and new count
reader observes new count
reader reads old allocation using new count
```

Each scalar read can succeed. The combined interpretation can still be wrong.

When you control the producer, publish a stable snapshot using a documented synchronization protocol. For example, a producer can mark an update in progress with an odd sequence, write a complete record, and publish an even sequence after completion. A reader observes the sequence, copies the payload, and observes the sequence again; it accepts only equal even values.

That description is a protocol sketch. A real implementation needs the language's memory-ordering rules, appropriate access widths, and an acquisition path that does not return stale sequence bytes. It must also keep referenced data valid for the read. Merely adding two integer fields does not make arbitrary remote reads atomic.

The lab's beginning and ending sequence fields demonstrate **validation of a static record**. They detect its deliberately malformed fixtures. They do not implement a live producer or prove a concurrent snapshot algorithm.

## Deeper detail: retries need a budget

A retry may recover from a transient change, but retrying forever can hide a broken layout. Set a limit, record the reason, and return an explicit unavailable result when the budget is exhausted.

Re-reading a pointer and getting the same value is useful but incomplete. An allocation can disappear and another object can reuse the address between observations—the ABA problem. A producer-provided generation or object ID can strengthen identity checks when its lifetime rules are known.

## Checkpoint

You successfully read a list pointer and count, but reading the list fails intermittently. Why might adding retries help without fixing the underlying consistency problem?

[Check your answer](../appendices/answers.md#chapter-06).

<!-- BOOK:FOOT:START -->

[Previous: Acquisition](05-acquisition.md) · [Contents](../README.MD#table-of-contents) · [Next: Controlled experiments](07-controlled-experiments.md)

<!-- BOOK:FOOT:END -->
