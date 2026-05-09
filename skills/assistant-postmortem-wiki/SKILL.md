---
name: assistant-postmortem-wiki
description: Build both a full private AI-assistant postmortem and a redacted public postmortem from Codex or other assistant conversations plus repository artifacts. Use when the user wants an audit-level private trace with read-only conversation sources, sequenced prompt-response exchange notes, artifact and citation registers, commit-specific permalinks, and a public-safe derivative while keeping the full archive out of GitHub.
---

# Assistant Postmortem Wiki

Use this skill when the user wants to convert AI-assistant collaboration history into durable postmortem evidence that can be preserved locally and selectively published.

Default rules:

- Always create two outputs unless the user explicitly says otherwise:
  - a full local postmortem archive
  - a redacted public postmortem
- The full local archive is an audit-level trace, not a summary set. Preserve the read-only conversation sources and the sequenced exchanges needed to reconstruct what the user supplied, what the assistant inferred, and which repository artifacts support the result.
- Keep the full archive out of GitHub by default. Before writing a private archive inside a repository, either put it outside the repository or add the chosen private archive path to `.gitignore` before generation.
- Prefer regeneration from source transcripts and repository artifacts over hand-editing dozens of notes.
- Use commit-specific GitHub permalinks for tracked artifacts where public linking is needed.
- Treat third-party methodology sources conservatively unless license or permission is clear.

## Workflow

1. Establish the evidence boundary.

- Identify the repository root, branch, and any baseline tag or commit that should anchor the timeline.
- If the user wants a preserved baseline, tag or branch before postmortem generation.
- Decide where the private archive and the public derivative will live. Default to `postmortem/` for the private archive and `postmortem-public/` for the public derivative unless the target repository already uses another convention.
- Verify the private archive path cannot be committed: place it outside the repository or ensure the exact path is ignored by Git before generation.

2. Inventory the inputs.

- Locate local assistant session exports or transcript files.
- Identify key repository artifacts, reports, screenshots, and design notes that the postmortem should cite.
- Derive human-readable conversation titles from content rather than opaque ids.

3. Build the full private archive.

- Write one read-only source file per conversation.
- Preserve timestamps, session ids, cwd or repo context, and material command or tool evidence.
- Preserve the full visible user and assistant exchange needed for later audit or reconstruction rather than collapsing the archive into prose summaries.
- Keep raw transcript bodies, local paths, screenshots, and localized third-party source copies here if needed for evidence.

4. Split the interactions into exchange notes.

- Create one ordered file per user prompt plus assistant response set.
- Keep numbering stable and explicit in filenames.
- Link each exchange back to its parent conversation source.

5. Build the wiki structure.

- Create index, conversation summary, repository evidence, methodology, decision register, and postmortem synthesis pages.
- Keep `sources/`, `exchanges/`, and `data/` clearly separated.
- Cross-link the narrative to the exact exchange or artifact that supports it.

6. Register repository artifacts and external sources.

- Keep machine-readable registers for sessions, exchanges, artifacts, and external sources.
- For public artifact notes, prefer commit-specific GitHub permalinks.
- Mark local-only evidence as local-only rather than inventing a public URL.

7. Create the redacted public postmortem.

- Exclude the full private archive from GitHub by default.
- Redact or replace local filesystem paths, local config references, account state, and raw bundles.
- Prefer conversation summaries and redacted exchange notes over raw transcript dumps.
- Prefer citation metadata and short excerpts for third-party source bodies unless their publication license is explicit.

8. Validate the result.

- Scan for local paths, secrets, account identifiers, copied third-party bodies, and broken links.
- Validate internal links and register consistency.
- If the repository uses lockstep tracking docs, update them.

9. Deliver the outcome.

- State clearly what is private-only, what is public-safe, and what remains blocked for publication.
- Record the regeneration command so the workflow stays repeatable.

## Expected Output Shape

Adapt names to the target repository, but default to a split like this:

```text
postmortem/
  sources/
    conversations/
    external/
  wiki/
    exchanges/
    sources/
    data/

postmortem-public/
  wiki/
    exchanges/
    sources/
    data/
```

Typical data products:

- session or conversation register
- exchange register
- artifact register
- external-source register
- publication decision register
- publication lint report

## Reference Implementation

When adapting this from `ai-engineering-lab-hackathon-london-2026`, read [references/reference-implementation.md](references/reference-implementation.md) for the concrete builder, folder layout, publication rules, and validation commands that worked there.
