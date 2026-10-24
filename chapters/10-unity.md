# Chapter 10: Unity in practice

<!-- BOOK:NAV:START -->

[Previous: Troubleshooting](09-troubleshooting.md) · [Contents](../README.MD#table-of-contents) · [Next: Address translation](11-address-translation.md)

<!-- BOOK:NAV:END -->

**You will learn:** how Unity's scripting backend affects analysis, why managed and native state need separate treatment, and how to build a small experiment with known ground truth.

**Before you start:** understand [object lifetime](02-memory-foundations.md) and [controlled experiments](07-controlled-experiments.md). The optional exercise requires your own Unity project.

## Establish the build identity first

Record the Unity editor version, target platform, architecture, scripting backend, development/release settings, and relevant binary hashes. The editor environment and a built player can differ. Two builds from the same project need not preserve layout or code locations.

Unity supports different scripting backends. Mono and IL2CPP take different compilation routes; IL2CPP converts managed assemblies through C++ into native code ahead of time. Backend support also depends on the target platform. Consult the matching Unity manual for [backend choices](https://docs.unity3d.com/Manual/scripting-backends.html) and [IL2CPP](https://docs.unity3d.com/6000.0/Documentation/Manual/scripting-backends-il2cpp.html).

| Evidence | What it can tell you | What it does not establish alone |
| --- | --- | --- |
| Project source | Intended types and behavior | Exact runtime offsets |
| Managed metadata | Type and member relationships that survived the build | A live instance's location |
| Native symbols and generated artifacts | Relationships for that specific build | Compatibility with another build |
| Profiler and application logs | Allocation and state behavior | Universal external object layouts |
| Memory observation | Bytes at a place and time | Their meaning without supporting evidence |

<a id="layouts"></a>
## Managed and native objects are different views

A C# object can contain runtime bookkeeping, fields, references, and padding. A `UnityEngine.Object` can also represent an engine object with a native side. A C# reference is not a promise that every property is stored inline in that managed object's bytes.

Properties may execute code. Collections have their own layouts. A list's capacity differs from its logical count. A string requires a verified encoding and length representation. A `Vector3` value in a known serialized schema is straightforward; locating the current transform of an engine object is a different problem.

Avoid publishing a universal table such as “every Unity object has health at offset X.” Derive and version the layout for the specific application, backend, and architecture you actually inspected.

## Garbage collection is only part of lifetime

Do not assume all managed runtimes move objects, or that a non-moving collector makes an address permanent. Unity's documented collector behavior is version-specific; see the [garbage collector overview](https://docs.unity3d.com/6000.0/Documentation/Manual/performance-garbage-collector.html). An object can still become unreachable, be destroyed at the engine level, or be replaced by a new instance.

Scene changes, collection growth, domain reload behavior, and pooling can all change what a previously observed reference means. Revalidate identity after those events.

<a id="unity-lab"></a>
## Optional lab: observe your own component

Create an empty project or a disposable scene. Add a file named `MemoryObservationLab.cs` with the following component, then attach it to one active GameObject:

```csharp
using UnityEngine;

public sealed class MemoryObservationLab : MonoBehaviour
{
    public float Health = 87.5f;
    private uint generation;

    [ContextMenu("Lab/Set health to 60")]
    private void SetHealthTo60()
    {
        Health = 60.0f;
        generation++;
        Debug.Log($"Lab generation={generation} health={Health:R}");
    }

    [ContextMenu("Lab/Reset health")]
    private void ResetHealth()
    {
        Health = 87.5f;
        generation++;
        Debug.Log($"Lab generation={generation} health={Health:R}");
    }
}
```

Enter Play mode. Use the component's context menu to set and reset health. Observe the Inspector and Console. Clear existing Console messages before recording the sequence. The generation is an experiment label; it is not a remote-memory synchronization protocol.

For an analysis exercise, use your project's supported debugger and symbols to inspect the field. Record the object instance and exact build context. Reload the scene and repeat. Then, if your platform supports both backends, compare a separate Mono build and IL2CPP build using the corresponding supported tooling. Preserve separate records for each.

The expected application behavior is a logged transition to `60` and back to `87.5`. This repository does not include a Unity project or claim a tested editor/player build. The Python lab remains the reproducible automated baseline.

## Deeper detail: choose a stable observation interface

When building your own tooling, an explicit exported snapshot can be more maintainable than depending on private runtime structures. Give it a version, byte order, field sizes, bounds, and a documented publication protocol. Your application can translate engine objects into that format internally.

This is also a useful comparison experiment: use the exported snapshot as ground truth while investigating internal layouts, and record where the views differ in timing or meaning.

## Checkpoint

A C# class has three declared fields. Why can you not determine all external byte offsets by adding the apparent sizes of those fields?

[Check your answer](../appendices/answers.md#chapter-10).

<!-- BOOK:FOOT:START -->

[Previous: Troubleshooting](09-troubleshooting.md) · [Contents](../README.MD#table-of-contents) · [Next: Address translation](11-address-translation.md)

<!-- BOOK:FOOT:END -->
