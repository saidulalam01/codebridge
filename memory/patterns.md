# Learned Mapping Patterns

Patterns learned from past anonymizations. AI agent reads this before suggesting mappings.

## Domain: SaaS / Fintech (Example)

| Real Pattern | Generic Pattern | Reason |
|---|---|---|
| `accounts` | `user_accounts` | Trading platform user accounts |
| `customers` | `users` | Customer records |
| `orders` | `purchases` | Purchase/order records |
| `trades` | `transactions` | Trading transactions |
| `wallet_transactions` | `wallet_transfers` | Wallet/payout records |
| `countries` | `regions` | Country reference table |
| `coupons` | `promo_codes` | Discount/coupon codes |
| `plans` | `subscription_plans` | Account plans/tiers |
| `account_metrics` | `performance_metrics` | Account performance data |
| `challenge` / `phase` | `evaluation` / `stage` | Multi-phase challenges |
| `payout` / `withdrawal` | `disbursement` | Financial payouts |
| `breach` / `violation` | `rule_violation` | Account rule violations |
| `funded` / `real` | `active` / `live` | Account status after passing |
| `customer_id` | `user_id` | User identifier |
| `login` | `account_id` | Account login identifier |
| `profit` | `pnl` | Profit/loss column |
| `grand_total` | `total_amount` | Order total |
| `breachedby` | `violation_reason` | Violation reason column |

## Domain: General SaaS

(grows as more projects are processed)

## Naming Conventions

- **Tables**: `app.{noun_plural}` (e.g., `app.users`, `app.transactions`)
- **Columns**: snake_case, generic (e.g., `user_id`, `created_at`, `amount`)
- **Business terms**: Simple nouns (Plan A, Plan B, Stage 1, Stage 2)
- **Company name**: Always "AcmeCorp" or "TradePlatform"
- **Schemas**: `core` (main app), `analytics` (data mart), `reporting` (reports)
