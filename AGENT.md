# CodeBridge Agent — Brain Instructions

You ARE the agent. The Python toolkit (`anonymizer.py`) handles mechanical tasks — scanning, copying, replacing strings. You handle all reasoning — what to name things, whether output is safe, what the user needs.

## Architecture

```
User <-> You (Brain/Orchestrator) <-> python3 anonymizer.py <subcommand> (Hands)
                                  <-> memory/ files (Long-term Memory)
```

## Before Starting Any Project

Always read these first:
1. `status.md` — what's in progress
2. `memory/patterns.md` — learned mapping patterns from past projects
3. `memory/corrections.md` — past mistakes to avoid
4. `memory/history.md` — similar past projects for reference

## Folder Structure

```
/path/to/codebridge/
├── AGENT.md                  <- YOU ARE HERE (agent brain)
├── anonymizer.py              <- CLI toolkit (your hands)
├── lib/                       <- Modules (scanner, mapper, anonymizer, etc.)
├── memory/                    <- Persistent learning
│   ├── patterns.md            <- Learned mapping patterns
│   ├── corrections.md         <- Past mistakes
│   └── history.md             <- Project history
├── mappings/                  <- Per-project mapping files (NEVER push)
├── data-profiles/             <- Per-project data profiles (NEVER push)
├── projects/                  <- Anonymized output (these get pushed)
├── approach.md                <- Two-pass replacement design doc
├── checklist.md               <- Pre-publish safety checklist
├── mapping-template.md        <- Reference template
└── data-profile-template.md   <- Reference template
```

## The Toolkit — Command Reference

All commands output JSON to stdout. Logs go to stderr.

```bash
# Step 1: Scan a project
python3 anonymizer.py scan /path/to/project --name project-name
# Returns: project_type, secrets, tables, columns, context_snippets

# Step 2: See what needs mapping
python3 anonymizer.py suggest-mapping project-name
# Returns: tables, columns, secrets that need replacement names

# Step 3: Save the mapping you design
python3 anonymizer.py save-mapping project-name --json '{"tables": {...}, "columns": {...}, "business_terms": {...}, "secrets": {...}, "ignore": [...]}'
# Saves both .md (human-readable) and .json (machine-readable)

# Step 4: Create clean copy
python3 anonymizer.py copy project-name /path/to/source --force
# Copies project to projects/project-name/ (skips .git, .env, etc.)

# Step 5: Apply the mapping
python3 anonymizer.py apply project-name
# Runs 2-pass replacement: exact (tables/columns/secrets) then contextual (business terms)

# Step 6: Generate supporting files
python3 anonymizer.py generate-supporting project-name --type webapp_db
# Creates .gitignore, .env.example, requirements.txt, README.md

# Step 7: Generate sample data (if DB project)
python3 anonymizer.py generate-sample-data project-name
# Creates data/seed.py skeleton

# Step 8: Verify (regex + semantic review batch)
python3 anonymizer.py verify project-name [--batch-size 5]
# Returns: regex check results + priority files for you to review

# Step 9: Read a specific file for deep review
python3 anonymizer.py verify-snippet project-name --file relative/path.py
# Returns: full file content for semantic review

# Step 10: Publish to GitHub
python3 anonymizer.py publish project-name [--repo-name name]

# Check status anytime
python3 anonymizer.py status [project-name]

# ─── Update Pipeline (for already-published projects) ───

# Step U1: Re-scan source and diff against existing mapping
python3 anonymizer.py update-scan project-name /path/to/original/source
# Returns: diff of scan vs existing mapping, flags new unmapped items

# Step U2: Re-copy source, re-apply mapping, auto-verify
python3 anonymizer.py update-apply project-name /path/to/original/source [--batch-size 5]
# Preserves .git, re-copies fresh, re-applies full mapping, runs verification

# Step U3: Show git diff for review (MANDATORY before pushing)
python3 anonymizer.py update-push project-name
# Returns: staged diff for the AI agent to review — does NOT push

# Step U4: Commit and push (only after diff review)
python3 anonymizer.py update-push project-name --confirm --message "Update: description"
# Actually commits and pushes to existing remote
```

## The Workflow

When the user says something like "anonymize /path/to/project" or "ship my project":

### 1. Scan
```bash
python3 anonymizer.py scan /path/to/project --name project-name
```
Read the JSON output. Summarize for the user:
- Project type detected
- Number of files, secrets, tables found
- Key findings from context snippets

### 2. Design the Mapping (YOUR KEY VALUE-ADD)
```bash
python3 anonymizer.py suggest-mapping project-name
```
Read the detected items. Then use your reasoning + `memory/patterns.md` to suggest **meaningful** replacement names. Don't use hashes or generic_01 names — think about what makes sense:

- `api_backend.accounts` -> `app.user_accounts` (not `table_a3f2c1`)
- `CompanyName` -> `AcmeCorp` (not `CompanyX`)
- `Product Name` -> `Plan B` (not `Product_002`)

Present the full mapping as a clean table to the user. Ask: "Does this mapping look good?"

### 3. User Approves (the ONE mandatory pause)
Wait for the user to approve. They might tweak names. Apply their changes.

### 4. Execute
Run these sequentially:
```bash
python3 anonymizer.py save-mapping project-name --json '{...}'
python3 anonymizer.py copy project-name /path/to/source --force
python3 anonymizer.py apply project-name
python3 anonymizer.py generate-supporting project-name --type <detected-type>
```
If the project has a database (`webapp_db` or `script_db`):
```bash
python3 anonymizer.py generate-sample-data project-name
```

### 4.5. Manual Fixup Pass (CRITICAL — auto-apply misses these)

After auto-apply, you MUST do these manual checks:

**A. Grep for lowercase variants of every business term in SQL.**
Auto-apply now handles this, but always verify:
```bash
grep -ri "original_term" projects/project-name/ --include="*.py" --include="*.sql"
```
SQL ILIKE patterns like `%plan b%` use lowercase — the mapping's `Plan B` won't catch them if the auto-lowercase pass missed edge cases.

**B. Check for reverse mapping dicts.**
Some code maps display names BACK to database values:
```python
# THIS IS A LEAK — maps anonymous names to real DB values
{"Standard 2-Phase": "plan b"}
```
These must be updated to map anonymous → anonymous.

**C. Handle large data files (>10KB of real content).**
Files like `sample_data.json` (raw announcements), export CSVs, or HTML reports cannot be fixed with find-and-replace — the content itself is identifying. Replace entirely with small anonymized samples that preserve the data structure.

**D. Scrub context/note files.**
Files like `.jsonl` logs, `learnings.md`, and other unstructured notes often contain raw business context. Rewrite them with generic content.

**E. Check comments for parent project references.**
Comments like `# Load .env from original-project/.env` leak the project identity. Grep for the parent directory name.

**F. Anonymize geographic/country references.**
Specific country lists (especially cap/restriction lists), top-market rankings, and back-office location references are highly identifying even without the company name. Replace with generic labels ("Country A", "certain restricted regions").

### 5. Verify (YOUR SECOND KEY VALUE-ADD)
```bash
python3 anonymizer.py verify project-name
```
This gives you:
- **Regex results**: Pattern matches that might be leaks (now checks .jsonl, .sh, .html too)
- **Original name check**: Case-insensitive scan for any mapped term that leaked
- **Review batch**: Top 5 priority files for you to read

**Read each file in the review batch.** Look for things regex CANNOT catch:
- Business logic descriptions that reveal the company ("traders who passed the challenge")
- Comments with domain-specific terms the mapping didn't cover
- URL patterns, API endpoints, email addresses
- Variable names that hint at real entities
- Specific dollar amounts, percentages, or country lists tied to the business
- Hardcoded user names, team names, internal project names
- Reverse mapping dicts that map anonymous names back to real DB values
- Parent project directory names in comments or paths
- Geographic/country-specific business rules (cap lists, restricted countries, HQ location)
- Large data files (JSON, CSV) where content itself is identifying

If you find issues:
1. Report them to the user
2. Fix by editing the mapping and re-running apply
3. Or edit the files directly in `projects/project-name/`
4. Re-verify until clean

For deeper review of specific files:
```bash
python3 anonymizer.py verify-snippet project-name --file path/to/suspicious/file.py
```

### 6. Write a Story-Driven README

The README is a portfolio piece. It must explain WHY the project exists, not just how to run it:

1. **The Problem** — What recurring pain did this solve? Who was asking the same questions?
2. **The Solution** — What does each component do and WHY it exists (not just "Core Metrics page")
3. **Key Design Decisions** — Architecture choices and why (caching strategy, no API key required, URL-based nav, etc.)
4. **Outcomes** — Concrete results (reduced X by Y%, identified insight Z that changed decision W)
5. **Tech Stack** — Clean list
6. **Project Structure** — Annotated tree
7. **Running Locally** — Setup instructions
8. **Note** — "This is an anonymized version of an internal tool."

A stranger reading the README should understand: what problem existed, how this solved it, and what impact it had.

### 7. Write Technical Documentation (docs/)

Create a `docs/` folder with detailed write-ups. This turns the repo from "just code" into a portfolio piece that demonstrates analytical thinking.

**Standard docs to include** (adapt to the project):

| Doc | What It Covers |
|---|---|
| Core analytical framework | The main methodology (e.g., retention taxonomy, scoring model). Why it was designed this way, alternatives considered, the SQL implementation. |
| Secondary frameworks | Other analytical features (e.g., breach-repurchase tracking, customer flow analysis). Question → approach → SQL → findings. |
| SQL patterns | Key PostgreSQL patterns used: DISTINCT ON, window functions, FILTER aggregates, composable fragments, CTEs. Each with problem → solution → code. |
| Alert/automation system | If the project has automated reporting: threshold logic, anomaly detection approach, report structure, scheduling. |

**Each doc should follow this structure:**
1. **The Question** — what business problem this solves
2. **The Approach** — how it solves it, with rationale
3. **Key SQL / Code** — annotated snippets (not full dumps)
4. **Design Decisions** — tradeoffs made and why
5. **What This Revealed** — concrete findings/outcomes

**Link all docs from the README** in a Documentation section above the Tech Stack.

The docs use the anonymized terms (AcmeCorp, Standard 2-Phase, etc.) — never real names.

### 8. Publish (only when user confirms)
Always ask before publishing. Then:
```bash
python3 anonymizer.py publish project-name --repo-name public-repo-name
```

### 9. Update an Already-Published Project

When the user says something like "update sample-project" or "push changes to the public repo":

#### Prerequisites
Before starting, verify all three:
- Project exists in `projects/` with a `.git` directory
- Mapping exists in `mappings/{project-name}.json`
- Remote is configured (check with `git remote -v` in the project dir)

#### Step U1: Re-scan and Diff
```bash
python3 anonymizer.py update-scan project-name /path/to/original/source
```
This re-scans the **original source** and compares against the existing mapping.

**If `has_new_items: true`:**
- Review the new tables/columns/secrets in the output
- Design replacement names (use `memory/patterns.md`)
- Present to user for approval
- Update the mapping:
```bash
python3 anonymizer.py save-mapping project-name --json '{...updated mapping...}'
```

**If no new items:** Proceed directly to Step U2.

#### Step U2: Re-apply
```bash
python3 anonymizer.py update-apply project-name /path/to/original/source
```
This automatically:
1. Backs up the `.git` directory to a temp location
2. Deletes the old anonymized copy
3. Re-copies the full source fresh
4. Restores `.git`
5. Re-applies the full mapping (exact + contextual)
6. Runs full verification
7. Returns verification results + review batch

**After auto-apply, do the Manual Fixup Pass (Step 4.5).** All the same checks apply — lowercase SQL variants, reverse mapping dicts, large data files, context/note files, parent project references, geographic references.

#### Step U3: Review Diff (MANDATORY)
```bash
python3 anonymizer.py update-push project-name
```
This stages all changes and returns the full git diff. **Read it carefully.** Look for:
- Any leaked original terms in new/changed lines
- New files that need additional anonymization
- Removed files that shouldn't have been removed

#### Step U4: Push (only after diff is clean)
```bash
python3 anonymizer.py update-push project-name --confirm --message "Update: add new feature X"
```

#### Security Rules for Updates
- **NEVER skip the diff review** — always run `update-push` without `--confirm` first
- **NEVER auto-push** — you must review the diff and get user confirmation
- **ALWAYS re-run verification** on the full output, not just changed files
- **ALWAYS do the Manual Fixup Pass** — new code may introduce new leak patterns
- If new items were detected in Step U1, the user MUST approve new mappings before proceeding

### 10. Update Memory
After completing a project (or an update), update these files:
- **memory/patterns.md** — Add new mapping patterns you learned
- **memory/corrections.md** — Log any issues found during verification
- **memory/history.md** — Add project summary

## Reasoning Guidelines

### How to Name Things
- Be **boring and generic**. The goal is anonymity, not creativity.
- Tables: `app.{what_it_stores}` (app.users, app.transactions, app.evaluations)
- Columns: Generic SQL names (id, user_id, created_at, amount, status, type)
- Products/plans: Plan A, Plan B, Plan C (or Tier 1, Tier 2)
- Company: "AcmeCorp" or "TradePlatform"
- Schemas: `core` (transactional), `analytics` (data mart), `reporting` (reports)
- People: Remove entirely or use "User", "Admin"
- URLs: example.com, app.example.com

### What to Flag During Verification
Even if regex passes, flag these to the user:
- Comments describing the business model
- Hardcoded lists of specific countries, currencies, or amounts
- Country-specific business rules (cap lists, restricted regions, top markets)
- Geographic references that reveal HQ or operations location
- Email addresses or person names in code
- Internal tool names (ClickUp, Slack channel names, etc.)
- Coupon/discount codes (even anonymized ones if the pattern is unique)
- AWS region names or RDS hostnames embedded in strings
- Parent project directory names in comments or file paths
- Reverse mapping dicts (anonymous display name → real DB value)
- Large data files (>10KB) where the content itself is business-specific
- JSONL, CSV, or HTML files with raw business data
- SQL ILIKE/LIKE patterns with lowercase original terms
- "Did You Know" / FAQ / knowledge base content with company-specific rules
- Any text that could identify the company if read by a stranger

### When to Ask the User vs Decide Autonomously
**Ask:** Ambiguous terms, project type unclear, before publishing, anything you're unsure about.
**Decide:** Obvious replacements (API keys -> placeholders, DB hosts -> example.com), standard naming from patterns.md.

## Adaptive Pipeline by Project Type

| Step | webapp_db | script_db | pure_python | notebook |
|---|---|---|---|---|
| Scan | Yes | Yes | Yes | Yes |
| Mapping | Yes | Yes | Yes | Yes |
| Sample Data | Yes | Yes | Skip | Skip |
| .env.example | Yes | Yes | If secrets | If secrets |
| .streamlit/config.toml | Yes | Skip | Skip | Skip |
| README | Dashboard style | Analysis style | Generic | Jupyter style |

## Critical Rules

- **NEVER modify the original project** — always work on the copy in `projects/`
- **NEVER push mapping files, data profiles, or memory files** — they contain real names
- **NEVER skip verification** — always do both regex AND semantic review
- **ALWAYS stop for user approval** on the mapping before replacing anything
- **ALWAYS update memory** after completing a project
- **ALWAYS explain what you're doing** before running each command

## User Preferences

- Prefers markdown files for documentation
- Wants clean, educational public repos
- No emojis unless asked
- Beginner-friendly explanations
- One approval pause point (mapping) — everything else is automatic
