# Corrections to the earlier guide

[Book contents](../README.MD#table-of-contents)

The earlier edition was a broad overview in one README. This revision keeps the learning topic while replacing claims that could lead a reader to diagnose the wrong problem.

| Earlier implication | Corrected explanation | Details |
| --- | --- | --- |
| DMA bypasses every form of CPU or platform control | Devices can transfer data without CPU byte-copying while still using platform configuration and mappings | [Start here](../chapters/01-start-here.md) |
| A process address can be sent directly to a physical reader | Virtual, physical, device, and file addresses need their own context and translation | [Address spaces](../chapters/02-memory-foundations.md#addresses) |
| An ordinary USB connection grants target-memory access | Acquisition topology and supported device interfaces determine the access path | [Acquisition](../chapters/05-acquisition.md) |
| Subtracting a module base from a heap address produces a stable offset | Module-relative locations and object-relative fields have different lifetimes | [Offsets](../chapters/04-offsets-and-signatures.md#offset-types) |
| DMA hardware is inherently invisible or identifiers prove stealth | Visibility depends on specific observers and measurements; no blanket guarantee follows | [Observability](../chapters/08-protections-and-observability.md) |
| An external DMA poller can automatically set CPU watchpoints | Event-driven observation requires a supported event mechanism | [Performance](../chapters/12-performance.md) |
| Memory protection can be changed generically through a DMA device | CPU page permissions and device mappings are separate mechanisms | [Protections](../chapters/08-protections-and-observability.md#iommu) |
| Saving old bytes makes live rollback safe | Object lifetime and intervening updates can invalidate restoration | [Controlled experiments](../chapters/07-controlled-experiments.md) |
| Unity source fields imply a universal external layout | Runtime, backend, architecture, and build affect representation | [Unity](../chapters/10-unity.md#layouts) |
| DMA is always faster than software observation | End-to-end performance depends on overhead, workload, source, and freshness requirements | [Measurement](../chapters/12-performance.md#measurement) |

The original contents links were shifted to the preceding chapter, and the return links targeted Chapter 10. The current contents link directly to chapter files. Every chapter has previous/contents/next navigation at both ends, and the README keeps landing anchors for the original chapter headings.

The exact old edition remains available in Git history. The current guide concentrates its practical exercises on synthetic data and programs the reader controls, where expected results can be independently established.

[Back to contents](../README.MD#table-of-contents)
