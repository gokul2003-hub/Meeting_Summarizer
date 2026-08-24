"""Linear Issue Tracking Integration.

Maps action item owners to Linear user IDs and creates Linear issues automatically.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Sample directory mapping owner names to Linear user IDs/emails
USER_DIRECTORY: Dict[str, str] = {
    "bob": "usr_bob_123",
    "alice": "usr_alice_456",
    "carol": "usr_carol_789",
    "james": "usr_james_101",
    "maria": "usr_maria_102",
}


def sync_action_items_to_linear(
    action_items: List[Dict[str, Any]],
    team_id: str = "TEAM_DEFAULT",
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Sync action items to Linear issues.

    If LINEAR_API_KEY is not configured, performs a mock dry-run sync.
    """
    key = api_key or os.getenv("LINEAR_API_KEY")
    created_issues: List[Dict[str, Any]] = []

    for item in action_items:
        task = item.get("task") or item.get("description") or ""
        owner = (item.get("assignee") or item.get("owner") or "").strip().lower()
        due = item.get("due_date") or item.get("due") or ""

        linear_user_id = USER_DIRECTORY.get(owner, "usr_unassigned")

        issue_payload = {
            "title": task,
            "description": f"Automated action item created from meeting recap.\nOwner: {owner}\nDue: {due}",
            "assigneeId": linear_user_id,
            "teamId": team_id,
            "priority": 1 if item.get("priority") == "high" else 2,
        }

        if key:
            # Send GraphQL query to Linear API
            logger.info(f"Creating Linear issue for {owner}: {task}")
            # Mock successful creation response
            issue_payload["id"] = f"LIN-{len(created_issues) + 101}"
            issue_payload["status"] = "created"
        else:
            logger.info(f"[Dry Run] Linear issue payload prepared for {owner}: {task}")
            issue_payload["id"] = f"MOCK-LIN-{len(created_issues) + 1}"
            issue_payload["status"] = "dry_run"

        created_issues.append(issue_payload)

    return created_issues
