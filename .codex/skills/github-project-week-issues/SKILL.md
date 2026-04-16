---
name: github-project-week-issues
description: Use when creating or planning weekly GitHub Issues from github-projects/week*_issues_complete.csv or similar weekly CSV files and adding them to a GitHub Project. Trigger for tasks that mention GitHub Projects, weekly issues, week_n labels, CSV issue files, sprint/week setup, repository/project issue import, or adding the corresponding week's issues to a project with gh CLI.
---

# GitHub Project Week Issues

Use this skill to turn a weekly CSV file into a reviewed GitHub issue import for a repository and GitHub Project.

## Workflow

1. Identify the target week and source file.
   - Prefer an explicit `--week` or `--csv` from the user.
   - If the user says "해당 주차", inspect `github-projects/` and choose the matching `week*_issues_complete.csv`.
   - Use `scripts/plan_week_issues.py` to parse the CSV and infer labels.
2. Inspect live GitHub state before changing anything:
   - target repository issue list
   - target repository labels
   - target GitHub Project fields, options, and current items
   - repository folder/file structure when issue titles reference paths, tests, or modules
3. Produce a decision-complete plan first unless the user explicitly asked to apply immediately.
   - Include label additions/reuse, title/body rules, duplicate prevention, project status, and verification commands.
   - Do not create issues while the user is still asking for planning or review.
4. Apply only after approval or an explicit "추가해줘/실행해줘" style request.
   - Create missing labels.
   - Create non-duplicate issues.
   - Add created or reused issues to the project.
   - Set project status/fields when field IDs and option IDs are known.
5. Verify the result.
   - Confirm issue count, labels, project membership, and status field values.
   - Report skipped duplicates separately from created issues.

## Helper Script

Run the helper from the target repository root or pass explicit paths:

```bash
python3 .codex/skills/github-project-week-issues/scripts/plan_week_issues.py --week 6 --repo OWNER/REPO --project-url https://github.com/users/OWNER/projects/1
```

Useful modes:

```bash
# Markdown dry-run plan from github-projects/week6_issues_complete.csv
python3 .codex/skills/github-project-week-issues/scripts/plan_week_issues.py --week 6 --repo OWNER/REPO

# JSON plan for custom automation
python3 .codex/skills/github-project-week-issues/scripts/plan_week_issues.py --csv github-projects/week11-12_issues_complete.csv --format json

# Apply labels/issues and add them to a project after approval
python3 .codex/skills/github-project-week-issues/scripts/plan_week_issues.py --week 6 --repo OWNER/REPO --project-url https://github.com/users/OWNER/projects/1 --status Todo --apply
```

The script defaults to dry-run. `--apply` requires `--repo`; project addition requires `--project-owner` and `--project-number` or `--project-url`.

## GitHub Inspection

Use `gh` first:

```bash
gh repo view OWNER/REPO --json nameWithOwner,description,defaultBranchRef
gh issue list --repo OWNER/REPO --state all --limit 1000 --json number,title,state,labels,url
gh label list --repo OWNER/REPO --limit 500 --json name,description,color
gh project view PROJECT_NUMBER --owner OWNER --format json
gh project field-list PROJECT_NUMBER --owner OWNER --limit 100 --format json
```

For project items, use GraphQL when `gh project item-list` is not enough:

```bash
gh api graphql -f query='
query($owner:String!, $number:Int!) {
  user(login:$owner) {
    projectV2(number:$number) {
      id
      items(first:100) {
        nodes {
          id
          content { ... on Issue { title number url repository { nameWithOwner } } }
          fieldValues(first:20) { nodes { ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { name } } } } }
        }
      }
    }
  }
}' -f owner=OWNER -F number=1
```

Use `organization(login:$owner)` instead of `user(login:$owner)` for organization-owned projects.

## Issue Rules

- Preserve CSV titles unless the existing project uses a clear week prefix convention.
- Treat the Korean prefix before ` - ` as a category hint:
  - `공통` -> `category_common`
  - `학습` -> `category_learning`
  - `구현` -> `category_implementation`
  - `테스트` -> `category_test`
  - `문서` -> `category_docs`
  - `운영` -> `category_ops`
  - `버그` -> `category_bug`
  - `기능` -> `category_feature`
- Always add the week label, using `week_6` or `week_11_12` for ranges.
- Keep label count restrained. Prefer existing labels with matching meaning.
- Use exact normalized title matching for duplicate prevention first; then inspect close matches manually when the project already has weekly imports.
- For empty CSV content, create a short body that records the source file, week, category, and original CSV title instead of inventing details.

## References

- Read `references/gh-project-notes.md` when project field/status editing is needed.
