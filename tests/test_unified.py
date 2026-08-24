import os
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from backend.services.parser import parse_transcript, parse_transcript_file
from backend.services.regex_extractor import extract_action_items_regex, generate_4section_recap
from backend.services.exporter import Exporter


def test_transcript_parsing():
    content = "Alice: Let's discuss the Q3 goals.\nBob: I will draft the specification by Friday."
    transcript = parse_transcript(content, source_format="text")
    assert len(transcript.segments) == 2
    assert transcript.speakers() == ["Alice", "Bob"]


def test_regex_action_item_extraction():
    content = "Bob: I'll write the documentation by tomorrow."
    transcript = parse_transcript(content, source_format="text")
    items = extract_action_items_regex(transcript)
    assert len(items) == 1
    assert items[0].owner == "Bob"
    assert "write the documentation" in items[0].description
    assert items[0].due == "tomorrow"


def test_4section_recap():
    content = "Alice: We agreed to launch next month.\nBob: I'll draft the specification by Friday."
    transcript = parse_transcript(content, source_format="text")
    recap = generate_4section_recap(transcript)
    assert len(recap.action_items) == 1
    assert len(recap.decisions) == 1
    assert "agreed" in recap.decisions[0].lower()


def test_export_engine(tmp_path):
    exporter = Exporter(output_dir=tmp_path)
    file_path = exporter.export_data(
        title="Test Sync",
        summary="Executive summary test.",
        action_items=[{"description": "Draft spec", "assignee": "Bob", "priority": "high"}],
        fmt="markdown",
    )
    assert file_path.exists()
    content = file_path.read_text(encoding="utf-8")
    assert "Test Sync" in content
    assert "Bob" in content
