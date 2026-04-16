#!/usr/bin/env python3
"""Plan or apply weekly GitHub issues from github-projects CSV files."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


CATEGORY_LABELS = {
    "공통": ("category_common", "Common weekly work"),
    "학습": ("category_learning", "Learning and research work"),
    "구현": ("category_implementation", "Implementation work"),
    "테스트": ("category_test", "Test cases and validation"),
    "문서": ("category_docs", "Documentation work"),
    "운영": ("category_ops", "Operations and coordination"),
    "버그": ("category_bug", "Bug fixes"),
    "기능": ("category_feature", "Feature work"),
    "회고": ("category_review", "Review and retrospective work"),
    "리뷰": ("category_review", "Review and retrospective work"),
}

LABEL_COLORS = {
    "category_common": "6A737D",
    "category_learning": "0366D6",
    "category_implementation": "0E8A16",
    "category_test": "D93F0B",
    "category_docs": "0075CA",
    "category_ops": "5319E7",
    "category_bug": "D73A4A",
    "category_feature": "A2EEEF",
    "category_review": "FBCA04",
    "category_other": "C5DEF5",
}


@dataclass
class IssuePlan:
    index: int
    title: str
    source_title: str
    content: str
    category: str
    labels: list[str]
    body: str


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def normalize_week(value: str) -> str:
    raw = value.strip().lower()
    raw = re.sub(r"^(w|week)[-_ ]*", "", raw)
    raw = raw.replace("~", "-").replace("_", "-")
    parts = [part for part in re.split(r"[^0-9]+", raw) if part]
    if not parts:
        raise ValueError(f"Cannot parse week value: {value}")
    return "-".join(str(int(part)) for part in parts)


def week_label(week: str) -> str:
    return "week_" + normalize_week(week).replace("-", "_")


def week_display(week: str) -> str:
    normalized = normalize_week(week)
    if "-" in normalized:
        return "W" + "-".join(part.zfill(2) for part in normalized.split("-"))
    return "W" + normalized.zfill(2)


def find_week_csv(project_dir: Path, week: str) -> Path:
    wanted = normalize_week(week)
    matches: list[Path] = []
    for path in sorted(project_dir.glob("*.csv")):
        match = re.search(r"week([0-9]+(?:[-_][0-9]+)?)", path.name, re.IGNORECASE)
        if not match:
            continue
        candidate = normalize_week(match.group(1))
        if candidate == wanted:
            matches.append(path)
    if not matches:
        raise FileNotFoundError(f"No CSV found for week {week} in {project_dir}")
    if len(matches) > 1:
        names = ", ".join(str(path) for path in matches)
        raise RuntimeError(f"Multiple CSV files match week {week}: {names}")
    return matches[0]


def parse_project_url(url: str | None) -> tuple[str | None, str | None]:
    if not url:
        return None, None
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 4 and parts[0] in {"users", "orgs"} and parts[2] == "projects":
        return parts[1], parts[3]
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], parts[1]
    raise ValueError(f"Unsupported project URL or owner/number value: {url}")


def detect_repo() -> str | None:
    try:
        result = run(["git", "remote", "get-url", "origin"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    remote = result.stdout.strip()
    patterns = [
        r"github\.com[:/]([^/]+/[^/.]+?)(?:\.git)?$",
        r"https://github\.com/([^/]+/[^/.]+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, remote)
        if match:
            return match.group(1)
    return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "title" not in reader.fieldnames:
            raise ValueError(f"{path} must contain a title column")
        rows = []
        for row in reader:
            title = (row.get("title") or "").strip()
            if not title:
                continue
            rows.append({key: (value or "").strip() for key, value in row.items()})
        return rows


def split_category(title: str) -> tuple[str, str]:
    if " - " in title:
        prefix, rest = title.split(" - ", 1)
        return prefix.strip(), rest.strip()
    return "기타", title.strip()


def build_body(*, week: str, csv_path: Path, source_title: str, category: str, content: str) -> str:
    lines = [
        f"## Source",
        f"- Week: {week_display(week)}",
        f"- CSV: `{csv_path}`",
        f"- Original title: {source_title}",
        f"- Category: {category}",
    ]
    if content:
        lines.extend(["", "## Content", content])
    else:
        lines.extend(["", "## Content", "CSV content was empty. Fill in task-specific notes during execution."])
    return "\n".join(lines)


def build_plan(rows: list[dict[str, str]], *, week: str, csv_path: Path, title_prefix: str = "") -> tuple[list[IssuePlan], dict[str, str]]:
    week_tag = week_label(week)
    label_descriptions = {week_tag: f"Issues for {week_display(week)}"}
    issues: list[IssuePlan] = []
    for index, row in enumerate(rows, start=1):
        source_title = row["title"].strip()
        content = row.get("content", "").strip()
        category, _ = split_category(source_title)
        category_label, description = CATEGORY_LABELS.get(category, ("category_other", "Other work"))
        label_descriptions[category_label] = description
        title = f"{title_prefix}{source_title}" if title_prefix else source_title
        labels = [week_tag, category_label]
        issues.append(
            IssuePlan(
                index=index,
                title=title,
                source_title=source_title,
                content=content,
                category=category,
                labels=labels,
                body=build_body(
                    week=week,
                    csv_path=csv_path,
                    source_title=source_title,
                    category=category,
                    content=content,
                ),
            )
        )
    return issues, label_descriptions


def markdown_plan(args: argparse.Namespace, csv_path: Path, issues: list[IssuePlan], label_descriptions: dict[str, str]) -> str:
    project = ""
    if args.project_owner and args.project_number:
        project = f"{args.project_owner}/projects/{args.project_number}"
    lines = [
        f"# Weekly GitHub Issue Plan: {week_display(args.week)}",
        "",
        f"- Source CSV: `{csv_path}`",
        f"- Target repo: `{args.repo or '(not provided)'}`",
        f"- Target project: `{project or '(not provided)'}`",
        f"- Issue count: {len(issues)}",
        f"- Apply mode: `{bool(args.apply)}`",
        "",
        "## Labels",
    ]
    for name in sorted(label_descriptions):
        color = LABEL_COLORS.get(name, "C5DEF5")
        lines.append(f"- `{name}` ({color}): {label_descriptions[name]}")
    lines.extend(["", "## Issues", "", "| # | Title | Labels | Content |", "|---:|---|---|---|"])
    for issue in issues:
        content_state = "present" if issue.content else "empty"
        labels = ", ".join(f"`{label}`" for label in issue.labels)
        safe_title = issue.title.replace("|", "\\|")
        lines.append(f"| {issue.index} | {safe_title} | {labels} | {content_state} |")
    lines.extend(
        [
            "",
            "## Duplicate Strategy",
            "",
            "- Compare exact normalized issue titles against all open and closed issues in the target repository.",
            "- Skip exact matches during apply.",
            "- Manually inspect near matches if the repository already has weekly imports with a different title prefix.",
            "",
            "## Verification",
            "",
            "```bash",
            f"gh issue list --repo {args.repo or 'OWNER/REPO'} --state all --limit 1000 --json number,title,labels,url",
            f"gh label list --repo {args.repo or 'OWNER/REPO'} --limit 500 --json name,description,color",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def json_plan(csv_path: Path, issues: list[IssuePlan], label_descriptions: dict[str, str], args: argparse.Namespace) -> str:
    data: dict[str, Any] = {
        "week": normalize_week(args.week),
        "week_display": week_display(args.week),
        "source_csv": str(csv_path),
        "repo": args.repo,
        "project_owner": args.project_owner,
        "project_number": args.project_number,
        "labels": [
            {
                "name": name,
                "description": description,
                "color": LABEL_COLORS.get(name, "C5DEF5"),
            }
            for name, description in sorted(label_descriptions.items())
        ],
        "issues": [
            {
                "index": issue.index,
                "title": issue.title,
                "source_title": issue.source_title,
                "category": issue.category,
                "labels": issue.labels,
                "body": issue.body,
            }
            for issue in issues
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def gh_json(cmd: list[str]) -> Any:
    result = run(cmd)
    return json.loads(result.stdout or "{}")


def ensure_labels(repo: str, labels: dict[str, str]) -> None:
    existing_raw = gh_json(["gh", "label", "list", "--repo", repo, "--limit", "500", "--json", "name"])
    existing = {item["name"] for item in existing_raw}
    for name, description in sorted(labels.items()):
        if name in existing:
            continue
        color = LABEL_COLORS.get(name, "C5DEF5")
        run(["gh", "label", "create", name, "--repo", repo, "--description", description, "--color", color])


def existing_issues(repo: str) -> dict[str, dict[str, Any]]:
    raw = gh_json(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "all",
            "--limit",
            "1000",
            "--json",
            "number,title,url,state",
        ]
    )
    return {item["title"].strip().lower(): item for item in raw}


def create_issue(repo: str, issue: IssuePlan) -> dict[str, Any]:
    cmd = [
        "gh",
        "issue",
        "create",
        "--repo",
        repo,
        "--title",
        issue.title,
        "--body",
        issue.body,
    ]
    for label in issue.labels:
        cmd.extend(["--label", label])
    result = run(cmd)
    url = result.stdout.strip().splitlines()[-1]
    return {"title": issue.title, "url": url, "created": True}


def add_project_item(project_owner: str, project_number: str, issue_url: str) -> str | None:
    result = gh_json(
        [
            "gh",
            "project",
            "item-add",
            project_number,
            "--owner",
            project_owner,
            "--url",
            issue_url,
            "--format",
            "json",
        ]
    )
    return result.get("id") or result.get("item", {}).get("id")


def project_metadata(project_owner: str, project_number: str) -> tuple[str | None, list[dict[str, Any]]]:
    project = gh_json(["gh", "project", "view", project_number, "--owner", project_owner, "--format", "json"])
    fields = gh_json(
        [
            "gh",
            "project",
            "field-list",
            project_number,
            "--owner",
            project_owner,
            "--limit",
            "100",
            "--format",
            "json",
        ]
    )
    return project.get("id"), fields.get("fields", [])


def find_status_ids(fields: list[dict[str, Any]], status_name: str, field_name: str | None) -> tuple[str | None, str | None]:
    wanted_fields = [field_name] if field_name else ["Status", "상태"]
    for field in fields:
        if field.get("name") not in wanted_fields:
            continue
        for option in field.get("options", []):
            if option.get("name", "").lower() == status_name.lower():
                return field.get("id"), option.get("id")
    return None, None


def apply_plan(args: argparse.Namespace, issues: list[IssuePlan], labels: dict[str, str]) -> dict[str, Any]:
    if not args.repo:
        raise ValueError("--apply requires --repo")
    ensure_labels(args.repo, labels)
    existing = existing_issues(args.repo)
    created: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    project_items: list[dict[str, Any]] = []

    project_id = None
    status_field_id = None
    status_option_id = None
    if args.project_owner and args.project_number and args.status:
        project_id, fields = project_metadata(args.project_owner, args.project_number)
        status_field_id, status_option_id = find_status_ids(fields, args.status, args.status_field)

    for issue in issues:
        existing_issue = existing.get(issue.title.strip().lower())
        if existing_issue:
            issue_record = {
                "title": issue.title,
                "url": existing_issue["url"],
                "number": existing_issue["number"],
                "created": False,
            }
            skipped.append(issue_record)
        else:
            issue_record = create_issue(args.repo, issue)
            created.append(issue_record)

        if args.project_owner and args.project_number:
            item_id = add_project_item(args.project_owner, args.project_number, issue_record["url"])
            project_item = {"title": issue.title, "url": issue_record["url"], "item_id": item_id}
            project_items.append(project_item)
            if item_id and project_id and status_field_id and status_option_id:
                run(
                    [
                        "gh",
                        "project",
                        "item-edit",
                        "--project-id",
                        project_id,
                        "--id",
                        item_id,
                        "--field-id",
                        status_field_id,
                        "--single-select-option-id",
                        status_option_id,
                    ]
                )

    return {
        "created": created,
        "skipped_duplicates": skipped,
        "project_items": project_items,
        "status_set": bool(project_id and status_field_id and status_option_id),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--week", help="Week value such as 6, W06, week6, or 11-12")
    source.add_argument("--csv", dest="csv_path", help="Explicit CSV path")
    parser.add_argument("--project-dir", default="github-projects", help="Directory containing week CSV files")
    parser.add_argument("--repo", help="Target repo as OWNER/REPO. Defaults to git origin when possible")
    parser.add_argument("--project-url", help="GitHub Project URL or OWNER/NUMBER")
    parser.add_argument("--project-owner", help="Project owner login")
    parser.add_argument("--project-number", help="Project number")
    parser.add_argument("--status", help="Project status option to set after item-add")
    parser.add_argument("--status-field", help="Project single-select field name. Defaults to Status or 상태")
    parser.add_argument("--title-prefix", default="", help="Optional prefix prepended to every issue title")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--apply", action="store_true", help="Create labels/issues and add project items")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    project_owner, project_number = parse_project_url(args.project_url)
    args.project_owner = args.project_owner or project_owner
    args.project_number = args.project_number or project_number
    args.repo = args.repo or detect_repo()

    if args.csv_path:
        csv_path = Path(args.csv_path)
        args.week = args.week or normalize_week(csv_path.stem)
    else:
        csv_path = find_week_csv(Path(args.project_dir), args.week)
    args.week = normalize_week(args.week)

    rows = read_csv(csv_path)
    issues, labels = build_plan(rows, week=args.week, csv_path=csv_path, title_prefix=args.title_prefix)

    if args.apply:
        result = apply_plan(args, issues, labels)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    output = json_plan(csv_path, issues, labels, args) if args.format == "json" else markdown_plan(args, csv_path, issues, labels)
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
