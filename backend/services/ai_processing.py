"""AI Processing Engine — Summary, Action Extraction, Email Drafting & Speaker Diarization.

Combines OpenAI GPT-4o LLM capabilities with deterministic fallback mechanisms (parser & regex_extractor).
"""

import json
import os
import logging
from typing import Any, Dict, List, Optional

from .parser import parse_transcript
from .regex_extractor import extract_action_items_regex, generate_4section_recap

logger = logging.getLogger(__name__)

_client = None
CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def get_client():
    global _client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    if _client is None:
        try:
            from openai import OpenAI
            _client = OpenAI(api_key=api_key)
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
            return None
    return _client


SUMMARY_SYSTEM_PROMPT = """You are an expert meeting analyst. Analyze the meeting transcript and return a JSON object with:
- "summary": An executive summary of the meeting based on requested style (concise, detailed, or executive)
- "key_points": An array of key discussion topics/points as strings
- "decisions": An array of key decisions made in the meeting
- "open_questions": An array of open questions remaining

Return only valid JSON with these exact keys."""

ACTION_ITEMS_SYSTEM_PROMPT = """You are an expert at extracting action items from meeting transcripts.
Extract all action items from the transcript and return a JSON object with:
- "action_items": An array of objects, each containing:
  - "description": What needs to be done (string)
  - "assignee": Who is responsible (string or null if unclear)
  - "due_date": Deadline in YYYY-MM-DD or readable format (string or null if not mentioned)
  - "priority": "high", "medium", or "low" based on urgency language

Return only valid JSON with the "action_items" array."""

EMAIL_SYSTEM_PROMPT = """You are an expert at writing professional business emails.
Write a professional follow-up email for this meeting and return a JSON object with:
- "subject": A concise, professional email subject line (string)
- "body": The complete email body including: brief meeting recap, action items with owners, next steps, and professional closing (string)

Return only valid JSON with these exact keys."""


def _chat_json(system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
    client = get_client()
    if not client:
        return None
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.warning(f"OpenAI API call failed: {e}. Falling back to deterministic engine.")
        return None


def generate_summary(transcript_text: str, style: str = "concise") -> dict:
    """Generate meeting summary with key points, decisions, and open questions."""
    parsed_transcript = parse_transcript(transcript_text)
    
    # Check if 4-section recap or deterministic requested/fallback
    if style == "four_section":
        recap = generate_4section_recap(parsed_transcript)
        return {
            "summary": recap.summary,
            "key_points": [f"Decisions: {len(recap.decisions)}", f"Actions: {len(recap.action_items)}"],
            "decisions": recap.decisions,
            "open_questions": recap.open_questions,
        }

    # Attempt LLM generation
    prompt = f"Meeting transcript:\n\n{transcript_text}\n\nRequested summary style: {style}"
    result = _chat_json(SUMMARY_SYSTEM_PROMPT, prompt)

    if result:
        return {
            "summary": result.get("summary", ""),
            "key_points": result.get("key_points", []),
            "decisions": result.get("decisions", []),
            "open_questions": result.get("open_questions", []),
        }

    # Fallback to deterministic recap
    recap = generate_4section_recap(parsed_transcript)
    return {
        "summary": recap.summary,
        "key_points": [s.text[:80] + "..." for s in parsed_transcript.segments[:5]],
        "decisions": recap.decisions,
        "open_questions": recap.open_questions,
    }


def generate_action_items(transcript_text: str) -> list[dict]:
    """Extract action items with assignee, due date, and priority."""
    result = _chat_json(
        ACTION_ITEMS_SYSTEM_PROMPT,
        f"Meeting transcript:\n\n{transcript_text}",
    )
    if result:
        items = result.get("action_items", [])
        validated = []
        for item in items:
            validated.append({
                "description": item.get("description", ""),
                "assignee": item.get("assignee") or None,
                "due_date": item.get("due_date") or None,
                "priority": item.get("priority", "medium") or "medium",
            })
        return validated

    # Fallback to regex action extractor with first-person attribution
    parsed_transcript = parse_transcript(transcript_text)
    regex_actions = extract_action_items_regex(parsed_transcript)
    return [
        {
            "description": item.description,
            "assignee": item.owner if item.owner else None,
            "due_date": item.due if item.due else None,
            "priority": item.priority,
        }
        for item in regex_actions
    ]


def detect_speakers(transcript_text: str) -> dict:
    """Identify unique speakers and segments."""
    parsed = parse_transcript(transcript_text)
    if parsed.segments and any(s.speaker for s in parsed.segments):
        speakers = parsed.speakers()
        segments = [
            {"speaker": s.speaker or "Speaker", "text": s.text, "sequence": i}
            for i, s in enumerate(parsed.segments)
        ]
        return {"speakers": speakers, "segments": segments}

    client = get_client()
    if client:
        try:
            prompt = """Analyze transcript and identify distinct speakers. Return JSON with 'speakers' array and 'segments' array ({speaker, text, sequence})."""
            res = _chat_json(prompt, f"Transcript:\n\n{transcript_text}")
            if res:
                return {
                    "speakers": res.get("speakers", ["Speaker 1"]),
                    "segments": res.get("segments", [{"speaker": "Speaker 1", "text": transcript_text, "sequence": 0}]),
                }
        except Exception:
            pass

    return {
        "speakers": ["Speaker 1"],
        "segments": [{"speaker": "Speaker 1", "text": transcript_text, "sequence": 0}],
    }


def generate_email_draft(transcript_text: str, summary: str, action_items: list[dict]) -> dict:
    """Draft professional follow-up email."""
    action_items_text = "\n".join(
        f"- {item['description']}"
        + (f" (Owner: {item['assignee']})" if item.get("assignee") else "")
        + (f" (Due: {item['due_date']})" if item.get("due_date") else "")
        for item in action_items
    )

    user_content = (
        f"Meeting summary:\n{summary}\n\n"
        f"Action items:\n{action_items_text or 'No specific action items identified.'}\n\n"
        f"Full transcript:\n{transcript_text[:3000]}"
    )
    result = _chat_json(EMAIL_SYSTEM_PROMPT, user_content)
    if result:
        return {
            "subject": result.get("subject", "Meeting Follow-up"),
            "body": result.get("body", ""),
        }

    # Deterministic Email Fallback
    lines = [
        "Hi Team,",
        "",
        "Thank you for attending today's meeting. Here is a summary of our discussion and key action items:",
        "",
        "Summary:",
        summary,
        "",
        "Action Items:",
        action_items_text or "- Continue planned work items.",
        "",
        "Best regards,",
        "AI Meeting Assistant",
    ]
    return {
        "subject": "Meeting Summary & Action Items Follow-up",
        "body": "\n".join(lines),
    }
