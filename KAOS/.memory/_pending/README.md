# Pending Review Queue

This directory holds changes that require human approval.
When an agent applies a change via timeout (30 min without human response),
it writes a record here for deferred review.

## File Format
- `YYYY-MM-DD--agent-name--description.md`
- Frontmatter: status, agent, timestamp, reason

## Process
1. Agent applies change (auto-approved after timeout)
2. Agent writes record to `_pending/` describing what changed
3. Human reviews at convenience
4. If rejected: revert via `git revert <commit>`
5. If accepted: delete the file from `_pending/`
6. If no review in 30 days: considered auto-approved (logged in log.md)

## Current Items
