from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

GENERIC_TITLE_RE = re.compile(r"^Track\s+\d+$", re.IGNORECASE)

BIBLE_BOOKS = [
    "Genesis",
    "Exodus",
    "Leviticus",
    "Numbers",
    "Deuteronomy",
    "Joshua",
    "Judges",
    "Ruth",
    "1 Samuel",
    "2 Samuel",
    "Samuel",
    "1 Kings",
    "2 Kings",
    "Kings",
    "1 Chronicles",
    "2 Chronicles",
    "Chronicles",
    "Ezra",
    "Nehemiah",
    "Esther",
    "Job",
    "Psalms",
    "Psalm",
    "Proverbs",
    "Ecclesiastes",
    "Song of Songs",
    "Isaiah",
    "Jeremiah",
    "Lamentations",
    "Ezekiel",
    "Daniel",
    "Hosea",
    "Joel",
    "Amos",
    "Obadiah",
    "Jonah",
    "Micah",
    "Nahum",
    "Habakkuk",
    "Zephaniah",
    "Haggai",
    "Zechariah",
    "Malachi",
    "Matthew",
    "Mark",
    "Luke",
    "John",
    "Acts",
    "Romans",
    "1 Corinthians",
    "2 Corinthians",
    "Corinthians",
    "Galatians",
    "Ephesians",
    "Philippians",
    "Colossians",
    "1 Thessalonians",
    "2 Thessalonians",
    "Thessalonians",
    "1 Timothy",
    "2 Timothy",
    "Timothy",
    "Titus",
    "Philemon",
    "Hebrews",
    "James",
    "1 Peter",
    "2 Peter",
    "Peter",
    "1 John",
    "2 John",
    "3 John",
    "Jude",
    "Revelation",
]

BIBLE_REFERENCE_RE = re.compile(
    rf"\b({'|'.join(re.escape(book) for book in BIBLE_BOOKS)})\s+"
    r"(\d{1,3})(?::(\d{1,3}))?"
    r"(?:\s*[-]\s*(?:(\d{1,3}):)?(\d{1,3}))?\b",
    re.IGNORECASE,
)

SPEAKER_NAME_RE = re.compile(
    r"\b(Avery Willis|Jim Slack|Grant Lovejoy|Marcus Vegh)\b", re.IGNORECASE
)


@dataclass(frozen=True)
class AudioCatalogueRecord:
    recovery_set: str
    file_key: str
    album_folder: str
    file_name: str
    title: str
    destination_path: str
    disc_index: int | None = None
    track_index: int | None = None
    duration_seconds: float | None = None


@dataclass(frozen=True)
class SemanticEntry:
    recovery_set: str
    file_key: str
    album_folder: str
    file_name: str
    embedded_title: str
    semantic_title: str
    track_type: str
    bible_reference: str | None
    bible_book: str | None
    speaker_names: list[str]
    speaker_confidence: str
    storying_role: str
    module_role: str | None
    process_step: str | None
    memory_verse: str | None
    worldview_issue: str | None
    summary_short: str
    summary_long: str
    keywords: list[str]
    transcript_path: str
    srt_path: str | None
    transcript_chars: int
    metadata_confidence: str
    evidence_json: str
    created_at: str
    analysis_backend: str = "heuristic_v1"


@dataclass(frozen=True)
class VerificationResult:
    total_files: int
    catalogued_files: int
    transcript_files: int
    missing_catalogue: list[str]
    missing_transcripts: list[str]
    empty_transcripts: list[str]
    verified_at: str
    short_transcripts: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return (
            self.total_files == self.catalogued_files
            and not self.missing_catalogue
            and not self.missing_transcripts
            and not self.empty_transcripts
            and not self.short_transcripts
        )


@dataclass(frozen=True)
class GoldQuestion:
    question_id: str
    prompt: str
    lookup: dict[str, str]
    expected: dict[str, Any]
    rubric: dict[str, float]


@dataclass(frozen=True)
class GoldQuestionScore:
    question_id: str
    score: float
    max_score: float
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")


def is_generic_title(title: str | None) -> bool:
    if not title:
        return True
    return GENERIC_TITLE_RE.match(title.strip()) is not None


def normalise_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def first_sentence(text: str, max_chars: int = 180) -> str:
    cleaned = normalise_space(text)
    if not cleaned:
        return ""
    match = re.search(r"(?<=[.!?])\s+", cleaned)
    sentence = cleaned[: match.start() if match else max_chars]
    if len(sentence) > max_chars:
        sentence = sentence[: max_chars - 1].rstrip() + "."
    return sentence


def transcript_output_stem(record: AudioCatalogueRecord, output_dir: Path) -> Path:
    album = slugify(record.album_folder) or "unknown_album"
    disc = record.disc_index if record.disc_index is not None else "x"
    track = record.track_index if record.track_index is not None else "x"
    file_stem = slugify(Path(record.file_name).stem) or "audio"
    return output_dir / "transcripts" / album / f"d{disc}_t{track}_{record.file_key}_{file_stem}"


def parse_srt_timestamp(value: str) -> float:
    hours, minutes, seconds = value.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def parse_srt_end_seconds(path: Path) -> float | None:
    if not path.exists():
        return None
    latest_end: float | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if "-->" not in line:
            continue
        _start, end = line.split("-->", 1)
        end_timestamp = end.strip().split()[0]
        try:
            end_seconds = parse_srt_timestamp(end_timestamp)
        except (ValueError, IndexError):
            continue
        latest_end = end_seconds if latest_end is None else max(latest_end, end_seconds)
    return latest_end


def parse_srt_text(path: Path) -> str:
    if not path.exists():
        return ""
    text_parts: list[str] = []
    blocks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8").strip())
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) >= 3 and "-->" in lines[1]:
            text_parts.extend(lines[2:])
    return normalise_space(" ".join(text_parts))


def extract_bible_references(text: str) -> list[str]:
    refs: list[str] = []
    for match in BIBLE_REFERENCE_RE.finditer(text):
        book = " ".join(part.capitalize() for part in match.group(1).split())
        chapter = match.group(2)
        verse = match.group(3)
        end_chapter = match.group(4)
        end_verse = match.group(5)
        ref = f"{book} {chapter}"
        if verse:
            ref += f":{verse}"
        if end_verse:
            ref += "-"
            if end_chapter:
                ref += f"{end_chapter}:"
            ref += end_verse
        if ref not in refs:
            refs.append(ref)
    return refs


def infer_known_story_reference(text: str) -> str | None:
    lower = text.lower()
    if "serpent" in lower and (
        "forbidden fruit" in lower or ("garden" in lower and "fruit" in lower)
    ):
        return "Genesis 3"
    if "feed my sheep" in lower and "peter" in lower:
        return "John 21:1-22"
    if "tabernacle" in lower and (
        "moses" in lower or "glory of the lord filled" in lower
    ):
        return "Exodus 40"
    if "lazarus" in lower and (
        "grain of wheat" in lower or "kernel of wheat" in lower or "single seed" in lower
    ):
        return "John 11:1-12:26"
    if "gerasene" in lower or "gadarene" in lower:
        return "Mark 5 / Luke 8"
    if "jacob" in lower and "bethel" in lower:
        return "Genesis 28"
    return None


def bible_book_from_reference(reference: str | None) -> str | None:
    if not reference:
        return None
    match = re.match(r"([1-3]?\s?[A-Za-z ]+?)\s+\d", reference)
    return match.group(1).strip() if match else None


def extract_speaker_names(text: str) -> list[str]:
    names: list[str] = []
    canonical = {
        "avery willis": "Avery Willis",
        "jim slack": "Jim Slack",
        "grant lovejoy": "Grant Lovejoy",
        "marcus vegh": "Marcus Vegh",
    }
    for match in SPEAKER_NAME_RE.finditer(text):
        name = canonical[match.group(1).lower()]
        if name not in names:
            names.append(name)
    return names


def classify_track(
    record: AudioCatalogueRecord, transcript_text: str
) -> tuple[str, str, str | None]:
    title = record.title.lower()
    album = record.album_folder.lower()
    text = transcript_text.lower()

    if "wake up to orality" in title or "roundtable" in text:
        return (
            "roundtable_training",
            "Foundational training and rationale for orality-based discipleship.",
            "foundational_training",
        )
    if (
        "this is module" in text
        or "welcome to module" in text
        or ("mission with god" in text and "spiritual markers" in text)
        or ("module " in title and "welcome" in title)
    ):
        return (
            "module_overview",
            "Module orientation; explains audience, structure, and intended use.",
            "module_orientation",
        )
    if "ask the right kinds of questions" in text or (
        "questions" in text and "story" in text and "worldview" in text
    ):
        return (
            "training_guidance",
            "Facilitator training; explains story dialogue and discussion practice.",
            "facilitator_training",
        )
    if "memory verse" in text:
        return (
            "bible_story",
            "Bible story narration with explicit memory verse.",
            "memory_verse_story",
        )
    if any(word in text for word in ["jesus", "god", "moses", "peter", "serpent", "lazarus"]):
        return ("bible_story", "Bible story narration.", "story_narration")
    if "following jesus" in album:
        return ("training_guidance", "Training or storying resource segment.", "training_segment")
    return ("unknown", "Unclassified audio segment.", None)


def suggest_semantic_title(record: AudioCatalogueRecord, transcript_text: str) -> str:
    lower = transcript_text.lower()
    if "serpent" in lower and (
        "forbidden fruit" in lower or ("garden" in lower and "fruit" in lower)
    ):
        return "Adam and Eve: disobedience, shame, judgment, and exile"
    if "feed my sheep" in lower and "peter" in lower:
        return "Jesus restores Peter: feed my sheep and follow me"
    if "ask the right kinds of questions" in lower:
        return "How to ask story dialogue questions"
    if "tabernacle" in lower and (
        "moses" in lower or "glory of the lord filled" in lower
    ):
        return "Moses sets up the tabernacle and God's glory fills it"
    if "lazarus" in lower and (
        "grain of wheat" in lower or "kernel of wheat" in lower or "single seed" in lower
    ):
        return "Lazarus, Mary's anointing, triumphal entry, and the grain of wheat"
    if "our mission with god" in lower or "spiritual markers" in lower:
        return "Mission with God: God's big story and spiritual markers"
    if "wake up to orality" in record.title.lower() or "orality and literacy" in lower:
        return "Wake Up to Orality and Literacy: why literate methods fail oral learners"
    if not is_generic_title(record.title):
        return record.title
    sentence = first_sentence(transcript_text, max_chars=100)
    return sentence or record.title or record.file_name


def extract_keywords(text: str, track_type: str, bible_reference: str | None) -> list[str]:
    lower = text.lower()
    candidates = [
        "orality",
        "literacy",
        "primary oral learners",
        "worldview",
        "discipleship",
        "storying",
        "evangelism",
        "memory verse",
        "mission",
        "tabernacle",
        "lazarus",
        "peter",
        "moses",
        "genesis",
        "john",
        "exodus",
    ]
    keywords = [candidate for candidate in candidates if candidate in lower]
    if track_type not in keywords:
        keywords.insert(0, track_type)
    if bible_reference:
        keywords.append(bible_reference)
    return list(dict.fromkeys(keywords))


def metadata_confidence(
    record: AudioCatalogueRecord, transcript_text: str, bible_reference: str | None
) -> str:
    if transcript_text and bible_reference:
        return "high"
    if transcript_text and not is_generic_title(record.title):
        return "medium"
    if transcript_text:
        return "low"
    return "unverified"


def build_semantic_entry(
    record: AudioCatalogueRecord,
    transcript_text: str,
    transcript_path: Path,
    srt_path: Path | None,
    speaker_names: Sequence[str] | None = None,
    analysis_backend: str = "heuristic_v1",
) -> SemanticEntry:
    references = extract_bible_references(transcript_text)
    inferred_reference = infer_known_story_reference(transcript_text)
    bible_reference = inferred_reference or (references[0] if references else None)
    track_type, storying_role, module_role = classify_track(record, transcript_text)
    detected_speakers = list(speaker_names or extract_speaker_names(transcript_text))
    semantic_title = suggest_semantic_title(record, transcript_text)
    summary_short = first_sentence(transcript_text, max_chars=180)
    summary_long = first_sentence(transcript_text, max_chars=600)
    speaker_confidence = "high" if speaker_names else ("medium" if detected_speakers else "unknown")
    memory_verse = next(
        (ref for ref in references if "memory verse" in transcript_text.lower()), None
    )
    worldview_issue = "worldview discussion" if "worldview" in transcript_text.lower() else None
    evidence = {
        "detected_references": references,
        "inferred_reference": inferred_reference,
        "first_300_chars": normalise_space(transcript_text)[:300],
    }
    return SemanticEntry(
        recovery_set=record.recovery_set,
        file_key=record.file_key,
        album_folder=record.album_folder,
        file_name=record.file_name,
        embedded_title=record.title,
        semantic_title=semantic_title,
        track_type=track_type,
        bible_reference=bible_reference,
        bible_book=bible_book_from_reference(bible_reference),
        speaker_names=detected_speakers,
        speaker_confidence=speaker_confidence,
        storying_role=storying_role,
        module_role=module_role,
        process_step=None,
        memory_verse=memory_verse,
        worldview_issue=worldview_issue,
        summary_short=summary_short,
        summary_long=summary_long,
        keywords=extract_keywords(transcript_text, track_type, bible_reference),
        transcript_path=str(transcript_path),
        srt_path=str(srt_path) if srt_path else None,
        transcript_chars=len(transcript_text),
        metadata_confidence=metadata_confidence(record, transcript_text, bible_reference),
        evidence_json=json.dumps(evidence, sort_keys=True),
        created_at=utc_now_iso(),
        analysis_backend=analysis_backend,
    )


def semantic_entry_row(entry: SemanticEntry) -> dict[str, Any]:
    row = asdict(entry)
    row["speaker_names"] = json.dumps(entry.speaker_names)
    row["keywords"] = json.dumps(entry.keywords)
    return row


def semantic_entry_from_mapping(row: Mapping[str, Any]) -> SemanticEntry:
    speaker_names = row.get("speaker_names", [])
    keywords = row.get("keywords", [])
    if isinstance(speaker_names, str):
        speaker_names = json.loads(speaker_names)
    if isinstance(keywords, str):
        keywords = json.loads(keywords)
    return SemanticEntry(
        recovery_set=str(row["recovery_set"]),
        file_key=str(row["file_key"]),
        album_folder=str(row["album_folder"]),
        file_name=str(row["file_name"]),
        embedded_title=str(row["embedded_title"]),
        semantic_title=str(row["semantic_title"]),
        track_type=str(row["track_type"]),
        bible_reference=row.get("bible_reference"),
        bible_book=row.get("bible_book"),
        speaker_names=list(speaker_names),
        speaker_confidence=str(row["speaker_confidence"]),
        storying_role=str(row["storying_role"]),
        module_role=row.get("module_role"),
        process_step=row.get("process_step"),
        memory_verse=row.get("memory_verse"),
        worldview_issue=row.get("worldview_issue"),
        summary_short=str(row["summary_short"]),
        summary_long=str(row["summary_long"]),
        keywords=list(keywords),
        transcript_path=str(row["transcript_path"]),
        srt_path=row.get("srt_path"),
        transcript_chars=int(row["transcript_chars"]),
        metadata_confidence=str(row["metadata_confidence"]),
        evidence_json=str(row["evidence_json"]),
        created_at=str(row["created_at"]),
        analysis_backend=str(row.get("analysis_backend", "heuristic_v1")),
    )


def verify_catalogue_outputs(
    records: Sequence[AudioCatalogueRecord],
    entries: Mapping[str, SemanticEntry],
    transcript_paths: Mapping[str, Path],
    srt_paths: Mapping[str, Path] | None = None,
    duration_tolerance_seconds: float = 10.0,
) -> VerificationResult:
    missing_catalogue: list[str] = []
    missing_transcripts: list[str] = []
    empty_transcripts: list[str] = []
    short_transcripts: list[str] = []
    transcript_count = 0

    for record in records:
        if record.file_key not in entries:
            missing_catalogue.append(record.file_key)
        transcript_path = transcript_paths.get(record.file_key)
        if transcript_path is None or not transcript_path.exists():
            missing_transcripts.append(record.file_key)
            continue
        transcript_count += 1
        if transcript_path.stat().st_size == 0:
            empty_transcripts.append(record.file_key)
        if srt_paths is not None and record.duration_seconds is not None:
            srt_path = srt_paths.get(record.file_key)
            srt_end_seconds = parse_srt_end_seconds(srt_path) if srt_path else None
            if srt_end_seconds is None:
                short_transcripts.append(record.file_key)
            elif srt_end_seconds + duration_tolerance_seconds < record.duration_seconds:
                short_transcripts.append(record.file_key)

    return VerificationResult(
        total_files=len(records),
        catalogued_files=len(entries),
        transcript_files=transcript_count,
        missing_catalogue=missing_catalogue,
        missing_transcripts=missing_transcripts,
        empty_transcripts=empty_transcripts,
        verified_at=utc_now_iso(),
        short_transcripts=short_transcripts,
    )


def load_gold_questions(path: Path) -> list[GoldQuestion]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        GoldQuestion(
            question_id=str(item["question_id"]),
            prompt=str(item["prompt"]),
            lookup=dict(item["lookup"]),
            expected=dict(item["expected"]),
            rubric={str(key): float(value) for key, value in item["rubric"].items()},
        )
        for item in raw["questions"]
    ]


def entry_matches_lookup(entry: SemanticEntry, lookup: Mapping[str, str]) -> bool:
    for key, expected in lookup.items():
        actual = getattr(entry, key)
        if str(actual) != str(expected):
            return False
    return True


def value_matches(actual: Any, expected: Any) -> bool:
    if isinstance(actual, list):
        if isinstance(expected, list):
            return all(item in actual for item in expected)
        return expected in actual
    if isinstance(expected, list):
        return actual in expected
    return str(actual or "").casefold() == str(expected or "").casefold()


def score_gold_question(
    question: GoldQuestion, entries: Iterable[SemanticEntry], pass_threshold: float = 0.8
) -> GoldQuestionScore:
    matching = [entry for entry in entries if entry_matches_lookup(entry, question.lookup)]
    details: dict[str, Any] = {"lookup_matches": len(matching), "fields": {}}
    max_score = sum(question.rubric.values())
    if not matching:
        return GoldQuestionScore(
            question_id=question.question_id,
            score=0.0,
            max_score=max_score,
            passed=False,
            details=details,
        )

    entry = matching[0]
    score = 0.0
    for field_name, weight in question.rubric.items():
        actual = getattr(entry, field_name)
        expected = question.expected.get(field_name)
        matched = value_matches(actual, expected)
        if matched:
            score += weight
        details["fields"][field_name] = {
            "actual": actual,
            "expected": expected,
            "matched": matched,
            "weight": weight,
        }

    return GoldQuestionScore(
        question_id=question.question_id,
        score=round(score, 6),
        max_score=max_score,
        passed=(score / max_score if max_score else 0.0) >= pass_threshold,
        details=details,
    )


def score_gold_questions(
    questions: Sequence[GoldQuestion], entries: Sequence[SemanticEntry]
) -> list[GoldQuestionScore]:
    return [score_gold_question(question, entries) for question in questions]
