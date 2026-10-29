"""Validate, analyze, and visualize synthetic sourcing data."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'
OUT.mkdir(exist_ok=True)
suppliers = pd.read_csv(ROOT / 'suppliers.csv')
tx = pd.read_csv(ROOT / 'transactions.csv', parse_dates=['invoice_date'])
required = {'transaction_id', 'invoice_id', 'supplier_id', 'invoice_date', 'amount_usd'}
if not required.issubset(tx.columns):
    raise ValueError(f'Missing columns: {required - set(tx.columns)}')
if tx['transaction_id'].duplicated().any():
    raise ValueError('Duplicate transaction IDs')
if tx['amount_usd'].isna().any() or (tx['amount_usd'] <= 0).any():
    raise ValueError('Missing or nonpositive transaction amounts')
if not tx['supplier_id'].isin(suppliers['supplier_id']).all():
    raise ValueError('Transactions contain unknown supplier IDs')
df = tx.merge(suppliers, on='supplier_id', validate='many_to_one')
spend = df.groupby(['supplier_id', 'supplier_name'], as_index=False)['amount_usd'].sum().sort_values('amount_usd', ascending=False)
spend['share_pct'] = spend['amount_usd'] / spend['amount_usd'].sum() * 100
spend['cumulative_share_pct'] = spend['share_pct'].cumsum()
spend.to_csv(OUT / 'supplier_spend.csv', index=False)
category = df.groupby('category')['amount_usd'].sum().sort_values(ascending=False)
category.rename('spend_usd').to_csv(OUT / 'category_spend.csv')
# Same supplier + invoice ID is a review flag, not proof of duplicate payment.
duplicate = df[df.duplicated(['supplier_id', 'invoice_id'], keep=False)].sort_values(['supplier_id', 'invoice_id'])
duplicate.to_csv(OUT / 'duplicate_invoice_flags.csv', index=False)
# Supplier-level exposure >10% of total spend; threshold is illustrative.
concentration = spend[spend['share_pct'] > 10]
concentration.to_csv(OUT / 'concentration_flags.csv', index=False)
# Uncontracted spend is an opportunity indicator, not guaranteed savings.
uncontracted = df.loc[~df['contracted'], 'amount_usd'].sum()
scenario_savings = uncontracted * .03
summary = pd.DataFrame([{
    'total_spend_usd': round(df['amount_usd'].sum(), 2),
    'active_suppliers': df['supplier_id'].nunique(),
    'top_10_supplier_spend_pct': round(spend.head(10)['share_pct'].sum(), 2),
    'flagged_invoice_rows': len(duplicate),
    'flagged_invoice_pairs': duplicate[['supplier_id', 'invoice_id']].drop_duplicates().shape[0],
    'uncontracted_spend_usd': round(uncontracted, 2),
    'illustrative_savings_at_3pct_usd': round(scenario_savings, 2),
}])
summary.to_csv(OUT / 'executive_summary.csv', index=False)

# EXECUTIVE SAVINGS OPPORTUNITY MODEL
# Synthetic scenarios, not realized or guaranteed savings.

total_spend = df['amount_usd'].sum()
off_contract = df.loc[~df['contracted']].copy()

scenarios = {
    'Conservative': {'addressable_pct': 0.25, 'savings_rate': 0.02},
    'Moderate': {'addressable_pct': 0.50, 'savings_rate': 0.05},
    'Ambitious': {'addressable_pct': 0.75, 'savings_rate': 0.08},
}

scenario_rows = []

for name, assumptions in scenarios.items():
    addressable = uncontracted * assumptions['addressable_pct']
    savings = addressable * assumptions['savings_rate']

    scenario_rows.append({
        'scenario': name,
        'addressable_spend_usd': round(addressable, 2),
        'estimated_savings_usd': round(savings, 2),
        'savings_pct_total_spend': round(savings / total_spend * 100, 2),
    })

savings_df = pd.DataFrame(scenario_rows)
savings_df.to_csv(OUT / 'savings_scenarios.csv', index=False)

# Rank categories by potential off-contract savings.
category_opportunities = (
    off_contract.groupby('category', as_index=False)['amount_usd']
    .sum()
    .rename(columns={'amount_usd': 'off_contract_spend_usd'})
)

category_opportunities['estimated_savings_usd'] = (
    category_opportunities['off_contract_spend_usd'] * 0.50 * 0.05
)

category_opportunities = category_opportunities.sort_values(
    'estimated_savings_usd', ascending=False
)

category_opportunities['priority_rank'] = range(
    1, len(category_opportunities) + 1
)

category_opportunities.to_csv(
    OUT / 'sourcing_opportunities.csv', index=False
)

print('\nEXECUTIVE SAVINGS SCENARIOS')
print(savings_df.to_string(index=False))

print('\nTOP SOURCING OPPORTUNITIES')
print(category_opportunities.head(5).to_string(index=False))

# EXECUTIVE PROCUREMENT DASHBOARD
# Synthetic demonstration data. Savings are illustrative.

from matplotlib.ticker import FuncFormatter
total_spend = df['amount_usd'].sum()
off_contract_pct = uncontracted / total_spend * 100
moderate_savings = savings_df.loc[
    savings_df['scenario'] == 'Moderate',
    'estimated_savings_usd'
].iloc[0]
