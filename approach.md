# Approach & Design

## The Problem

Share code publicly on GitHub without exposing:
- API keys, DB credentials, secrets
- Real table and column names
- Business-specific terms and company names
- Any identifiable internal information

## Architecture

```
Private Code → Scan → Mapping → Replace → Review → Public Code
```

### Two-Pass Replacement System

**Pass 1: Exact (Automated)**
- Code and SQL: table names, column names, credentials
- Safe, deterministic, always consistent

**Pass 2: Contextual (LLM-reviewed)**
- Comments, docs, README, natural language
- Agent reads context to avoid replacing common English words
- Example: "accounts" (table) gets replaced, but "account for the delay" does not

**Pass 3: Human Review**
- Agent generates a diff
- Nothing goes public without user approval

## Consistency Strategy

- Single `mapping.yaml` file is the source of truth
- Every file goes through the same mapping
- Mapping has three categories:
  - `exact` — always replace (SQL, code references)
  - `contextual` — replace in business context only
  - `ignore` — never touch (common English phrases)
