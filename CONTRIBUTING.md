# Improving this book

[Book contents](README.MD#table-of-contents)

Help a reader reach a correct result and understand why it is correct. A useful contribution can be a clearer explanation, a corrected assumption, a reproducible failure case, or a better connection between chapters.

## Writing a chapter

Start with what the reader will learn and what they need beforehand. Explain a concrete example before introducing additional terminology. Define new terms where they first matter and link to the glossary when useful.

Give advanced details enough precision to be actionable: identify the address space, target width, layout version, failure behavior, and evidence boundary. Prefer one worked example with expected output over several vague promises.

End with a question that checks understanding and add its answer to the answer appendix. Keep “tested fixture,” “documented API sketch,” and “live/hardware observation” distinct. Never invent benchmark results or compatibility claims.

## Maintain navigation

Chapter order and titles live in [book.json](book.json). Navigation blocks and the main contents table are generated from it:

```sh
python tools/book.py sync
python tools/book.py check
```

Keep the `BOOK` markers in chapter files. Use a stable, lowercase ASCII explicit anchor for important cross-chapter destinations when a heading may change. Keep existing public anchors as aliases when practical. Use relative file links with the actual filename case, including `README.MD`.

For predictable local checking, author links as ordinary inline Markdown links with simple destinations or angle-bracket destinations. Use ATX headings (`# Heading`) and fenced code blocks. The checker supports reference-style links too; it is a project checker, not a complete Markdown conformance implementation. Raw HTML is limited to simple anchors in this book.

## Verify a change locally

```sh
python tools/book.py check
python -m unittest discover -s tests -v
python labs/memory_lab.py demo
git diff --check
```

The checks validate local destinations and fragments, navigation order, and executable lab behavior. They do not certify external website availability, third-party runtime compatibility, Unity builds, or DMA hardware.

For prose-only changes, run the book checker and whitespace check. Run the lab tests when modifying examples, expected output, or parser behavior. Keep generated images and scratch captures in `out/`; keep private captures outside the repository.

For a navigation change, an optional [GitHub rendering checker](tools/verify_github_render.py) can validate the actual renderer:

```sh
python tools/verify_github_render.py source
python tools/verify_github_render.py published
```

The first command requires an authenticated GitHub CLI and renders local Markdown through GitHub's API. The second requires a clean, already published commit and inspects its public pages for the referenced fragment destinations. Both make network requests, save inspection evidence under `out/`, and perform no publication or Actions operation. The source-render check validates links and custom anchors; the published check also verifies GitHub's generated heading anchors.

## GitHub Actions policy

Do not create, enable, dispatch, or re-enable GitHub Actions without the repository owner's explicit approval. Implementing, checking, committing, pushing, or opening a pull request does not by itself authorize an Actions run. Inspect triggers, reusable/dependent workflows, required checks, and operational dependencies before an operation that can start automation. This repository uses local checks and does not need a workflow to validate the book.

## Describe the evidence

In a change description, explain the reader-facing improvement, the checks performed, and any limits. Cite primary sources for version-sensitive technical claims. If a hardware result is contributed later, include the exact supported configuration and test procedure rather than a general claim that “DMA works.”
