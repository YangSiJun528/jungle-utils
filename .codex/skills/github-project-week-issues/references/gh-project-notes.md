# GitHub Project Notes

Use these notes only when applying weekly issues to a GitHub Project or setting project fields.

## Project URL Parsing

Common project URLs:

- `https://github.com/users/OWNER/projects/NUMBER`
- `https://github.com/orgs/ORG/projects/NUMBER`

The owner value for `gh project` is `OWNER` or `ORG`; the number is `NUMBER`.

## Add Issues To A Project

After creating or finding an issue URL:

```bash
gh project item-add PROJECT_NUMBER --owner OWNER --url ISSUE_URL --format json
```

The JSON output includes the project item ID. Keep this ID if a status field must be set.

## Set A Single-Select Status

1. Get the project ID, field ID, and option ID:

```bash
gh project view PROJECT_NUMBER --owner OWNER --format json
gh project field-list PROJECT_NUMBER --owner OWNER --limit 100 --format json
```

2. Find the field named `Status`, `상태`, or the user-specified field name.
3. Find the option whose name matches the requested status, such as `Todo`, `Backlog`, or `Ready`.
4. Edit each item:

```bash
gh project item-edit --project-id PROJECT_ID --id ITEM_ID --field-id FIELD_ID --single-select-option-id OPTION_ID
```

Do not guess IDs. If the field or option cannot be found, report the issue and leave the item in the default project status.
