from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models import (
    ActionItem, EmbeddingChunk, FollowUpEmail, Meeting, MeetingSpeaker,
    MeetingSummary, Transcript, TranscriptSegment, User,
)
from schemas import (
    ActionItemResponse,
    ActionItemUpdate,
    ActionItemFullUpdate,
    MeetingDetailResponse,
    MeetingResponse,
    MeetingStatusResponse,
)
from services.ai_processing import (
    generate_action_items, generate_email_draft, generate_summary, detect_speakers,
)
from services.parser import parse_transcript_file, parse_transcript
from services.exporter import Exporter
from services.linear import sync_action_items_to_linear
from services.auth import get_current_user
from services.storage import delete_file, save_upload_file
from services.transcription import transcribe
from services.youtube import download_youtube_audio

router = APIRouter()

SPEAKER_COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"]
TRANSCRIPT_EXTENSIONS = {".vtt", ".srt", ".txt", ".json"}


def process_meeting(meeting_id: str, summary_style: str = "concise") -> None:
    """Background task — runs in its own thread with its own DB session."""
    db = SessionLocal()
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return

        meeting.status = "processing"
        meeting.updated_at = datetime.utcnow()
        db.commit()

        # Step 1: Transcribe audio or parse transcript file
        existing_transcript = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).first()
        if existing_transcript:
            text = existing_transcript.text
        else:
            file_ext = Path(meeting.file_path).suffix.lower()
            if file_ext in TRANSCRIPT_EXTENSIONS:
                parsed = parse_transcript_file(meeting.file_path, meeting_title=meeting.title)
                text = parsed.full_text()
            else:
                text = transcribe(meeting.file_path)

            transcript = Transcript(meeting_id=meeting_id, text=text)
            db.add(transcript)
            db.commit()

        # Step 1.5: Speaker diarization
        existing_segments = db.query(TranscriptSegment).filter(
            TranscriptSegment.meeting_id == meeting_id
        ).first()
        if not existing_segments:
            diarization = detect_speakers(text)
            if diarization["speakers"] and diarization["segments"]:
                speaker_map = {}
                for i, label in enumerate(diarization["speakers"]):
                    speaker = MeetingSpeaker(
                        meeting_id=meeting_id,
                        label=label,
                        color=SPEAKER_COLORS[i % len(SPEAKER_COLORS)],
                    )
                    db.add(speaker)
                    db.flush()
                    speaker_map[label] = speaker.id

                for seg in diarization["segments"]:
                    db.add(TranscriptSegment(
                        meeting_id=meeting_id,
                        speaker_id=speaker_map.get(seg["speaker"]),
                        text=seg["text"],
                        sequence_order=seg["sequence"],
                    ))
                db.commit()

        # Step 2: Generate summary
        summary_data = generate_summary(text, style=summary_style)
        summary = MeetingSummary(
            meeting_id=meeting_id,
            summary=summary_data["summary"],
            key_points=summary_data.get("key_points", []),
            decisions=summary_data.get("decisions", []),
            open_questions=summary_data.get("open_questions", []),
        )
        db.add(summary)
        db.commit()

        # Step 3: Extract action items
        items_data = generate_action_items(text)
        for item in items_data:
            db.add(ActionItem(meeting_id=meeting_id, **item))
        db.commit()

        # Step 4: Draft follow-up email
        email_data = generate_email_draft(text, summary_data["summary"], items_data)
        email = FollowUpEmail(
            meeting_id=meeting_id,
            subject=email_data["subject"],
            body=email_data["body"],
            recipients=[],
        )
        db.add(email)

        meeting.status = "completed"
        meeting.updated_at = datetime.utcnow()
        db.commit()

        # Step 5: Slack notification (non-fatal)
        try:
            from services.slack import send_slack_notification
            send_slack_notification(meeting_id, meeting.user_id, db)
        except Exception:
            pass

        # Step 6: Ingest embeddings for RAG (non-fatal)
        try:
            from services.rag import ingest_meeting_embeddings
            ingest_meeting_embeddings(meeting_id, db)
        except Exception:
            pass

    except Exception as exc:
        try:
            db.rollback()
            meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
            if meeting:
                meeting.status = "failed"
                meeting.error_message = str(exc)
                meeting.updated_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("/upload", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    style: str = Form("concise"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stored_name, abs_path = save_upload_file(file)

    meeting = Meeting(
        user_id=current_user.id,
        title=title,
        filename=stored_name,
        original_filename=file.filename,
        file_path=abs_path,
        status="pending",
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    background_tasks.add_task(process_meeting, meeting.id, style)
    return meeting


@router.post("/upload-url", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
def upload_meeting_from_url(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    title: str = Form(...),
    style: str = Form("concise"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stored_name, abs_path = download_youtube_audio(url)

    meeting = Meeting(
        user_id=current_user.id,
        title=title,
        filename=stored_name,
        original_filename=url,
        file_path=abs_path,
        status="pending",
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    background_tasks.add_task(process_meeting, meeting.id, style)
    return meeting


@router.get("/", response_model=List[MeetingResponse])
def list_meetings(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Meeting)
        .filter(Meeting.user_id == current_user.id)
        .order_by(Meeting.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
def get_meeting(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
        .first()
    )
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting


@router.get("/{meeting_id}/export")
def export_meeting(
    meeting_id: str,
    format: str = "markdown",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
        .first()
    )
    if not meeting or not meeting.summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting or summary not found")

    exporter = Exporter()
    action_items_data = [
        {
            "description": a.description,
            "assignee": a.assignee,
            "due_date": a.due_date,
            "priority": a.priority,
        }
        for a in meeting.action_items
    ]

    exported_path = exporter.export_data(
        title=meeting.title,
        summary=meeting.summary.summary,
        action_items=action_items_data,
        key_topics=meeting.summary.key_points or [],
        decisions=meeting.summary.decisions or [],
        open_questions=meeting.summary.open_questions or [],
        fmt=format,
        date=meeting.created_at.strftime("%Y-%m-%d"),
    )

    return FileResponse(
        path=str(exported_path),
        filename=exported_path.name,
        media_type="application/octet-stream",
    )


@router.post("/{meeting_id}/export/linear")
def export_to_linear(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
        .first()
    )
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    action_items_data = [
        {
            "description": a.description,
            "assignee": a.assignee,
            "due_date": a.due_date,
            "priority": a.priority,
        }
        for a in meeting.action_items
    ]

    issues = sync_action_items_to_linear(action_items_data)
    return {"status": "success", "synced_issues": issues}


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
        .first()
    )
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    delete_file(meeting.file_path)
    db.delete(meeting)
    db.commit()


@router.get("/{meeting_id}/status", response_model=MeetingStatusResponse)
def get_meeting_status(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
        .first()
    )
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return MeetingStatusResponse(id=meeting.id, status=meeting.status, error_message=meeting.error_message)


@router.post("/{meeting_id}/regenerate", response_model=MeetingResponse)
def regenerate_meeting(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    style: str = Form("concise"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
        .first()
    )
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    if meeting.status in ("pending", "processing"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Meeting is already being processed")

    # Clear prior generated data
    if meeting.summary:
        db.delete(meeting.summary)
    for item in list(meeting.action_items):
        db.delete(item)
    if meeting.follow_up_email:
        db.delete(meeting.follow_up_email)

    meeting.status = "pending"
    meeting.error_message = None
    meeting.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(meeting)

    background_tasks.add_task(process_meeting, meeting.id, style)
    return meeting
