"""CLI Interface for AI Meeting Summarizer & Action Items Extractor.

Powered by Rich terminal UI formatting.
"""

from __future__ import annotations

import argparse
import sys
import io
from pathlib import Path

# Force UTF-8 output encoding for Windows terminals
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add parent directory to sys.path so backend services can be imported
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from backend.services.parser import parse_transcript_file
from backend.services.ai_processing import generate_summary, generate_action_items
from backend.services.exporter import Exporter
from backend.services.regex_extractor import generate_4section_recap

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    console = Console(force_terminal=True, legacy_windows=False)
    HAS_RICH = True
except Exception:
    HAS_RICH = False


def run_cli():
    parser = argparse.ArgumentParser(
        description="AI Meeting Intelligence Suite CLI — Summarize & Extract Action Items"
    )
    parser.add_argument("-i", "--input", required=True, help="Path to input transcript (.vtt, .srt, .txt, .json) or audio file")
    parser.add_argument("-o", "--output", default="./output", help="Output directory for generated reports (default: ./output)")
    parser.add_argument("-f", "--format", choices=["markdown", "json", "pdf", "all"], default="markdown", help="Export format (default: markdown)")
    parser.add_argument("-s", "--style", choices=["concise", "detailed", "executive", "four_section"], default="concise", help="Summary style (default: concise)")
    parser.add_argument("-t", "--title", default="", help="Meeting title (auto-detected if omitted)")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' not found.")
        sys.exit(1)

    title = args.title or input_path.stem.replace("_", " ").replace("-", " ").title()

    if HAS_RICH:
        console.print(
            Panel.fit(
                f"[bold blue]📋 AI Meeting Intelligence Suite[/bold blue]\n[dim]Processing: {input_path.name}[/dim]",
                border_style="blue",
            )
        )

    # 1. Parse Transcript
    print(f"📄 Parsing transcript from '{input_path.name}'...")
    parsed_transcript = parse_transcript_file(input_path, meeting_title=title)
    full_text = parsed_transcript.full_text()
    print(f"✓ Parsed {len(parsed_transcript.segments)} segments with {len(parsed_transcript.speakers())} detected speakers.")

    # 2. Generate Summary
    print(f"🤖 Generating summary (style: {args.style})...")
    summary_data = generate_summary(full_text, style=args.style)
    print("✓ Summary generated successfully.")

    # 3. Extract Action Items
    print("🚀 Extracting action items...")
    action_items = generate_action_items(full_text)
    print(f"✓ Extracted {len(action_items)} action items.")

    # 4. Display Terminal Rich Table
    if HAS_RICH and action_items:
        table = Table(title="🚀 Action Items", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Task Description")
        table.add_column("Assignee", style="cyan")
        table.add_column("Priority", style="bold")
        table.add_column("Due Date", style="yellow")

        for idx, item in enumerate(action_items, 1):
            prio = (item.get("priority") or "medium").upper()
            prio_color = "red" if prio == "HIGH" else ("yellow" if prio == "MEDIUM" else "green")
            table.add_row(
                str(idx),
                item.get("description", ""),
                item.get("assignee") or "Unassigned",
                f"[{prio_color}]{prio}[/{prio_color}]",
                item.get("due_date") or "—",
            )
        console.print(table)

    # 5. Export Report
    print(f"💾 Exporting report (format: {args.format})...")
    exporter = Exporter(output_dir=args.output)
    exported_file = exporter.export_data(
        title=title,
        summary=summary_data.get("summary", ""),
        action_items=action_items,
        key_topics=summary_data.get("key_points", []),
        decisions=summary_data.get("decisions", []),
        open_questions=summary_data.get("open_questions", []),
        fmt=args.format,
    )

    print(f"✅ Processing complete! Exported to: {exported_file}")


if __name__ == "__main__":
    run_cli()
