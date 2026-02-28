# Mapping Template

This file serves as the template for creating project-specific mappings.
Each project will get its own mapping file inside `mappings/`.

## Structure

### Tables (exact replacement in SQL/code)

| Original | Replacement |
|----------|-------------|
| `schema.real_table` | `app.generic_table` |

### Columns (exact replacement in SQL/code)

| Original | Replacement |
|----------|-------------|
| `realColumn` | `genericColumn` |

### Business Terms (contextual replacement)

| Original | Replacement |
|----------|-------------|
| "CompanyName" | "MyPlatform" |
| "Product X" | "Plan A" |

### Secrets (remove or replace with placeholders)

| Type | Replacement |
|------|-------------|
| API keys | `your-api-key` |
| DB host | `localhost` |
| DB password | `your-password` |

### Ignore List (never replace these)

- Common English phrases that happen to match table/column names
- Example: "account for", "order of", "trade off"

---

> **Note**: The mapping file is NEVER pushed to GitHub. It stays local only.
