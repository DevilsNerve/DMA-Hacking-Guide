# Sources and further reading

[Book contents](../README.MD#table-of-contents) · [Glossary](glossary.md)

References reviewed on **2026-10-23**. These are primary documentation sources. Follow documentation matching your installed version; a link to a current manual is not a compatibility guarantee for an older runtime.

## Memory and platform behavior

| Source | Read it for |
| --- | --- |
| [Linux kernel DMA mapping guide](https://docs.kernel.org/core-api/dma-api-howto.html) | CPU, physical, and device addresses; DMA mapping responsibilities |
| [Microsoft PE format](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format) | RVA terminology, executable sections, and on-disk versus loaded representation |
| [ReadProcessMemory](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-readprocessmemory) | Windows software-read permissions and return contract |
| [Windows memory protection constants](https://learn.microsoft.com/en-us/windows/win32/memory/memory-protection-constants) | Page protections and guard-page behavior |
| [Windows Kernel DMA Protection](https://learn.microsoft.com/en-us/windows/security/hardware-security/kernel-dma-protection-for-thunderbolt) | Platform support, remapping, and checking the configured state |
| [Debugger virtual-to-physical conversion](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/converting-virtual-addresses-to-physical-addresses) | Translation in an explicit process context; examples are architecture-specific |
| [Intel architecture manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html) | Paging details and instruction encodings; select the applicable architecture and volume |

## Acquisition APIs

| Source | Read it for |
| --- | --- |
| [LeechCore documentation](https://github.com/ufrisk/LeechCore/wiki) | Acquisition sources and backend-specific requirements |
| [MemProcFS documentation](https://github.com/ufrisk/MemProcFS/wiki) | Supported analysis sources and overall tool behavior |
| [MemProcFS Python base API](https://github.com/ufrisk/MemProcFS/wiki/API_Python_Base) | Creating and closing a VMM session and selecting a process |
| [MemProcFS Python process API](https://github.com/ufrisk/MemProcFS/wiki/API_Python_Process) | Process virtual-memory reads and process/module views |
| [MemProcFS C API](https://github.com/ufrisk/MemProcFS/wiki/API_C) | Native integration and ownership conventions; use the matching SDK header |

The integration sketch in Chapter 6 was checked against the documented Python API shape. It was not executed against a real capture or DMA device as part of this edition. The dependency-free Python fixtures exercise the book's own format only. External projects retain their own licenses and distribution requirements.

## Unity

| Source | Read it for |
| --- | --- |
| [Scripting backends](https://docs.unity3d.com/Manual/scripting-backends.html) | Backend choices and platform support; this unversioned link follows current documentation |
| [Unity 6 IL2CPP overview](https://docs.unity3d.com/6000.0/Documentation/Manual/scripting-backends-il2cpp.html) | The ahead-of-time compilation route |
| [Unity 6 garbage collector overview](https://docs.unity3d.com/6000.0/Documentation/Manual/performance-garbage-collector.html) | Runtime-specific collection behavior |
| [Unity ContextMenu attribute](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/ContextMenu.html) | Invoking the optional exercise's component commands in the Inspector |

The optional Unity component is an instructional exercise, not a bundled or validated Unity project. Preserve your editor version and build settings when recording results.

## Decoding and book maintenance

| Source | Read it for |
| --- | --- |
| [Python struct module](https://docs.python.org/3/library/struct.html) | Explicit byte order, standard widths, and binary decoding |
| [GitHub Markdown syntax](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax) | Relative links, heading links, and custom anchors |

## How to add a source

Place the link beside the claim it supports, then add it here if it is useful beyond that paragraph. Describe the specific scope of the source. Prefer a vendor manual, project API reference, architecture specification, or reproducible experiment over a claim repeated in a forum.

When evidence changes, update the explanation and its limitations together. Do not turn a single successful configuration into a universal statement.

[Back to contents](../README.MD#table-of-contents)
