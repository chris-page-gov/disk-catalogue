#!/usr/bin/env python3
"""Build private and public assistant postmortem archives for this repository.

The private archive preserves local Codex session sources and exchange notes under
``postmortem/``. That path is intentionally ignored by Git. The public derivative under
``postmortem-public/`` keeps the reconstruction useful without publishing raw transcripts,
local paths, tokens, or private runtime details.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
DEFAULT_SESSION_IDS = [
    "019e09be-f0e7-7211-a66f-d0a174cc4534",
    "019e0a27-41cf-7050-8848-9591dd397e7f",
    "019e0a27-4e3e-7820-8fde-91f3de35e560",
    "019e0a2e-852f-7ee0-8e74-8b4008787092",
    "019e0a43-4285-71c0-9c03-b8bebe20f681",
    "019e0c20-6b15-7853-8513-083f659b13f0",
]
DEFAULT_SESSION_ROOTS = [
    HOME / ".codex" / "sessions",
    HOME / ".codex" / "archived_sessions",
]
PUBLIC_ROOT = REPO_ROOT / "postmortem-public"
PRIVATE_ROOT = REPO_ROOT / "postmortem"
REPO_URL = "https://github.com/chris-page-gov/disk-catalogue"

SECRET_PATTERNS = [
    (
        "github_oauth_token",
        re.compile(r"\bgho_[A-Za-z0-9_]{8,}\b"),
        "gho_[REDACTED]",
    ),
    (
        "huggingface_token",
        re.compile(r"\bhf_[A-Za-z0-9_]{8,}\b"),
        "hf_[REDACTED]",
    ),
    (
        "openai_api_key",
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
        "sk-[REDACTED]",
    ),
    (
        "aws_access_key",
        re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
        "[AWS_ACCESS_KEY_REDACTED]",
    ),
    (
        "google_api_key",
        re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
        "[GOOGLE_API_KEY_REDACTED]",
    ),
    (
        "private_key_header",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        "-----BEGIN REDACTED PRIVATE KEY-----",
    ),
    (
        "generic_secret_assignment",
        re.compile(
            r"\b([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASSWD|API[_-]?KEY|"
            r"PRIVATE[_-]?KEY)[A-Z0-9_]*)\s*=\s*(?!\[REDACTED\])"
            r"([^\s'\"`]{8,})",
            re.IGNORECASE,
        ),
        r"\1=[REDACTED]",
    ),
    (
        "token_header",
        re.compile(
            r"\b(Token|Authorization|Bearer)\s*[:=]\s*(?!\[REDACTED\])" r"[A-Za-z0-9_./+=:-]{8,}",
            re.IGNORECASE,
        ),
        r"\1: [REDACTED]",
    ),
    (
        "connection_string_with_password",
        re.compile(r"\b[a-z][a-z0-9+.-]+://[^\s:/@]+:[^\s@]+@[^\s]+", re.IGNORECASE),
        "[CONNECTION_STRING_REDACTED]",
    ),
]

PHASE_RULES = [
    (
        "repo-orientation",
        "Repo Orientation",
        ("readme", "changelog", "agents", "guiding documents", "review this repo"),
    ),
    (
        "material-discovery",
        "Material Discovery",
        ("old music library", "avery willis", "storying", "following jesus", "track names"),
    ),
    (
        "recovery-copy-metadata",
        "Recovery, Copy, Metadata",
        ("connected the ext-10", "extssd-data", "retrieve", "embedded tags", "metadata"),
    ),
    (
        "transcription-sampling",
        "Transcription Sampling",
        ("transcribe", "sample transcript", "summary of the contents", "whisper"),
    ),
    (
        "speaker-diarization",
        "Speaker Diarization",
        ("speaker", "pyannote", "diarization", "diarisation", "apple gpu", "davinci"),
    ),
    (
        "full-semantic-catalogue",
        "Full Semantic Catalogue",
        (
            "full semantic catalogue",
            "unattended",
            "test coverage",
            "duplicates",
            "completeness",
        ),
    ),
    (
        "rename-release",
        "Rename and Release",
        ("rename", "publish a version", "release", "v1.0", "catalogue file"),
    ),
    (
        "postmortem-security-navigation",
        "Postmortem, Security, Navigation",
        ("postmortem", "security review", "obsidian", "graph view", "navigable"),
    ),
]

TOPIC_RULES = {
    "repo-review": ("repo", "readme", "changelog", "agents", "guiding documents"),
    "disk-catalogue": ("disk catalogue", "duckdb", "catalogue.duckdb", "database"),
    "following-jesus": ("following jesus", "avery willis", "progressive vision"),
    "drive-recovery": ("ext-10", "extssd-data", "external ssd", "retrieve", "copy"),
    "metadata": ("metadata", "embedded tag", "m4a", "itunes"),
    "transcription": ("transcribe", "transcription", "transcript", "whisper"),
    "diarization": ("speaker", "pyannote", "diarization", "diarisation", "embedding"),
    "semantic-catalogue": ("semantic catalogue", "summary", "bible passage", "storying role"),
    "verification": ("verify", "verification", "coverage", "complete", "completeness"),
    "duplicates": ("duplicate", "duplicates", "sha-256", "checksum"),
    "rename-plan": ("rename", "naming", "album", "track"),
    "release-ci": ("release", "publish", "ci", "github actions", "mypy"),
    "postmortem": ("postmortem", "methodology", "decision register"),
    "security": ("security", "redact", "secret", "token", "publication lint"),
    "obsidian-navigation": ("obsidian", "graph view", "links", "facets", "hover", "folding"),
}

TOPIC_LABELS = {
    "repo-review": "Repo Review",
    "disk-catalogue": "Disk Catalogue",
    "following-jesus": "Following Jesus",
    "drive-recovery": "Drive Recovery",
    "metadata": "Metadata",
    "transcription": "Transcription",
    "diarization": "Diarization",
    "semantic-catalogue": "Semantic Catalogue",
    "verification": "Verification",
    "duplicates": "Duplicates",
    "rename-plan": "Rename Plan",
    "release-ci": "Release and CI",
    "postmortem": "Postmortem",
    "security": "Security",
    "obsidian-navigation": "Obsidian Navigation",
}

ENTITY_ALIASES = {
    "Following Jesus": ("following jesus",),
    "Avery Willis": ("avery willis",),
    "Progressive Vision": ("progressive vision",),
    "Ext-10": ("ext-10",),
    "ExtSSD-Data": ("extssd-data",),
    "DuckDB": ("duckdb", "catalogue.duckdb"),
    "Obsidian": ("obsidian",),
    "GitHub": ("github",),
    "GitHub Actions": ("github actions",),
    "Codex": ("codex",),
    "pyannote.audio": ("pyannote", "pyannote.audio"),
    "whisper.cpp": ("whisper.cpp", "whisper"),
    "DaVinci Resolve": ("davinci resolve",),
    "iTunes": ("itunes",),
    "Nuffield Interactive Book System": ("nuffield interactive book system", "nibs"),
    "SeeLinks": ("seelinks",),
}


@dataclass(frozen=True)
class Conversation:
    session_id: str
    path: Path
    title: str
    started_at: str
    updated_at: str
    cwd: str
    source: str
    branch: str
    commit: str
    role: str
    events: list[dict[str, Any]]


@dataclass(frozen=True)
class Exchange:
    exchange_id: str
    session_id: str
    ordinal: int
    timestamp: str
    role: str
    kind: str
    title: str
    text: str


@dataclass(frozen=True)
class ExchangeView:
    exchange: Exchange
    session_title: str
    phase_slug: str
    phase_label: str
    topics: list[str]
    entities: list[str]
    artifacts: list[str]
    previous_id: str
    next_id: str
    session_previous_id: str
    session_next_id: str
    turn_id: str
    turn_number: int
    turn_position: str
    excerpt: str


def slugify(value: str, fallback: str = "item") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    cleaned = re.sub(r"-+", "-", cleaned)
    return cleaned[:80] or fallback


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def json_loads(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def load_session_index(path: Path | None = None) -> dict[str, str]:
    index_path = path or (HOME / ".codex" / "session_index.jsonl")
    if not index_path.exists():
        return {}
    titles: dict[str, str] = {}
    for row in read_jsonl(index_path):
        session_id = str(row.get("id", ""))
        title = str(row.get("thread_name", ""))
        if session_id and title:
            titles[session_id] = title
    return titles


def locate_session_files(
    session_ids: list[str],
    session_roots: list[Path] | None = None,
) -> dict[str, Path]:
    roots = session_roots or DEFAULT_SESSION_ROOTS
    found: dict[str, Path] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.jsonl"):
            for session_id in session_ids:
                if session_id in path.name:
                    found[session_id] = path
    missing = sorted(set(session_ids) - set(found))
    if missing:
        raise FileNotFoundError(f"Missing Codex session files: {', '.join(missing)}")
    return found


def content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text") or item.get("input_text") or item.get("output_text")
        if isinstance(text, str):
            parts.append(text)
    return "\n".join(parts).strip()


def command_summary(arguments: str) -> str:
    data = json_loads(arguments)
    if not isinstance(data, dict):
        return str(data)[:400]
    command = data.get("cmd") or data.get("command")
    if isinstance(command, list):
        return " ".join(str(part) for part in command)[:400]
    if isinstance(command, str):
        return command[:400]
    return json.dumps(data, sort_keys=True)[:400]


def output_summary(output: str) -> str:
    lines = output.strip().splitlines()
    if not lines:
        return "(no output)"
    important = [line for line in lines if line.strip()]
    return "\n".join(important[:12])[:1600]


def session_prefix(session_id: str) -> str:
    return session_id[:8].strip("-") or "session"


def exchange_id(session_id: str, ordinal: int, title: str) -> str:
    return f"{ordinal:04d}-{session_prefix(session_id)}-{slugify(redact(title))}"


def event_to_exchange(event: dict[str, Any], session_id: str, ordinal: int) -> Exchange | None:
    timestamp = str(event.get("timestamp", ""))
    payload = event.get("payload", {})
    if not isinstance(payload, dict):
        return None

    if event.get("type") == "response_item":
        payload_type = payload.get("type")
        if payload_type == "message":
            role = str(payload.get("role", "assistant"))
            text = content_text(payload.get("content"))
            if not text:
                return None
            title_source = text.splitlines()[0][:80]
            kind = f"{role}-message" if role in {"assistant", "user"} else "message"
            return Exchange(
                exchange_id=exchange_id(session_id, ordinal, title_source),
                session_id=session_id,
                ordinal=ordinal,
                timestamp=timestamp,
                role=role,
                kind=kind,
                title=title_source,
                text=text,
            )
        if payload_type == "function_call":
            name = str(payload.get("name", "tool"))
            text = command_summary(str(payload.get("arguments", "")))
            return Exchange(
                exchange_id=exchange_id(session_id, ordinal, name),
                session_id=session_id,
                ordinal=ordinal,
                timestamp=timestamp,
                role="tool",
                kind=f"call:{name}",
                title=name,
                text=text,
            )
        if payload_type == "function_call_output":
            text = output_summary(str(payload.get("output", "")))
            return Exchange(
                exchange_id=f"{ordinal:04d}-{session_id[:8]}-tool-output",
                session_id=session_id,
                ordinal=ordinal,
                timestamp=timestamp,
                role="tool",
                kind="tool-output",
                title="tool output",
                text=text,
            )

    if event.get("type") == "event_msg" and payload.get("type") == "user_message":
        text = str(payload.get("message", "")).strip()
        if not text:
            return None
        title_source = text.splitlines()[0][:80]
        return Exchange(
            exchange_id=exchange_id(session_id, ordinal, title_source),
            session_id=session_id,
            ordinal=ordinal,
            timestamp=timestamp,
            role="user",
            kind="user-message",
            title=title_source,
            text=text,
        )
    return None


def load_conversations(session_ids: list[str]) -> list[Conversation]:
    titles = load_session_index()
    paths = locate_session_files(session_ids)
    conversations: list[Conversation] = []
    for session_id in session_ids:
        path = paths[session_id]
        events = read_jsonl(path)
        meta = next(
            (row.get("payload", {}) for row in events if row.get("type") == "session_meta"),
            {},
        )
        if not isinstance(meta, dict):
            meta = {}
        git = meta.get("git", {})
        if not isinstance(git, dict):
            git = {}
        title = titles.get(session_id) or derive_title(events) or session_id
        conversations.append(
            Conversation(
                session_id=session_id,
                path=path,
                title=title,
                started_at=str(meta.get("timestamp") or events[0].get("timestamp", "")),
                updated_at=str(events[-1].get("timestamp", "")) if events else "",
                cwd=str(meta.get("cwd", "")),
                source=json.dumps(meta.get("source", ""), sort_keys=True),
                branch=str(git.get("branch", "")),
                commit=str(git.get("commit_hash", "")),
                role=str(meta.get("agent_role", "")),
                events=events,
            )
        )
    return conversations


def derive_title(events: list[dict[str, Any]]) -> str:
    for event in events:
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        if payload.get("type") == "message" and payload.get("role") == "user":
            text = content_text(payload.get("content"))
            if text:
                return text.splitlines()[0][:80]
    return ""


def extract_exchanges(conversations: list[Conversation]) -> list[Exchange]:
    exchanges: list[Exchange] = []
    ordinal = 1
    for conversation in conversations:
        for event in conversation.events:
            exchange = event_to_exchange(event, conversation.session_id, ordinal)
            if exchange is None:
                continue
            exchanges.append(exchange)
            ordinal += 1
    return exchanges


def redact(text: str) -> str:
    redacted = text
    replacements = {
        str(REPO_ROOT): "[REPO]",
        str(HOME): "[HOME]",
        "/Volumes/ExtSSD-Data": "[EXTSSD_DATA]",
        "/Volumes/Ext-10": "[EXT_10]",
    }
    for source, target in replacements.items():
        redacted = redacted.replace(source, target)
    redacted = re.sub(r"/Volumes/[^\s)\"'`]+", "[VOLUME_PATH]", redacted)
    redacted = re.sub(r"/Users/crpage[^\s)\"'`]+", "[HOME_PATH]", redacted)
    for _name, pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def public_excerpt(text: str, limit: int = 700) -> str:
    squashed = re.sub(r"\s+", " ", redact(text)).strip()
    if len(squashed) <= limit:
        return squashed
    return squashed[: limit - 3].rstrip() + "..."


def surrogate_excerpt(text: str, limit: int = 280) -> str:
    cleaned = strip_markdown_links(redact(text))
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"<[^>]{0,80}>", " ", cleaned)
    cleaned = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*[-*+]\s+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def yaml_scalar(value: str | int) -> str:
    return json.dumps(safe_markdown_text(str(value)))


def yaml_list(values: list[str]) -> str:
    if not values:
        return "[]"
    return "\n" + "\n".join(f"  - {yaml_scalar(value)}" for value in values)


def unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def strip_markdown_links(value: str) -> str:
    previous = value
    while True:
        stripped = re.sub(r"\[([^\]\n]+)\]\([^\)\n]+(?:\s+\"[^\"]*\")?\)", r"\1", previous)
        if stripped == previous:
            return stripped
        previous = stripped


def safe_markdown_text(value: str) -> str:
    escaped = (
        strip_markdown_links(value)
        .replace("[[", r"\[\[")
        .replace("]]", r"\]\]")
        .replace("[", r"\[")
        .replace("]", r"\]")
    )
    return escaped.replace("<", "&lt;").replace(">", "&gt;")


def markdown_table_cell(value: str) -> str:
    return safe_markdown_text(value).replace("\n", " ").replace("|", "\\|")


def safe_link_label(value: str, limit: int = 55) -> str:
    cleaned = re.sub(r"\s+", " ", strip_markdown_links(redact(value))).strip()
    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned)
    cleaned = cleaned.replace("[", "(").replace("]", ")").replace("|", "-")
    cleaned = cleaned.replace("<", "").replace(">", "")
    return (cleaned[: limit - 3].rstrip() + "...") if len(cleaned) > limit else cleaned


def table_internal_link(
    current_section: str | None,
    target_section: str,
    slug: str,
    label: str,
    suffix: str = ".md",
) -> str:
    same_section = current_section == target_section and current_section is not None
    prefix = "" if current_section is None or same_section else "../"
    if same_section or not target_section:
        target_parts = [f"{slug}{suffix}"]
    else:
        target_parts = [target_section, f"{slug}{suffix}"]
    target = quote(f"{prefix}{'/'.join(target_parts)}", safe="/.")
    return f"[{safe_link_label(label)}]({target})"


def table_exchange_link(current_section: str | None, exchange_id: str, label: str) -> str:
    return table_internal_link(current_section, "exchanges", exchange_id, label)


def internal_link(
    current_section: str | None,
    target_section: str,
    slug: str,
    label: str,
    suffix: str = ".md",
) -> str:
    return table_internal_link(current_section, target_section, slug, label, suffix=suffix)


def exchange_link(current_section: str | None, exchange_id: str, label: str) -> str:
    return internal_link(current_section, "exchanges", exchange_id, label)


def fenced_text_block(text: str) -> str:
    longest = max((len(match.group(0)) for match in re.finditer(r"`{3,}", text)), default=3)
    fence = "`" * max(4, longest + 1)
    return f"{fence}text\n{text}\n{fence}"


def safe_visible_transcript(text: str, limit: int = 2200) -> str:
    redacted = redact(text).replace("\r\n", "\n").replace("\r", "\n").strip()
    redacted = re.sub(r"\n{3,}", "\n\n", redacted)
    if len(redacted) > limit:
        redacted = redacted[: limit - 4].rstrip() + "\n..."
    escaped = safe_markdown_text(redacted)
    lines: list[str] = []
    for line in escaped.splitlines():
        line = line.replace("`", r"\`")
        line = re.sub(r"^(\s*)(#{1,6}\s)", r"\1\\\2", line)
        line = re.sub(r"^(\s*)([-*+]\s)", r"\1\\\2", line)
        line = re.sub(r"^(\s*)(\d+[.)]\s)", r"\1\\\2", line)
        lines.append(line)
    return "\n".join(lines)


def display_title(value: str, limit: int = 90) -> str:
    return safe_markdown_text(surrogate_excerpt(value, limit=limit))


def plain_display_title(value: str, limit: int = 90) -> str:
    return surrogate_excerpt(value, limit=limit)


def page_slug(kind: str, label: str) -> str:
    return slugify(label, fallback=kind)


def classify_phase(exchange: Exchange) -> tuple[str, str]:
    text = f"{exchange.title}\n{exchange.text}".lower()
    for slug, label, keywords in PHASE_RULES:
        if any(keyword in text for keyword in keywords):
            return slug, label
    return "other", "Other"


def extract_topics(exchange: Exchange) -> list[str]:
    text = f"{exchange.title}\n{exchange.text}".lower()
    topics = [
        topic
        for topic, keywords in TOPIC_RULES.items()
        if any(keyword in text for keyword in keywords)
    ]
    if not topics:
        topics.append("conversation-mechanics")
    return topics


def extract_entities(exchange: Exchange) -> list[str]:
    text = f"{exchange.title}\n{exchange.text}".lower()
    entities = [
        label
        for label, aliases in ENTITY_ALIASES.items()
        if any(alias in text for alias in aliases)
    ]
    commit_ids = re.findall(r"\b[0-9a-f]{7,40}\b", exchange.text)
    for commit_id in commit_ids[:5]:
        entities.append(f"commit {commit_id[:7]}")
    return unique_ordered(entities)[:16]


def extract_artifacts(exchange: Exchange) -> list[str]:
    candidates: list[str] = []
    for match in re.findall(r"`([^`]+)`", exchange.text):
        if "/" in match or "." in match:
            candidates.append(match)
    path_pattern = re.compile(
        r"\b(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\b|"
        r"\b[A-Za-z0-9_.-]+\.(?:py|md|sql|csv|json|jsonl|toml|yml|yaml|sh|duckdb)\b"
    )
    candidates.extend(path_pattern.findall(exchange.text))
    normalized_candidates = [
        f"/{candidate}" if candidate.startswith(("Users/", "Volumes/")) else candidate
        for candidate in candidates
    ]
    clean = [
        redact(candidate).strip(".,);:")
        for candidate in normalized_candidates
        if len(candidate.strip()) <= 140
    ]
    return unique_ordered([item for item in clean if item])[:20]


def build_exchange_views(
    conversations: list[Conversation],
    exchanges: list[Exchange],
    public: bool,
) -> list[ExchangeView]:
    session_titles = {conversation.session_id: conversation.title for conversation in conversations}
    session_previous: dict[str, str] = {}
    session_next: dict[str, str] = {}
    by_session: dict[str, list[Exchange]] = defaultdict(list)
    for exchange in exchanges:
        by_session[exchange.session_id].append(exchange)
    for session_exchanges in by_session.values():
        for index, exchange in enumerate(session_exchanges):
            session_previous[exchange.exchange_id] = (
                session_exchanges[index - 1].exchange_id if index else ""
            )
            session_next[exchange.exchange_id] = (
                session_exchanges[index + 1].exchange_id
                if index < len(session_exchanges) - 1
                else ""
            )

    turn_ids: dict[str, str] = {}
    turn_numbers: dict[str, int] = {}
    turn_positions: dict[str, str] = {}
    for session_id, session_exchanges in by_session.items():
        turn_number = 0
        current_turn_id = ""
        last_role = ""
        last_user_text = ""
        for exchange in session_exchanges:
            duplicate_prompt = (
                exchange.role == "user"
                and last_role == "user"
                and bool(current_turn_id)
                and exchange.text == last_user_text
            )
            if duplicate_prompt:
                position = "user-prompt-copy"
            elif exchange.role == "user" or not current_turn_id:
                turn_number += 1
                current_turn_id = (
                    f"turn-{turn_number:04d}-{session_prefix(session_id)}-"
                    f"{slugify(redact(exchange.title))}"
                )
                position = "user-prompt" if exchange.role == "user" else "context-before-prompt"
            elif exchange.role == "assistant":
                position = "assistant-answer"
            elif exchange.role == "tool":
                position = "tool-evidence"
            else:
                position = f"{slugify(exchange.role)}-message"
            turn_ids[exchange.exchange_id] = current_turn_id
            turn_numbers[exchange.exchange_id] = turn_number
            turn_positions[exchange.exchange_id] = position
            last_role = exchange.role
            if exchange.role == "user":
                last_user_text = exchange.text

    views: list[ExchangeView] = []
    for index, exchange in enumerate(exchanges):
        phase_slug, phase_label = classify_phase(exchange)
        text = redact(exchange.text) if public else exchange.text
        views.append(
            ExchangeView(
                exchange=exchange,
                session_title=session_titles.get(exchange.session_id, exchange.session_id),
                phase_slug=phase_slug,
                phase_label=phase_label,
                topics=extract_topics(exchange),
                entities=extract_entities(exchange),
                artifacts=extract_artifacts(exchange),
                previous_id=exchanges[index - 1].exchange_id if index else "",
                next_id=exchanges[index + 1].exchange_id if index < len(exchanges) - 1 else "",
                session_previous_id=session_previous.get(exchange.exchange_id, ""),
                session_next_id=session_next.get(exchange.exchange_id, ""),
                turn_id=turn_ids[exchange.exchange_id],
                turn_number=turn_numbers[exchange.exchange_id],
                turn_position=turn_positions[exchange.exchange_id],
                excerpt=surrogate_excerpt(text),
            )
        )
    return views


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = "\n".join(line.rstrip() for line in text.splitlines()).rstrip()
    path.write_text(cleaned + "\n", encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_private_ignored() -> None:
    gitignore = REPO_ROOT / ".gitignore"
    text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if "/postmortem/" not in text.splitlines():
        raise RuntimeError("Refusing to write private archive because /postmortem/ is not ignored")


def clean_generated(root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)


def copy_private_sources(conversations: list[Conversation], private_root: Path) -> None:
    sources_dir = private_root / "sources" / "conversations"
    sources_dir.mkdir(parents=True, exist_ok=True)
    for conversation in conversations:
        filename = f"{conversation.session_id}-{slugify(conversation.title)}.jsonl"
        shutil.copy2(conversation.path, sources_dir / filename)


def exchange_frontmatter(view: ExchangeView) -> str:
    exchange = view.exchange
    tags = [
        "postmortem/exchange",
        f"role/{slugify(exchange.role)}",
        f"kind/{slugify(exchange.kind)}",
        f"phase/{view.phase_slug}",
        *[f"topic/{topic}" for topic in view.topics],
    ]
    return "\n".join(
        [
            "---",
            f"type: {yaml_scalar('exchange')}",
            f"exchange_id: {yaml_scalar(exchange.exchange_id)}",
            f"session_id: {yaml_scalar(exchange.session_id)}",
            f"ordinal: {yaml_scalar(exchange.ordinal)}",
            f"timestamp: {yaml_scalar(exchange.timestamp)}",
            f"role: {yaml_scalar(exchange.role)}",
            f"kind: {yaml_scalar(exchange.kind)}",
            f"turn_id: {yaml_scalar(view.turn_id)}",
            f"turn_position: {yaml_scalar(view.turn_position)}",
            f"phase: {yaml_scalar(view.phase_label)}",
            f"topics: {yaml_list([TOPIC_LABELS.get(topic, topic) for topic in view.topics])}",
            f"entities: {yaml_list(view.entities)}",
            f"artifacts: {yaml_list(view.artifacts)}",
            f"tags: {yaml_list(tags)}",
            "---",
            "",
        ]
    )


def exchange_markdown(view: ExchangeView, root_name: str, public: bool) -> str:
    exchange = view.exchange
    session_slug = page_slug("session", f"session-{exchange.session_id}")
    current_section = "exchanges"
    session_link = internal_link(current_section, "sessions", session_slug, "Session")
    turn_link = internal_link(
        current_section,
        "turns",
        view.turn_id,
        f"Turn {view.turn_number}",
    )
    phase_link = internal_link(current_section, "phases", view.phase_slug, view.phase_label)
    role_link = internal_link(
        current_section, "roles", page_slug("role", exchange.role), exchange.role
    )
    kind_link = internal_link(
        current_section, "kinds", page_slug("kind", exchange.kind), exchange.kind
    )
    topic_links = [
        internal_link(current_section, "topics", topic, TOPIC_LABELS.get(topic, topic))
        for topic in view.topics
    ]
    entity_links = [
        internal_link(current_section, "entities", page_slug("entity", entity), entity)
        for entity in view.entities
    ]
    artifact_links = [
        internal_link(current_section, "artifacts", page_slug("artifact", artifact), artifact)
        for artifact in view.artifacts
    ]
    previous_link = (
        exchange_link(current_section, view.previous_id, "Previous exchange")
        if view.previous_id
        else "Start of archive"
    )
    next_link = (
        exchange_link(current_section, view.next_id, "Next exchange")
        if view.next_id
        else "End of archive"
    )
    session_previous_link = (
        exchange_link(current_section, view.session_previous_id, "Previous in session")
        if view.session_previous_id
        else "Start of session"
    )
    session_next_link = (
        exchange_link(current_section, view.session_next_id, "Next in session")
        if view.session_next_id
        else "End of session"
    )
    details_label = "Redacted Detail" if public else "Full Detail"
    source_line = (
        "The raw source transcript is private-only."
        if public
        else f"Source session: `{exchange.session_id}`."
    )
    topic_text = ", ".join(topic_links) if topic_links else "None"
    entity_text = ", ".join(entity_links) if entity_links else "None"
    artifact_text = ", ".join(artifact_links) if artifact_links else "None"
    title = display_title(redact(exchange.title) if public else exchange.title, limit=120)
    session_title = safe_markdown_text(redact(view.session_title) if public else view.session_title)
    excerpt = safe_markdown_text(view.excerpt)
    detail_body = (
        safe_visible_transcript(exchange.text) if public else fenced_text_block(exchange.text)
    )
    context_path = (
        f"{internal_link(current_section, '', 'index', 'Index')} > "
        f"{session_link} > {turn_link} > {phase_link} > Exchange `{exchange.ordinal}`"
    )
    body = f"""# Exchange {exchange.ordinal}: {title}

## Structural Context

{context_path}

Global: {previous_link} | {next_link}
Session: {session_previous_link} | {session_next_link}

## Surrogate

- Title: {title}
- Exchange ID: `{exchange.exchange_id}`
- Turn: {turn_link} ({view.turn_position})
- Session: {session_link} `{exchange.session_id}` ({session_title})
- Timestamp: `{exchange.timestamp}`
- Role / kind: {role_link} / {kind_link}
- Phase: {phase_link}
- Topics: {topic_text}
- Entities: {entity_text}
- Artifacts: {artifact_text}
- Excerpt: {excerpt}

## {details_label}

{source_line}

{detail_body}
"""
    return exchange_frontmatter(view) + body


def exchange_register_from_views(views: list[ExchangeView], public: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for view in views:
        exchange = view.exchange
        rows.append(
            {
                "exchange_id": exchange.exchange_id,
                "session_id": exchange.session_id,
                "ordinal": exchange.ordinal,
                "timestamp": exchange.timestamp,
                "role": exchange.role,
                "kind": exchange.kind,
                "title": redact(exchange.title) if public else exchange.title,
                "turn_id": view.turn_id,
                "turn_number": view.turn_number,
                "turn_position": view.turn_position,
                "phase": view.phase_label,
                "topics": [TOPIC_LABELS.get(topic, topic) for topic in view.topics],
                "entities": view.entities,
                "artifacts": view.artifacts,
                "previous_id": view.previous_id,
                "next_id": view.next_id,
                "session_previous_id": view.session_previous_id,
                "session_next_id": view.session_next_id,
                "excerpt": view.excerpt,
            }
        )
    return rows


def session_register(conversations: list[Conversation]) -> list[dict[str, Any]]:
    return [
        {
            "session_id": item.session_id,
            "title": item.title,
            "started_at": item.started_at,
            "updated_at": item.updated_at,
            "cwd": item.cwd,
            "source": item.source,
            "branch": item.branch,
            "commit": item.commit,
            "role": item.role,
        }
        for item in conversations
    ]


def exchange_register(exchanges: list[Exchange], public: bool) -> list[dict[str, Any]]:
    return [
        {
            "exchange_id": exchange.exchange_id,
            "session_id": exchange.session_id,
            "ordinal": exchange.ordinal,
            "timestamp": exchange.timestamp,
            "role": exchange.role,
            "kind": exchange.kind,
            "title": redact(exchange.title) if public else exchange.title,
        }
        for exchange in exchanges
    ]


def views_by_field(views: list[ExchangeView], field: str) -> dict[str, list[ExchangeView]]:
    grouped: dict[str, list[ExchangeView]] = defaultdict(list)
    for view in views:
        values = getattr(view, field)
        if isinstance(values, list):
            for value in values:
                grouped[str(value)].append(view)
        else:
            grouped[str(values)].append(view)
    return dict(grouped)


def write_collection_page(
    root: Path,
    root_name: str,
    section: str,
    slug: str,
    title: str,
    views: list[ExchangeView],
) -> None:
    title = title.strip()
    display_title = safe_markdown_text(title)
    lines = [
        "---",
        f"type: {yaml_scalar(section.rstrip('s'))}",
        f"title: {yaml_scalar(title)}",
        f"exchange_count: {yaml_scalar(len(views))}",
        "---",
        "",
        f"# {display_title}",
        "",
        f"Up: {internal_link(section, '', 'navigation', 'Navigation')}",
        "",
        "| # | Exchange | Turn | Session | Role / kind | Excerpt |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for view in sorted(views, key=lambda item: item.exchange.ordinal):
        exchange = view.exchange
        session_slug = page_slug("session", f"session-{exchange.session_id}")
        session = table_internal_link(section, "sessions", session_slug, exchange.session_id[:8])
        turn = table_internal_link(section, "turns", view.turn_id, f"Turn {view.turn_number}")
        exchange_ref = table_exchange_link(section, exchange.exchange_id, exchange.title)
        role = markdown_table_cell(f"{exchange.role} / {exchange.kind}")
        excerpt = markdown_table_cell(view.excerpt)
        lines.append(
            f"| {exchange.ordinal} | {exchange_ref} | {turn} | {session} | {role} | {excerpt} |"
        )
    write_text(root / "wiki" / section / f"{slug}.md", "\n".join(lines))


def write_session_pages(
    root: Path,
    root_name: str,
    conversations: list[Conversation],
    views: list[ExchangeView],
    public: bool,
) -> None:
    by_session: dict[str, list[ExchangeView]] = defaultdict(list)
    for view in views:
        by_session[view.exchange.session_id].append(view)
    conversations_by_id = {conversation.session_id: conversation for conversation in conversations}
    for session_id, session_views in by_session.items():
        conversation = conversations_by_id.get(session_id)
        title = session_views[0].session_title
        display_title = safe_markdown_text(redact(title) if public else title)
        lines = [
            "---",
            f"type: {yaml_scalar('session')}",
            f"session_id: {yaml_scalar(session_id)}",
            f"title: {yaml_scalar(redact(title) if public else title)}",
            f"exchange_count: {yaml_scalar(len(session_views))}",
            "---",
            "",
            f"# Session {session_id[:8]}: {display_title}",
            "",
            f"Up: {internal_link('sessions', '', 'navigation', 'Navigation')}",
            "",
        ]
        if conversation:
            lines.extend(
                [
                    f"- Started: `{conversation.started_at}`",
                    f"- Updated: `{conversation.updated_at}`",
                    f"- Role: `{conversation.role or 'main'}`",
                    "",
                ]
            )
        for phase_slug, phase_label, _keywords in [*PHASE_RULES, ("other", "Other", ())]:
            phase_views = [view for view in session_views if view.phase_slug == phase_slug]
            if not phase_views:
                continue
            lines.extend(
                [
                    f"## {phase_label}",
                    "",
                    "| # | Exchange | Turn position | Role / kind | Topics | Excerpt |",
                    "| ---: | --- | --- | --- | --- | --- |",
                ]
            )
            for view in phase_views:
                exchange = view.exchange
                topics = ", ".join(TOPIC_LABELS.get(topic, topic) for topic in view.topics)
                exchange_ref = table_exchange_link("sessions", exchange.exchange_id, exchange.title)
                turn_position = markdown_table_cell(view.turn_position)
                role = markdown_table_cell(f"{exchange.role} / {exchange.kind}")
                topic_cell = markdown_table_cell(topics)
                excerpt = markdown_table_cell(view.excerpt)
                lines.append(
                    f"| {exchange.ordinal} | {exchange_ref} | {turn_position} | "
                    f"{role} | {topic_cell} | {excerpt} |"
                )
            lines.append("")
        session_slug = page_slug("session", f"session-{session_id}")
        write_text(
            root / "wiki" / "sessions" / f"{session_slug}.md",
            "\n".join(lines),
        )


def graph_register(
    root_name: str,
    views: list[ExchangeView],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    nodes: dict[str, dict[str, str]] = {}
    edges: list[dict[str, str]] = []

    def add_node(node_id: str, label: str, kind: str) -> None:
        nodes[node_id] = {"id": node_id, "label": label, "kind": kind}

    def add_edge(source: str, target: str, kind: str) -> None:
        edges.append({"source": source, "target": target, "kind": kind})

    for view in views:
        exchange = view.exchange
        exchange_node = f"exchange:{exchange.exchange_id}"
        add_node(exchange_node, exchange.exchange_id, "exchange")
        turn_node = f"turn:{view.turn_id}"
        add_node(turn_node, f"Turn {view.turn_number}", "turn")
        session_node = f"session:{exchange.session_id}"
        add_node(session_node, exchange.session_id[:8], "session")
        phase_node = f"phase:{view.phase_slug}"
        add_node(phase_node, view.phase_label, "phase")
        role_node = f"role:{exchange.role}"
        kind_node = f"kind:{exchange.kind}"
        add_node(role_node, exchange.role, "role")
        add_node(kind_node, exchange.kind, "kind")
        add_edge(exchange_node, session_node, "belongs_to")
        add_edge(exchange_node, turn_node, "in_turn")
        add_edge(turn_node, session_node, "belongs_to")
        add_edge(exchange_node, phase_node, "in_phase")
        add_edge(exchange_node, role_node, "has_role")
        add_edge(exchange_node, kind_node, "has_kind")
        if view.previous_id:
            add_edge(exchange_node, f"exchange:{view.previous_id}", "previous")
        if view.next_id:
            add_edge(exchange_node, f"exchange:{view.next_id}", "next")
        for topic in view.topics:
            topic_node = f"topic:{topic}"
            add_node(topic_node, TOPIC_LABELS.get(topic, topic), "topic")
            add_edge(exchange_node, topic_node, "mentions_topic")
        for entity in view.entities:
            entity_node = f"entity:{page_slug('entity', entity)}"
            add_node(entity_node, entity, "entity")
            add_edge(exchange_node, entity_node, "mentions_entity")
        for artifact in view.artifacts:
            artifact_node = f"artifact:{page_slug('artifact', artifact)}"
            add_node(artifact_node, artifact, "artifact")
            add_edge(exchange_node, artifact_node, "mentions_artifact")

    for view in views:
        for topic in view.topics:
            for entity in view.entities:
                add_edge(
                    f"topic:{topic}",
                    f"entity:{page_slug('entity', entity)}",
                    "co_occurs",
                )
    _ = root_name
    return list(nodes.values()), edges


def write_graph_page(root: Path, root_name: str, views: list[ExchangeView]) -> None:
    top_topics = Counter(topic for view in views for topic in view.topics).most_common(12)
    top_entities = Counter(entity for view in views for entity in view.entities).most_common(12)
    lines = [
        "# Graph Map",
        "",
        f"Up: {internal_link(None, '', 'navigation', 'Navigation')}",
        "",
        "This page gives Obsidian a compact hub graph in addition to the full exchange graph.",
        "",
        "```mermaid",
        "graph LR",
    ]
    for topic, _count in top_topics:
        topic_label = TOPIC_LABELS.get(topic, topic)
        lines.append(f"  topic_{slugify(topic)}[{json.dumps(topic_label)}]")
    for entity, _count in top_entities:
        entity_slug = slugify(entity)
        lines.append(f"  entity_{entity_slug}[{json.dumps(entity)}]")
    for view in views:
        for topic in view.topics[:3]:
            for entity in view.entities[:3]:
                if topic in dict(top_topics) and entity in dict(top_entities):
                    lines.append(f"  topic_{slugify(topic)} --> entity_{slugify(entity)}")
    lines.extend(["```", ""])
    write_text(root / "wiki" / "graph.md", "\n".join(unique_ordered(lines)))


def write_navigation_pages(
    root: Path,
    root_name: str,
    conversations: list[Conversation],
    views: list[ExchangeView],
    public: bool,
) -> None:
    write_session_pages(root, root_name, conversations, views, public)

    phase_groups = defaultdict(list)
    role_groups = defaultdict(list)
    kind_groups = defaultdict(list)
    turn_position_groups = defaultdict(list)
    topic_groups = views_by_field(views, "topics")
    entity_groups = views_by_field(views, "entities")
    artifact_groups = views_by_field(views, "artifacts")
    for view in views:
        phase_groups[view.phase_slug].append(view)
        role_groups[view.exchange.role].append(view)
        kind_groups[view.exchange.kind].append(view)
        turn_position_groups[view.turn_position].append(view)

    for slug, phase_views in phase_groups.items():
        label = phase_views[0].phase_label
        write_collection_page(root, root_name, "phases", slug, f"Phase: {label}", phase_views)
    for topic, topic_views in topic_groups.items():
        label = TOPIC_LABELS.get(topic, topic)
        write_collection_page(root, root_name, "topics", topic, f"Topic: {label}", topic_views)
    for entity, entity_views in entity_groups.items():
        write_collection_page(
            root,
            root_name,
            "entities",
            page_slug("entity", entity),
            f"Entity: {entity}",
            entity_views,
        )
    for artifact, artifact_views in artifact_groups.items():
        write_collection_page(
            root,
            root_name,
            "artifacts",
            page_slug("artifact", artifact),
            f"Artifact: {artifact}",
            artifact_views,
        )
    for role, role_views in role_groups.items():
        write_collection_page(
            root,
            root_name,
            "roles",
            page_slug("role", role),
            f"Role: {role}",
            role_views,
        )
    for kind, kind_views in kind_groups.items():
        write_collection_page(
            root,
            root_name,
            "kinds",
            page_slug("kind", kind),
            f"Kind: {kind}",
            kind_views,
        )
    for turn_position, position_views in turn_position_groups.items():
        write_collection_page(
            root,
            root_name,
            "turn-positions",
            page_slug("turn-position", turn_position),
            f"Turn Position: {turn_position}",
            position_views,
        )

    write_turn_pages(root, root_name, views)
    write_surrogates_page(root, root_name, views)
    write_timeline_page(root, root_name, views)
    write_navigation_index(root, root_name, views)
    write_graph_page(root, root_name, views)
    nodes, edges = graph_register(root_name, views)
    write_json(root / "wiki" / "data" / "graph_nodes.json", nodes)
    write_json(root / "wiki" / "data" / "graph_edges.json", edges)
    write_json(root / "wiki" / "data" / "facets.json", facet_register(views))
    write_json(root / "wiki" / "data" / "turns.json", turn_register(views))


def facet_register(views: list[ExchangeView]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "phases": dict(sorted(Counter(view.phase_label for view in views).items())),
        "topics": dict(
            sorted(
                Counter(
                    TOPIC_LABELS.get(topic, topic) for view in views for topic in view.topics
                ).items()
            )
        ),
        "entities": dict(
            sorted(Counter(entity for view in views for entity in view.entities).items())
        ),
        "artifacts": dict(
            sorted(Counter(artifact for view in views for artifact in view.artifacts).items())
        ),
        "roles": dict(sorted(Counter(view.exchange.role for view in views).items())),
        "kinds": dict(sorted(Counter(view.exchange.kind for view in views).items())),
        "turn_positions": dict(sorted(Counter(view.turn_position for view in views).items())),
    }


def views_by_turn(views: list[ExchangeView]) -> dict[str, list[ExchangeView]]:
    turns: dict[str, list[ExchangeView]] = defaultdict(list)
    for view in views:
        turns[view.turn_id].append(view)
    return dict(turns)


def turn_title(turn_views: list[ExchangeView]) -> str:
    prompt = next((view for view in turn_views if view.exchange.role == "user"), turn_views[0])
    return plain_display_title(prompt.exchange.title or prompt.exchange.text, limit=120)


def turn_register(views: list[ExchangeView]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for turn_id, turn_views in views_by_turn(views).items():
        prompt = next((view for view in turn_views if view.exchange.role == "user"), None)
        answer_count = sum(1 for view in turn_views if view.turn_position == "assistant-answer")
        tool_count = sum(1 for view in turn_views if view.turn_position == "tool-evidence")
        rows.append(
            {
                "turn_id": turn_id,
                "turn_number": turn_views[0].turn_number,
                "session_id": turn_views[0].exchange.session_id,
                "title": turn_title(turn_views),
                "prompt_exchange_id": prompt.exchange.exchange_id if prompt else "",
                "exchange_count": len(turn_views),
                "assistant_answer_count": answer_count,
                "tool_evidence_count": tool_count,
                "first_ordinal": turn_views[0].exchange.ordinal,
                "last_ordinal": turn_views[-1].exchange.ordinal,
            }
        )
    return sorted(rows, key=lambda row: (str(row["session_id"]), int(row["turn_number"])))


def write_turn_pages(root: Path, root_name: str, views: list[ExchangeView]) -> None:
    rows = turn_register(views)
    index_lines = [
        "# Turn Index",
        "",
        f"Up: {internal_link('turns', '', 'navigation', 'Navigation')}",
        "",
        "| Turn | Session | Prompt | Exchanges | Assistant answers | Tool evidence |",
        "| ---: | --- | --- | ---: | ---: | ---: |",
    ]
    turns = views_by_turn(views)
    for row in rows:
        turn_id = str(row["turn_id"])
        turn_views = turns[turn_id]
        session_id = str(row["session_id"])
        session_slug = page_slug("session", f"session-{session_id}")
        turn_link = internal_link("turns", "turns", turn_id, f"Turn {row['turn_number']}")
        session_link = internal_link("turns", "sessions", session_slug, session_id[:8])
        index_lines.append(
            "| {} | {} | {} | {} | {} | {} |".format(
                turn_link,
                session_link,
                markdown_table_cell(str(row["title"])),
                row["exchange_count"],
                row["assistant_answer_count"],
                row["tool_evidence_count"],
            )
        )
        lines = [
            "---",
            f"type: {yaml_scalar('turn')}",
            f"turn_id: {yaml_scalar(turn_id)}",
            f"session_id: {yaml_scalar(session_id)}",
            f"title: {yaml_scalar(str(row['title']))}",
            f"exchange_count: {yaml_scalar(row['exchange_count'])}",
            "---",
            "",
            f"# Turn {row['turn_number']}: {safe_markdown_text(str(row['title']))}",
            "",
            f"Up: {internal_link('turns', 'turns', 'index', 'Turn Index')}",
            "",
            f"Session: {session_link}",
            "",
            "| # | Position | Role / kind | Exchange | Excerpt |",
            "| ---: | --- | --- | --- | --- |",
        ]
        for view in turn_views:
            exchange = view.exchange
            exchange_ref = table_exchange_link("turns", exchange.exchange_id, exchange.title)
            role_kind = f"{exchange.role} / {exchange.kind}"
            position = markdown_table_cell(view.turn_position)
            role_kind_cell = markdown_table_cell(role_kind)
            excerpt = markdown_table_cell(view.excerpt)
            lines.append(
                f"| {exchange.ordinal} | {position} | {role_kind_cell} | "
                f"{exchange_ref} | {excerpt} |"
            )
        write_text(root / "wiki" / "turns" / f"{turn_id}.md", "\n".join(lines))
    write_text(root / "wiki" / "turns" / "index.md", "\n".join(index_lines))


def write_surrogates_page(root: Path, root_name: str, views: list[ExchangeView]) -> None:
    lines = [
        "# Surrogate Catalogue",
        "",
        f"Up: {internal_link(None, '', 'navigation', 'Navigation')}",
        "",
        "Each row is a compact surrogate that links to the full exchange note.",
        "",
        "| # | Exchange | Turn | Position | Phase | Topics | Entities | Excerpt |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for view in views:
        exchange = view.exchange
        topics = ", ".join(TOPIC_LABELS.get(topic, topic) for topic in view.topics)
        entities = ", ".join(view.entities)
        exchange_ref = table_exchange_link(None, exchange.exchange_id, exchange.title)
        turn = table_internal_link(None, "turns", view.turn_id, f"Turn {view.turn_number}")
        position = markdown_table_cell(view.turn_position)
        phase = markdown_table_cell(view.phase_label)
        topic_cell = markdown_table_cell(topics)
        entity_cell = markdown_table_cell(entities)
        excerpt = markdown_table_cell(view.excerpt)
        lines.append(
            f"| {exchange.ordinal} | {exchange_ref} | {turn} | {position} | "
            f"{phase} | {topic_cell} | {entity_cell} | {excerpt} |"
        )
    write_text(root / "wiki" / "surrogates.md", "\n".join(lines))


def write_timeline_page(root: Path, root_name: str, views: list[ExchangeView]) -> None:
    lines = [
        "# Timeline",
        "",
        f"Up: {internal_link(None, '', 'navigation', 'Navigation')}",
        "",
        "| # | Timestamp | Exchange | Turn | Session | Role / kind | Phase |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for view in views:
        exchange = view.exchange
        session_slug = page_slug("session", f"session-{exchange.session_id}")
        exchange_ref = table_exchange_link(None, exchange.exchange_id, exchange.title)
        turn = table_internal_link(None, "turns", view.turn_id, f"Turn {view.turn_number}")
        session = table_internal_link(None, "sessions", session_slug, exchange.session_id[:8])
        role = markdown_table_cell(f"{exchange.role} / {exchange.kind}")
        phase = table_internal_link(None, "phases", view.phase_slug, view.phase_label)
        lines.append(
            f"| {exchange.ordinal} | `{exchange.timestamp}` | {exchange_ref} | "
            f"{turn} | {session} | {role} | {phase} |"
        )
    write_text(root / "wiki" / "timeline.md", "\n".join(lines))


def write_navigation_index(root: Path, root_name: str, views: list[ExchangeView]) -> None:
    topic_counts = Counter(topic for view in views for topic in view.topics).most_common()
    entity_counts = Counter(entity for view in views for entity in view.entities).most_common()
    phase_counts = Counter(view.phase_slug for view in views)
    lines = [
        "# Navigation",
        "",
        "Use this page as the structured entry point for the exchange archive.",
        "",
        "## Core Views",
        "",
        f"- {internal_link(None, '', 'timeline', 'Timeline')}",
        f"- {internal_link(None, '', 'surrogates', 'Surrogate Catalogue')}",
        f"- {internal_link(None, 'turns', 'index', 'Turn Index')}",
        f"- {internal_link(None, '', 'graph', 'Graph Map')}",
        f"- {internal_link(None, 'data', 'facets', 'Facet Register', suffix='.json')}",
        f"- {internal_link(None, 'data', 'graph_edges', 'Graph Edges', suffix='.json')}",
        "",
        "## Phases",
        "",
    ]
    for slug, label, _keywords in [*PHASE_RULES, ("other", "Other", ())]:
        if phase_counts.get(slug, 0):
            phase = internal_link(None, "phases", slug, label)
            lines.append(f"- {phase} ({phase_counts[slug]})")
    lines.extend(["", "## Topics", ""])
    for topic, count in topic_counts:
        topic_link = internal_link(None, "topics", topic, TOPIC_LABELS.get(topic, topic))
        lines.append(f"- {topic_link} ({count})")
    lines.extend(["", "## Entities", ""])
    for entity, count in entity_counts:
        entity_link = internal_link(None, "entities", page_slug("entity", entity), entity)
        lines.append(f"- {entity_link} ({count})")
    write_text(root / "wiki" / "navigation.md", "\n".join(lines))


def commit_link(revision: str, path: str) -> str:
    return f"{REPO_URL}/blob/{revision}/{path}"


def artifact_register(head: str) -> list[dict[str, Any]]:
    release = "v1.0.0"
    artifacts = [
        ("CHANGELOG.md", release, "release notes and post-release fixed item"),
        ("README.md", head, "operator workflow documentation"),
        ("README_cataloguing.md", head, "cataloguing workflow documentation"),
        ("AGENTS.md", head, "repository operating rules"),
        ("pyproject.toml", release, "package version and test configuration"),
        ("scripts/catalogue_following_jesus_semantic.py", release, "semantic catalogue runner"),
        ("scripts/plan_following_jesus_rename.py", release, "rename-plan generator"),
        ("scripts/rename_following_jesus_files.py", release, "rename apply script"),
        ("scripts/validate_following_jesus_rename.py", release, "rename validation script"),
        ("src/disk_catalogue/audio_semantic.py", release, "semantic analysis library"),
        ("src/disk_catalogue/following_jesus_rename.py", release, "rename planning library"),
        ("tests/test_audio_semantic.py", release, "semantic catalogue tests"),
        ("tests/test_following_jesus_rename.py", release, "rename workflow tests"),
        (".github/workflows/release.yml", release, "tag-triggered release workflow"),
        (".github/workflows/ci.yml", head, "post-release CI mypy alignment"),
        ("skills/assistant-postmortem-wiki/SKILL.md", head, "postmortem skill contract"),
    ]
    rows = [
        {
            "path": path,
            "revision": revision,
            "status": "tracked",
            "public_url": commit_link(revision, path),
            "notes": notes,
        }
        for path, revision, notes in artifacts
    ]
    rows.extend(
        [
            {
                "path": "output/recovery_plans/following_jesus_team_ext10/",
                "revision": "",
                "status": "local-only",
                "public_url": "",
                "notes": "generated recovery plans, transcripts, logs, metadata, and evaluations",
            },
            {
                "path": "catalogue.duckdb",
                "revision": "",
                "status": "local-only",
                "public_url": "",
                "notes": "local catalogue database containing scan and audio catalogue tables",
            },
            {
                "path": "[EXTSSD_DATA]/",
                "revision": "",
                "status": "local-only",
                "public_url": "",
                "notes": "external SSD recovered playable audio tree and renamed fileset",
            },
        ]
    )
    return rows


def build_private(conversations: list[Conversation], exchanges: list[Exchange]) -> None:
    ensure_private_ignored()
    clean_generated(PRIVATE_ROOT)
    copy_private_sources(conversations, PRIVATE_ROOT)
    views = build_exchange_views(conversations, exchanges, public=False)
    for view in views:
        filename = f"{view.exchange.exchange_id}.md"
        write_text(
            PRIVATE_ROOT / "wiki" / "exchanges" / filename,
            exchange_markdown(view, "postmortem", public=False),
        )
    write_navigation_pages(PRIVATE_ROOT, "postmortem", conversations, views, public=False)
    write_json(PRIVATE_ROOT / "wiki" / "data" / "sessions.json", session_register(conversations))
    write_json(
        PRIVATE_ROOT / "wiki" / "data" / "exchanges.json",
        exchange_register_from_views(views, False),
    )
    write_text(
        PRIVATE_ROOT / "wiki" / "index.md",
        f"""# Private Assistant Postmortem Archive

Generated: {datetime.now(UTC).isoformat()}

This archive preserves raw Codex session sources and exchange notes for local audit only.
It is intentionally excluded from Git via `/postmortem/`.

- Conversation sources: `sources/conversations/`
- Exchange notes: `wiki/exchanges/`
- Navigation hub: [Navigation](navigation.md)
- Surrogate catalogue: [Surrogate Catalogue](surrogates.md)
- Graph data and registers: `wiki/data/`
""",
    )


def build_public(conversations: list[Conversation], exchanges: list[Exchange], head: str) -> None:
    clean_generated(PUBLIC_ROOT)
    write_text(
        PUBLIC_ROOT / "AGENTS.md",
        """# Public Postmortem Rules

- Do not add raw Codex JSONL transcripts to this tree.
- Redact local filesystem paths, account state, tokens, and raw external source bodies.
- Prefer commit-pinned repository links and machine-readable registers.
- Keep the private archive in `postmortem/`, which is ignored by Git.
""",
    )
    public_exchanges = [item for item in exchanges if item.role in {"user", "assistant"}][:80]
    views = build_exchange_views(conversations, public_exchanges, public=True)
    for view in views:
        filename = f"{view.exchange.exchange_id}.md"
        write_text(
            PUBLIC_ROOT / "wiki" / "exchanges" / filename,
            exchange_markdown(view, "postmortem-public", public=True),
        )
    write_navigation_pages(PUBLIC_ROOT, "postmortem-public", conversations, views, public=True)
    artifacts = artifact_register(head)
    decisions = decision_register()
    write_json(PUBLIC_ROOT / "wiki" / "data" / "sessions.json", public_sessions(conversations))
    write_json(
        PUBLIC_ROOT / "wiki" / "data" / "exchanges.json",
        exchange_register_from_views(views, True),
    )
    write_json(PUBLIC_ROOT / "wiki" / "data" / "artifacts.json", artifacts)
    write_json(PUBLIC_ROOT / "wiki" / "data" / "decisions.json", decisions)
    write_text(PUBLIC_ROOT / "wiki" / "index.md", public_index())
    write_text(
        PUBLIC_ROOT / "wiki" / "conversation-summary.md",
        conversation_summary(conversations),
    )
    write_text(PUBLIC_ROOT / "wiki" / "repository-evidence.md", repository_evidence(artifacts))
    write_text(PUBLIC_ROOT / "wiki" / "decisions.md", decisions_page(decisions))
    write_text(PUBLIC_ROOT / "wiki" / "methodology.md", methodology_page())
    write_text(PUBLIC_ROOT / "wiki" / "postmortem.md", postmortem_page(head))
    lint = publication_lint(PUBLIC_ROOT)
    write_json(PUBLIC_ROOT / "wiki" / "data" / "publication_lint.json", lint)
    if lint["issue_count"]:
        raise RuntimeError(f"Publication lint failed with {lint['issue_count']} issue(s)")


def public_sessions(conversations: list[Conversation]) -> list[dict[str, Any]]:
    rows = []
    for item in session_register(conversations):
        rows.append(
            {
                **item,
                "cwd": "[REPO]" if item["cwd"] else "",
                "source_path": "private-only",
            }
        )
    return rows


def public_index() -> str:
    return """# Disk Catalogue Assistant Postmortem

This public wiki is the redacted companion to the local private archive generated with
`python tools/build_assistant_postmortem.py`.

- [Navigation](navigation.md)
- [Surrogate Catalogue](surrogates.md)
- [Timeline](timeline.md)
- [Graph Map](graph.md)
- [Postmortem](postmortem.md)
- [Conversation Summary](conversation-summary.md)
- [Repository Evidence](repository-evidence.md)
- [Decision Register](decisions.md)
- [Methodology](methodology.md)
- Machine-readable registers: [data/](data/)
"""


def conversation_summary(conversations: list[Conversation]) -> str:
    lines = [
        "# Conversation Summary",
        "",
        "The reviewed work covered the recovery and cataloguing of the Following Jesus audio",
        "set from the disk catalogue repository, ending with the `v1.0.0` release and a",
        "post-release CI/skill cleanup PR.",
        "",
        "| Session | Title | Role | Start | End |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in conversations:
        lines.append(
            "| `{}` | {} | {} | {} | {} |".format(
                item.session_id,
                redact(item.title).replace("|", "\\|"),
                item.role or "main",
                item.started_at,
                item.updated_at,
            )
        )
    lines.extend(
        [
            "",
            "The raw session JSONL files are preserved only in the ignored private archive.",
            "The public exchange notes are excerpts and summaries, not a full transcript dump.",
        ]
    )
    return "\n".join(lines)


def repository_evidence(artifacts: list[dict[str, Any]]) -> str:
    lines = [
        "# Repository Evidence",
        "",
        "| Artifact | Status | Evidence | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for artifact in artifacts:
        link = artifact["public_url"]
        evidence = f"[{artifact['revision']}]({link})" if link else "local-only"
        lines.append(
            "| `{}` | {} | {} | {} |".format(
                artifact["path"],
                artifact["status"],
                evidence,
                artifact["notes"].replace("|", "\\|"),
            )
        )
    return "\n".join(lines)


def decision_register() -> list[dict[str, str]]:
    return [
        {
            "id": "D001",
            "decision": "Use the disk catalogue database as the source of truth.",
            "rationale": "The database already had stable drive/file identifiers and scan history.",
            "outcome": (
                "All recovery, transcript, duplicate, and rename artefacts were tied back "
                "to DuckDB."
            ),
        },
        {
            "id": "D002",
            "decision": "Copy recovered M4A files to an external SSD before semantic processing.",
            "rationale": (
                "The source drive could then be ejected and the long-running process could "
                "continue."
            ),
            "outcome": "Later work proceeded without the Ext-10 source drive attached.",
        },
        {
            "id": "D003",
            "decision": "Keep long-running transcription resumable and checkpointed.",
            "rationale": (
                "The library contained 1,536 files and unattended completion required "
                "status checks."
            ),
            "outcome": "State, logs, verification exports, and evaluation exports were generated.",
        },
        {
            "id": "D004",
            "decision": "Add completeness and duplicate validation before declaring completion.",
            "rationale": (
                "Partial transcripts and folder-level duplication were explicit user concerns."
            ),
            "outcome": (
                "Duration coverage and duplicate-audit outputs became part of final verification."
            ),
        },
        {
            "id": "D005",
            "decision": "Use pyannote locally for diarization experiments.",
            "rationale": (
                "The user wanted local speaker recognition with a small known speaker set."
            ),
            "outcome": (
                "Sample diarization tables and an effectiveness report were created in the "
                "local database."
            ),
        },
        {
            "id": "D006",
            "decision": "Publish `v1.0.0` after merging the semantic catalogue branch to `main`.",
            "rationale": (
                "The project had crossed from scanning utility into full recovery/catalogue "
                "workflow."
            ),
            "outcome": (
                "The GitHub release workflow published wheel and source assets for `v1.0.0`."
            ),
        },
        {
            "id": "D007",
            "decision": (
                "Keep full assistant transcripts private and publish a redacted derivative."
            ),
            "rationale": (
                "Raw sessions contain local paths, account state, and generated operational "
                "details."
            ),
            "outcome": (
                "The full archive is ignored in `postmortem/`; `postmortem-public/` is publishable."
            ),
        },
        {
            "id": "D008",
            "decision": "Treat Markdown rendering compatibility as a publication quality gate.",
            "rationale": (
                "Obsidian and VS Code exposed broken table links, raw HTML folding, flattened "
                "redacted details, and filename-like headings that made the archive hard to use."
            ),
            "outcome": (
                "The generator now emits standard Markdown links, turn pages, escaped public "
                "detail, meaningful headings, and publication lint checks for those regressions."
            ),
        },
    ]


def decisions_page(decisions: list[dict[str, str]]) -> str:
    lines = ["# Decision Register", ""]
    for row in decisions:
        lines.extend(
            [
                f"## {row['id']}: {row['decision']}",
                "",
                f"- Rationale: {row['rationale']}",
                f"- Outcome: {row['outcome']}",
                "",
            ]
        )
    return "\n".join(lines)


def methodology_page() -> str:
    return """# Methodology

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
"""


def postmortem_page(head: str) -> str:
    release_url = f"{REPO_URL}/releases/tag/v1.0.0"
    pr_url = f"{REPO_URL}/pull/1"
    head_link = f"{REPO_URL}/commit/{head}"
    return f"""# Postmortem: Following Jesus Catalogue to v1.0.0

## Executive Summary

The project moved from a general disk catalogue into a complete, reproducible workflow for
recovering, transcribing, semantically cataloguing, validating, and renaming the Following
Jesus audio library. The `v1.0.0` release was published successfully, with the GitHub release
workflow creating both wheel and source assets.

Release: [`v1.0.0`]({release_url})

Current post-release head reviewed for this postmortem: [`{head[:7]}`]({head_link})

## What Happened

The user first asked for a repository review and then narrowed the work to an old Avery
Willis / Progressive Vision Following Jesus audio library. The workflow discovered the
primary iTunes material, copied the recovered files to external SSD storage, extracted
source metadata, sampled and then expanded transcription, experimented with local
speaker diarization, added completeness and duplicate checks, generated a human-readable
rename scheme, and finally published version `1.0.0`.

After the release, CI exposed an alignment issue: the GitHub workflow still ran `mypy .`
while the local lint script used configured package targets. PR [#1]({pr_url}) fixed that
and added the postmortem skill now used to generate this archive.

## Impact

- `1,536` M4A source files were treated as the target Following Jesus corpus.
- The source drive was no longer needed after the copy, reducing operational risk.
- The database became the durable catalogue for embedded metadata, transcripts,
  semantic summaries, verification, duplicate audits, evaluation, and rename planning.
- The public repository now has release artifacts and a reproducible postmortem workflow.

## What Went Well

- The work stayed anchored in the existing DuckDB-backed catalogue rather than creating a
  separate unmanaged inventory.
- The long-running transcription path was made resumable, with status and verification files.
- User concerns about partial transcripts and duplicates were converted into automated
  validation requirements before completion.
- Release publication was verified through GitHub Actions and the release assets were checked.
- The postmortem skill itself was reviewed, adjusted, merged, and then used here.
- Obsidian and VS Code rendering failures were converted into explicit generator behavior,
  skill guidance, and regression tests.

## What Went Wrong

- The first release attempt exposed a CI/local mismatch around `mypy`, even though local
  release checks passed.
- Some generated recovery tooling lived in ignored output space, which is useful locally but
  makes reconstruction dependent on the private archive and database exports.
- Speaker recognition remained experimental: pyannote diarization was useful for samples, but
  the process still needs a stronger reviewed voice-reference library before being treated as
  authoritative metadata.
- Documentation drift existed after release: the README version string still lagged the
  package version until this postmortem pass.
- The first public wiki was not navigable enough: exchange nodes were too isolated, table
  wikilinks split across columns, raw HTML folding showed literal tags, redacted detail was
  flattened into generic code blocks, and opaque filenames were repeated as headings.

## Detection

The key quality signals were explicit user prompts and local verification:

- status checks for the unattended semantic catalogue process
- transcript duration verification to catch early-stopped transcripts
- duplicate-audit exports for exact audio duplicates and repeated album-folder sequences
- `scripts/lint.sh`, `scripts/run_tests.sh`, and schema validation before release
- GitHub Actions release and CI runs after pushing

## Root Causes

- The repository evolved quickly from scanner into recovery pipeline, so local scripts,
  CI, generated outputs, documentation, and release process had to be aligned in a short
  window.
- The project had multiple evidence classes with different publication rules: tracked source,
  ignored generated outputs, local database content, raw assistant transcripts, and external
  SSD media.
- The audio domain needs richer verification than ordinary code tests because success
  depends on full-duration media processing and cataloguing quality, not just executable code.

## Corrective Actions

| Action | Status |
| --- | --- |
| Align CI mypy invocation with local lint config | Done in PR #1 |
| Keep private postmortem archive ignored | Done via `/postmortem/` ignore rule |
| Add rebuildable public/private postmortem generator | Done |
| Add publication lint for local paths, token-like strings, and rendering regressions | Done |
| Replace aliased wikilinks with table-safe Markdown links | Done |
| Add turn pages, surrogate catalogue, graph/facet registers, and structural context | Done |
| Replace raw HTML folding and generic redacted-detail code blocks with portable Markdown | Done |
| Escape public titles and excerpts so placeholders such as `[REPO]` render as text | Done |
| Update README version after `v1.0.0` | Done in this postmortem pass |
| Treat speaker IDs as provisional until reviewed references exist | Open |
| Keep generated recovery outputs documented and exportable from DuckDB | Open |

## Residual Risk

The semantic catalogue is operationally useful, but catalogue quality still depends on
transcription accuracy and final human review of speaker identities, Bible passages, and
storying roles. The postmortem also marks local-only evidence explicitly because the raw
database, generated transcripts, and recovered audio cannot safely be published wholesale.
"""


def publication_lint(root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    forbidden = [
        ("local_user_path", re.compile(r"/Users/crpage")),
        ("local_volume_path", re.compile(r"/Volumes/")),
        *[(name, pattern) for name, pattern, _replacement in SECRET_PATTERNS],
    ]
    forbidden_path_parts = [
        ("local_user_slug", re.compile(r"\busers[-_/]crpage\b", re.IGNORECASE)),
    ]
    render_rules = [
        ("wikilink", re.compile(r"\[\[")),
        ("raw_html_folding", re.compile(r"</?(?:details|summary)\b", re.IGNORECASE)),
        ("text_code_block", re.compile(r"(?m)^```text\s*$")),
    ]
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative_path = str(path.relative_to(root))
        for name, pattern in forbidden_path_parts:
            if pattern.search(relative_path):
                findings.append(
                    {
                        "path": relative_path,
                        "pattern": name,
                    }
                )
        text = path.read_text(encoding="utf-8")
        for name, pattern in forbidden:
            if pattern.search(text):
                findings.append(
                    {
                        "path": relative_path,
                        "pattern": name,
                    }
                )
        for name, pattern in render_rules:
            if pattern.search(text):
                findings.append(
                    {
                        "path": relative_path,
                        "pattern": name,
                    }
                )
        for line_number, line in enumerate(text.splitlines(), start=1):
            if "[[" in line and "|" in line:
                findings.append(
                    {
                        "path": relative_path,
                        "pattern": "table_wikilink",
                        "line": str(line_number),
                    }
                )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "issue_count": len(findings),
        "findings": findings,
    }


def exchange_stats(exchanges: list[Exchange]) -> dict[str, Any]:
    roles = Counter(exchange.role for exchange in exchanges)
    kinds = Counter(exchange.kind for exchange in exchanges)
    return {
        "exchange_count": len(exchanges),
        "roles": dict(sorted(roles.items())),
        "kinds": dict(sorted(kinds.items())),
    }


def build(args: argparse.Namespace) -> None:
    session_ids = args.session_id or DEFAULT_SESSION_IDS
    conversations = load_conversations(session_ids)
    exchanges = extract_exchanges(conversations)
    head = run_git(["rev-parse", "HEAD"])
    build_private(conversations, exchanges)
    build_public(conversations, exchanges, head)
    write_json(
        PUBLIC_ROOT / "wiki" / "data" / "build_summary.json",
        {
            "generated_at": datetime.now(UTC).isoformat(),
            "head": head,
            "sessions": len(conversations),
            **exchange_stats(exchanges),
        },
    )
    print(f"Wrote private archive: {PRIVATE_ROOT}")
    print(f"Wrote public postmortem: {PUBLIC_ROOT}")
    print(f"Sessions: {len(conversations)}")
    print(f"Exchanges: {len(exchanges)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--session-id",
        action="append",
        help="Codex session id to include. Defaults to the known Following Jesus sessions.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    build(parse_args())
