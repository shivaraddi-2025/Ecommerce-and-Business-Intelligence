from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path('data/raw/ecommerce_sales_raw.csv')
OUT = Path('data/raw/daily_sales_dataset.csv')


START_DATE = pd.Timestamp('2024-01-01')
END_DATE = pd.Timestamp('2026-12-31')


def synthesize_daily(row: pd.Series) -> pd.Series:
    """Create a deterministic synthetic daily record for a calendar date without raw order rows."""
    date = pd.Timestamp(row['Order Date'])
    days = (date - START_DATE).days
    year = date.year
    year_factor = 1 + (year - 2024) * 0.12
    month_factor = 1 + 0.03 * np.sin(date.month / 12 * np.pi * 2)
    weekday = date.dayofweek
    weekday_factor = {
        0: 1.08,
        1: 1.10,
        2: 1.12,
        3: 1.09,
        4: 1.14,
        5: 0.96,
        6: 0.86,
    }[weekday]
    trend = 1 + (days / max(1, (END_DATE - START_DATE).days)) * 0.18
    baseline_sales = 25000 * year_factor * month_factor * weekday_factor * trend
    sales = round(baseline_sales, 2)
    profit = round(sales * (0.26 + 0.04 * np.sin(date.day / 31 * np.pi)), 2)
    orders = int(round(sales / 350))
    orders = max(orders, 1)
    return_rate = round(4.0 + (weekday % 4) * 1.2 + 2.2 * abs(np.sin(date.day / 31 * np.pi)), 2)
    return_orders = int(round(orders * return_rate / 100))

    return pd.Series({
        'Order Date': date,
        'sales': sales,
        'profit': profit,
        'orders': orders,
        'return_orders': return_orders,
        'return_rate': return_rate,
    })


def main() -> None:
    frame = pd.read_csv(SRC)
    frame['Order Date'] = pd.to_datetime(frame['Order Date'], errors='coerce')
    frame = frame.dropna(subset=['Order Date']).copy()

    # Aggregate the raw ecommerce source to one row per calendar day.
    raw_daily = frame.groupby(frame['Order Date'].dt.normalize(), as_index=False).agg(
        sales=('Sales', 'sum'),
        profit=('Profit', 'sum'),
        orders=('Order ID', 'nunique'),
        return_orders=('Return Status', lambda s: s.eq('Returned').sum()),
    )

    raw_daily['Order Date'] = pd.to_datetime(raw_daily['Order Date'], errors='coerce').dt.normalize()
    raw_daily['return_rate'] = np.where(
        raw_daily['orders'] == 0,
        0,
        (raw_daily['return_orders'] / raw_daily['orders'] * 100).round(2),
    )

    # Create one row for every date from 2024-01-01 through 2026-12-31.
    serial_dates = pd.date_range(START_DATE, END_DATE, freq='D')
    serial = pd.DataFrame({'Order Date': serial_dates})

    # Merge the real raw rows into the calendar series.
    daily = serial.merge(raw_daily, on='Order Date', how='left')

    # Synthetic rows for dates missing from the source materialize the datewise product line.
    missing_mask = daily['sales'].isna() | daily['profit'].isna() | daily['orders'].isna()
    if missing_mask.any():
        synthetic = daily.loc[missing_mask].copy()
        for idx, row in synthetic.iterrows():
            out = synthesize_daily(row)
            daily.loc[idx, 'sales'] = out['sales']
            daily.loc[idx, 'profit'] = out['profit']
            daily.loc[idx, 'orders'] = out['orders']
            daily.loc[idx, 'return_orders'] = out['return_orders']
            daily.loc[idx, 'return_rate'] = out['return_rate']

    # Fill the remaining nulls defensively.
    daily['sales'] = daily['sales'].fillna(0).round(2)
    daily['profit'] = daily['profit'].fillna(0).round(2)
    daily['orders'] = daily['orders'].fillna(0).astype(int)
    daily['return_orders'] = daily['return_orders'].fillna(0).astype(int)
    daily['return_rate'] = daily['return_rate'].fillna(0).round(2)

    # Snap to the required output contract.
    daily['Order Date'] = daily['Order Date'].dt.strftime('%Y-%m-%d')
    daily = daily.sort_values('Order Date').reset_index(drop=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(OUT, index=False)
    print(f'Wrote {len(daily)} daily rows to {OUT}')


if __name__ == '__main__':
    main()

