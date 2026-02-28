# Project History

Records of anonymized projects, decisions made, and outcomes.
AI agent reads this for context on past work.

## Template

```
## project-name (YYYY-MM-DD)
- Source: /path/to/original
- Type: webapp_db / script_db / pure_python / notebook
- Files: X scanned, Y modified
- Mapping: X tables, Y columns, Z business terms
- Verification: Passed / Failed (details)
- Published: github.com/username/repo (or "local only")
- Lessons: Key takeaways for future projects
```

## sample-project (2026-02-28)
- Source: /path/to/original/project
- Type: webapp_db
- Files: 24 scanned, 15 auto-modified + 8 manually fixed
- Mapping: 16 tables, 10 columns, 25 business terms, 5 secrets
- Verification: Passed — regex + manual review of all files
- Published: https://github.com/yourusername/sample-project
- Lessons:
  - Lowercase SQL ILIKE patterns (e.g. `%plan b%`) are NOT caught by case-sensitive business_terms mapping — must do separate lowercase pass
  - sample_data.json (125KB raw announcements) needs full replacement, not find-and-replace
  - DYK facts with specific country lists, dollar amounts, and business rules are identifiable even with company name changed — must generalize
  - Context files (notes.jsonl) may not be processed by auto-apply if format is JSONL
  - Comments referencing parent project directories (original-project) leak project identity
