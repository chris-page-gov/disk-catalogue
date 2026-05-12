# Methodology

The postmortem follows the repository-local `assistant-postmortem-wiki` skill.

1. Establish an evidence boundary anchored on the `v1.0.0` release and the post-release
   CI/skill PR.
2. Preserve local Codex JSONL session sources in the ignored private archive.
3. Extract ordered exchange notes for audit and public summaries.
4. Register tracked artifacts with commit-specific GitHub links.
5. Mark local-only artifacts explicitly rather than fabricating public URLs.
6. Generate a public derivative that redacts local paths, tokens, and raw transcript bodies.
7. Run publication lint and store the result in `wiki/data/publication_lint.json`.
8. Validate portable rendering rules: no public wikilinks, no raw HTML folding, no generic
   redacted-detail `text` blocks, and no broken relative Markdown links.

Regeneration command:

```bash
python tools/build_assistant_postmortem.py
```
