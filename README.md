# CodeBridge

A private-to-public code publishing pipeline. Scans private codebases for sensitive content, builds consistent anonymization mappings, and publishes clean public versions to GitHub — with incremental update support.

## The Problem

Private codebases contain company names, database schemas, API keys, business logic, and internal terminology baked into every file. Manually scrubbing a project for public sharing is tedious, error-prone, and usually results in either missed leaks or an incomplete portfolio piece.

Existing solutions (`.gitignore`, secret scanners) only catch credentials. They don't handle the deeper problem: business terms in SQL queries, company names in comments, domain-specific variable names, geographic references, and reverse-mapping dictionaries that expose real database values.

## The Solution

CodeBridge is a CLI toolkit orchestrated by an AI agent. The toolkit handles mechanical tasks (scanning, copying, replacing strings). The agent handles reasoning — designing meaningful replacement names, reviewing output for semantic leaks regex can't catch, and writing documentation.

### How It Works

```
Private Code  -->  Scan  -->  Mapping  -->  Apply  -->  Verify  -->  Publish
                     |           |            |           |
                  Detect      Design       2-Pass     Regex +
                  secrets,    replacement  replace:   semantic
                  schemas,    names        exact +    review
                  terms                    contextual
```

**Publish pipeline** (first time):
1. **Scan** — detect secrets, SQL identifiers, business terms
2. **Map** — build a replacement mapping (user reviews and approves)
3. **Apply** — two-pass replacement: exact (tables/columns/secrets) then contextual (business terms + lowercase variants)
4. **Manual fixup** — six specific checks for patterns auto-apply misses
5. **Verify** — regex checks + semantic review of priority files
6. **Publish** — story-driven README, technical docs, push to GitHub

**Update pipeline** (incremental changes):
1. **Re-scan** — diff original source against existing mapping, flag new unmapped items
2. **Re-apply** — fresh copy with `.git` preserved, full mapping re-applied, automatic verification
3. **Review diff** — mandatory diff review before pushing
4. **Push** — commit and push only after explicit confirmation

### Key Design Decisions

**Two-pass replacement system.** Exact replacements (tables, columns, secrets) run first with longest-match-first ordering to prevent partial replacements. Contextual replacements (business terms) run second with an additional lowercase pass to catch SQL `ILIKE` patterns. This separation prevents business term replacements from corrupting SQL identifiers.

**Agent-as-brain architecture.** The Python toolkit outputs JSON. The AI agent reads it, reasons about what names make sense, reviews output for things regex can't catch (business logic descriptions, geographic references, reverse-mapping dictionaries), and makes judgment calls. This is critical — the hardest anonymization problems are semantic, not syntactic.

**Mandatory verification gates.** The pipeline has two hard stops: mapping approval (before any replacement) and diff review (before any push). The update pipeline adds a third: new-item detection forces re-approval if the source introduced unmapped terms.

**Delete-and-recopy for updates.** Instead of syncing individual files (complex, risk of stale files), updates back up `.git`, delete the old copy, re-copy fresh from source, restore `.git`, and re-apply the full mapping. Simple, reliable, and ensures no orphaned files survive.

**Memory system.** Learned patterns, past corrections, and project history persist across sessions. The agent reads these before starting any project, avoiding repeated mistakes and maintaining consistent naming conventions.

## Project Structure

```
codebridge/
├── anonymizer.py              # CLI entry point — 14 subcommands
├── AGENT.md                  # Agent brain — workflow instructions
├── lib/
│   ├── scanner.py             # Phase 1: detect secrets, SQL, project type
│   ├── mapper.py              # Phase 2: mapping CRUD (.json + .md)
│   ├── anonymize.py           # Phase 4: two-pass replacement engine
│   ├── supporting.py          # Phase 5: generate .gitignore, README, etc.
│   ├── sample_data.py         # Phase 6: generate seed data skeleton
│   ├── verifier.py            # Phase 7: regex + semantic review batch
│   ├── publisher.py           # Phase 8: git init/push + incremental updates
│   ├── differ.py              # Update pipeline: scan-vs-mapping diff
│   ├── status.py              # Session handoff tracking
│   └── utils.py               # Constants, patterns, helpers
├── memory/                    # Persistent learning across projects
│   ├── patterns.md            # Learned mapping patterns by domain
│   ├── corrections.md         # Past mistakes and fixes
│   └── history.md             # Project history and outcomes
├── mappings/                  # Per-project mapping files (never pushed)
├── projects/                  # Anonymized output (these get pushed)
├── approach.md                # Two-pass replacement design document
└── checklist.md               # Pre-publish safety checklist
```

## Tech Stack

- Python 3
- GitHub CLI (`gh`) for repo creation and pushing
- No external dependencies — standard library only

## Usage

CodeBridge is designed to be orchestrated by an AI agent, but each subcommand works standalone:

```bash
# Scan a project
python3 anonymizer.py scan /path/to/project --name my-project

# See what needs mapping
python3 anonymizer.py suggest-mapping my-project

# Save a mapping
python3 anonymizer.py save-mapping my-project --json '{"tables": {...}, "business_terms": {...}, ...}'

# Copy, apply, verify
python3 anonymizer.py copy my-project /path/to/source --force
python3 anonymizer.py apply my-project
python3 anonymizer.py verify my-project

# Publish
python3 anonymizer.py publish my-project --repo-name public-repo-name

# Update an already-published project
python3 anonymizer.py update-scan my-project /path/to/source
python3 anonymizer.py update-apply my-project /path/to/source
python3 anonymizer.py update-push my-project --confirm --message "Update description"
```

## Note

This tool was built to publish portfolio pieces from private work. It is itself published using its own pipeline.
