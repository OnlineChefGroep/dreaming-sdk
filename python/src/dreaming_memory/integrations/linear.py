"""Linear GraphQL client — read/write issues and comments into agent memory."""

from __future__ import annotations

import os
from typing import Any

import httpx

from dreaming_memory.session import SessionContext
from dreaming_memory.store.postgres import AgentMemoryStore
from dreaming_memory.types import MemoryRecord, MemorySource, MemoryType

LINEAR_ENDPOINT = "https://api.linear.app/graphql"
TEAM_KEY = os.environ.get("LINEAR_TEAM_KEY", "CHEF")


class LinearClient:
    """Lightweight Linear API wrapper aligned with utrecht-data-os/scripts/linear_api.py."""

    def __init__(self, api_key: str | None = None, team_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("LINEAR_API_KEY", "")
        self.team_key = team_key or os.environ.get("LINEAR_TEAM_KEY", "CHEF")
        if not self.api_key:
            raise ValueError("LINEAR_API_KEY required")

    def gql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = httpx.post(
            LINEAR_ENDPOINT,
            json={"query": query, "variables": variables or {}},
            headers={"Authorization": self.api_key, "Content-Type": "application/json"},
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        if errors := data.get("errors"):
            raise RuntimeError(f"Linear GraphQL errors: {errors}")
        return data.get("data", {})

    def normalize_issue_id(self, raw: str) -> str:
        raw = raw.strip().upper()
        if raw.isdigit():
            return f"{self.team_key}-{raw}"
        return raw

    def get_issue(self, issue_id: str) -> dict[str, Any]:
        normalized = self.normalize_issue_id(issue_id)
        data = self.gql(
            """
            query Issue($id: String!) {
              issue(id: $id) {
                id identifier title description
                state { name } priority url
                assignee { name }
                labels { nodes { name } }
                comments { nodes { id body createdAt user { name } } }
                createdAt updatedAt
              }
            }
            """,
            {"id": normalized},
        )
        issue = data.get("issue")
        if not issue:
            raise ValueError(f"Issue {normalized} not found")
        return issue

    def create_issue(
        self, title: str, description: str = "", team_key: str | None = None
    ) -> dict[str, Any]:
        team_id = self._resolve_team_id(team_key or self.team_key)
        data = self.gql(
            """
            mutation CreateIssue($input: IssueCreateInput!) {
              issueCreate(input: $input) {
                success issue { id identifier url title }
              }
            }
            """,
            {"input": {"teamId": team_id, "title": title, "description": description}},
        )
        result = data.get("issueCreate", {})
        if not result.get("success"):
            raise RuntimeError("Failed to create Linear issue")
        return result["issue"]

    def add_comment(self, issue_id: str, body: str) -> dict[str, Any]:
        issue = self.get_issue(issue_id)
        data = self.gql(
            """
            mutation CreateComment($input: CommentCreateInput!) {
              commentCreate(input: $input) {
                success comment { id body }
              }
            }
            """,
            {"input": {"issueId": issue["id"], "body": body}},
        )
        result = data.get("commentCreate", {})
        if not result.get("success"):
            raise RuntimeError("Failed to add comment")
        return result["comment"]

    def update_status(self, issue_id: str, state_name: str) -> dict[str, Any]:
        issue = self.get_issue(issue_id)
        team_id = self._resolve_team_id(self.team_key)
        states = self.gql(
            """
            query WorkflowStates($teamId: ID!) {
              workflowStates(filter: { team: { id: { eq: $teamId } } }) {
                nodes { id name }
              }
            }
            """,
            {"teamId": team_id},
        ).get("workflowStates", {}).get("nodes", [])
        target = next((s for s in states if s["name"].lower() == state_name.lower()), None)
        if not target:
            raise ValueError(f"State '{state_name}' not found")
        data = self.gql(
            """
            mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
              issueUpdate(id: $id, input: $input) {
                success issue { identifier url state { name } }
              }
            }
            """,
            {"id": issue["id"], "input": {"stateId": target["id"]}},
        )
        result = data.get("issueUpdate", {})
        if not result.get("success"):
            raise RuntimeError("Failed to update issue status")
        return result["issue"]

    def list_issues(
        self,
        state: str | None = None,
        *,
        limit: int = 50,
        team_key: str | None = None,
    ) -> list[dict[str, Any]]:
        """List issues for a team, optionally filtered by workflow state name."""
        filt: dict[str, Any] = {"team": {"key": {"eq": (team_key or self.team_key)}}}
        if state:
            filt["state"] = {"name": {"eq": state}}
        data = self.gql(
            """
            query Issues($filter: IssueFilter, $first: Int) {
              issues(filter: $filter, first: $first, orderBy: updatedAt) {
                nodes {
                  id identifier title description priority url
                  state { name type }
                  labels { nodes { id name } }
                  updatedAt
                }
              }
            }
            """,
            {"filter": filt, "first": limit},
        )
        return data.get("issues", {}).get("nodes", [])

    def team_labels(self, team_key: str | None = None) -> dict[str, str]:
        """Return {label_name_lower: label_id} for the team."""
        team_id = self._resolve_team_id(team_key or self.team_key)
        data = self.gql(
            """
            query Labels($teamId: ID!) {
              issueLabels(filter: { team: { id: { eq: $teamId } } }, first: 250) {
                nodes { id name }
              }
            }
            """,
            {"teamId": team_id},
        )
        return {n["name"].lower(): n["id"] for n in data.get("issueLabels", {}).get("nodes", [])}

    def update_issue(
        self,
        issue_id: str,
        *,
        priority: int | None = None,
        label_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        issue = self.get_issue(issue_id)
        inp: dict[str, Any] = {}
        if priority is not None:
            inp["priority"] = priority
        if label_ids is not None:
            inp["labelIds"] = label_ids
        if not inp:
            return issue
        data = self.gql(
            """
            mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
              issueUpdate(id: $id, input: $input) {
                success issue { identifier url priority }
              }
            }
            """,
            {"id": issue["id"], "input": inp},
        )
        result = data.get("issueUpdate", {})
        if not result.get("success"):
            raise RuntimeError("Failed to update issue")
        return result["issue"]

    def _resolve_team_id(self, team_key: str) -> str:
        cached = os.environ.get("LINEAR_TEAM_ID", "")
        if cached:
            return cached
        teams = self.gql("query { teams { nodes { id key } } }").get("teams", {}).get("nodes", [])
        for team in teams:
            if team["key"].upper() == team_key.upper():
                return team["id"]
        raise ValueError(f"Team {team_key} not found")


class LinearMemoryBridge:
    """Sync Linear issues/comments ↔ agent_memory."""

    def __init__(self, store: AgentMemoryStore, client: LinearClient | None = None) -> None:
        self.store = store
        self.client = client or LinearClient()

    def ingest_issue(self, issue_id: str, session: SessionContext) -> MemoryRecord:
        issue = self.client.get_issue(issue_id)
        labels = [lb["name"] for lb in issue.get("labels", {}).get("nodes", [])]
        record = MemoryRecord(
            agent_id=session.agent_id,
            session_id=session.session_id,
            session_type=session.session_type,
            memory_type=MemoryType.ISSUE_SNAPSHOT,
            source=MemorySource.LINEAR,
            content={
                "identifier": issue["identifier"],
                "title": issue["title"],
                "description": issue.get("description"),
                "state": issue["state"]["name"],
                "url": issue["url"],
            },
            metadata={"linear_issue_id": issue["id"], "labels": labels},
        )
        saved = self.store.write(record)
        for comment in issue.get("comments", {}).get("nodes", []):
            self.store.write(
                MemoryRecord(
                    agent_id=session.agent_id,
                    session_id=session.session_id,
                    session_type=session.session_type,
                    memory_type=MemoryType.COMMENT,
                    source=MemorySource.LINEAR,
                    content={
                        "issue_identifier": issue["identifier"],
                        "body": comment["body"],
                        "author": (comment.get("user") or {}).get("name"),
                        "created_at": comment.get("createdAt"),
                    },
                    metadata={
                        "linear_comment_id": comment["id"],
                        "parent_memory_id": str(saved.id),
                    },
                )
            )
        return saved

    def create_issue_from_memory(
        self, session: SessionContext, title: str, description: str
    ) -> MemoryRecord:
        issue = self.client.create_issue(title, description)
        return self.store.write(
            MemoryRecord(
                agent_id=session.agent_id,
                session_id=session.session_id,
                session_type=session.session_type,
                memory_type=MemoryType.ISSUE_SNAPSHOT,
                source=MemorySource.LINEAR,
                content={
                    "identifier": issue["identifier"],
                    "title": issue["title"],
                    "url": issue["url"],
                },
                metadata={"linear_issue_id": issue["id"], "created_from_memory": True},
            )
        )

    def comment_from_memory(
        self, session: SessionContext, issue_id: str, body: str
    ) -> MemoryRecord:
        comment = self.client.add_comment(issue_id, body)
        return self.store.write(
            MemoryRecord(
                agent_id=session.agent_id,
                session_id=session.session_id,
                session_type=session.session_type,
                memory_type=MemoryType.COMMENT,
                source=MemorySource.LINEAR,
                content={"issue_id": issue_id, "body": body},
                metadata={"linear_comment_id": comment["id"]},
            )
        )
