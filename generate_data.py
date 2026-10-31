"""Generate reproducible synthetic procurement transactions. No real company data."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
rng = np.random.default_rng(42)
n = 10000
supplier_ids = [f'SUP-{i:03d}' for i in range(1, 251)]
categories = ['Electronics', 'Packaging', 'Logistics', 'Raw Materials', 'MRO', 'Professional Services']
regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America']
suppliers = pd.DataFrame({
    'supplier_id': supplier_ids,
    'supplier_name': [f'Synthetic Supplier {i:03d}' for i in range(1, 251)],
    'region': rng.choice(regions, 250, p=[.35, .25, .30, .10]),
    'category': rng.choice(categories, 250),
    'contracted': rng.choice([True, False], 250, p=[.75, .25]),
})
# Fictional supplier identity for portfolio demonstration
suppliers.loc[suppliers['supplier_id'] == 'SUP-016', 'supplier_name'] = 'KG Soundworks'
suppliers.to_csv(ROOT / 'suppliers.csv', index=False)
weights = rng.pareto(1.6, 250) + .2
weights /= weights.sum()
selected = rng.choice(supplier_ids, n, p=weights)
dates = pd.Timestamp('2025-01-01') + pd.to_timedelta(rng.integers(0, 365, n), unit='D')
amounts = np.round(rng.lognormal(7.2, 1.0, n), 2)
invoices = [f'INV-{i:06d}' for i in range(1, n+1)]
# Inject a small number of intentional duplicate invoice identifiers for testing.
for i in range(150, 180):
    selected[i] = selected[i-100]
    invoices[i] = invoices[i-100]
transactions = pd.DataFrame({
    'transaction_id': [f'TXN-{i:06d}' for i in range(1, n+1)],
    'invoice_id': invoices,
    'supplier_id': selected,
    'invoice_date': dates,
    'amount_usd': amounts,
})
transactions.to_csv(ROOT / 'transactions.csv', index=False)
print(f'Generated {len(suppliers):,} suppliers and {len(transactions):,} transactions')
