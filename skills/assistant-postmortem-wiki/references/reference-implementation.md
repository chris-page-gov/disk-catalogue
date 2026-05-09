# Reference Implementation

This note captures the working pattern from `ai-engineering-lab-hackathon-london-2026`.

## Core Builder

- Builder: `tools/build_codex_postmortem.py`
- Tests: `tests/test_build_codex_postmortem.py`
- Full private archive: `postmortem/`
- Redacted public derivative: `postmortem-public/`

The builder regenerates the private archive and the public derivative from local Codex rollout JSONL files plus repository artifacts and external methodology references.

These paths are concrete examples from the source repository, not universal commands. In another target repository, scaffold or adapt the builder and tests under paths that fit that project before running the validation commands below.

The private archive is audit-oriented: read-only conversation sources and ordered exchange notes are kept so a reviewer can reconstruct the visible prompt/response sequence and the evidence trail, rather than relying on a narrative summary alone.

## Private vs Public Split

The repository keeps:

- `postmortem/` as the full local evidence archive
- `postmortem-public/` as the GitHub-safe derivative

The public operating rules in `postmortem-public/AGENTS.md` require:

- no raw Codex JSONL files or raw transcript sources
- no full copied third-party methodology source bodies unless licensing or permission is recorded
- redaction of local filesystem paths, screenshot paths, and private reference repositories
- commit-specific GitHub permalinks for tracked repository artifacts

## Concrete Public Outputs

The public derivative includes:

- `postmortem-public/wiki/index.md`
- `postmortem-public/wiki/postmortem.md`
- `postmortem-public/wiki/conversation-summary.md`
- `postmortem-public/wiki/repository-evidence.md`
- `postmortem-public/wiki/decisions.md`
- `postmortem-public/wiki/methodology.md`
- machine-readable registers under `postmortem-public/wiki/data/`

Exchange files are numbered and slugged, for example:

- `postmortem-public/wiki/exchanges/0056-20260418065216-create-codex-postmortem-wiki.md`

Conversation sources use derived titles, for example:

- `postmortem-public/wiki/sources/conv-005-codex-postmortem-publication-assessment-and-version-1-1-pr.md`

## Artifact Pattern

Repository evidence linked into the postmortem included:

- `output/doc/challenge-2-realtime-delivery-report.md`
- `README.md`
- `Changelog.md`
- `Context.md`
- `Progress.md`
- selected Challenge 2 wiki, workbench, and evaluation files

Public artifact notes used commit-specific GitHub permalinks where possible and explicit local-only markers where not.

## External Methodology Handling

The implementation localized Karpathy X posts and the Karpathy gist for research tracing, but public publication remained conservative:

- private archive may keep localized copies for verification
- public derivative should prefer citation metadata and short excerpts when no explicit redistribution license is recorded

## Validation Used Here

Validation included:

- `python3 -m py_compile tools/build_codex_postmortem.py`
- `python3 tools/build_codex_postmortem.py`
- `python3 -m unittest tests/test_build_codex_postmortem.py`
- targeted publication scans for local paths, credential-like strings, and copied external source bodies

If the repository used documentation lockstep, the tracking files were updated as part of the same change.

## Porting Notes

When reusing this pattern in another project:

- keep the skill generic and the builder repo-specific
- keep the full archive and public derivative separate
- keep the full archive excluded from GitHub by default
- derive conversation titles from content
- keep exchange numbering deterministic
- store publication decisions explicitly
- prefer regeneration over manual maintenance of many wiki files
