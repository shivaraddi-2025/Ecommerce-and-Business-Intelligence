# E-Commerce Dataset Profile

- Rows: **6,040**
- Columns: **17**
- Date range: **2023-01-01 to 2025-12-31**
- Expected schema match: **True**

## Quality Findings

- Exact Duplicate Rows: **39**
- Duplicate Order Ids: **40**
- Invalid Dates: **0**
- Nonpositive Quantity: **0**
- Negative Sales: **0**
- Negative Profit: **485**
- Invalid Discount: **0**
- Invalid Return Status: **0**
- Missing Customer Name: **30**
- Inconsistent Region Case: **60**

## Column Profile

| column | dtype | row_count | missing_count | missing_percent | unique_count | duplicate_value_count |
| --- | --- | --- | --- | --- | --- | --- |
| Order ID | object | 6040 | 0 | 0.0 | 6000 | 40 |
| Order Date | object | 6040 | 0 | 0.0 | 1093 | 4947 |
| Customer ID | object | 6040 | 0 | 0.0 | 800 | 5240 |
| Customer Name | object | 6040 | 30 | 0.4967 | 340 | 5700 |
| Product ID | object | 6040 | 0 | 0.0 | 5112 | 928 |
| Product Name | object | 6040 | 0 | 0.0 | 53 | 5987 |
| Category | object | 6040 | 0 | 0.0 | 5 | 6035 |
| Sub-Category | object | 6040 | 0 | 0.0 | 20 | 6020 |
| Region | object | 6040 | 0 | 0.0 | 8 | 6032 |
| State | object | 6040 | 0 | 0.0 | 14 | 6026 |
| City | object | 6040 | 0 | 0.0 | 29 | 6011 |
| Quantity | int64 | 6040 | 0 | 0.0 | 7 | 6033 |
| Sales | float64 | 6040 | 0 | 0.0 | 5995 | 45 |
| Profit | float64 | 6040 | 0 | 0.0 | 5981 | 59 |
| Discount | float64 | 6040 | 60 | 0.9934 | 8 | 6032 |
| Shipping Mode | object | 6040 | 0 | 0.0 | 4 | 6036 |
| Return Status | object | 6040 | 0 | 0.0 | 2 | 6038 |

## Category Summary

| Category | records | sales | profit |
| --- | --- | --- | --- |
| Electronics | 1678 | 179696482.15 | 20164220.0 |
| Furniture | 1084 | 49425772.93 | 3758637.74 |
| Home & Kitchen | 902 | 13070514.38 | 1586462.36 |
| Clothing | 1367 | 10135784.28 | 2075839.02 |
| Office Supplies | 1009 | 3813983.91 | 678456.87 |