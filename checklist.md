# Pre-Publish Checklist

Run through this before pushing any anonymized code to GitHub.

## Secrets
- [ ] No API keys in any file
- [ ] No database credentials (host, port, user, password)
- [ ] No hardcoded tokens or session IDs
- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` exists with placeholder values

## Schema & Data
- [ ] No real table names remain
- [ ] No real column names remain
- [ ] No real schema names remain
- [ ] Sample data uses fake/generic values
- [ ] No original coupon/promo codes remain
- [ ] The word "Futures" does not appear (use "Derivatives")

## Insights
- [ ] Pre-built insights exist in insights/ folder
- [ ] Numbers are shifted from real values (not identical)
- [ ] Trends preserved (direction same, magnitude different)
- [ ] Dashboard reads from insights/ when no DB connected

## Business Identity
- [ ] No company name anywhere
- [ ] No product names (use generic: Plan A, Plan B)
- [ ] No internal URLs or endpoints
- [ ] No employee names or emails
- [ ] No references to specific cloud resources (RDS instances, S3 buckets, etc.)

## Documentation
- [ ] README uses generic terms only
- [ ] Comments don't reference real business logic
- [ ] Any screenshots are clean (no sensitive data visible)

## Consistency
- [ ] Same original term maps to same replacement everywhere
- [ ] Code still makes logical sense after replacement
- [ ] No broken references (renamed in one place but not another)

## Final
- [ ] Full text search for known sensitive terms — zero matches
- [ ] Reviewed the full diff one last time
- [ ] Ready to push
