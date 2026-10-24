# Chapter 20: A complete investigation

<!-- BOOK:NAV:START -->

[Previous: Testing unfamiliar layouts](19-testing-layouts.md) · [Contents](../README.MD#table-of-contents) · [Practice labs](../labs/README.md)

<!-- BOOK:NAV:END -->

**You will build:** a short, reproducible investigation that separates byte changes, application-state changes, and failures in the observation stream.

**Before you start:** read Chapters [15](15-strings-and-collections.md) through [19](19-testing-layouts.md), or use them as references. All commands below run from the repository root with Python 3.10 or newer.

## The question

You receive three synthetic observations and a replay trace. Someone reports: “The collection moved, health changed, and then the reader became unreliable.” Your job is to split that sentence into claims you can test.

The setup gives you a documented format and one session in which entity IDs are stable. The captures are complete when decoding succeeds. You are not trying to infer a real operating system's memory layout, prove hardware compatibility, or recover an unknown producer's synchronization rules.

The goal is a precise conclusion that another person can reproduce from the same files.

<a id="investigation"></a>
## Step 1: create and identify the evidence

```sh
python labs/advanced_lab.py create out/advanced/before.obs --case before
python labs/advanced_lab.py create out/advanced/relocated.obs --case relocated
python labs/advanced_lab.py create out/advanced/after.obs --case after
```

Each command prints the byte count and SHA-256 of the file it created. Keep those values with your [experiment record](../templates/experiment.md). The files are generated from the reference implementation; they are not supplied as captured private data.

Creation refuses to overwrite an existing file. If repeating the exercise, choose new paths or deliberately use `--force` to regenerate the fixtures. Do not silently replace evidence from an experiment you intend to retain.

## Step 2: validate each input on its own

```sh
python labs/advanced_lab.py inspect out/advanced/before.obs
python labs/advanced_lab.py inspect out/advanced/relocated.obs
python labs/advanced_lab.py inspect out/advanced/after.obs
```

Confirm that the first two have generation 2 and the same entity values. Their array order differs. The final observation has generation 4 and IDs 20, 10, and 30 in storage order.

Read the label as `Pilot 🧭`. The command prints an escaped representation so the output is safe on terminals that cannot display the compass. The escape is a presentation choice; the underlying string is decoded as Unicode.

At this stage you have three valid observations. You have not yet established which differences are meaningful.

## Step 3: test the layout-only hypothesis

```sh
python labs/advanced_lab.py compare out/advanced/before.obs out/advanced/relocated.obs
```

Expected output:

```text
generations=2->2
label_changed=no
added=[] removed=[]
changed=[]
```

The fixture bytes and hashes differ because the name and array moved and the array order changed. The normalized entity state is equal. This supports the narrow conclusion that the reported movement did not change the fields tracked by this schema.

It does not establish that every possible application property stayed the same. Your schema observes a label, IDs, health, and two coordinates; it says nothing about fields outside that scope.

## Step 4: identify the actual state changes

```sh
python labs/advanced_lab.py compare out/advanced/before.obs out/advanced/after.obs
```

Expected output:

```text
generations=2->4
label_changed=no
added=[30] removed=[40]
changed=['10.health:87.5->60', '20.y:12->13']
```

The identity rule lets you describe these changes even though array order differs. The completeness rule lets you describe ID 40 as removed from this collection. If the second array had been only partially available, that removal claim would not be justified.

The generation difference does not tell you the exact number of missed application updates. The fixture contract only says that a larger generation is newer; it does not promise consecutive numbering.

## Step 5: investigate the reader's behavior over time

```sh
python labs/advanced_lab.py replay
```

Use [Chapter 18's trace](18-polling-and-replay.md#state-transitions) to explain every outcome. There is an unavailable sample, an invalid format, a regression, a same-generation conflict, and finally a duplicate that exceeds the progress budget.

These are different findings. The replay does not identify a defective device, because there is no device in this exercise. It proves that the monitor handles the modeled conditions without silently replacing good state with unsupported observations.

Record that the last accepted advancement occurs at 40 ms. Failures at 50 and 60 ms must not make the final repeated state look newly advanced.

## Step 6: challenge your interpretation

Run the automated checks:

```sh
python -m unittest discover -s tests -v
python tools/book.py check
```

Then make one independent prediction: reverse the entity order again without changing IDs or values. Should the semantic report change? The tests include this kind of challenge, and your explanation should agree with it.

Next, consider a producer restart that reuses the same entity IDs. Which evidence would be missing before comparing the two sessions? Do not simply reuse the single-session identity rule.

## Write the conclusion

A defensible report might say:

> In the generated `OBS2` test session, relocation and array reordering preserved the decoded label and tracked entity fields. The later complete observation changed ID 10's health from 87.5 to 60, changed ID 20's y coordinate from 12 to 13, added ID 30, and removed ID 40 from the observed collection. The replay monitor retained its last accepted state through the modeled failures and reported a lack of observed progress at 200 ms.

Attach your actual commands, input hashes, and test results. State that this is a synthetic investigation. The quote describes the expected result; your own report should be based on the output you obtained.

## Continue with a real source when you are ready

Keep the analysis contract and replace one boundary at a time. A new source needs evidence for its address context, availability, process or session identity, and lifecycle. A new layout needs its own schema and independent validation. Live polling needs an actual backend timeout and cleanup contract.

Use your own instrumented application as the first live comparison. Its producer-side evidence can tell you whether the new acquisition route observes the same state and where timing differs. Preserve the synthetic fixtures so later regressions can still be isolated without hardware.

## Checkpoint

Which claims in the worked conclusion are supported by byte equality, which require semantic decoding, and which require the ordered replay history?

[Check your answer](../appendices/answers.md#chapter-20).

<!-- BOOK:FOOT:START -->

[Previous: Testing unfamiliar layouts](19-testing-layouts.md) · [Contents](../README.MD#table-of-contents) · [Practice labs](../labs/README.md)

<!-- BOOK:FOOT:END -->
