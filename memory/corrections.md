# Corrections Log

Things that went wrong in past anonymizations and how they were fixed.
AI agent reads this to avoid repeating mistakes.

## Template

```
### YYYY-MM-DD — project-name

**What**: Description of the issue
**Why missed**: Root cause
**Fix**: How it was resolved
**Rule**: General rule to prevent recurrence
```

### 2026-02-28 — sample-project

**What**: Lowercase product name in SQL ILIKE patterns (`%plan b%`) survived the auto-apply step
**Why missed**: The mapping had `Plan B` (title case) but SQL used lowercase. Auto-apply is case-sensitive for exact matches.
**Fix**: Manual replace_all of lowercase variants in the affected Python files
**Rule**: Always check for lowercase/ILIKE variants of business terms in SQL queries after auto-apply

### 2026-02-28 — sample-project

**What**: `platform-e` (lowercase) in SQL filter strings not caught
**Why missed**: Mapping had `Platform-E` (capital T). Same case-sensitivity issue.
**Fix**: replace_all of `platform-e` → `platform-e` in shared.py and core_metrics.py
**Rule**: For SQL ILIKE/NOT ILIKE patterns, always add lowercase variants to the mapping

### 2026-02-28 — sample-project

**What**: context/notes.jsonl still had original `acme-brand` after auto-apply
**Why missed**: JSONL files may not be reliably processed by the apply step
**Fix**: Manually rewrote the file
**Rule**: Always verify JSONL and other non-standard format files after auto-apply

### 2026-02-28 — sample-project

**What**: DYK facts with specific country lists and back-office location references identifiable even after company name change
**Why missed**: Auto-apply only does text replacement, not semantic anonymization of identifying context
**Fix**: Replaced country lists with generic references ("certain restricted regions", "Country A/B/C/D")
**Rule**: Always review hardcoded country lists, specific dollar amounts in context, and geographic references during semantic review
