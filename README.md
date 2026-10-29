# Strategic Sourcing & Supplier Spend Intelligence

![Strategic Sourcing Dashboard](outputs/sourcing_dashboard.png)

**Python-based procurement analytics and automated exception reporting using synthetic demonstration data.**

## Business question
How can a sourcing team identify spend concentration, contract coverage gaps, and transactions requiring review?

## What the solution does
- Generates a reproducible synthetic dataset of 250 suppliers and 10,000 transactions.
- Validates transaction IDs, supplier references, and positive amounts.
- Produces category spend, supplier rankings, and Pareto concentration analysis.
- Flags repeated invoice identifiers within the same supplier for manual review.
- Models **illustrative** savings as 3% of uncontracted spend, not verified savings.
- Generates an executive dashboard and CSV reports automatically.

## Run locally
```bash
python3 -m pip install -r requirements.txt
python3 generate_data.py
python3 analyze.py
```

## Outputs
- `outputs/sourcing_dashboard.png`: four-panel executive dashboard
- `outputs/executive_summary.csv`: KPIs and scenario estimates
- `outputs/supplier_spend.csv`: ranked supplier spend
- `outputs/category_spend.csv`: category totals
- `outputs/duplicate_invoice_flags.csv`: potential duplicates for investigation
- `outputs/concentration_flags.csv`: suppliers above the illustrative 10% threshold

## Limitations
All supplier names and transactions are synthetic. Duplicate invoice flags are not confirmed duplicate payments. The 3% savings assumption is illustrative and excludes implementation costs. This project is a portfolio demonstration, not a production procurement system.

## Technologies
Python, pandas, NumPy, Matplotlib.
