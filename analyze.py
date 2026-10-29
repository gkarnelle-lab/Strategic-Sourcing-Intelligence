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
NAVY = '#17324D'
TEAL = '#197F8C'
GOLD = '#D99A36'
GRAY = '#66788A'

fig = plt.figure(figsize=(16, 11), facecolor='#F5F7FA')

fig.text(
    .06, .955,
    'STRATEGIC SOURCING | EXECUTIVE INTELLIGENCE',
    fontsize=20, fontweight='bold', color=NAVY
)
fig.text(
    .06, .923,
    '2025 Procurement Cost Optimization | Synthetic Data',
    fontsize=11, color=GRAY
)

# Executive KPI cards
kpis = [
    ('TOTAL PROCUREMENT SPEND', total_spend, 'money'),
    ('OFF-CONTRACT SPEND', uncontracted, 'money'),
    ('OFF-CONTRACT SHARE', off_contract_pct, 'percent'),
    ('MODERATE SAVINGS CASE', moderate_savings, 'money')
]

for i, (label, value, kind) in enumerate(kpis):
    x = .06 + i * .235
    ax = fig.add_axes([x, .79, .215, .105])
    ax.set_facecolor('white')
    ax.set_xticks([])
    ax.set_yticks([])

    for spine in ax.spines.values():
        spine.set_visible(False)

    display = (
        f'${value / 1e6:,.2f}M'
        if kind == 'money' and value >= 1e6
        else f'${value / 1000:,.1f}K'
        if kind == 'money'
        else f'{value:.1f}%'
    )

    ax.text(.05, .70, label, transform=ax.transAxes,
            fontsize=9, color=GRAY, fontweight='bold')
    ax.text(.05, .18, display, transform=ax.transAxes,
            fontsize=23, color=TEAL, fontweight='bold')

# Savings scenarios
ax1 = fig.add_axes([.08, .43, .39, .29])
ax1.set_facecolor('white')
colors = ['#A6C5CA', TEAL, GOLD]

bars = ax1.bar(
    savings_df['scenario'],
    savings_df['estimated_savings_usd'],
    color=colors,
    width=.58
)

ax1.set_title(
    '01 | Annual Savings Scenarios',
    loc='left', fontweight='bold', color=NAVY, pad=15
)
ax1.yaxis.set_major_formatter(
    FuncFormatter(lambda x, pos: f'${x / 1000:,.0f}K')
)
ax1.spines[['top', 'right']].set_visible(False)

for bar in bars:
    height = bar.get_height()
    ax1.text(
        bar.get_x() + bar.get_width() / 2,
        height + 5000,
        f'${height / 1000:,.1f}K',
        ha='center', fontsize=10, fontweight='bold'
    )

ax1.set_ylim(
    0, savings_df['estimated_savings_usd'].max() * 1.22
)

# Ranked sourcing opportunities
ax2 = fig.add_axes([.57, .43, .37, .29])
ax2.set_facecolor('white')

top = category_opportunities.head(5).iloc[::-1]

ax2.barh(
    top['category'],
    top['estimated_savings_usd'],
    color=TEAL
)

ax2.set_title(
    '02 | Top Sourcing Opportunities',
    loc='left', fontweight='bold', color=NAVY, pad=15
)
ax2.xaxis.set_major_formatter(
    FuncFormatter(lambda x, pos: f'${x / 1000:,.0f}K')
)
ax2.spines[['top', 'right']].set_visible(False)

for i, value in enumerate(top['estimated_savings_usd']):
    ax2.text(
        value + 500, i,
        f'${value / 1000:,.1f}K',
        va='center', fontsize=9
    )

ax2.set_xlim(
    0, top['estimated_savings_usd'].max() * 1.28
)

# Executive recommendations
ax3 = fig.add_axes([.06, .10, .88, .24])
ax3.set_facecolor('white')
ax3.set_xticks([])
ax3.set_yticks([])

for spine in ax3.spines.values():
    spine.set_visible(False)

ax3.text(
    .025, .83, '03 | EXECUTIVE RECOMMENDATIONS',
    fontsize=13, fontweight='bold', color=NAVY,
    transform=ax3.transAxes
)

recommendations = [
    'PRIORITY 1  |  Review off-contract Professional Services spend.',
    'PRIORITY 2  |  Evaluate MRO and Packaging for negotiated agreements.',
    'PRIORITY 3  |  Establish monthly contract coverage and savings KPIs.'
]

for i, recommendation in enumerate(recommendations):
    ax3.text(
        .035, .60 - i * .20,
        recommendation, fontsize=11, color=NAVY,
        transform=ax3.transAxes
    )

fig.text(
    .06, .055,
    'Savings assumptions: 25% / 50% / 75% addressable spend; '
    '2% / 5% / 8% savings rates.',
    fontsize=9, color=GRAY
)
fig.text(
    .06, .035,
    'Illustrative opportunities only. No realized savings or '
    'validated supplier negotiations are implied.',
    fontsize=9, color=GRAY
)

fig.savefig(
    OUT / 'sourcing_dashboard.png',
    dpi=180, bbox_inches='tight',
    facecolor=fig.get_facecolor()
)
plt.close(fig)

print(summary.to_string(index=False))
print('Executive dashboard and reports saved in outputs/')
