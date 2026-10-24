# Chapter 11: Address translation

<!-- BOOK:NAV:START -->

[Previous: Unity in practice](10-unity.md) · [Contents](../README.MD#table-of-contents) · [Next: Performance and freshness](12-performance.md)

<!-- BOOK:NAV:END -->

**You will learn:** what a process-memory view must resolve, why page boundaries matter, and why translation success does not guarantee source availability.

**Before you start:** be comfortable with the [address-space table](02-memory-foundations.md#addresses). This chapter is reference material; you do not need to implement a page-table walker to complete the lab.

## A virtual address is a question in a process context

The operating system uses translation structures to map virtual pages to backing memory. The appropriate process context matters: the same virtual address can resolve differently in two processes.

A translation service needs the architecture, translation mode, relevant root, and readable translation structures. Debuggers expose this relationship explicitly; Microsoft's [virtual-to-physical conversion guide](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/converting-virtual-addresses-to-physical-addresses) illustrates the need for the correct process and directory base.

Do not use a page-table root from one capture or process as though it were a timeless property of an executable name.

## A simplified x86-64 map

For the specific case of four-level x86-64 paging with a 4 KiB page, a virtual address is divided into four nine-bit indices and a twelve-bit page offset. The indices select successive translation entries; the final mapping supplies the physical page base. Other modes and larger pages change the walk.

```text
virtual address
  -> index into first table
  -> index into second table
  -> index into third table
  -> index into fourth table
  -> mapped page base + offset within page
```

This is an explanatory model, not a complete implementation. A real walker must handle mode-specific address validity, entry flags, supported physical address widths, large-page termination, and unavailable entries. Intel's [system programming manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html) are the architectural reference.

## A request can cross two different mappings

Assume 4 KiB pages. A sixteen-byte read starting at virtual address `0x1FF8` contains eight bytes from the page ending at `0x1FFF` and eight from the next page starting at `0x2000`.

```text
first segment:  VA 0x1FF8, length 8
second segment: VA 0x2000, length 8
```

The physical pages need not be adjacent. The second page may be unavailable even if the first is readable. Translating the first byte and then reading sixteen consecutive physical bytes can therefore return unrelated data.

An exact-read interface should preserve this failure. A scanner may deliberately skip unavailable regions, but it must not join the surrounding bytes into a fictitious contiguous range.

## Unavailable pages have several explanations

Some virtual pages have no resident physical backing at the moment of observation. Captures may omit pages. A physical source may not include data held in another backing store. Translation metadata itself may be incomplete. A live mapping may change between reading the translation and reading the payload.

Report what you know: “The process view could not supply all sixteen bytes.” Avoid turning that directly into “the object does not exist” or “the device is broken.”

## Deeper detail: there can be more than one translation boundary

Virtualized environments add distinctions between guest virtual, guest physical, and host physical addresses. Device mappings introduce another address space. A number obtained in one layer must be translated by the appropriate mechanism before use in another.

Maintain explicit types or labels in your design: `ProcessVA`, `GuestPA`, `HostPA`, and `DeviceAddress` are conceptually different even if represented as the same integer width. This prevents accidental cross-layer arithmetic.

## A useful exercise without real page tables

On paper, map virtual page `0x1000` to physical page `0x9000` and virtual page `0x2000` to physical page `0x3000`. Split the sixteen-byte request above. The correct source ranges are `0x9FF8..0x9FFF` and `0x3000..0x3007`, in that order.

Now mark the second mapping unavailable. The observation becomes incomplete. Padding it with zeros would create a different sixteen-byte sequence rather than recover the missing evidence.

## Checkpoint

Why can a successful translation of the first byte of a structure be insufficient to read the whole structure?

[Check your answer](../appendices/answers.md#chapter-11).

<!-- BOOK:FOOT:START -->

[Previous: Unity in practice](10-unity.md) · [Contents](../README.MD#table-of-contents) · [Next: Performance and freshness](12-performance.md)

<!-- BOOK:FOOT:END -->
