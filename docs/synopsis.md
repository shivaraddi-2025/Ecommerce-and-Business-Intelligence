# Project Synopsis

## 1. Title

**E-commerce Sales and Business Intelligence Decision Support System**

## 2. Student and Course

- **Degree:** Master of Computer Applications (MCA)
- **Project Type:** Final-year major project
- **Domain:** E-commerce analytics, business intelligence, machine learning, and decision support systems

## 3. Abstract

The proposed project is an enterprise-style analytics and decision support system for e-commerce businesses. The system converts raw transaction data into meaningful descriptive, diagnostic, predictive, and prescriptive insights. It helps management understand sales performance, profitability, customer behavior, product contribution, regional performance, return risk, and business opportunities.

The project uses an actual e-commerce transaction dataset containing 80,000 records and 20 source attributes, including order date/time, customer segment, product category, quantity, prices, discounts, payment method, region, city, and order status. The data pipeline normalizes these source fields for the dashboard, performs validation and quality analysis, and derives daily aggregates. A Python and Pandas analytics layer provides KPIs, monthly trends, category performance, product rankings, customer analysis, recommendations, and data-quality indicators. The source dataset does not contain cost or profit fields, so profit is estimated transparently at a 30% planning margin and marked as estimated.

A FastAPI backend exposes secure REST endpoints, while a responsive web dashboard provides interactive filters, KPI cards, bar charts, customer intelligence, recommendation views, prediction controls, and data-quality monitoring. The proposed extended system includes customer segmentation, sales forecasting, return prediction, profit prediction, anomaly detection, automated reports, Power BI integration, explainable AI, and management recommendations.

The system is designed to support evidence-based business decisions by answering four questions: what happened, why it happened, what is likely to happen next, and what action should be taken.

## 4. Introduction

E-commerce organizations generate large volumes of transaction data through orders, customers, products, locations, discounts, shipping methods, and returns. Raw data alone does not provide sufficient insight for strategic decision-making. Managers need a unified system that can measure performance, identify causes, predict future outcomes, and recommend practical actions.

This project develops a modular E-commerce Sales and Business Intelligence Decision Support System. It combines data engineering, SQL, Python analytics, machine learning, REST APIs, and interactive visualization in a single platform.

## 5. Problem Statement

Many small and medium e-commerce businesses rely on spreadsheets or isolated reports. These approaches make it difficult to:

- Monitor sales and profit from a single source
- Identify loss-making products and categories
- Understand customer value and retention risk
- Compare regional and monthly performance
- Detect the business effect of discounts and returns
- Predict future sales and potential returns
- Provide timely and explainable recommendations

The absence of an integrated decision support platform can lead to delayed decisions, inefficient promotions, avoidable losses, and poor customer targeting.

## 6. Proposed Solution

The proposed system will provide an integrated analytics platform with the following capabilities:

1. Validate and profile raw transaction data.
2. Clean, standardize, and prepare analytical datasets.
3. Store normalized business data and analytical facts.
4. Generate descriptive and diagnostic business analytics.
5. Segment customers using RFM analysis and clustering.
6. Forecast future sales using evaluated forecasting models.
7. Predict return probability and expected profit.
8. Recommend products using popularity and customer purchase behavior.
9. Identify anomalies, loss-making products, and high-risk areas.
10. Present results through REST APIs, a web dashboard, and Power BI.
11. Generate explainable business insights and management recommendations.

## 7. Dataset Summary

The primary dataset is an 80,000-order e-commerce transaction CSV file with the following source attributes:

- order_id
- order_date
- order_datetime
- day_of_week
- month
- year
- customer_id
- customer_segment
- product_category
- product_name
- quantity
- unit_price
- gross_amount
- discount_pct
- discount_amount
- net_amount
- payment_method
- region
- city
- order_status

Initial profiling identified:

- 80,000 records
- 20 source columns
- Date range from January 1, 2023 to December 31, 2025
- 11,984 unique customers
- 7 product categories
- 4 regions
- 11,427 returned orders
- 45,904 delivered orders
- 11,473 pending orders
- 11,196 cancelled orders
- Net sales of approximately ₹444.03 million

These findings form the data-quality baseline for subsequent processing.

## 8. Objectives

### Primary Objective

To design and implement an integrated e-commerce analytics and business intelligence system that transforms transaction data into actionable management decisions.

### Secondary Objectives

- Build a reusable data-validation and preprocessing pipeline.
- Generate reliable sales, profit, customer, product, regional, and return metrics.
- Design a normalized relational database and analytical star schema.
- Apply machine learning to forecasting, classification, segmentation, and regression problems.
- Provide interactive dashboard-based exploration for business users.
- Implement authentication and role-based API access.
- Produce explainable, data-backed business recommendations.
- Improve decision speed and reduce dependence on manual spreadsheet analysis.

## 9. Scope of the Project

### In Scope

- CSV ingestion and data-quality profiling
- Data cleaning and feature engineering
- Sales and profit analytics
- Customer and product analysis
- Return and discount analysis
- RFM customer segmentation
- Sales forecasting
- Return and profit prediction
- Recommendation generation
- REST API development
- Interactive web dashboard
- SQL database and analytical views
- Power BI dashboard design
- Automated insight and report generation
- Testing and project documentation

### Out of Scope

- Processing real-time payment transactions
- Direct integration with a live e-commerce marketplace
- Automatic execution of pricing or marketing campaigns
- Financial accounting or statutory reporting
- Production cloud deployment in the academic prototype phase

## 10. System Modules

### 10.1 Data Engineering Module

Reads the raw CSV, validates the expected schema, identifies missing values and duplicates, parses dates, validates numeric fields, standardizes categories and regions, and produces quality reports.

### 10.2 Database Module

Stores customers, products, categories, locations, orders, order items, returns, and sales facts in normalized relational tables. Analytical views support monthly sales, category performance, product performance, and return analysis.

### 10.3 Business Analytics Module

Provides KPIs and trends such as total sales, profit, orders, customers, quantity, average order value, profit margin, return rate, monthly performance, and category contribution.

### 10.4 Customer Intelligence Module

Calculates Recency, Frequency, and Monetary values. Customer segments may include VIP, loyal, regular, new, at-risk, and lost customers.

### 10.5 Product and Profitability Module

Ranks products by sales and profit, identifies loss-making products, calculates margins, measures discount impact, and supports ABC and Pareto analysis.

### 10.6 Predictive Analytics Module

Uses supervised machine learning and time-series methods for sales forecasting, return classification, and expected-profit regression. Models are evaluated using appropriate validation metrics.

### 10.7 Recommendation Module

Generates popularity-based and customer-aware product recommendations using sales, units, profit, purchase history, category, and product similarity.

### 10.8 Web Dashboard Module

Provides a responsive interface with authentication, KPI cards, filters, bar charts, trend charts, category analysis, customer tables, recommendations, data quality monitoring, and prediction controls.

### 10.9 Reporting and Recommendation Module

Creates business summaries, downloadable reports, automated insights, KPI alerts, and management recommendations based on calculated values.

## 11. System Architecture

```text
Raw CSV Dataset
      |
      v
Data Validation and Profiling
      |
      v
Cleaning and Feature Engineering
      |
      +------------------+
      |                  |
      v                  v
SQL Database        Analytical DataFrames
      |                  |
      +--------+---------+
               |
               v
        Machine Learning Layer
               |
               v
        FastAPI REST Services
               |
      +--------+---------+
      |                  |
      v                  v
Interactive Web       Power BI
Dashboard             Reports
```

## 12. Technologies Used

- **Programming language:** Python
- **Data processing:** Pandas, NumPy
- **Visualization:** Matplotlib, Seaborn, Chart.js, Power BI
- **Machine learning:** Scikit-learn
- **Backend:** FastAPI and Uvicorn
- **Database:** MySQL
- **API security:** Password hashing, signed tokens, role-based authorization
- **Testing:** Pytest and FastAPI TestClient
- **Documentation:** Markdown and diagrams
- **Development environment:** Visual Studio Code

## 13. Methodology

1. Inspect the actual dataset and document its structure.
2. Generate the baseline data-quality report.
3. Validate schema, types, identifiers, dates, numeric fields, and business rules.
4. Clean duplicates, missing values, inconsistent text, and invalid records according to documented rules.
5. Engineer date, customer, product, profitability, return, and growth features.
6. Load normalized records into the database and create analytical views.
7. Perform exploratory data analysis using statistical summaries and visualizations.
8. Train and compare segmentation, forecasting, classification, and regression models.
9. Evaluate models with reproducible metrics.
10. Expose analytical services through REST APIs.
11. Present insights through the responsive web dashboard and Power BI.
12. Test data processing, APIs, authentication, database operations, and user workflows.

## 14. Machine Learning Methodology

### Customer Segmentation

RFM features will be scaled and clustered using K-Means. The elbow method and silhouette score will support the selection of a suitable cluster count. PCA will be used for visual cluster interpretation.

### Sales Forecasting

Historical sales will be aggregated by day or month. At least two approaches will be compared, such as a regression-based model and a time-series model. MAE, RMSE, MAPE, and R2 where appropriate will guide model selection.

### Return Prediction

Return Status will be used as the classification target. Candidate models include Logistic Regression, Decision Tree, Random Forest, and Gradient Boosting. Accuracy, precision, recall, F1 score, ROC-AUC, and a confusion matrix will be reported.

### Profit Prediction

Expected profit will be treated as a regression target using quantity, sales, discount, product, category, region, shipping mode, and customer-related features. MAE, RMSE, and R2 will be used for comparison.

### Explainable AI

Important prediction factors will be presented to users. Where practical, feature importance or SHAP-based explanations will be used to explain model outputs in business terms.

## 15. Functional Requirements

- The system shall load the supplied e-commerce CSV dataset.
- The system shall generate a data-quality report.
- The system shall calculate sales and profitability KPIs.
- The system shall support filtering by region and category.
- The system shall display monthly sales and profit bar charts.
- The system shall display product and customer rankings.
- The system shall provide recommendation results.
- The system shall provide prediction inputs and outputs.
- The system shall authenticate users.
- The system shall restrict administrative operations by role.
- The system shall expose analytical REST APIs.
- The system shall generate business insights from actual data.

## 16. Non-functional Requirements

- **Accuracy:** Analytics must be calculated from validated source data.
- **Security:** Passwords and secrets must not be hard-coded.
- **Performance:** Common dashboard requests should return quickly for the project dataset.
- **Usability:** The interface must be understandable to managers and analysts.
- **Maintainability:** Modules should be separated by responsibility.
- **Scalability:** The design should support migration from CSV processing to MySQL and cloud deployment.
- **Reliability:** Invalid input and API errors should be handled clearly.
- **Explainability:** Predictions should include understandable contributing factors.

## 17. Expected Outcomes

The completed system is expected to provide:

- A trusted data-quality baseline
- Faster access to business KPIs
- Identification of high-performing and loss-making products
- Improved understanding of customer segments
- Early visibility of return risk
- Sales and profit forecasts for planning
- Product recommendations for promotions
- Evidence-based management recommendations
- A reusable foundation for future cloud and Power BI deployment

## 18. Advantages

- Integrates data engineering, analytics, machine learning, and visualization.
- Uses actual business transaction data rather than fabricated results.
- Supports descriptive, diagnostic, predictive, and prescriptive analytics.
- Reduces manual spreadsheet work.
- Provides role-aware access to analytical services.
- Helps management connect operational metrics with actions.
- Demonstrates practical application of MCA-level technologies.

## 19. Limitations

- The quality of predictions depends on historical data quality and feature availability.
- The dataset does not contain all possible business factors, such as advertising cost, inventory, payment failures, or customer feedback.
- Forecasts may be less reliable during unusual market conditions.
- The academic prototype is not a replacement for a production data warehouse.
- Production deployment requires stronger secret management, persistent user storage, monitoring, and database operations.

## 20. Future Enhancements

- Deploy the application on Azure or another cloud platform.
- Add persistent MySQL user and model-registry storage.
- Add scheduled data ingestion and report delivery.
- Add cohort and retention analysis.
- Add scenario simulation for discount and pricing decisions.
- Add natural-language business assistant backed by safe analytical queries.
- Add SHAP explanations and model drift monitoring.
- Add Power BI semantic models and row-level security.
- Add inventory and marketing data integrations.
- Add automated email alerts for KPI anomalies.

## 21. Project Schedule

| Phase | Work | Duration |
| --- | --- | --- |
| 1 | Dataset inspection and profiling | Week 1 |
| 2 | Data cleaning and feature engineering | Weeks 2-3 |
| 3 | Database schema and SQL analytics | Week 4 |
| 4 | Exploratory data analysis | Week 5 |
| 5 | Customer segmentation | Week 6 |
| 6 | Forecasting and prediction models | Weeks 7-8 |
| 7 | Recommendation and anomaly modules | Week 9 |
| 8 | FastAPI services and security | Week 10 |
| 9 | Dashboard and Power BI design | Weeks 11-12 |
| 10 | Testing, documentation, and presentation | Weeks 13-14 |

## 22. Deliverables

- Source code
- Raw, processed, and feature datasets
- Data-quality reports
- SQL schema and analytical views
- EDA and machine-learning notebooks
- Trained model artifacts and evaluation reports
- FastAPI backend
- Interactive web dashboard
- Power BI dashboard documentation
- Test cases and test results
- Technical documentation
- Final project report and presentation

## 23. Conclusion

The E-commerce Sales and Business Intelligence Decision Support System provides a complete academic and practical framework for converting transaction data into management intelligence. It combines data quality, analytics, machine learning, APIs, security, visualization, and recommendations in a modular platform. The project demonstrates how an e-commerce business can move from raw data to measurable insights and informed decisions through a single integrated system.

## 24. References

1. Wes McKinney, *Python for Data Analysis*, O'Reilly Media.
2. Scikit-learn User Guide, https://scikit-learn.org/stable/user_guide.html
3. Pandas Documentation, https://pandas.pydata.org/docs/
4. NumPy Documentation, https://numpy.org/doc/
5. FastAPI Documentation, https://fastapi.tiangolo.com/
6. MySQL 8.0 Reference Manual, https://dev.mysql.com/doc/
7. Microsoft Power BI Documentation, https://learn.microsoft.com/power-bi/
8. CRISP-DM: Cross-Industry Standard Process for Data Mining.
