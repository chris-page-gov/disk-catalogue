from __future__ import annotations

import json
from pathlib import Path

from disk_catalogue.audio_semantic import (
    AudioCatalogueRecord,
    GoldQuestion,
    build_semantic_entry,
    extract_bible_references,
    extract_keywords,
    extract_speaker_names,
    first_sentence,
    infer_known_story_reference,
    is_generic_title,
    load_gold_questions,
    normalise_space,
    parse_srt_end_seconds,
    parse_srt_text,
    score_gold_question,
    score_gold_questions,
    semantic_entry_from_mapping,
    semantic_entry_row,
    slugify,
    transcript_output_stem,
    value_matches,
    verify_catalogue_outputs,
)


def make_record(title: str = "Track 08", file_key: str = "k1") -> AudioCatalogueRecord:
    return AudioCatalogueRecord(
        recovery_set="following_jesus_team_ext10_primary_itunes",
        file_key=file_key,
        album_folder="Following Jesus 2--Living in the Family",
        file_name="1-08 Track 08.m4a",
        title=title,
        destination_path="/Volumes/ExtSSD-Data/audio.m4a",
        disc_index=1,
        track_index=8,
        duration_seconds=249.0,
    )


def test_basic_text_helpers_and_output_stem(tmp_path: Path) -> None:
    record = make_record()

    assert (
        slugify("Following Jesus 2--Living in the Family")
        == "Following_Jesus_2_Living_in_the_Family"
    )
    assert is_generic_title("Track 08")
    assert not is_generic_title("Avery's Welcome")
    assert normalise_space("  a\n b\t c  ") == "a b c"
    assert first_sentence("First sentence. Second sentence.") == "First sentence."

    stem = transcript_output_stem(record, tmp_path)
    assert stem.parent.name == "Following_Jesus_2_Living_in_the_Family"
    assert stem.name == "d1_t8_k1_1_08_Track_08"


def test_parse_srt_text_extracts_only_caption_lines(tmp_path: Path) -> None:
    srt = tmp_path / "sample.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHello there.\n\n"
        "2\n00:00:01,000 --> 00:00:02,000\nSecond line.\n",
        encoding="utf-8",
    )

    assert parse_srt_text(srt) == "Hello there. Second line."
    assert parse_srt_text(tmp_path / "missing.srt") == ""
    assert parse_srt_end_seconds(srt) == 2.0
    assert parse_srt_end_seconds(tmp_path / "missing.srt") is None


def test_reference_and_speaker_extraction() -> None:
    text = (
        "Avery Willis, Jim Slack and Grant Lovejoy discuss John 12:24, "
        "Genesis 3, and Mark 5:1-20."
    )

    assert extract_bible_references(text) == ["John 12:24", "Genesis 3", "Mark 5:1-20"]
    assert extract_speaker_names(text) == ["Avery Willis", "Jim Slack", "Grant Lovejoy"]
    assert value_matches(["Avery Willis", "Jim Slack"], ["Avery Willis"])
    assert value_matches("Genesis 3", "genesis 3")


def test_known_story_inference_patterns() -> None:
    assert infer_known_story_reference("The serpent offered forbidden fruit.") == "Genesis 3"
    assert infer_known_story_reference("Peter, do you love me? Feed my sheep.") == "John 21:1-22"
    assert (
        infer_known_story_reference(
            "The tabernacle was finished and the glory of the Lord filled it."
        )
        == "Exodus 40"
    )
    assert (
        infer_known_story_reference("Lazarus and a grain of wheat are mentioned.")
        == "John 11:1-12:26"
    )
    assert (
        infer_known_story_reference("The Gerasene demoniac story is our example.")
        == "Mark 5 / Luke 8"
    )
    assert infer_known_story_reference("Jacob was at Bethel.") == "Genesis 28"
    assert infer_known_story_reference("No known pattern.") is None


def test_build_semantic_entry_for_bible_story() -> None:
    transcript = (
        "Well, the serpent was more crafty than any of the wild animals. "
        "The woman ate the forbidden fruit and Adam ate it too. "
        "God sent them from the garden."
    )

    entry = build_semantic_entry(
        make_record(),
        transcript,
        Path("transcript.txt"),
        Path("transcript.srt"),
    )

    assert entry.semantic_title == "Adam and Eve: disobedience, shame, judgment, and exile"
    assert entry.track_type == "bible_story"
    assert entry.bible_reference == "Genesis 3"
    assert entry.bible_book == "Genesis"
    assert entry.metadata_confidence == "high"
    assert "Genesis 3" in entry.keywords


def test_build_semantic_entry_for_overview_training_roundtable_and_named_speakers() -> None:
    welcome = build_semantic_entry(
        make_record(title="Avery's Welcome"),
        "This is Module 2 in the following Jesus series.",
        Path("welcome.txt"),
        None,
        speaker_names=["Avery Willis"],
    )
    assert welcome.track_type == "module_overview"
    assert welcome.module_role == "module_orientation"
    assert welcome.speaker_confidence == "high"

    training = build_semantic_entry(
        make_record(),
        "One difficult thing for storyers is how to ask the right kinds of questions "
        "about worldview.",
        Path("training.txt"),
        None,
    )
    assert training.semantic_title == "How to ask story dialogue questions"
    assert training.track_type == "training_guidance"
    assert training.worldview_issue == "worldview discussion"

    roundtable = build_semantic_entry(
        make_record(title="Wake Up To Orality And Literacy"),
        "Avery Willis and Jim Slack discuss orality and literacy in a roundtable.",
        Path("roundtable.txt"),
        None,
    )
    assert roundtable.track_type == "roundtable_training"
    assert roundtable.speaker_names == ["Avery Willis", "Jim Slack"]


def test_build_semantic_entry_for_other_known_story_titles() -> None:
    cases = [
        (
            "Peter saw Jesus by the sea. Jesus said, feed my sheep.",
            "Jesus restores Peter: feed my sheep and follow me",
            "John 21:1-22",
        ),
        (
            "Moses set up the tabernacle and the glory of the Lord filled it.",
            "Moses sets up the tabernacle and God's glory fills it",
            "Exodus 40",
        ),
        (
            "Lazarus was raised, and Jesus said a grain of wheat must die.",
            "Lazarus, Mary's anointing, triumphal entry, and the grain of wheat",
            "John 11:1-12:26",
        ),
        (
            "Our Mission With God names eight spiritual markers.",
            "Mission with God: God's big story and spiritual markers",
            None,
        ),
    ]

    for transcript, title, reference in cases:
        entry = build_semantic_entry(make_record(), transcript, Path("x.txt"), None)
        assert entry.semantic_title == title
        assert entry.bible_reference == reference


def test_semantic_entry_row_round_trips_json_fields() -> None:
    entry = build_semantic_entry(
        make_record(title="John Story"),
        "John 12:24 is the memory verse.",
        Path("john.txt"),
        None,
    )

    row = semantic_entry_row(entry)
    restored = semantic_entry_from_mapping(row)

    assert json.loads(row["speaker_names"]) == []
    assert restored == entry
    assert restored.memory_verse == "John 12:24"


def test_verify_catalogue_outputs_reports_missing_and_empty(tmp_path: Path) -> None:
    record_one = make_record(file_key="one")
    record_two = make_record(file_key="two")
    empty = tmp_path / "empty.txt"
    empty.write_text("", encoding="utf-8")
    present = tmp_path / "present.txt"
    present.write_text("text", encoding="utf-8")

    entry = build_semantic_entry(record_one, "text", present, None)
    result = verify_catalogue_outputs(
        [record_one, record_two],
        {"one": entry},
        {"one": present, "two": empty},
    )

    assert not result.complete
    assert result.catalogued_files == 1
    assert result.transcript_files == 2
    assert result.missing_catalogue == ["two"]
    assert result.empty_transcripts == ["two"]


def test_verify_catalogue_outputs_flags_short_transcripts(tmp_path: Path) -> None:
    record_full = make_record(file_key="full")
    record_short = make_record(file_key="short")
    full_txt = tmp_path / "full.txt"
    full_txt.write_text("text", encoding="utf-8")
    full_srt = tmp_path / "full.srt"
    full_srt.write_text(
        "1\n00:00:00,000 --> 00:04:05,000\nText.\n",
        encoding="utf-8",
    )
    short_txt = tmp_path / "short.txt"
    short_txt.write_text("text", encoding="utf-8")
    short_srt = tmp_path / "short.srt"
    short_srt.write_text(
        "1\n00:00:00,000 --> 00:01:00,000\nText.\n",
        encoding="utf-8",
    )

    result = verify_catalogue_outputs(
        [record_full, record_short],
        {
            "full": build_semantic_entry(record_full, "text", full_txt, full_srt),
            "short": build_semantic_entry(record_short, "text", short_txt, short_srt),
        },
        {"full": full_txt, "short": short_txt},
        {"full": full_srt, "short": short_srt},
        duration_tolerance_seconds=5.0,
    )

    assert not result.complete
    assert result.short_transcripts == ["short"]


def test_gold_question_loading_and_scoring(tmp_path: Path) -> None:
    entry = build_semantic_entry(
        make_record(),
        "The serpent and forbidden fruit story.",
        Path("genesis.txt"),
        None,
    )
    gold_path = tmp_path / "gold.json"
    gold_path.write_text(
        json.dumps(
            {
                "questions": [
                    {
                        "question_id": "genesis",
                        "prompt": "Which passage is this?",
                        "lookup": {"file_key": "k1"},
                        "expected": {
                            "bible_reference": "Genesis 3",
                            "track_type": "bible_story",
                            "keywords": ["Genesis 3"],
                        },
                        "rubric": {
                            "bible_reference": 0.5,
                            "track_type": 0.25,
                            "keywords": 0.25,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    questions = load_gold_questions(gold_path)
    score = score_gold_question(questions[0], [entry])
    missing = score_gold_question(
        GoldQuestion(
            question_id="missing",
            prompt="Missing",
            lookup={"file_key": "missing"},
            expected={"track_type": "bible_story"},
            rubric={"track_type": 1.0},
        ),
        [entry],
    )

    assert score.passed
    assert score.score == 1.0
    assert score_gold_questions(questions, [entry]) == [score]
    assert not missing.passed
    assert missing.score == 0.0


def test_extract_keywords_deduplicates_and_includes_reference() -> None:
    keywords = extract_keywords(
        "Storying and discipleship with storying in John.", "bible_story", "John 1"
    )

    assert keywords[0] == "bible_story"
    assert keywords.count("storying") == 1
    assert keywords[-1] == "John 1"
