"""Action item extractor using regex patterns & first-person speaker mapping.

Pulls task descriptions, owners, due dates, decisions, and open questions from transcripts.
Provides a deterministic fallback engine when LLMs are offline or for fast processing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from .parser import Transcript, Segment


@dataclass
class ExtractedActionItem:
    """One extracted action item with owner, description, and optional due date."""
    owner: str
    description: str
    due: str = ""
    priority: str = "medium"
    evidence: str = ""


@dataclass
class FourSectionRecap:
    """Four-section meeting recap structure."""
    summary: str
    decisions: list[str]
    action_items: list[ExtractedActionItem]
    open_questions: list[str]

    def to_markdown(self) -> str:
        lines = [
            "# Meeting recap",
            "",
            "## Summary",
            "",
            self.summary,
            "",
            "## Decisions",
            "",
        ]
        for d in self.decisions:
            lines.append(f"- {d}")
        if not self.decisions:
            lines.append("- No explicit decisions recorded.")
        lines.extend(["", "## Action items", ""])
        for a in self.action_items:
            due_str = f" (due {a.due})" if a.due else ""
            lines.append(f"- [{a.owner}] {a.description}{due_str}")
        if not self.action_items:
            lines.append("- No action items recorded.")
        lines.extend(["", "## Open questions", ""])
        for q in self.open_questions:
            lines.append(f"- {q}")
        if not self.open_questions:
            lines.append("- No open questions recorded.")
        return "\n".join(lines)


# ── Action Item Regex Patterns ────────────────────────────────────────

_FIRST_PERSON_PATTERNS = [
    re.compile(r"\bI\s+will\s+([a-z][^.!?]*)", re.M),
    re.compile(r"\bI'?ll\s+([a-z][^.!?]*)", re.M),
    re.compile(r"\bI'?m\s+going\s+to\s+([a-z][^.!?]*)", re.M),
]

_THIRD_PERSON_PATTERNS = [
    re.compile(r"\b([A-Z][a-zA-Z\-']+)\s+will\s+([a-z][^.!?]*)", re.M),
    re.compile(r"\b([A-Z][a-zA-Z\-']+)\s+is\s+going\s+to\s+([a-z][^.!?]*)", re.M),
]

_REQUEST_PATTERNS = [
    re.compile(r"([A-Z][a-zA-Z\-']+),\s*(?:can\s+you|could\s+you|please|you'?ll)\s+([a-z][^.!?]*)", re.M),
]

_ASSIGNMENT_VERBS = {
    "send", "draft", "write", "review", "follow up", "schedule", "set up",
    "investigate", "look into", "ship", "deploy", "file", "create", "build",
    "test", "share", "publish", "post", "email", "ping", "loop in", "introduce",
    "prepare", "circulate", "submit", "deliver", "finish", "complete",
    "handle", "own", "reach out", "check", "confirm", "move", "rotate",
    "audit", "book", "put together", "write up",
}

_DUE_PATTERNS = [
    re.compile(
        r"by\s+(end of\s+\w+(?:\s+\w+)?|\w+day|next\s+\w+|tomorrow|today|"
        r"\d{4}-\d{2}-\d{2}|"
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d+)",
        re.I,
    ),
    re.compile(r"by\s+(EOD|EOW|EOM|COB)\b", re.I),
    re.compile(r"before\s+(end of\s+\w+|\w+day|next\s+\w+|tomorrow)", re.I),
    re.compile(r"\b(tomorrow|today|this\s+\w+day|next\s+\w+day)\s*[.!?]?\s*$", re.I),
]

_NOT_NAMES = {
    "And", "But", "Or", "Now", "Then", "So", "If", "Because",
    "Let", "Let's", "We", "You", "They", "It", "This", "That",
    "Here", "There", "When", "Where", "Why", "How",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
    "Saturday", "Sunday", "January", "February", "March",
}


def extract_action_items_regex(transcript: Transcript) -> list[ExtractedActionItem]:
    """Extract action items from transcript using regex and first-person attribution."""
    items: list[ExtractedActionItem] = []
    seen_descriptions: set[str] = set()

    for seg in transcript.segments:
        for sentence in _split_sentences(seg.text):
            for item in _extract_from_sentence(sentence, current_speaker=seg.speaker):
                key = item.description.lower().strip()
                if key in seen_descriptions:
                    continue
                seen_descriptions.add(key)
                items.append(item)
    return items


def generate_4section_recap(transcript: Transcript) -> FourSectionRecap:
    """Generate a deterministic 4-section recap (Summary, Decisions, Actions, Open Questions)."""
    # 1. Action Items
    actions = extract_action_items_regex(transcript)

    # 2. Decisions (sentences containing 'agreed', 'decided', 'approved')
    decisions: list[str] = []
    decision_keywords = ["agreed", "decided", "approved", "confirmed", "settled"]

    # 3. Open Questions (sentences ending in ? or containing 'what should we')
    questions: list[str] = []

    substantive_sentences: list[str] = []

    for seg in transcript.segments:
        for sent in _split_sentences(seg.text):
            lower = sent.lower()
            if len(sent.split()) > 4:
                substantive_sentences.append(sent)

            if any(kw in lower for kw in decision_keywords):
                if sent not in decisions:
                    decisions.append(sent)

            if sent.endswith("?") or "what should" in lower or "how do we" in lower:
                if sent not in questions:
                    questions.append(sent)

    # Summary: first 2 substantive sentences
    summary_text = " ".join(substantive_sentences[:2]) if substantive_sentences else "Meeting recorded."

    return FourSectionRecap(
        summary=summary_text,
        decisions=decisions,
        action_items=actions,
        open_questions=questions,
    )


# ── Helpers ─────────────────────────────────────────────────────────

def _extract_from_sentence(sentence: str, current_speaker: str = "") -> list[ExtractedActionItem]:
    found: list[ExtractedActionItem] = []
    consumed_spans: list[tuple[int, int]] = []

    if current_speaker:
        for pattern in _FIRST_PERSON_PATTERNS:
            for m in pattern.finditer(sentence):
                description = _clean_description(m.group(1))
                if not _has_assignment_verb(description):
                    continue
                if _overlaps(m.span(), consumed_spans):
                    continue
                consumed_spans.append(m.span())
                due = _extract_due(sentence)
                priority = "high" if "urgent" in sentence.lower() or "asap" in sentence.lower() else "medium"
                found.append(
                    ExtractedActionItem(
                        owner=current_speaker,
                        description=description,
                        due=due,
                        priority=priority,
                        evidence=sentence.strip(),
                    )
                )

    for pattern in _THIRD_PERSON_PATTERNS + _REQUEST_PATTERNS:
        for m in pattern.finditer(sentence):
            owner = m.group(1).strip()
            if owner in _NOT_NAMES:
                continue
            description = _clean_description(m.group(2))
            if not _has_assignment_verb(description):
                continue
            if _overlaps(m.span(), consumed_spans):
                continue
            consumed_spans.append(m.span())
            due = _extract_due(sentence)
            priority = "high" if "urgent" in sentence.lower() or "asap" in sentence.lower() else "medium"
            found.append(
                ExtractedActionItem(
                    owner=owner,
                    description=description,
                    due=due,
                    priority=priority,
                    evidence=sentence.strip(),
                )
            )
    return found


def _overlaps(span: tuple[int, int], consumed: list[tuple[int, int]]) -> bool:
    for s, e in consumed:
        if span[0] < e and span[1] > s:
            return True
    return False


def _clean_description(description: str) -> str:
    desc = description.strip().rstrip(".,;!?")
    for pat in _DUE_PATTERNS:
        desc = pat.sub("", desc).strip().rstrip(".,;!?")
    return desc


def _has_assignment_verb(description: str) -> bool:
    lower = description.lower()
    return any(verb in lower for verb in _ASSIGNMENT_VERBS)


def _extract_due(sentence: str) -> str:
    for pattern in _DUE_PATTERNS:
        m = pattern.search(sentence)
        if m:
            return m.group(1).strip()
    return ""


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]
