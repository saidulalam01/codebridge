# Data Profile Template: {project-name}

This file defines how to generate realistic sample data for the public version.
Each project gets its own data profile in `data-profiles/`.

> **This file is NEVER pushed to GitHub.**

## Tables and Relationships

| Table (anonymized name) | Sample Rows | Primary Key | Foreign Keys |
|--------------------------|-------------|-------------|--------------|
| `app.users` | 500 | `id` | — |
| `app.trades` | 5,000 | `id` | `user_id → users.id` |

## Column Definitions

### app.users

| Column | Type | Generation Rule |
|--------|------|-----------------|
| `id` | int | sequential, 1 to N |
| `country` | str | random from [US, UK, DE, FR, JP, AU, CA, BR, IN, SG] |
| `plan_type` | str | weighted random: Plan A (50%), Plan B (30%), Plan C (20%) |
| `created_at` | date | uniform between 2025-01-01 and 2025-06-30 |
| `initial_amount` | float | normal distribution, mean=100000, std=25000 |

### app.trades

| Column | Type | Generation Rule |
|--------|------|-----------------|
| `id` | int | sequential |
| `user_id` | int | FK, random from users |
| `amount` | float | normal distribution, mean=50, std=500 |
| `symbol` | str | random from [EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD] |
| `created_at` | datetime | within parent user's date range |

## Patterns to Preserve

These patterns must exist in the sample data so dashboards look realistic:

- [ ] Pattern: "Plan C conversion drops in Q4" — ensure Plan C rows in Oct-Dec have lower success rates
- [ ] Pattern: "Country DE shows decline in Nov-Dec" — reduce DE activity in those months
- [ ] Pattern: "Overall win rate ~18%" — only ~18% of trades should be profitable

## Output Files

```
data/
├── sample_users.csv
├── sample_trades.csv
└── seed.py          ← script to regenerate all CSVs with same rules
```
