# Chapter 20: A complete investigation

<!-- BOOK:NAV:START -->

[Previous: Testing unfamiliar layouts](19-testing-layouts.md) · [Contents](../README.MD#table-of-contents) · [Practice labs](../labs/README.md)

<!-- BOOK:NAV:END -->

**You will build:** a short, reproducible investigation that separates byte changes, application-state changes, and failures in the observation stream.

**Before you start:** read Chapters [15](15-strings-and-collections.md) through [19](19-testing-layouts.md), or use them as references. All commands below run from the repository root with Python 3.10 or newer.

## In this chapter

- [Run the six-step investigation](#investigation).
- [Build an evidence dossier](#evidence-dossier).
- [Verify field changes by hand](#manual-verification).
- [Challenge alternative explanations](#competing-explanations).
- [Handle a failed input without inventing results](#failure-branch).
- [Write a report someone else can reproduce](#final-report).
- [Transfer the method to your own live source](#live-transition).
- [Work the final exercises](#chapter-exercises).

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

<a id="evidence-dossier"></a>
## Build an evidence dossier

The six steps give you a working result. A complete investigation also needs enough retained context to explain how you reached it. Think of the dossier as the smallest collection of artifacts that lets another person challenge each conclusion without asking you to reconstruct your memory of the session.

Begin with the question: “Which differences are storage layout, which are tracked entity state, and which are observation failures?” This wording makes three different comparisons explicit. A single statement that “the memory changed” would not tell you which evidence to collect.

### Record the scope before inspecting values

The source is the repository's synthetic `OBS2` generator. Its schema version is 2. Its entity IDs identify records within one declared teaching session. The label is text, health is a finite value within 0–100, and x/y are finite synthetic coordinates. No physical distance unit is assigned to those coordinates.

The comparison policy requires complete valid inputs and exact numeric equality. It ignores array order, payload positions, and unused padding. It preserves exact label text. The replay policy treats a higher generation as advancement, requires unchanged semantic state for a repeated generation, and does not permit generation rollback within the same monitor session.

These assumptions should appear before the conclusions. Otherwise it is too easy to adopt a different equality rule after seeing an inconvenient difference, or to describe coordinates as meters without any source contract assigning that unit.

### Identify the exact artifacts

The three fixture identities are:

| Case | Bytes | Generation | IDs in storage order |
| --- | ---: | ---: | --- |
| `before` | 96 | 2 | 10, 20, 40 |
| `relocated` | 112 | 2 | 40, 20, 10 |
| `after` | 112 | 4 | 20, 10, 30 |

Expected SHA-256 values for the current reference fixtures:

```text
before
6ba403a2af1c2058b0dd4f7a13f93ef3a47d50cebc71bff8f9ea29bf54161b2e

relocated
2f542a573c7d33f461e78fdd8680b83dd9cf5dd9c23e340feb9bfe3584cff346

after
ab9cc8774ccc34f8d73044e0caeb4c9896334d825a4059f598d89085346378d1
```

Compare these with the actual hashes printed by your `create` commands. A mismatch means you should first establish whether your fixture generator, version, or retained files differ. It is not evidence of a particular entity change until the differing file is decoded under a known schema.

The hash identifies file bytes for this exercise; it does not identify a process lifetime or authenticate the story told about the file. Those meanings come from the evidence record and the controlled generation procedure.

### Capture a machine-readable reference

Run:

```sh
python labs/deep_dive.py evidence
```

The output is JSON containing reference fixture sizes and hashes, storage IDs, both comparison reports, and each replay transition. Replay entries include the input length and hash when bytes exist; the unavailable event has null input metadata. This preserves the distinction between no observation and an observation that failed validation.

The command generates the reference cases in memory. It does **not** reopen or verify files you created earlier. Use it as an expected-results artifact, and retain the actual file commands and outputs separately. Confusing a regenerated reference with verification of a retained file would leave accidental file replacement undetected.

Record the checkout and interpreter used for your run:

```sh
git rev-parse HEAD
python --version
```

If you edited source locally, also describe those changes and retain their diff. A commit ID alone cannot identify an uncommitted implementation. Avoid recording secrets or unrelated machine configuration; the relevant context here is the lab source, schema, interpreter, commands, files, and outputs.

### Preserve provenance through later edits

Treat the original files as inputs. If you construct a malformed or modified case, give it a new filename and record which bytes changed. Keep derived comparison output separate from the underlying files. A neat report is useful, but it cannot replace the evidence needed to recompute it.

For a longer experiment, use one directory per run and a small manifest connecting each filename to its role and hash. The [experiment template](../templates/experiment.md) provides the starting structure. Keep a failed run when it explains a correction; do not relabel its outputs as if they came from the corrected implementation.

<a id="manual-verification"></a>
## Verify the key field changes by hand

An automated comparison is stronger when at least one important result has an independent derivation. Use the documented offsets and entity stride to verify ID 10's health without asking the comparator which field changed.

### Locate ID 10 in the baseline

The baseline header puts the array at byte 48. Its first entity has ID 10, and health is four bytes into a sixteen-byte entity. Therefore:

```text
record start = 48 + 0 * 16 = 48 = 0x30
health start = 48 + 4      = 52 = 0x34
health range = [52, 56)
stored bytes = 00 00 af 42
decoded f32  = 87.5
```

The ID check matters. A plausible float at byte 52 is not enough to label it “ID 10's health” without establishing the containing record and its identity. The field name comes from the schema, while the entity association comes from the decoded ID.

### Locate ID 10 in the later observation

The later array begins at byte 64 and stores IDs 20, 10, and 30. ID 10 is now in the second slot:

```text
record start = 64 + 1 * 16 = 80 = 0x50
health start = 80 + 4      = 84 = 0x54
health range = [84, 88)
stored bytes = 00 00 70 42
decoded f32  = 60
```

Comparing byte 52 in both files would not perform this check. In the later file, byte 52 is inside the label. Comparing byte 84 in both would also fail to track identity: the baseline's record at byte 80 belongs to ID 40.

This calculation establishes the observed transition for ID 10 under the single-session identity rule. It does not establish why health changed. A cause requires a controlled intervention or additional producer-side evidence; these fixtures simply encode the specified before and after values.

### Verify the remaining findings

For ID 20, inspect both records and compare their y fields. In this particular pair, both y fields happen to occur at offset 76: the baseline's second record starts at 64, while the later file's first record also starts at 64. The equal location is a coincidence of the relocation and reordering, not a general identity rule.

The values are 12 and 13. Health remains 100 and x remains 10. The report's changed-field list should contain only y for that ID.

Then compare ID sets: `{10, 20, 40}` and `{10, 20, 30}`. Their intersection is `{10, 20}`, their new-only set is `{30}`, and their old-only set is `{40}`. Because both arrays are complete, “added” and “removed” describe membership in this observed collection. They do not prove object allocation, destruction, or absence from every other collection in a hypothetical application.

The label's decoded text is equal in all three cases. Its location changes between baseline and relocated files, so compare each file's declared name range rather than one fixed byte slice.

### Reconcile the timeline

Run the detailed monitor trace:

```sh
python labs/deep_dive.py trace
```

The final row must be:

```text
200 no-progress 4 200 40
```

Read it using the printed column headings: at 200 ms the status is `no-progress`, the accepted generation is 4, the last observation time is 200 ms, and the last progress time is 40 ms. The elapsed interval since advancement is therefore 160 ms, which exceeds the 100 ms budget.

The event at 60 ms contains valid bytes with conflicting same-generation state. It must not replace the accepted health value of 60 with 55. This is a temporal-policy rejection, not a structural decode failure. A parser-only inspection and a replay-policy inspection can therefore produce different, compatible findings about the same input.

<a id="competing-explanations"></a>
## Challenge competing explanations

A useful investigation does more than list its preferred conclusion. It asks what else could explain the same surface symptom and chooses checks that distinguish those possibilities.

| Surface observation | Competing explanation | Discriminating check |
| --- | --- | --- |
| Whole-file hashes differ | Only payload positions or padding changed | Compare decoded state by ID and inspect declared ranges |
| First array slot has different health | A different entity occupies that slot | Read the ID in each record before comparing fields |
| An ID is absent from a result | Input was incomplete or failed to decode | Require complete valid arrays before membership claims |
| Displayed values look equal | Formatting hid a binary32 difference | Retain bytes and print enough significant digits |
| Same generation has different values | Producer contract violation or mixed observation | Preserve both inputs and reject advancement pending source evidence |
| A lower generation arrives | Old buffered input or a source restart | Check session identity and acquisition history |
| No progress is observed | Stable source, missed updates, stalled acquisition, or producer policy | Compare producer-side publication evidence with reader observations |

The fixture answers some of these because its construction is known. A real capture may leave alternatives unresolved. Record that uncertainty rather than selecting the most dramatic explanation.

### Use both a negative and a positive control

The relocated fixture is the negative control for semantic change: bytes and positions change, but the selected state does not. It exposes a comparator that mistakes storage order for identity.

The later fixture is the positive control: specific fields and membership do change. It exposes a comparator that ignores too much or always reports equality. A tool that passes only the negative control could be broken by returning “unchanged” for every input.

Together the controls test two opposing mistakes. Keep their expected differences explicit so adding a new field later does not silently change what “same state” means.

### Do not infer missing history

Generations 2 and 4 tell you that the later accepted observation has a larger generation. The schema does not require consecutive numbering, so the difference does not establish exactly one missing snapshot or exactly two application updates.

Likewise, a measured value changing from 87.5 to 60 does not imply a smooth decline, one event, or a particular rate. You have two endpoint observations. Intermediate behavior requires intermediate evidence.

This distinction becomes important when people turn a small report into a broader story. Keep the observation, interpretation, and proposed cause in separate sentences so each can be assessed against its own support.

<a id="failure-branch"></a>
## Follow the failed-input branch

Now suppose the later file is truncated by one byte. The header still says there are three entities, but the final record is incomplete. A reader must stop before presenting a normal comparison result.

The correct outcome is an input failure with the range problem identified. It is not a valid empty array, not a collection with two entities, and not evidence that ID 30 was absent. The completeness requirement applies to the whole declared observation.

The command-line contract requires status 1 and no normal comparison output. Preserve the valid baseline and the failed later input. Your report can say that the attempted comparison was unavailable because the later observation did not satisfy the format. It cannot claim additions or removals from that attempt.

### Keep recovery separate from reinterpretation

If you later obtain a complete valid observation, record it as a new input and perform a new comparison. Do not fill the missing byte with zero, silently reduce the entity count, or reuse a prior record while labeling the result as fully current.

A more advanced application can display retained old state alongside an explicit availability indicator. That is a user-interface policy. It should carry the accepted observation's age and identity so retained values cannot be mistaken for fresh measurements.

The replay monitor demonstrates this separation: rejected input changes the observed status while the last accepted snapshot remains available. The two outputs answer different questions—what happened on this attempt, and what valid state was last accepted.

### Treat a new session explicitly

Suppose a producer restarts and publishes generation 0 with IDs 10 and 20. The existing monitor rejects that generation as regressed. If independent source evidence establishes a new session, create a new monitor and start a new identity scope.

Do not compare reused IDs across the restart as if they necessarily identify the same entities. A report can compare aggregate collection sizes across sessions, for example, without asserting entity continuity. The intended question determines which cross-session comparisons are meaningful.

<a id="final-report"></a>
## Write a reviewable final report

Organize the report around claims and their evidence. The following ledger is a useful model for this exercise:

| Claim | Required evidence | Limit |
| --- | --- | --- |
| The reference files differ in bytes | Actual sizes, hashes, or direct byte comparison | Does not identify semantic differences |
| Relocation preserves tracked state | Complete decoding and equality under the declared semantic view | Excludes padding, order, and untracked fields |
| ID 10 health and ID 20 y changed | ID-matched field values, supported by manual checks | Does not establish the cause or intervening history |
| ID 30 entered and ID 40 left the collection | Complete input arrays and set differences | Does not prove allocation or destruction |
| Replay retained good state and detected no progress | Ordered inputs, statuses, and retained-state history | Describes this synthetic policy and trace |

Attach the exact commands and their actual outputs. Record any failures and the corrected rerun separately. Include the source revision, relevant local edits, interpreter version, input hashes, schema assumptions, and test exit status. You do not need a large report, but someone should be able to connect each sentence to an artifact or calculation.

### Example conclusion with calibrated wording

> Under the declared single-session `OBS2` contract, all three reference files decoded successfully. Relocating payloads and reversing storage order changed file bytes while preserving the label and tracked entity values. The later complete observation changed ID 10's health from 87.5 to 60 and ID 20's y from 12 to 13, with ID 30 added and ID 40 removed from this collection. The replay accepted its last advancement at 40 ms, retained that state through subsequent rejected observations, and reported no observed advancement at 200 ms.

Follow that with the evidence boundary: the files and timeline were generated locally; the exercise contains no acquisition device, measured live latency, or real process lifecycle. This is a scope statement that lets the reader know exactly what was demonstrated.

Avoid inserting a copied test count as proof if you did not run the command. The repository's test suite can evolve. Your report should preserve the result from your checkout and environment, including any failed check that remains unresolved.

### Review the investigation as a second reader

Try reproducing the report from a fresh output directory. Can you generate the same hashes, obtain the same comparison, and explain the final replay age without relying on an unstated fact? Can you find the exact byte range supporting the health claim?

Then deliberately remove one kind of evidence in your reasoning. Without a valid later input, membership changes become unsupported. Without session identity, per-entity continuity becomes uncertain. Without ordered replay, the final no-progress diagnosis cannot be derived from a single snapshot. These counterfactuals show which evidence is actually doing the work.

<a id="live-transition"></a>
## Transfer the method one boundary at a time

The next step is your own instrumented program, where the producer can publish known values and an explicit snapshot/session contract. Keep the schema and comparator simple while changing only the acquisition boundary. This gives you a reference for distinguishing a read problem from a decoder problem.

For a live software read, establish permissions, address space, target pointer width, exact-read behavior, process lifetime, and cleanup ownership. Compare the observed fields with producer-side records under controlled changes. Measure request and completion times locally; do not call them source age unless the timestamp relationship supports that claim.

For a Unity development build, record editor version, scripting backend, architecture, and build artifacts. Use the procedure in [Chapter 10](10-unity.md) to establish the relevant layout and lifecycle rather than copying the synthetic file offsets into a managed object. `OBS2` is an interchange exercise, not a Unity object layout.

For a hardware acquisition route, retain the already verified parser and comparison layer while validating source configuration, translation, availability, coherence, and cleanup separately. Follow the backend's documented API and applicable platform protections. A software fixture cannot establish device compatibility; a successful device read cannot establish that every decoded field has the right meaning.

At each transition, keep the old deterministic cases as regressions. Add evidence for the new boundary and update the claim ledger. The practical skill you carry forward is the ability to say what an observation means, what could invalidate that meaning, and which experiment would resolve the remaining uncertainty.

<a id="chapter-exercises"></a>
## Practice exercises

1. Derive ID 10's health offset in `before` and `after`. Why does reading the same absolute file offset in both fail to track that field?
2. The later input fails validation. Which of the report's entity-change claims can still be made from that attempted pair, and what evidence should be retained?
3. At 200 ms, the last accepted generation is 4 and the last progress time is 40 ms. Calculate the observed progress age and explain why the 60 ms conflict does not reset it.
4. A new device produces the expected three records once. Which additional claims would still require evidence before presenting the full synthetic investigation as live-device validation?

[Worked solutions](../appendices/deep-dive-answers.md#chapter-20).

## Checkpoint

Which claims in the worked conclusion are supported by byte equality, which require semantic decoding, and which require the ordered replay history?

[Check your answer](../appendices/answers.md#chapter-20).

<!-- BOOK:FOOT:START -->

[Previous: Testing unfamiliar layouts](19-testing-layouts.md) · [Contents](../README.MD#table-of-contents) · [Practice labs](../labs/README.md)

<!-- BOOK:FOOT:END -->
