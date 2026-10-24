# Chapter 7: Controlled experiments

<!-- BOOK:NAV:START -->

[Previous: Reading memory reliably](06-reading-memory.md) · [Contents](../README.MD#table-of-contents) · [Next: Protections and observability](08-protections-and-observability.md)

<!-- BOOK:NAV:END -->

**You will learn:** how to establish that a field means what you think it means, and how to study changes without confusing a readable value with an authoritative one.

**Before you start:** understand [exact reads and consistency](06-reading-memory.md).

## Ask one question at a time

Suppose two addresses both contain `87.5`. One might be current health, another a UI animation target, and another a saved checkpoint. Matching a displayed number is a useful clue, but it does not identify the authoritative state.

Write a prediction before the experiment: “When I set health to 60 through my application's debug control, this field should become the binary32 representation of 60 within one published update.” Then change only health, record the application's own log, and compare candidate observations.

Repeat with a second value and a lifecycle change such as reloading the scene. A locator that works only until the first object recreation is not yet a reliable locator.

## Use the fixture to practice causal reasoning

The valid fixture has a documented record and known item list. Its fault variants change one property at a time:

| Change | Question being tested |
| --- | --- |
| Null root | Does the reader refuse to dereference an absent object? |
| Excessive count | Is the length bounded before array access? |
| Odd sequence | Does the reader reject a record marked as being updated? |
| Mismatched sequence | Does it reject inconsistent record markers? |
| NaN health | Does the decoder distinguish a float bit pattern from a valid measurement? |
| Truncated image | Does missing data remain a read failure? |

Run each case using the [failure lab](../labs/README.md#failure-lab). A clear failure is a correct outcome. The purpose is to understand the boundary between supported data and unsupported data.

## Change your own program through a supported control

In a development build, a debug button or test command can update state through the same code path used by the application. That preserves application invariants and gives you a known cause. Observe the memory afterward to study representation.

For Unity, the [instrumented-build exercise](10-unity.md#unity-lab) changes a field from application code and logs the value. It teaches the relationship between state, representation, and observation without requiring a universal object layout.

If your goal is a mod or extension, check whether the program already exposes a plugin API, scripting interface, or supported data format. That interface can express intent more reliably than editing an implementation detail.

## Why a raw write is a different experiment

A write can race with the application's own updates, target an object whose lifetime ended, break a checksum or invariant, or update a cached copy that the application immediately replaces. A saved old value does not automatically make rollback safe: restoring it later can overwrite legitimate intervening changes.

Study mutation on disposable fixtures or in a purpose-built test program whose ownership and synchronization rules you control. Define the expected transition and recovery method before the experiment. For a file fixture, recovery is simply regeneration. For a live object, recovery belongs to the application's lifecycle, not just to an old byte buffer.

CPU page permissions and device DMA mappings are separate mechanisms. A physical-access interface is not a general replacement for an operating-system page-protection API; see [Chapter 8](08-protections-and-observability.md).

## Deeper detail: local observation and authority

A networked application may retain predicted, interpolated, replicated, and authoritative versions of related state. A local value changing does not show that a server accepted the change. Even offline software can maintain multiple derived caches.

Label the claim narrowly: “This client-side field changed after this input.” Expand it only when you can trace how the application consumes the field. This habit makes debugging faster because it separates what you observed from what you inferred.

## Checkpoint

A candidate field changes when health changes, but also changes during a menu animation while health stays constant. What should happen to your hypothesis?

[Check your answer](../appendices/answers.md#chapter-07).

<!-- BOOK:FOOT:START -->

[Previous: Reading memory reliably](06-reading-memory.md) · [Contents](../README.MD#table-of-contents) · [Next: Protections and observability](08-protections-and-observability.md)

<!-- BOOK:FOOT:END -->
