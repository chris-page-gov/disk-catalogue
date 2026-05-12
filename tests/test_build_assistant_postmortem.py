from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_builder():
    path = Path(__file__).resolve().parents[1] / "tools" / "build_assistant_postmortem.py"
    spec = importlib.util.spec_from_file_location("build_assistant_postmortem", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_slugify_has_stable_fallback() -> None:
    builder = load_builder()

    assert (
        builder.slugify("Following Jesus: Disc 01 / Track 03") == "following-jesus-disc-01-track-03"
    )
    assert builder.slugify("!!!", fallback="fallback") == "fallback"


def test_redact_removes_local_paths_and_tokens() -> None:
    builder = load_builder()
    text = (
        f"{builder.REPO_ROOT}/catalogue.duckdb "
        f"{builder.HOME}/.codex/session.jsonl "
        "/Volumes/ExtSSD-Data/audio "
        "Token: gho_abc123456789 "
        "AKIAABCDEFGHIJKLMNOP "
        "AIzaabcdefghijklmnopqrstuvwxyzabcdefghi "
        "SERVICE_TOKEN=super-secret-value"
    )

    redacted = builder.redact(text)

    assert str(builder.REPO_ROOT) not in redacted
    assert str(builder.HOME) not in redacted
    assert "/Volumes/" not in redacted
    assert "gho_abc123456789" not in redacted
    assert "AKIAABCDEFGHIJKLMNOP" not in redacted
    assert "AIzaabcdefghijklmnopqrstuvwxyzabcdefghi" not in redacted
    assert "super-secret-value" not in redacted
    assert "[REPO]" in redacted
    assert "[HOME]" in redacted


def test_event_to_exchange_extracts_message_text() -> None:
    builder = load_builder()
    event = {
        "timestamp": "2026-05-09T00:00:00Z",
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Publish a version 1.0"}],
        },
    }

    exchange = builder.event_to_exchange(event, "session-id", 7)

    assert exchange is not None
    assert exchange.role == "user"
    assert exchange.kind == "user-message"
    assert exchange.text == "Publish a version 1.0"
    assert exchange.exchange_id.startswith("0007-session-")


def test_event_to_exchange_redacts_local_paths_from_ids() -> None:
    builder = load_builder()
    event = {
        "timestamp": "2026-05-09T00:00:00Z",
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"# AGENTS.md instructions for {builder.REPO_ROOT}\n<INSTRUCTIONS>",
                }
            ],
        },
    }

    exchange = builder.event_to_exchange(event, "session-id", 2)

    assert exchange is not None
    assert "users-crpage" not in exchange.exchange_id
    assert exchange.exchange_id == "0002-session-agents-md-instructions-for-repo"
    conversation = builder.Conversation(
        session_id="session-id",
        path=Path("session.jsonl"),
        title="Local path context",
        started_at="2026-05-09T00:00:00Z",
        updated_at="2026-05-09T00:01:00Z",
        cwd="",
        source="",
        branch="main",
        commit="abcdef1",
        role="main",
        events=[],
    )
    views = builder.build_exchange_views([conversation], [exchange], public=True)

    assert "users-crpage" not in views[0].turn_id
    assert views[0].turn_id == "turn-0001-session-agents-md-instructions-for-repo"


def test_publication_lint_flags_private_patterns(tmp_path: Path) -> None:
    builder = load_builder()
    public_file = tmp_path / "wiki" / "postmortem.md"
    public_file.parent.mkdir()
    public_file.write_text(
        "bad /Users/crpage and gho_abc123456789 and -----BEGIN PRIVATE KEY-----",
        encoding="utf-8",
    )

    report = builder.publication_lint(tmp_path)

    assert report["issue_count"] == 3


def test_publication_lint_flags_local_user_slugs_in_public_paths(tmp_path: Path) -> None:
    builder = load_builder()
    public_file = tmp_path / "wiki" / "exchanges" / "0001-users-crpage-repos.md"
    public_file.parent.mkdir(parents=True)
    public_file.write_text("public content", encoding="utf-8")

    report = builder.publication_lint(tmp_path)

    assert report["issue_count"] == 1
    assert report["findings"][0]["pattern"] == "local_user_slug"


def test_publication_lint_flags_rendering_regressions(tmp_path: Path) -> None:
    builder = load_builder()
    public_file = tmp_path / "wiki" / "exchanges" / "bad.md"
    public_file.parent.mkdir(parents=True)
    public_file.write_text(
        "| Exchange |\n"
        "| --- |\n"
        "| [[wiki/exchanges/0001|Broken table link]] |\n\n"
        "<details open>\n"
        "<summary>Surrogate</summary>\n\n"
        "```text\n"
        "# Redacted detail\n"
        "```\n",
        encoding="utf-8",
    )

    report = builder.publication_lint(tmp_path)
    patterns = {finding["pattern"] for finding in report["findings"]}

    assert report["issue_count"] == 4
    assert patterns == {"wikilink", "raw_html_folding", "text_code_block", "table_wikilink"}


def test_exchange_view_adds_navigation_facets_and_links() -> None:
    builder = load_builder()
    conversation = builder.Conversation(
        session_id="session-id",
        path=Path("session.jsonl"),
        title="Following Jesus recovery",
        started_at="2026-05-09T00:00:00Z",
        updated_at="2026-05-09T00:02:00Z",
        cwd="",
        source="",
        branch="main",
        commit="abcdef1",
        role="main",
        events=[],
    )
    exchanges = [
        builder.Exchange(
            exchange_id="0001-session-following-jesus",
            session_id="session-id",
            ordinal=1,
            timestamp="2026-05-09T00:01:00Z",
            role="user",
            kind="user-message",
            title="Following Jesus copy",
            text="Copy Following Jesus M4A files from Ext-10 to ExtSSD-Data.",
        ),
        builder.Exchange(
            exchange_id="0002-session-obsidian",
            session_id="session-id",
            ordinal=2,
            timestamp="2026-05-09T00:02:00Z",
            role="assistant",
            kind="assistant-message",
            title="Obsidian navigation",
            text="Add Obsidian graph view links and facets.",
        ),
    ]

    views = builder.build_exchange_views([conversation], exchanges, public=True)
    markdown = builder.exchange_markdown(views[0], "postmortem-public", public=True)

    assert views[0].next_id == "0002-session-obsidian"
    assert views[0].turn_id == views[1].turn_id
    assert views[0].turn_position == "user-prompt"
    assert views[1].turn_position == "assistant-answer"
    assert "following-jesus" in views[0].topics
    assert "Ext-10" in views[0].entities
    assert "[Session](../sessions/session-session-id.md)" in markdown
    assert "[Next exchange](0002-session-obsidian.md)" in markdown
    assert "<details" not in markdown
    assert "<summary>" not in markdown
    assert "## Surrogate" in markdown
    assert "# Exchange 1: Following Jesus copy" in markdown
    assert "Turn 1" in markdown
    assert "[[" not in markdown
    assert "```text" not in markdown


def test_table_links_do_not_use_pipe_aliases() -> None:
    builder = load_builder()

    link = builder.table_exchange_link(None, "0001-session-title", "Title with | a pipe")
    same_section_link = builder.table_exchange_link(
        "exchanges",
        "0001-session-title",
        "Title",
    )
    nested_link = builder.table_internal_link(
        "topics",
        "sessions",
        "session-abc",
        "Session | Alias",
    )

    assert link == "[Title with - a pipe](exchanges/0001-session-title.md)"
    assert same_section_link == "[Title](0001-session-title.md)"
    assert nested_link == "[Session - Alias](../sessions/session-abc.md)"
    assert "[[" not in link
    assert "|" not in link
    assert (
        builder.markdown_table_cell("See [README]([REPO]/README.md) and A | B")
        == "See README and A \\| B"
    )
    assert builder.safe_markdown_text("<details>") == "&lt;details&gt;"
    assert builder.safe_markdown_text("[REPO]") == "\\[REPO\\]"
    assert builder.safe_link_label("<details>|summary") == "details-summary"
    assert builder.safe_visible_transcript("# Heading\n- item `code`") == (
        "\\# Heading\n\\- item \\`code\\`"
    )
    excerpt = builder.surrogate_excerpt(
        "# AGENTS.md instructions for [REPO] <INSTRUCTIONS>\n"
        "## Repository Guidelines\n"
        "- `src/disk_catalogue/`: Python package"
    )
    assert excerpt.startswith("AGENTS.md instructions for [REPO]")
    assert "#" not in excerpt
    assert "`" not in excerpt
    assert "&lt;" not in excerpt
