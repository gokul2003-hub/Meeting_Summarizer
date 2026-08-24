"""Unified Multi-Format Transcript Parser.

Parses meeting transcripts from four common formats:
  - WebVTT (.vtt): Zoom, Microsoft Teams, Google Meet recordings
  - SubRip (.srt): Subtitles and desktop transcription software
  - Plain Text (.txt): Speaker-attributed minutes ("Name: sentence")
  - Otter JSON (.json): Otter.ai, Fireflies.ai, Grain exports

Returns unified Transcript objects with speaker-attributed Segment items.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Segment:
    """One utterance in the transcript."""
    speaker: str  # may be empty if format doesn't track speakers
    text: str
    start_seconds: float = 0.0
    end_seconds: float = 0.0


@dataclass
class Transcript:
    """Full transcript with speaker-attributed segments."""
    segments: list[Segment]
    source_format: str  # "text" | "vtt" | "srt" | "otter_json"
    meeting_title: str = ""
    meeting_date: str = ""

    def speakers(self) -> list[str]:
        seen: list[str] = []
        for s in self.segments:
            if s.speaker and s.speaker not in seen:
                seen.append(s.speaker)
        return seen

    def duration_seconds(self) -> float:
        if not self.segments:
            return 0.0
        return max(s.end_seconds for s in self.segments)

    def full_text(self) -> str:
        """Speaker-attributed full text formatted as 'Speaker: text' lines."""
        return "\n".join(
            f"{s.speaker}: {s.text}" if s.speaker else s.text
            for s in self.segments
        )


def detect_format(content: str) -> str:
    """Detect transcript format from header content."""
    head = content[:500].strip()
    if head.startswith("WEBVTT"):
        return "vtt"
    if head.startswith("{") or head.startswith("["):
        try:
            data = json.loads(content)
            if isinstance(data, dict) and ("segments" in data or "transcript" in data):
                return "otter_json"
        except json.JSONDecodeError:
            pass
    if re.match(r"^\d+\s*\n\d{2}:\d{2}:\d{2}", head):
        return "srt"
    return "text"


def parse_transcript(
    content: str,
    source_format: str | None = None,
    meeting_title: str = "",
    meeting_date: str = "",
) -> Transcript:
    """Parse transcript content string into a Transcript object."""
    fmt = source_format or detect_format(content)
    if fmt == "vtt":
        segments = _parse_vtt(content)
    elif fmt == "srt":
        segments = _parse_srt(content)
    elif fmt == "otter_json":
        segments = _parse_otter_json(content)
    else:
        segments = _parse_text(content)

    return Transcript(
        segments=segments,
        source_format=fmt,
        meeting_title=meeting_title,
        meeting_date=meeting_date,
    )


def parse_transcript_file(
    path: Path | str,
    source_format: str | None = None,
    meeting_title: str = "",
    meeting_date: str = "",
) -> Transcript:
    """Parse a transcript file on disk."""
    p = Path(path)
    return parse_transcript(
        p.read_text(encoding="utf-8", errors="ignore"),
        source_format=source_format,
        meeting_title=meeting_title or p.stem,
        meeting_date=meeting_date,
    )


# ── Per-Format Parsers ───────────────────────────────────────────────

_SPEAKER_LINE = re.compile(r"^([A-Z][A-Za-z .'\-]{1,40}):\s*(.+)$")


def _parse_text(content: str) -> list[Segment]:
    segments: list[Segment] = []
    current_speaker = ""
    current_buffer: list[str] = []

    def flush():
        if current_buffer:
            segments.append(
                Segment(
                    speaker=current_speaker,
                    text=" ".join(current_buffer).strip(),
                )
            )
            current_buffer.clear()

    for line in content.splitlines():
        line = line.strip()
        if not line:
            flush()
            continue
        m = _SPEAKER_LINE.match(line)
        if m:
            flush()
            current_speaker = m.group(1).strip()
            current_buffer = [m.group(2).strip()]
        else:
            current_buffer.append(line)
    flush()
    return segments


_VTT_TIMESTAMP = re.compile(
    r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})"
)
_VTT_SPEAKER_TAG = re.compile(r"<v\s+([^>]+)>(.*)", re.DOTALL)


def _parse_vtt(content: str) -> list[Segment]:
    segments: list[Segment] = []
    blocks = re.split(r"\n\s*\n", content)
    for block in blocks:
        if block.startswith("WEBVTT") or not block.strip():
            continue
        lines = block.strip().splitlines()
        if not lines:
            continue
        ts_line = next((l for l in lines if _VTT_TIMESTAMP.search(l)), None)
        if not ts_line:
            continue
        m = _VTT_TIMESTAMP.search(ts_line)
        start = _vtt_to_seconds(m.group(1))
        end = _vtt_to_seconds(m.group(2))
        ts_idx = lines.index(ts_line)
        cue_text = " ".join(lines[ts_idx + 1:]).strip()
        speaker_match = _VTT_SPEAKER_TAG.match(cue_text)
        if speaker_match:
            speaker = speaker_match.group(1).strip()
            text = speaker_match.group(2).strip()
        else:
            speaker_match_line = _SPEAKER_LINE.match(cue_text)
            if speaker_match_line:
                speaker = speaker_match_line.group(1).strip()
                text = speaker_match_line.group(2).strip()
            else:
                speaker = ""
                text = cue_text
        segments.append(
            Segment(speaker=speaker, text=text, start_seconds=start, end_seconds=end)
        )
    return segments


def _vtt_to_seconds(timestamp: str) -> float:
    parts = timestamp.split(":")
    if len(parts) == 3:
        h, m, rest = parts
    else:
        h = "0"
        m, rest = parts
    s, ms = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


_SRT_TIMESTAMP = re.compile(
    r"(\d{2}:\d{2}:\d{2}),(\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}),(\d{3})"
)


def _parse_srt(content: str) -> list[Segment]:
    segments: list[Segment] = []
    blocks = re.split(r"\n\s*\n", content)
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        m = _SRT_TIMESTAMP.search(lines[1] if len(lines) > 1 else "")
        if not m:
            continue
        start = _srt_to_seconds(m.group(1), m.group(2))
        end = _srt_to_seconds(m.group(3), m.group(4))
        text_lines = lines[2:]
        full_text = " ".join(text_lines).strip()
        speaker_match = _SPEAKER_LINE.match(full_text)
        if speaker_match:
            speaker = speaker_match.group(1).strip()
            text = speaker_match.group(2).strip()
        else:
            speaker = ""
            text = full_text
        segments.append(
            Segment(speaker=speaker, text=text, start_seconds=start, end_seconds=end)
        )
    return segments


def _srt_to_seconds(hms: str, ms: str) -> float:
    h, m, s = hms.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def _parse_otter_json(content: str) -> list[Segment]:
    data = json.loads(content)
    raw_segments = data.get("segments") or data.get("transcript") or []
    segments: list[Segment] = []
    for s in raw_segments:
        segments.append(
            Segment(
                speaker=s.get("speaker") or s.get("speaker_name") or "",
                text=(s.get("text") or "").strip(),
                start_seconds=float(s.get("start") or s.get("start_time") or 0),
                end_seconds=float(s.get("end") or s.get("end_time") or 0),
            )
        )
    return segments
