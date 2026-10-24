# Chapter 9: Troubleshooting

<!-- BOOK:NAV:START -->

[Previous: Protections and observability](08-protections-and-observability.md) · [Contents](../README.MD#table-of-contents) · [Next: Unity in practice](10-unity.md)

<!-- BOOK:NAV:END -->

**You will learn:** how to isolate a failure without changing several unrelated settings at once.

**Before you start:** know which acquisition route you are using and keep one known-good fixture nearby.

## Work outward from a known result

When a full application fails, reduce the question. Can the fixture parser still decode the known image? Can the source initialize? Can it supply one known range? Can the process view resolve the expected module? Can the decoder reject an intentionally invalid record?

The first failing boundary is more useful than the last error printed by a complicated scan. Preserve the first error and the relevant input; downstream “not found” messages may only be consequences.

<a id="symptoms"></a>
## Start with the symptom

| Symptom | Plausible cause | Smallest useful next check |
| --- | --- | --- |
| Python command not found | Launcher name or installation differs | Check `python --version`, `python3 --version`, or `py -3 --version` |
| Fixture file not found | Command run from another directory | Confirm the path relative to the repository root |
| Source fails to initialize | Device, dependency, format, or configuration mismatch | Save the initialization error and check the documented supported combination |
| Process name returns the wrong instance | Several matching names | Select a verified PID and record process identity |
| Every field is zero | Genuine zeros, wrong location, or failure padding | Check exact returned lengths and raw bytes for one known field |
| Huge or negative item count | Wrong type, layout, byte order, or stale object | Compare the bounded record header and raw count bytes |
| Health is NaN or implausible | Wrong representation or invalid sample | Verify float width, byte order, object identity, and finite-value rules |
| Works until restart | Absolute address retained across lifecycles | Resolve the root and module base again |
| Works until a scene reload | Object was destroyed or replaced | Reacquire object identity and invalidate cached pointers |
| Fails at a page boundary | Second page unavailable or translated incorrectly | Split the request and inspect each page's availability |
| Pattern missing near chunk edges | Overlap handling error | Test a fixture with a match crossing a chunk boundary |
| Pattern appears across a hole | Noncontiguous data concatenated | Reset scanner overlap at the unreadable gap |
| Values lag behind the application | Cache, polling interval, or backlog | Compare source sequence IDs and acquisition timestamps |
| Fast loop, few useful samples | Repeated stale data or failed batches | Count unique valid generations, not only API calls |

These are hypotheses, not diagnoses. A symptom can have several causes. Choose a check that distinguishes them.

## A worked diagnosis: the believable wrong number

You expect `87.5`, but your tool prints `1118765056`. The read succeeded and returned four bytes. The raw bytes are `00 00 AF 42`.

Before questioning the device, decode the same bytes both ways using [Chapter 2's example](02-memory-foundations.md#bytes). The integer output exactly matches the observed failure. You have evidence for a type mismatch.

Now verify the schema says binary32 and change only the decoder. Rerun the known fixture and one intentionally invalid float case. The repair is justified by the bytes and the documented format, not by the fact that the new number looks nicer.

## A worked diagnosis: intermittent list failures

Suppose the header is valid but the item read sometimes fails. Capture the root, count, pointer, sequence values, requested range, and failure time. If failures cluster around object replacement, the likely issue is lifetime or consistency. If the same fixed file fails at the same offset, look instead at layout or bounds.

Do not log the entire address space. A narrow record of the failed operation is usually easier to interpret and share.

## Build a minimal reproduction

Keep the smallest input that still demonstrates the problem. For a parser bug, a synthetic image with one malformed count can be enough. For a translation problem, record the source format, process context, affected virtual range, and tool versions. For a transport problem, record topology and initialization diagnostics.

State expected and actual behavior. Include the exact command and exit status. If you cannot share a real capture, build a synthetic case that demonstrates the same parser assumption without exposing private data.

## Deeper detail: avoid repairs that erase evidence

Zero-padding failed reads, ignoring invalid headers, increasing every bound, or retrying indefinitely can make error messages disappear while making results less trustworthy. A successful diagnostic should explain why the failure occurred and why the new behavior respects the original contract.

After a fix, rerun the original reproducer and a nearby valid case. A parser that rejects everything is safe from some misinterpretations but is not a useful repair.

## Checkpoint

The same decoder works on yesterday's capture but fails on today's. What should you compare before changing the decoder?

[Check your answer](../appendices/answers.md#chapter-09).

<!-- BOOK:FOOT:START -->

[Previous: Protections and observability](08-protections-and-observability.md) · [Contents](../README.MD#table-of-contents) · [Next: Unity in practice](10-unity.md)

<!-- BOOK:FOOT:END -->
