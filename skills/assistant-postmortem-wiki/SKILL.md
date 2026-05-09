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
- Treat rendering problems as data quality problems. A postmortem that cannot be navigated in
  Obsidian and native VS Code Markdown preview is incomplete even if the source extraction worked.

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
- Link each exchange to its previous and next exchange, its previous and next exchange within the
  same session, its session page, and its phase/topic/entity/artifact facet pages.
- Use standard Markdown links for generated navigation by default. Obsidian treats Markdown links
  as internal links, and VS Code renders them natively without an extension.
- Add a turn layer that groups each user prompt with the assistant answer and tool evidence that
  followed it. Link raw exchanges to their turn so readers can browse by conversational unit rather
  than only by atomic event.
- Use meaningful visible page headings, not filename-like ids. Preserve opaque ids in metadata and
  surrogate fields instead.
- Prefer a surrogate-to-detail pattern: a compact open summary at the top of each note and the
  full transcript or redacted detail in a foldable section.
- Use ordinary headings for exchange sections. Do not wrap Markdown links in raw HTML
  `<details>`/`<summary>` blocks because Obsidian can stop parsing the contents as Markdown.
- For public redacted detail, render escaped visible Markdown text rather than a squashed `text`
  code block. Reserve fenced code blocks for private raw transcripts or real code/tool output.
- Classify atomic exchanges with enough detail to reconstruct the conversation shape:
  `user-message`, `assistant-message`, `tool-call`, `tool-output`, `system-context`, and
  `other`. Public derivatives may omit private tool bodies, but should keep enough turn and kind
  metadata to show user prompt -> assistant answer -> tool evidence structure.
- Detect repeated user prompts or prompt fragments inside the same session and group them into
  the same turn where they are clearly copies or context injections rather than new user intent.

5. Build the wiki structure.

- Create index, conversation summary, repository evidence, methodology, decision register, and postmortem synthesis pages.
- Keep `sources/`, `exchanges/`, `turns/`, facet folders, and `data/` clearly separated.
- Cross-link the narrative to the exact exchange or artifact that supports it.
- Add navigation hubs for timeline, sessions, phases, topics, entities, artifacts, roles, kinds,
  turn positions, surrogate catalogue, and graph data so tools such as Obsidian can render real
  graph edges rather than isolated exchange nodes.
- Include structural context in each note so the reader can see where they are in the hierarchy
  without opening a separate index. This should work like a lightweight NIBS-style location path:
  archive index > session > turn or phase > exchange.
- In Markdown tables, use table-safe Markdown links rather than aliased wikilinks. The `|` in
  `[[target|label]]` is a table delimiter in Obsidian and will split links across columns.
- Use surrogate-to-detail navigation for long transcripts: a compact table or bullet row should
  link to a full exchange note; the full note should link back to its parent turn, session, phase,
  topics, entities, and artifacts.

## Rendering Compatibility Rules

These rules capture failures found while testing the generated postmortem in Obsidian and native
VS Code Markdown preview.

- Prefer standard Markdown links (`[label](path.md)`) for visible generated navigation. Obsidian
  treats them as internal links and VS Code renders them without extra extensions.
- Do not emit aliased wikilinks in Markdown tables. If wikilinks are required for a target tool,
  generate them outside tables or in a separate Obsidian-specific derivative.
- Do not use raw HTML folding such as `<details>` and `<summary>` around Markdown links. Some
  viewers render the tags literally or stop parsing nested Markdown links.
- Use ordinary Markdown headings for foldable or scannable structure. Tool-specific folding can be
  added by the editor, but the source file should remain readable in plain Markdown.
- Escape visible transcript and excerpt text before writing it into public Markdown. In particular,
  escape square brackets in placeholders such as `[REPO]`, encode angle brackets, and protect table
  pipes in table cells.
- Clean short excerpts before display: remove leading heading markers, list markers, code span
  backticks, raw HTML tags, collapsed Markdown links, and excessive whitespace.
- Give pages meaningful visible headings such as `Exchange 17: Rename validation` or
  `Turn 4: User asks for release`, not opaque filenames or ids. Keep ids in front matter,
  registers, and surrogate metadata.
- Public redacted detail should be escaped visible prose. Do not place the whole redacted transcript
  in a generic `text` code block because it destroys headings, lists, links, and excerpt readability.

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
- Validate rendering compatibility:
  - zero broken Markdown links in the public derivative
  - zero aliased wikilinks in public tables
  - zero raw `<details>` or `<summary>` blocks in public exchange notes
  - zero generic `text` code blocks used for redacted transcript detail
  - visible titles and excerpts escape reference-link-looking text such as `[REPO]`
  - surrogate tables keep one row per exchange without pipe-splitting link labels
- Validate turn completeness:
  - every public exchange has a turn id, turn number, and turn position
  - turn registers agree with exchange registers
  - turn pages expose user prompts, assistant answers, and any retained tool-evidence markers
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
    turns/
    sources/
    sessions/
    phases/
    topics/
    entities/
    artifacts/
    roles/
    kinds/
    turn-positions/
    data/

postmortem-public/
  wiki/
    exchanges/
    turns/
    sources/
    sessions/
    phases/
    topics/
    entities/
    artifacts/
    roles/
    kinds/
    turn-positions/
    data/
```

Typical data products:

- session or conversation register
- exchange register
- turn register
- facet register
- graph node and edge registers
- artifact register
- external-source register
- publication decision register
- publication lint report

Minimum public validation artifacts:

- `wiki/data/publication_lint.json`
- `wiki/data/graph_nodes.json`
- `wiki/data/graph_edges.json`
- `wiki/data/facets.json`
- `wiki/data/turns.json`

## Reference Implementation

When adapting this from `ai-engineering-lab-hackathon-london-2026`, read [references/reference-implementation.md](references/reference-implementation.md) for the concrete builder, folder layout, publication rules, and validation commands that worked there.
