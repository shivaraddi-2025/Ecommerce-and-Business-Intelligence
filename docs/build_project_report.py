from __future__ import annotations

import html
import json
import zipfile
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "E-Commerce Analytics and Predictive Business Intelligence System - Project Report.docx"
TITLE = "E-Commerce Analytics and Predictive Business Intelligence System"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"


def q(tag: str) -> str:
    return f"{{{W}}}{tag}"


def paragraph(text: str = "", style: str | None = None, *, bold: bool = False, italic: bool = False, align: str | None = None, size: int | None = None, font: str | None = None, color: str | None = None):
    p = Element(q("p"))
    ppr = SubElement(p, q("pPr"))
    if style:
        SubElement(ppr, q("pStyle"), {q("val"): style})
    if align:
        SubElement(ppr, q("jc"), {q("val"): align})
    spacing = SubElement(ppr, q("spacing"))
    spacing.set(q("after"), "120")
    spacing.set(q("line"), "360")
    spacing.set(q("lineRule"), "auto")
    if style and style.startswith("Heading"):
        SubElement(ppr, q("keepNext"))
    for index, line in enumerate(text.split("\n")):
        if index:
            SubElement(p, q("r"))
            SubElement(p[-1], q("br"))
        run = SubElement(p, q("r"))
        rpr = SubElement(run, q("rPr"))
        if font:
            SubElement(rpr, q("rFonts"), {q("ascii"): font, q("hAnsi"): font, q("cs"): font})
        if bold:
            SubElement(rpr, q("b"))
        if italic:
            SubElement(rpr, q("i"))
        if size:
            SubElement(rpr, q("sz"), {q("val"): str(size)})
            SubElement(rpr, q("szCs"), {q("val"): str(size)})
        if color:
            SubElement(rpr, q("color"), {q("val"): color})
        t = SubElement(run, q("t"))
        if line.startswith(" ") or line.endswith(" "):
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t.text = line
    return p


def table(rows: list[list[str]], widths: list[int] | None = None):
    tbl = Element(q("tbl"))
    tblpr = SubElement(tbl, q("tblPr"))
    SubElement(tblpr, q("tblW"), {q("w"): "0", q("type"): "auto"})
    borders = SubElement(tblpr, q("tblBorders"))
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        SubElement(borders, q(edge), {q("val"): "single", q("sz"): "4", q("space"): "0", q("color"): "9AA7B8"})
    if widths:
        grid = SubElement(tbl, q("tblGrid"))
        for width in widths:
            SubElement(grid, q("gridCol"), {q("w"): str(width)})
    for row_index, values in enumerate(rows):
        tr = SubElement(tbl, q("tr"))
        for col_index, value in enumerate(values):
            tc = SubElement(tr, q("tc"))
            tcpr = SubElement(tc, q("tcPr"))
            if widths and col_index < len(widths):
                SubElement(tcpr, q("tcW"), {q("w"): str(widths[col_index]), q("type"): "dxa"})
            if row_index == 0:
                shade = SubElement(tcpr, q("shd"))
                shade.set(q("fill"), "20304A")
            p = SubElement(tc, q("p"))
            ppr = SubElement(p, q("pPr"))
            SubElement(ppr, q("spacing"), {q("after"): "60", q("line"): "240"})
            run = SubElement(p, q("r"))
            rpr = SubElement(run, q("rPr"))
            if row_index == 0:
                SubElement(rpr, q("b"))
                SubElement(rpr, q("color"), {q("val"): "FFFFFF"})
            SubElement(rpr, q("sz"), {q("val"): "18"})
            t = SubElement(run, q("t"))
            t.text = str(value)
    return tbl


def bullet(text: str):
    p = paragraph("• " + text)
    ppr = p.find(q("pPr"))
    SubElement(ppr, q("ind"), {q("left"): "360", q("hanging"): "180"})
    return p


pages: list[dict] = []


def add(title: str, paragraphs: list[str] | None = None, *, bullets: list[str] | None = None, rows: list[list[str]] | None = None, diagram: str | None = None, kind: str = "content"):
    pages.append({
        "title": title,
        "paragraphs": paragraphs or [],
        "bullets": bullets or [],
        "rows": rows,
        "diagram": diagram,
        "kind": kind,
    })


# Preliminary pages (8)
add(TITLE, ["PROJECT REPORT", "Submitted in partial fulfilment of the requirements for the degree of", "MASTER OF COMPUTER APPLICATIONS (MCA)", "", "Submitted by: [Student Name]", "USN / Registration Number: [USN / Registration Number]", "", "Under the guidance of", "[Project Guide Name]", "", "[Department Name]", "[College Name]", "[University Name]", "", "Project / Company: [Company Name — To be confirmed]", "Internship period: [Start Date] to [End Date — To be confirmed]", "Submission date: [Submission Date]"], kind="cover")
add("Abstract", [
    "E-commerce platforms generate transaction records describing orders, dates, customers, products, quantities, prices, discounts, payment methods, locations and order status. Converting these records into timely decisions requires data preparation, consistent metrics and accessible analysis. Nexus Commerce Intelligence is a browser-based decision-support application that brings together a React dashboard and a Python FastAPI service.",
    "The inspected implementation includes descriptive dashboards for sales, products, customers, regions and segments; data-quality views; reports and exports; daily sales forecasting; anomaly views; recommendations; data import; database status and synchronization; authentication; role-aware user administration; and browser-local audit events. Analytics are produced through Pandas and NumPy, with scikit-learn and XGBoost available for selected analytical paths. MySQL is the preferred user-account backend, with SQLite fallback behavior.",
    "Profit values require careful interpretation. When the source dataset lacks actual cost and profit, the analytics engine derives a planning estimate using a 30% margin. That output must not be treated as audited accounting profit. Feature completion, predictive accuracy, production deployment, and business impact require additional verification. Company, student, institutional, and guide details are placeholders because they were not supplied."
], kind="preliminary")
add("Acknowledgement", [
    "I would like to express my sincere gratitude to [Project Guide Name] for guidance, feedback, and encouragement during the development and documentation of this project. I also thank the faculty members of [Department Name], [College Name], and [University Name] for the academic support and learning opportunities provided during the MCA programme.",
    "I acknowledge the creators and maintainers of the open-source technologies used in this work, including React, Vite, FastAPI, Python, Pandas, NumPy, scikit-learn, XGBoost, Chart.js, SQLAlchemy, MySQL, and SQLite. Their documentation and software make it possible to build and study integrated analytics systems.",
    "Finally, I thank my family, friends, and everyone who provided feedback or encouragement. Names and acknowledgements should be reviewed and updated to reflect the actual contributions made to this project."
], kind="preliminary")
add("Certificate from Company", [
    "This page is reserved for the company certificate, if one is required by the institution and was actually issued by the organization.",
    "Company name: [Company Name — To be confirmed]",
    "Authorized signatory: [Name and designation — To be confirmed]",
    "Certificate text: [Insert the original, approved certificate wording here.]",
    "Do not treat this placeholder as a certificate. Do not add a company seal, signature, dates, or claims of internship completion unless the organization has verified and authorized them."
], kind="preliminary")
add("Student Declaration", [
    "I, [Student Name], declare that the report titled “E-Commerce Analytics and Predictive Business Intelligence System” is prepared for submission toward the Master of Computer Applications degree at [College Name], [University Name].",
    "I will verify that the report accurately identifies work performed by me and distinguishes it from third-party libraries, prior work, project documentation, and proposed enhancements. I will ensure citations are accurate and that no confidential credentials or personal information are disclosed.",
    "Student signature: ______________________________",
    "USN / Registration Number: [USN / Registration Number]",
    "Place: [Place — To be confirmed]     Date: [Date — To be confirmed]"
], kind="preliminary")
add("Table of Contents", [
    "Preliminary pages — 1–8",
    "Chapter 1: Introduction — 9–12",
    "Chapter 2: Company Profile — 13–16",
    "Chapter 3: Scope of the System — 17–21",
    "Chapter 4: System Analysis — 22–29",
    "Chapter 5: Planning and Requirements — 30–36",
    "Chapter 6: System Design — 37–48",
    "Chapter 7: Application Screenshots — 49–56",
    "Chapter 8: Software Testing — 57–63",
    "Chapter 9: Conclusion — 64–65",
    "Chapter 10: Limitations — 66–67",
    "Chapter 11: Future Enhancements — 68–69",
    "Chapter 12: References — 70–72",
    "Chapter 13: Appendices and User Manual — 73–80",
    "Pagination is explicitly arranged for an 80-page working draft. Word processors can repaginate based on installed fonts, printer settings, and compatibility; refresh this contents page after editing."
], kind="preliminary")
add("List of Figures and Tables", [
    "Figures: 6.1 System context diagram; 6.2 Logical component architecture; 6.3 Level 0 data-flow diagram; 6.4 Analytics data flow; 6.5 Authentication sequence; 6.6 Import activity; 6.7 Forecasting activity; 6.8 Conceptual component deployment; 6.9 Proposed analytical data model.",
    "Application screenshot placeholders: 7.1 Login; 7.2 Overview; 7.3 Sales; 7.4 Profitability; 7.5 Product and customer views; 7.6 Segments and geography; 7.7 Forecasting and anomaly views; 7.8 Data administration and API documentation.",
    "Tables: 4.1 Technology overview; 4.2 Resource recommendations; 5.1 User-role summary; 5.2 Functional requirements; 5.3 Non-functional requirements; 6.1 Verified user table; 6.2 API inventory; 8.1 Executed validation; 8.2–8.5 Test cases; 13.1 Troubleshooting."
], kind="preliminary")
add("List of Abbreviations", rows=[
    ["Abbreviation", "Meaning"],
    ["API", "Application Programming Interface"],
    ["BI", "Business Intelligence"],
    ["CSV", "Comma-Separated Values"],
    ["DFD", "Data-Flow Diagram"],
    ["ERD", "Entity-Relationship Diagram"],
    ["HTTP", "Hypertext Transfer Protocol"],
    ["JSON", "JavaScript Object Notation"],
    ["KPI", "Key Performance Indicator"],
    ["MCA", "Master of Computer Applications"],
    ["ML", "Machine Learning"],
    ["RBAC", "Role-Based Access Control"],
    ["REST", "Representational State Transfer"],
    ["SQL", "Structured Query Language"],
    ["UML", "Unified Modeling Language"],
], kind="preliminary")

# Chapter 1 (4 pages)
add("Chapter 1 — Introduction: Business Context", [
    "Digital commerce produces high-volume, multi-dimensional records. Each order can be examined by time, product, category, customer segment, location, payment method, discount, and fulfilment status. The practical challenge is not merely collecting rows; it is defining trustworthy measures and presenting them in a form that supports decisions.",
    "Business intelligence combines data integration, analysis, and communication. A dashboard can make comparisons more accessible than a collection of independent spreadsheets, but only when its source data, transformations, definitions, and limitations are visible. This project places summary indicators and detailed analytical views in a single browser interface.",
    "The application is intended as a decision-support prototype over transaction data. It is not a payment processor, order-management platform, or audited financial system. Its findings should be used as analytical indicators and checked against the authoritative operational and accounting systems."
])
add("Chapter 1 — Predictive Analytics and Motivation", [
    "Descriptive analytics answers what was observed; diagnostic exploration compares groups and periods; predictive methods estimate possible future outcomes; and prescriptive guidance frames actions for human review. These categories help explain why an integrated dashboard can be useful, while also preventing an unvalidated model output from being mistaken for certainty.",
    "The motivation for the project is to reduce friction between raw transaction files and routine business questions: which categories contribute sales, how do regions compare, what customer groups appear valuable, and which days or outcomes merit investigation? The project combines interactive filtering with backend endpoints so the same analytical service can support several views.",
    "A disciplined implementation must also communicate data constraints. Missing cost data makes estimated margins different from actual profit. Duplicate order identifiers may affect counting. Changes in data format or date range can alter model behavior. The report therefore treats data quality and model validation as part of the system, not as an afterthought."
])
add("Chapter 1 — Objectives and Success Criteria", paragraphs=[
    "The report is organized into chapters covering organizational context, scope, analysis, requirements, architecture, screenshots, testing, conclusions, limitations, future work, references, and operating instructions. This structure separates verified implementation from evaluation and proposed enhancements."
], bullets=[
    "Provide a unified user interface for verified commerce analytics and data-management functions.",
    "Use backend services to validate access and prepare responses for the frontend.",
    "Enable filtering by relevant dimensions such as region, city, category, customer segment, and year where supported.",
    "Present time trends, rankings, quality indicators, recommendations, and predictive views without claiming unmeasured accuracy.",
    "Support controlled account creation and administration according to backend role checks.",
    "Make the application's assumptions and known data limitations visible to users.",
    "Define success as correct, comprehensible behavior demonstrated through tests—not as an assumed improvement in revenue."
])

# Chapter 2 (4 pages)
add("Chapter 2 — Company Profile: Introduction", [
    "Company name: [Company Name — To be confirmed]. This section is intentionally a structured placeholder because no verified company profile or internship record was supplied with the project materials.",
    "The student should insert the organization's legal or commonly used name, a short approved description, location if permitted, and the organizational unit related to the project. Information should come from the organization itself or from an approved public profile. Avoid copying unverified claims or confidential internal material.",
    "If the project was completed as an academic project rather than an industry internship, replace company-specific wording with the institution's project context. This distinction should remain consistent in the title page, certificate, acknowledgements, and declaration."
], kind="chapter")
add("Chapter 2 — Company Background and Activities", [
    "Company background: [To be confirmed from an authorized company source]. Include founding history, business domain, operating regions, and scale only when supported by reliable material and approved for academic use.",
    "Business activities and services: [To be confirmed]. Explain the connection between the organization's actual commerce or analytics processes and the problem addressed by the dashboard. Do not present the project dataset as company production data unless its origin and permission are known.",
    "The system itself analyzes a dataset selected by the application configuration. Its existence does not establish that the company uses it, owns it, or provided it. Record data provenance, permitted use, and anonymization status separately."
])
add("Chapter 2 — Vision, Mission, and Structure", [
    "Vision: [Insert the organization's officially published vision, if applicable]. Mission: [Insert the organization's officially published mission, if applicable]. If these statements are unavailable or the institution does not require them, state that they were not provided rather than composing statements on the organization's behalf.",
    "Organizational structure: [Insert a verified diagram or approved summary]. If the project is academic, a generic stakeholder chart may instead identify the student, project guide, evaluator, and intended dashboard users; label it as a project stakeholder view rather than a company's organization chart.",
    "The intended software roles are not equivalent to company job titles. Application roles such as Admin, Business Manager, Analyst, and Viewer are access-control labels defined in the code; they should not be mapped to organizational positions without an explicit policy."
])
add("Chapter 2 — Project Context and Relevance", [
    "Project guide: [Project Guide Name — To be confirmed]. Internship dates: [Start Date] to [End Date — To be confirmed]. Company mentor: [Name and title — To be confirmed]. No certificate or employment relationship is implied by this template.",
    "The project's relevance is the general need to make transaction analysis easier to navigate and more repeatable. A real organizational benefit must be established by stakeholder interviews, user evaluation, or measured operational evidence. None is assumed in this report.",
    "Before submission, obtain permission for company names, data examples, screenshots, architecture details, and any performance claims. Replace this page with approved context or retain the placeholder if the project has no associated company."
])

# Chapter 3 (5 pages)
add("Chapter 3 — Existing System", [
    "A common baseline in small commerce teams is a set of exported spreadsheets, manually assembled monthly reports, and separate tools for customer, inventory, and sales questions. This description represents a general industry pattern, not a measured assessment of a named organization.",
    "Spreadsheet workflows are flexible and accessible, but repeating the same cleaning steps introduces opportunities for inconsistent filters, duplicated formulas, stale copies, and accidental edits. A report assembled by one analyst may be difficult for another person to reproduce if definitions and data provenance are not documented.",
    "Fragmented reporting also separates the decision from the evidence. A summary total may be visible without its date window, status exclusions, missing-value treatment, or calculation assumptions. The proposed dashboard addresses these risks by placing filters and several analytical views within one application."
])
add("Chapter 3 — Problem Statement", [
    "The project addresses the need for a practical interface that can turn e-commerce transaction data into consistent summaries and allow a user to explore those summaries without manually rebuilding every report.",
    "The system must manage more than visualization: it must prepare data, enforce API authentication, handle invalid inputs, provide understandable error messages, expose quality information, and disclose when metrics are estimates. Predictive screens require special care because a prediction is conditional on data and model assumptions.",
    "The problem is therefore defined as an application engineering problem: integrate data preparation, API access, interactive analytics, user administration, and documented limitations in a maintainable prototype. This report does not claim that the system has been deployed in a business or that it has improved business results."
])
add("Chapter 3 — Proposed System", [
    "The proposed system has a single-page React user interface and a FastAPI backend. The frontend contains module navigation, filters, charts, status controls, forms, and tabular results. The backend exposes endpoints for health, authentication, dashboard KPIs, sales, customers, products, segments, recommendations, forecasts, quality reporting, imports, database operations, and management.",
    "The analytics engine loads a configured dataset, normalizes known field shapes, derives date and return indicators, and prepares daily summaries. Separate API handlers apply filters and return JSON results. User accounts are managed using SQLAlchemy with configured MySQL and SQLite fallback paths.",
    "The design intentionally separates user-facing presentation from data calculations. This improves maintainability and helps focus testing at API, persistence, and browser interaction boundaries, while leaving security review and production deployment as separate activities."
])
add("Chapter 3 — Scope Boundaries", bullets=[
    "In scope: inspectable dashboard pages, filtering, CSV-oriented data handling, analytics APIs, user login, role-aware administration, and development startup.",
    "Out of scope: processing payments, replacing an e-commerce order system, guaranteeing data freshness from a live marketplace, and providing audited financial statements.",
    "Email delivery for invitation messages is not implemented by the invite flow; it creates a user account and requires secure out-of-band credential sharing.",
    "The browser audit stream is local to a browser profile and is not a central compliance log.",
    "Model accuracy and production readiness are not assumed; they require explicit evaluation and operational controls.",
    "Company-specific workflows, security policy, retention policy, and accessibility conformance require stakeholder confirmation."
])
add("Chapter 3 — Benefits, Assumptions, and Constraints", [
    "Potential benefits include faster navigation among related metrics, more consistent analytical views, and clearer visibility into data quality. These are design intentions; they must be evaluated with representative users before being reported as achieved outcomes.",
    "Assumptions include access to a supported CSV input, a configured Python environment, Node.js/npm for the frontend, and local availability of the database configured for the deployment. The application can fall back to SQLite for user accounts when its MySQL path is unavailable.",
    "Constraints include source-data quality, differences between dataset schemas, the absence of verified cost data, dependence on a local API port during development, and limited evidence of system performance under concurrent production load."
])

# Chapter 4 (8 pages)
add("Chapter 4 — Literature Review: Business Intelligence", [
    "Business intelligence systems organize data so that users can monitor indicators and investigate differences. A dashboard should connect each visible metric to a definition, period, source, and update path. Otherwise, visually attractive charts can obscure mismatched calculation rules.",
    "Dimensional analysis is useful for commerce because facts such as sales or order counts are interpreted by dimensions such as date, product, customer, and geography. Kimball and Ross describe dimensional modeling as a way to make analytical data understandable and queryable; their work is a reference for design concepts, not proof that this project implements a complete warehouse.",
    "This project has API-backed analytical views and a database synchronization capability. It should not be characterized as a mature enterprise BI platform or full warehouse unless the data model, refresh strategy, governance, and deployment are verified."
])
add("Chapter 4 — Literature Review: Dashboard Design", [
    "Dashboard design involves selecting a small number of meaningful indicators, arranging comparisons in a readable hierarchy, and supporting a path from summary to detail. Context matters: a revenue figure without time range, currency, or filter state can be misinterpreted.",
    "Interactive filters in the application provide a mechanism to narrow views by selected attributes. They should remain visibly synchronized with chart data and totals. Clear loading, empty, and error states are also important because a blank panel can otherwise be mistaken for an absence of business activity.",
    "For academic evaluation, usability should be assessed with representative users and tasks. This report does not claim a formal usability study was conducted; measures such as task completion, time, and user-reported clarity remain to be collected."
])
add("Chapter 4 — Literature Review: Data Preparation", [
    "Analytical systems depend on preprocessing. Typical tasks include parsing dates, normalizing labels, coercing numeric values, dealing with missing values, identifying duplicates, and deriving features such as month or return flags. Every transformation affects the semantics of downstream measures.",
    "The inspected analytics engine records basic source quality indicators, normalizes a second dataset schema, converts dates and numeric fields, standardizes region and city labels, and derives daily summaries. A profile file also records quality findings for a smaller CSV profile. The report should identify the profile's exact file and avoid assuming it describes every active dataset.",
    "Data validation should distinguish a correction from a measurement. For example, filling missing numeric values with zero is a modeling choice; it does not prove that the original value was zero. A production pipeline should document this decision and preserve raw inputs where retention policy allows."
])
add("Chapter 4 — Literature Review: Predictive Methods", [
    "Forecasting estimates future values from historical patterns. A credible evaluation compares a model against a suitable baseline, uses time-ordered splits, and reports error measures appropriate to the business task. Randomly shuffling time series can leak future information into training and produce misleading results.",
    "The code includes daily aggregation and forecast endpoints, including a comparison endpoint, and imports RandomForestRegressor with optional XGBoost support. These facts describe implementation structure; they do not establish accuracy, stability, or business usefulness.",
    "Before deployment, the forecast horizon, training window, missing dates, outliers, seasonality, and evaluation period must be specified. At minimum, report MAE or another justified measure alongside a naïve baseline, and explain how users should interpret uncertainty."
])
add("Chapter 4 — Literature Review: Anomaly Detection", [
    "An anomaly is an observation that differs from an expected pattern. It may be caused by a real event, a data error, a change in definition, or a normal rare case. A flag is therefore an invitation to investigate rather than evidence of fraud or wrongdoing.",
    "The application exposes a sales anomaly endpoint and an anomaly page. Exact algorithmic thresholds and evaluation evidence should be verified from the relevant implementation before making a claim about detection sensitivity or false-positive rates.",
    "Useful validation involves labeled examples, domain review, threshold analysis, and tracking false positives and missed events. Where labels are unavailable, communicate that detection is exploratory and provide users with the underlying values needed to verify a flag."
])
add("Chapter 4 — Feasibility and Ethics", [
    "Technical feasibility is supported by the use of commonly available open-source tooling and a local development command that starts backend and frontend services. Database connectivity and data availability remain environment-specific dependencies.",
    "Economic feasibility cannot be quantified without labor, hosting, maintenance, and licensing inputs. No savings estimate is included. Operational feasibility depends on users understanding filters, roles, estimates, and the manual credential-sharing step in account invitations.",
    "Ethical and legal considerations include permission to use transaction data, minimizing exposure of customer identifiers, securing credentials, controlling administrative operations, and avoiding consequential decisions based solely on unvalidated predictions."
])
add("Chapter 4 — Tools and Technology", rows=[
    ["Layer", "Technology", "Verified role"],
    ["UI", "React + Vite", "Component-based browser interface and development/build tooling"],
    ["Charts", "Chart.js + react-chartjs-2", "Dashboard chart rendering"],
    ["API", "FastAPI + Uvicorn", "HTTP endpoints and local ASGI server"],
    ["Analytics", "Pandas + NumPy", "Data transformation and calculations"],
    ["ML", "scikit-learn + optional XGBoost", "Selected predictive code paths"],
    ["Persistence", "SQLAlchemy, MySQL, SQLite", "User persistence and fallback selection"],
])
add("Chapter 4 — Resource Requirements", rows=[
    ["Resource", "Minimum / recommendation", "Status"],
    ["OS", "Windows/macOS/Linux supported by toolchains", "Environment-specific"],
    ["Python", "Use installed compatible version; project venv inspected at 3.11", "Verified in this environment"],
    ["Node.js", "Use an active LTS compatible with Vite 5", "Verify on target machine"],
    ["RAM", "8 GB recommended for local analytics", "Recommendation, not benchmark"],
    ["Storage", "Space for dataset, dependencies, and outputs", "Dataset-dependent"],
    ["Database", "MySQL configurable; SQLite fallback", "Verified code paths"],
    ["Browser", "Current Chromium/Firefox/Edge", "Recommendation"],
    ["Editor", "VS Code optional", "Recommendation"],
])

# Chapter 5 (7 pages)
add("Chapter 5 — Product Perspective", [
    "The product is a web application with a Vite development server, React client, FastAPI service, analytics engine, and relational user-account persistence. During development, the Vite proxy forwards `/api` calls to `127.0.0.1:8000`; starting only the frontend causes API connection-refused errors.",
    "The root `npm run dev` script runs the frontend and backend concurrently. The backend health endpoint reports service status, dataset name, record count, and selected authentication database backend. The deployment arrangement outside local development is not verified.",
    "External dependencies include the active dataset, Python packages, Node packages, the selected database configuration, and optionally XGBoost. Failure of an external dependency should be surfaced as an operational state rather than interpreted as valid zero-valued analytics."
])
add("Chapter 5 — User Modules", rows=[
    ["Module", "Purpose", "Status note"],
    ["Overview / Sales", "KPIs, trends, filtered sales and daily views", "API-backed"],
    ["Products / Customers", "Rankings and customer summaries", "API-backed"],
    ["Segments / Geography", "Breakdowns, matrix and regional views", "API-backed"],
    ["Forecast / Anomalies", "Daily forecast and anomaly outputs", "Validate models"],
    ["Quality / Import", "Profile data and upload CSV", "Validate per dataset"],
    ["Export / Reports", "Generate files from API results", "Browser initiated"],
    ["Database", "Show backend status and sync as Admin", "Admin sync"],
    ["Audit / Users", "Browser audit and account administration", "Different persistence scopes"],
])
add("Chapter 5 — User Roles and Permissions", rows=[
    ["Role", "Verified capability summary"],
    ["Admin", "May invite users, assign roles, delete other users, upload or synchronize data where endpoint checks permit."],
    ["Business Manager", "May view user directory and invite non-admin users; backend explicitly blocks inviting Admin role."],
    ["Analyst", "Authenticated analytics access; management endpoints require elevated role."],
    ["Viewer", "Authenticated read-oriented use; cannot invite users."],
    ["Important", "Check each endpoint: frontend visibility is not a security boundary. Backend authorization is authoritative."],
])
add("Chapter 5 — Functional Requirements I", rows=[
    ["ID", "Requirement", "Verification"],
    ["FR-01", "The system shall allow a user to authenticate with registered credentials.", "API present; test specific"],
    ["FR-02", "The system shall deny protected requests without valid authentication.", "Protected endpoint behavior"],
    ["FR-03", "The dashboard shall request KPI and quality data from the API.", "Frontend/API paths present"],
    ["FR-04", "Users shall filter supported analytics by available dimensions.", "Verify each endpoint"],
    ["FR-05", "The application shall provide sales trend, daily, category, and records views.", "Routes present"],
    ["FR-06", "The application shall provide product and customer summaries.", "Routes present"],
])
add("Chapter 5 — Functional Requirements II", rows=[
    ["ID", "Requirement", "Verification"],
    ["FR-07", "The application shall provide segment and geographic breakdowns.", "Routes present"],
    ["FR-08", "The application shall expose daily forecast outputs.", "Model validation pending"],
    ["FR-09", "The application shall expose anomaly and recommendation views.", "Review algorithm outputs"],
    ["FR-10", "The application shall report source data quality indicators.", "Quality endpoint present"],
    ["FR-11", "An Admin shall be able to upload accepted dataset files.", "Tested path exists"],
    ["FR-12", "An Admin shall be able to request database synchronization.", "Role-gated endpoint"],
])
add("Chapter 5 — Functional Requirements III", rows=[
    ["ID", "Requirement", "Verification"],
    ["FR-13", "Authorized users shall export supported data or reports.", "Verify each format"],
    ["FR-14", "Admin and Business Manager shall view the user directory.", "Role guard present"],
    ["FR-15", "Authorized users shall invite/create an account with a temporary password.", "API and UI verified"],
    ["FR-16", "An invite shall not claim to send email unless an email provider is implemented.", "No mail send in invite flow"],
    ["FR-17", "Only Admin shall assign roles or delete accounts, subject to self-protection checks.", "Backend route guards"],
    ["FR-18", "Audit events shall be displayed with object details formatted safely.", "Browser-local event store"],
])
add("Chapter 5 — Non-Functional Requirements", rows=[
    ["Quality", "Requirement statement"],
    ["Usability", "Show meaningful loading, empty, success and failure states; label estimated values."],
    ["Reliability", "Detect API/database failures and avoid presenting failure as valid business zeros."],
    ["Security", "Enforce server-side authentication and authorization; protect password hashes and secrets."],
    ["Privacy", "Minimize customer identifiers in exports, screenshots, and logs."],
    ["Maintainability", "Keep presentation, API, analytics, and persistence responsibilities understandable."],
    ["Performance", "Measure response time and memory on representative data before setting service objectives."],
    ["Compatibility", "Test supported browsers and deployment environments explicitly."],
])
add("Chapter 5 — Non-Functional Requirements", [
    "Acceptance should be attached to observable behavior: protected routes reject anonymous access; an authorized invitation creates an account that can sign in; unauthorized role assignments are denied; filters affect returned analytics; and backend failures are distinguishable from valid zero-valued results.",
    "Requirements should trace to a module, endpoint or component, and test case. The repository contains tests for health, authorization, registration/login, data, filtering, and invitation. Coverage is not inferred from the existence of a feature or a successful build. Run the full suite and update actual test outcomes from captured output."
], rows=[
    ["Acceptance evidence", "Example observable result"],
    ["Authentication", "Protected endpoint rejects missing/invalid token"],
    ["Invitations", "Account is created; subsequent login succeeds"],
    ["Authorization", "Disallowed roles receive a server-side denial"],
    ["Analytics", "Result corresponds to documented filters and metric"],
    ["Availability", "API failure is not shown as valid zero-valued data"],
])

# Chapter 6 (12 pages)
add("Chapter 6 — Architecture Overview", [
    "The browser client runs as a React application built with Vite. It owns navigation state, filter state, display composition, chart configuration, and forms. The backend is a FastAPI application that validates request models, applies authentication dependencies, invokes analytics/data operations, and returns JSON or files.",
    "The analytics engine loads the configured CSV into Pandas, normalizes known source shapes, derives analytical columns, and aggregates measures. SQLAlchemy is used for user records. Database synchronization is implemented through a separate module and should not be confused with the user-account database.",
    "The architecture separates responsibilities but shares a local development environment. In production, the API, static assets, database, secrets, TLS, backups, and monitoring require an explicit deployment design."
], diagram="Browser (React/Vite)  --HTTP / JSON-->  FastAPI routes\n        |                                      | \n        | local UI state                      +--> AnalyticsEngine (Pandas / NumPy)\n        |                                      +--> SQLAlchemy users DB (MySQL / SQLite)\n        +-- /api proxy in development          +--> CSV / database sync module")
add("Chapter 6 — Context-Level DFD", [
    "Figure 6.1 represents the system as one process with external actors. A business user supplies credentials, filters, and requests; the application returns dashboard values, charts, reports, and administrative results. An administrator additionally requests user and data-management operations.",
    "The external dataset is a source of commerce records. The database stores user-account information and may receive synchronized analytical data. The exact deployment arrangement for these stores must be confirmed for a hosted installation.",
    "Arrows describe conceptual data exchange and do not imply that every request writes to persistence. Read-only analytics requests and administrative mutations have different authorization and data-flow rules."
], diagram="Business User / Admin --> [Nexus Commerce Intelligence] --> Dashboard / Reports\nCSV Dataset -------------> [Nexus Commerce Intelligence]\n[Nexus Commerce Intelligence] <--> Relational Database")
add("Chapter 6 — Level 0 DFD", [
    "The system can be decomposed into authentication, data ingestion and preparation, analytics services, user administration, and report presentation. Authentication validates the bearer token before protected routes execute. Data ingestion validates the selected file and refreshes the runtime analytics engine where the endpoint succeeds.",
    "Analytics requests pass optional filters to the backend and receive summaries or records. User-management requests are restricted by role. Results are rendered in the browser; exports are generated from selected API data and downloaded by the client.",
    "This decomposition is a logical DFD, not a claim that each process runs as a separate microservice."
], diagram="1 Authenticate  <--> User Store\n2 Import / Prepare <--> CSV Dataset\n3 Calculate Analytics <--> Prepared Data\n4 Manage Accounts <--> User Store\n5 Present / Export <--> Browser User")
add("Chapter 6 — Analytics Data Flow", [
    "The analytics loader selects an active data path from environment/configuration and known candidate files, reads the file, captures source-level quality measures, and normalizes fields. It derives normalized dates, region/city labels, discounts, sales/profit numeric values, return flags, month labels, and daily aggregates.",
    "API route functions invoke engine operations using request filters, then serialize results for the frontend. The client maps result arrays into labels and values for chart components. Data-quality warnings and estimated values should accompany the output where their interpretation could otherwise be unclear.",
    "If the dataset cannot load, the service should not imply that an empty dashboard is a valid result. Startup logging and health checks are necessary to distinguish missing source data from genuinely empty data."
], diagram="CSV -> Read/Profile -> Normalize -> Derive fields -> Aggregate -> API filter -> JSON -> React view")
add("Chapter 6 — Login Sequence", [
    "The login flow begins with credentials entered in the browser. The frontend posts them to the login endpoint. The backend looks up the account, verifies the submitted secret against the stored representation, and returns a signed token and role when successful. The client stores the session values and adds the bearer token to protected requests.",
    "Expired or invalid tokens are rejected by the backend. The frontend's unauthorized handler clears local session state and presents the sign-in screen. Tokens and passwords must not be printed in screenshots, logs, or reports.",
    "The described sequence follows current source behavior at a high level; production authentication requirements such as token revocation, MFA, rate limiting, secure cookie storage, and centralized identity need a separate security design."
], diagram="User -> React: submit credentials\nReact -> FastAPI: POST /api/auth/login\nFastAPI -> User DB: lookup + verify password hash\nFastAPI --> React: token + role (or error)\nReact -> FastAPI: Authorization: Bearer <token>\nFastAPI --> React: protected response")
add("Chapter 6 — Import Activity", [
    "An authorized administrator selects a file in the frontend. The browser packages it as multipart form data and submits it with the bearer token. The backend verifies the role, checks the file type and content according to the endpoint logic, writes or processes the data, refreshes the runtime engine, and returns a result.",
    "Failure cases include an unsupported extension, malformed CSV, missing required columns, insufficient permissions, storage failure, or a dataset that cannot be parsed. The user interface should preserve the failure message and avoid reporting a successful refresh if the engine did not reload.",
    "The imported data is sensitive business material; access controls, upload limits, path validation, backups, and retention behavior should be reviewed before production use."
], diagram="Select file -> Submit multipart + bearer token -> Authorize -> Validate -> Save/process -> Reload engine -> Show result")
add("Chapter 6 — Forecast Activity", [
    "A user selects a forecast horizon and supported options. The client sends a request to the daily forecast endpoint. The service prepares or selects daily observations, applies the forecasting path, and returns forecast dates, predicted values, and descriptive basis information. The client renders observed and predicted series separately.",
    "A forecast must be treated as an estimate conditional on historical data, selected horizon, and implementation assumptions. The diagram does not imply a confidence interval unless the endpoint returns one.",
    "Model evaluation should use chronological holdouts and compare predictions with observed values. The report does not claim an accuracy result because no validated model score has been supplied."
], diagram="Choose horizon/model -> Request forecast -> Build daily history -> Fit/predict -> Return estimates -> Display with caveat")
add("Chapter 6 — Component and Deployment View", [
    "The component view identifies browser UI, API service, analytics engine, persistence, and source data. The codebase is deployed locally during development as two processes coordinated by npm; a hosted deployment may use a reverse proxy or serve the built frontend from the backend, depending on configuration.",
    "The backend can attempt MySQL and fall back to SQLite for account persistence. Environment configuration controls the MySQL connection. Do not place actual database passwords, application secrets, or production endpoints in a report.",
    "Figure 6.8 is a logical deployment view. It does not claim cloud hosting, a production TLS termination point, autoscaling, or a production network boundary."
], diagram="Developer workstation:\nBrowser -> Vite :5173 -> FastAPI :8000\n                         |-> CSV dataset\n                         |-> MySQL (preferred) / SQLite fallback\nProduction placement: [To be confirmed]")
add("Chapter 6 — Authentication and Authorization Design", [
    "The API uses bearer-token authentication for protected routes and role information in the validated token payload. Endpoint-specific checks determine whether a caller can upload files, synchronize data, list users, invite users, change roles, or delete accounts.",
    "The backend is the security authority. Hiding a button in the frontend is not sufficient, because a user can construct an HTTP request outside the UI. Route-level tests should cover allowed and denied roles for every administrative action.",
    "The current report describes the project's token-based design, not a full security audit. Production review should assess signing-secret management, token lifecycle, transport security, password reset behavior, rate limiting, CSRF exposure if cookies are introduced, and account recovery."
])
add("Chapter 6 — Verified Database Schema", rows=[
    ["Table", "Column", "Type / constraint", "Purpose"],
    ["users", "id", "Integer, primary key, autoincrement", "Account identifier"],
    ["users", "email", "String(255), unique, not null, indexed", "Login identity"],
    ["users", "phone", "String(32), nullable, indexed", "Optional phone/OTP identity"],
    ["users", "password", "String(512), not null", "Password representation/hash"],
    ["users", "role", "String(64), not null, default Viewer", "Authorization role"],
    ["users", "otp_code / otp_expires_at", "String(16) / DateTime, nullable", "Reset workflow fields"],
    ["users", "created_at / updated_at", "DateTime, not null", "Account timestamps"],
])
add("Chapter 6 — Dataset and Analytical Model", [
    "The active dataset is selected from configured paths and candidate files. One source shape uses fields such as order_id, order_date, customer_id, product_category, quantity, net_amount, region, city, and order_status; the engine normalizes this into analytical columns. Another profiled file reports 6,040 rows and 17 columns. These are different artifacts and must not be conflated.",
    "A project synopsis describes an 80,000-record dataset with 20 attributes, while a prior local health response reported 80,004 loaded records. Record counts can vary with file version and application state; the report uses 80,004 only as an observed local health response, not a permanent dataset guarantee.",
    "The analytical model includes order-level facts and dimensions inferred from input columns. The following conceptual diagram is not a claim that these are physical normalized tables."
], diagram="Order Fact: order/date/customer/product/location/status/quantity/sales/profit\nDimensions (conceptual): Date | Customer | Product | Geography | Order Status\nUser persistence: separate `users` table; analytical star schema requires DB sync verification")
add("Chapter 6 — Data Quality and Profit Semantics", [
    "A profile artifact in the repository describes a 6,040-row, 17-column source with duplicate order IDs, some missing customer names, inconsistent region case, and negative profit values. That file is a snapshot, not necessarily a profile of the currently selected 80,004-row runtime dataset.",
    "The analytics engine records missing values, rows with missing values, duplicate rows, and invalid dates. It standardizes numeric and category fields for analysis. The report must disclose that coercion and normalization can affect results.",
    "When profit is derived as 30% of net sales, it is a planning estimate. The assumption may not represent actual cost, fulfillment expense, discounts, taxes, or returns. Users should not use it for statutory or audited accounting."
])
add("Chapter 6 — API Contract and Error Handling", rows=[
    ["Concern", "Expected handling"],
    ["Unauthenticated request", "401 response; client clears stale session where configured"],
    ["Insufficient role", "403 response from server-side guard"],
    ["Duplicate invite", "409 response"],
    ["Invalid request body", "FastAPI/Pydantic validation response"],
    ["Unknown route", "404 response"],
    ["Operational failure", "Explicit error response; preserve useful message without secrets"],
    ["Success", "JSON or file response as appropriate to endpoint"],
])

# Chapter 7 (8 pages)
add("Chapter 7 — Screenshot Evidence: Login and Home", [
    "Figure 7.1 — Login Page. [Insert an actual screenshot captured from the current application here.]",
    "The login view collects an email and password and submits them to the authentication endpoint. Obscure the password and avoid capturing tokens or browser storage. Include an invalid-credential state only if it is captured from the real application.",
    "Figure 7.2 — Overview Dashboard. [Insert an actual screenshot captured from the current application here.]",
    "Explain visible KPI cards, active filters, charts, dataset status, and the selected date range. Confirm what each figure means from the API response and label estimated profit."
], kind="chapter")
add("Chapter 7 — Screenshot Evidence: Sales and Profitability", [
    "Figure 7.3 — Sales Analytics. [Insert actual screenshot here.] Explain the displayed sales trend, category comparison, record table, filter state, and any pagination.",
    "Figure 7.4 — Profitability Analysis. [Insert actual screenshot here.] State whether profit values come directly from source data or from the planning-margin estimate. Do not represent an estimate as actual profit.",
    "Screenshots should be captured at a readable browser size. Captions should include the page/module name and explain the evidence, not make claims about performance or user satisfaction."
])
add("Chapter 7 — Screenshot Evidence: Products and Customers", [
    "Figure 7.5 — Product Analytics. [Insert actual screenshot here.] Explain ranking criteria, currency, selected filters, and whether results are revenue-based or another measure.",
    "Figure 7.6 — Customer Intelligence. [Insert actual screenshot here.] Avoid showing identifiable customer names or IDs unless permission has been granted; anonymize examples while preserving chart meaning.",
    "Describe how the interface helps a user move from an aggregate to a detailed view. Verify the table columns and definitions against actual API payloads."
])
add("Chapter 7 — Screenshot Evidence: Segments and Geography", [
    "Figure 7.7 — Segment Analysis. [Insert actual screenshot here.] Explain the selected customer or product dimension and the way current filters alter the result.",
    "Figure 7.8 — Geographic Analysis. [Insert actual screenshot here.] Identify the geographic fields as they appear in the source schema; do not infer coordinates or map precision if the application shows only region/city breakdowns.",
    "Ensure each screenshot includes enough context to identify the page while cropping irrelevant desktop details. The figure should be legible at standard report print size."
])
add("Chapter 7 — Screenshot Evidence: Returns, Forecasts, and Anomalies", [
    "Figure 7.9 — Returns and Risk. [Insert actual screenshot here.] Describe the status/return indicators and their basis in the supplied dataset.",
    "Figure 7.10 — Sales Forecast. [Insert actual screenshot here.] Include the forecast horizon and label estimates clearly. Do not claim accuracy from the chart alone.",
    "Figure 7.11 — Anomaly Detection. [Insert actual screenshot here.] Explain that a flagged observation requires review and is not proof of misconduct or a confirmed business incident."
])
add("Chapter 7 — Screenshot Evidence: Quality and Import", [
    "Figure 7.12 — Data Quality. [Insert actual screenshot here.] Describe the record count, completeness or quality measures, and active dataset identity.",
    "Figure 7.13 — Data Import. [Insert actual screenshot here.] Remove file paths that reveal personal information. Show the selected file name only if safe and approved.",
    "A screenshot records one moment in one environment. Add capture date, application version/branch if known, and test data provenance. Do not imply every input file produces the same output."
])
add("Chapter 7 — Screenshot Evidence: Exports and Database", [
    "Figure 7.14 — Export and Reports. [Insert actual screenshot here.] Explain the selected date period, available formats, and the contents of the generated files.",
    "Figure 7.15 — Database Status and Synchronization. [Insert actual screenshot here.] Do not reveal hostnames, usernames, secrets, or connection strings. State which role can initiate synchronization.",
    "If the database reports a fallback backend, explain that the configured user database changed from the preferred connection path; do not call this a successful MySQL deployment."
])
add("Chapter 7 — Screenshot Evidence: Audit, Users, and API Docs", [
    "Figure 7.16 — Audit Logs. [Insert actual screenshot here.] Explain that events are stored in local browser storage in the inspected implementation and are not a central audit log.",
    "Figure 7.17 — User Management. [Insert actual screenshot here.] Mask email addresses and show only non-sensitive test accounts. The invite form creates an account but does not email the user.",
    "Figure 7.18 — API Documentation. [Insert actual screenshot of the authorized API docs page here, if enabled.] Remove authorization tokens and sensitive example values."
])

# Chapter 8 (7 pages)
add("Chapter 8 — Testing Strategy", [
    "Testing should proceed from isolated functions to integrated workflows. Unit tests verify calculations and validators. API tests verify request/response behavior and role enforcement. Database tests verify persistence and transactions. Browser checks verify navigation, form feedback, loading, empty, and error states.",
    "Regression testing reruns relevant tests after a change. User acceptance testing evaluates whether representative users can complete tasks and correctly interpret results. These are different kinds of evidence; a successful build alone proves compilation, not functional correctness.",
    "The repository includes pytest API tests. Three focused invitation tests were run and passed during the preceding development session: an Admin-created account could sign in; a Business Manager could not invite an Admin; and a Viewer could not invite an account. A frontend production build also completed successfully. Re-run them at submission time."
], rows=[
    ["Executed validation", "Observed result"],
    ["Invite create + subsequent login API test", "Passed in focused pytest run"],
    ["Business Manager cannot invite Admin", "Passed in focused pytest run"],
    ["Viewer cannot invite", "Passed in focused pytest run"],
    ["Frontend production build", "Succeeded; large-chunk advisory remains"],
    ["Browser invite submission", "Observed successful response and visible confirmation"],
])
add("Chapter 8 — Test Cases: Authentication and Dashboard", rows=[
    ["ID", "Scenario", "Expected result", "Actual / status"],
    ["TC-AUTH-01", "Sign in with valid account", "Token and role returned", "To be confirmed"],
    ["TC-AUTH-02", "Sign in with incorrect password", "Request rejected; no session", "To be confirmed"],
    ["TC-AUTH-03", "Open protected endpoint without token", "401 Unauthorized", "Existing suite covers; rerun"],
    ["TC-DASH-01", "Load overview with API available", "KPIs render from response", "To be confirmed"],
    ["TC-DASH-02", "API unavailable at startup", "Visible service error; not false zero data", "To be confirmed"],
    ["TC-DASH-03", "Apply a supported filter", "Request and results reflect filter", "To be confirmed"],
])
add("Chapter 8 — Test Cases: Analytics and Data Quality", rows=[
    ["ID", "Scenario", "Expected result", "Actual / status"],
    ["TC-AN-01", "View sales trends and categories", "Dates and totals match API", "To be confirmed"],
    ["TC-AN-02", "View customer/product rankings", "Ranking uses documented measure", "To be confirmed"],
    ["TC-AN-03", "Filter geography/segment", "Results match selected dimensions", "To be confirmed"],
    ["TC-AN-04", "Open data-quality view", "Quality metrics identify active data", "To be confirmed"],
    ["TC-AN-05", "Inspect estimated profit", "UI labels estimate and 30% assumption", "To be confirmed"],
    ["TC-AN-06", "Use daily report", "Summary and daily data render", "To be confirmed"],
])
add("Chapter 8 — Test Cases: Prediction and Export", rows=[
    ["ID", "Scenario", "Expected result", "Actual / status"],
    ["TC-PR-01", "Request forecast for supported horizon", "Dates and estimates returned", "To be confirmed"],
    ["TC-PR-02", "Compare forecast with held-out data", "Metrics vs baseline recorded", "Not run"],
    ["TC-PR-03", "Inspect anomaly flag", "Flag and source values visible", "To be confirmed"],
    ["TC-PR-04", "Generate supported export", "File opens and rows match filter", "To be confirmed"],
    ["TC-PR-05", "Request unsupported format/input", "Clear validation error", "To be confirmed"],
    ["TC-PR-06", "Use recommendations view", "Output corresponds to API payload", "To be confirmed"],
])
add("Chapter 8 — Test Cases: User Administration", rows=[
    ["ID", "Scenario", "Expected result", "Actual / status"],
    ["TC-USR-01", "Admin invites valid email/password", "Account is created", "Passed in focused run"],
    ["TC-USR-02", "New user signs in with invite password", "Login succeeds with assigned role", "Passed in focused run"],
    ["TC-USR-03", "Invite duplicate email", "409 conflict, no duplicate account", "To be confirmed"],
    ["TC-USR-04", "Password shorter than 8 characters", "Request validation error", "To be confirmed"],
    ["TC-USR-05", "Business Manager invites Admin", "403 forbidden", "Passed in focused run"],
    ["TC-USR-06", "Viewer invites any user", "403 forbidden", "Passed in focused run"],
])
add("Chapter 8 — Test Cases: Data Administration and Security", rows=[
    ["ID", "Scenario", "Expected result", "Actual / status"],
    ["TC-ADM-01", "Non-admin uploads dataset", "403 forbidden", "To be confirmed"],
    ["TC-ADM-02", "Admin uploads malformed CSV", "Clear failure; no false success", "To be confirmed"],
    ["TC-ADM-03", "Viewer requests database sync", "403 forbidden", "To be confirmed"],
    ["TC-ADM-04", "Business Manager changes role", "403 forbidden", "To be confirmed"],
    ["TC-ADM-05", "Attempt self-delete/self-role change", "Rejected by backend", "To be confirmed"],
    ["TC-SEC-01", "Inspect logs/screenshots", "No password/token leakage", "Security test pending"],
])
add("Chapter 8 — Test Execution Summary", [
    "Completed checks recorded in the current draft: three focused invitation permission/login tests passed; frontend Vite production build succeeded; a local browser invite submission returned success and displayed a confirmation. The browser-created test account was cleaned up from the local development database.",
    "The build emitted a bundle-size advisory concerning large generated chunks. This was not a build failure, but it is a performance optimization opportunity. Other tests listed in this chapter remain pending until executed against the submission build.",
    "Execution environment: [Record OS, Python version, Node version, database backend, commit/version, and test date]. Full suite result: [To be confirmed]. Acceptance sign-off: [To be confirmed]."
], rows=[
    ["Summary item", "Value"],
    ["Tests executed in this report", "Focused invite API checks, build, browser invite smoke check"],
    ["Full regression suite", "[To be confirmed]"],
    ["Known advisory", "Large frontend bundle warning"],
    ["Approved by", "[To be confirmed]"],
])

# Chapter 9 (2 pages)
add("Chapter 9 — Conclusion: Achievements", [
    "Nexus Commerce Intelligence brings together a browser-based dashboard and a Python API for e-commerce analysis. The inspected source contains modules for sales, product, customer, segment, geography, data quality, export, forecasting, anomalies, recommendations, database operations, audit display, and user management.",
    "The project demonstrates integration across a React/Vite frontend, FastAPI routes, Pandas-based analytics, and SQLAlchemy-backed account persistence. It also illustrates why an analytical application must communicate its assumptions and distinguish local development behavior from production deployment.",
    "The invite workflow was verified to create an account that can subsequently sign in. Role checks were exercised for the Admin, Business Manager, and Viewer cases. The frontend build completed successfully during validation."
])
add("Chapter 9 — Conclusion: Lessons and Completion", [
    "The principal engineering lesson is that correctness includes operational visibility: the frontend requires the backend, so API connection errors should be explained as service availability rather than treated as empty business data. Other lessons include guarding object rendering, surfacing form feedback, validating role permissions on the server, and documenting where logs are stored.",
    "The report does not establish measured business impact, forecasting accuracy, sustained production availability, accessibility conformance, or company adoption. These remain evaluation tasks.",
    "Before submission, the student should replace placeholders, capture current screenshots, execute the complete test suite, update references and API details, verify dataset provenance, and obtain institutional approval for company-related material."
])

# Chapter 10 (2 pages)
add("Chapter 10 — Limitations: Data and Metrics", [
    "Dataset versions and profiles differ. A repository profile reports 6,040 rows and 17 fields, while project documentation describes an 80,000-order dataset with 20 source fields and a prior local health response observed 80,004 loaded records. These observations refer to different points or artifacts and must be reconciled against the exact submission dataset.",
    "The engine may estimate profit from a 30% margin when actual profit is absent. This estimate is not a substitute for cost-of-goods, fulfillment, marketing, tax, refund, and accounting records. Quality indicators depend on the selected dataset and preprocessing decisions.",
    "Some source snapshots contain duplicate IDs, missing names, inconsistent labels, or negative profit values. A dashboard cannot fix the business meaning of imperfect source data by visualization alone."
])
add("Chapter 10 — Limitations: Model and Operations", [
    "Forecasting and anomaly outputs need independent validation, documented baselines, time-aware evaluation, review of false positives, and monitoring for data drift. No predictive accuracy or operational threshold is claimed.",
    "The audit interface uses browser-local storage, so entries do not provide cross-device retention, central access, tamper resistance, or compliance-grade auditability. Database fallback behavior improves local availability but does not itself provide backup, replication, or production failover.",
    "The project has not been established as a hardened production deployment. TLS, secrets, retention, database migrations, monitoring, resource limits, incident response, authorization review, and concurrent-load testing require further work."
])

# Chapter 11 (2 pages)
add("Chapter 11 — Future Enhancements: Analytics", [
    "A future analytics phase should create a repeatable data contract, retain source provenance, formalize metric definitions, and add automated validation before loading. Reconciliation against an authoritative accounting source would allow actual margin reporting instead of a planning estimate.",
    "Forecast work should compare candidate methods with seasonal-naïve baselines, chronological validation, uncertainty reporting, and monitoring. Anomaly detection should include review workflows and feedback to measure useful alerts rather than maximizing the number of flags.",
    "Customer intelligence could be extended through well-defined segmentation, privacy safeguards, and careful validation that any segment is actionable and not misleading."
])
add("Chapter 11 — Future Enhancements: Product and Operations", [
    "Operational improvements could include central audit event persistence with retention and access policy, verified invitation delivery using an approved email provider, secure temporary-password reset, managed identity or an established identity provider, and stronger monitoring.",
    "Productionization should add automated CI, dependency/security scanning, database migration management, API schema tests, browser end-to-end tests, backups, deployment automation, and performance testing on representative data.",
    "These items are proposals. They are not described as existing project capabilities."
])

# Chapter 12 (3 pages)
add("Chapter 12 — References: Official Documentation I", [
    "[1] React Team, “React Documentation,” React.dev. [Online]. Available: https://react.dev/. Accessed: Oct. 12, 2026.",
    "[2] Vite Team, “Vite Guide,” Vite. [Online]. Available: https://vite.dev/guide/. Accessed: Oct. 12, 2026.",
    "[3] Chart.js Contributors, “Chart.js Documentation.” [Online]. Available: https://www.chartjs.org/docs/latest/. Accessed: Oct. 12, 2026.",
    "[4] S. Ramirez, “FastAPI Documentation.” [Online]. Available: https://fastapi.tiangolo.com/. Accessed: Oct. 12, 2026.",
    "[5] Python Software Foundation, “Python 3 Documentation.” [Online]. Available: https://docs.python.org/3/. Accessed: Oct. 12, 2026.",
    "Cite these references in the relevant technology and implementation sections. Verify access dates and the institution's preferred citation style at submission."
], kind="reference")
add("Chapter 12 — References: Official Documentation II", [
    "[6] The pandas development team, “pandas Documentation.” [Online]. Available: https://pandas.pydata.org/docs/. Accessed: Oct. 12, 2026.",
    "[7] NumPy Developers, “NumPy Documentation.” [Online]. Available: https://numpy.org/doc/. Accessed: Oct. 12, 2026.",
    "[8] scikit-learn Developers, “scikit-learn User Guide.” [Online]. Available: https://scikit-learn.org/stable/user_guide.html. Accessed: Oct. 12, 2026.",
    "[9] XGBoost Developers, “XGBoost Documentation.” [Online]. Available: https://xgboost.readthedocs.io/. Accessed: Oct. 12, 2026.",
    "[10] SQLAlchemy Authors, “SQLAlchemy Documentation.” [Online]. Available: https://docs.sqlalchemy.org/. Accessed: Oct. 12, 2026.",
    "[11] Oracle, “MySQL 8.4 Reference Manual.” [Online]. Available: https://dev.mysql.com/doc/refman/8.4/en/. Accessed: Oct. 12, 2026.",
    "[12] SQLite Consortium, “SQLite Documentation.” [Online]. Available: https://www.sqlite.org/docs.html. Accessed: Oct. 12, 2026."
], kind="reference")
add("Chapter 12 — References: Design and Standards", [
    "[13] R. Kimball and M. Ross, The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling, 3rd ed. Hoboken, NJ, USA: Wiley, 2013.",
    "[14] M. Fowler, Patterns of Enterprise Application Architecture. Boston, MA, USA: Addison-Wesley, 2002.",
    "[15] Object Management Group, “Unified Modeling Language (UML),” OMG. [Online]. Available: https://www.omg.org/spec/UML/. Accessed: Oct. 12, 2026.",
    "[16] OWASP Foundation, “Authentication Cheat Sheet.” [Online]. Available: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html. Accessed: Oct. 12, 2026.",
    "[17] OWASP Foundation, “Password Storage Cheat Sheet.” [Online]. Available: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html. Accessed: Oct. 12, 2026.",
    "Only cite a source when it supports the corresponding claim. Add any institution-required academic publications after verifying the bibliographic record and DOI."
], kind="reference")

# Chapter 13 (8 pages)
add("Appendix A — User Manual: Prerequisites and Setup", [
    "The local project requires the repository directory, its Python virtual environment and dependencies, and frontend npm dependencies. The inspected project root defines `npm run dev` to launch Uvicorn on 127.0.0.1:8000 and the Vite frontend. Run the command from the project root, not from the frontend subdirectory.",
    "If setup is incomplete, install project requirements using the repository's documented process and run npm installation where the relevant package lock is located. Do not commit `.env` secrets. The application may load environment values from `.env`; inspect `.env.example` and supply local values securely.",
    "The frontend development server proxies `/api` requests to the backend. If the UI loads but API calls show ECONNREFUSED, confirm that Uvicorn started and is listening on port 8000."
], kind="appendix")
add("Appendix A — Database Configuration and Startup", [
    "The database module reads configuration values for MySQL host, port, user, password, and database name. It attempts MySQL and can select SQLite fallback. Use a local development database or the fallback; never place real credentials in this report.",
    "Start the complete app from the project root with `npm run dev`. The expected local addresses are the Vite frontend at `http://localhost:5173/` and the API at `http://127.0.0.1:8000/`. Vite may choose another port if 5173 is already occupied.",
    "Check `GET /api/health` to confirm the backend responds. The health response includes status, dataset name, record count, and authentication backend. Do not assume a successful frontend launch means the API is available."
], kind="appendix")
add("Appendix A — Sign-in and Dashboard Navigation", [
    "Open the local frontend URL and sign in using an account configured for the environment. The repository synopsis documents a demo account, but test/development credentials must not be reused in a public deployment. Change default credentials before any shared environment is used.",
    "Use the left navigation to open analytics and data-management views. The top filter area contains dimensions available to the dashboard; select a value and check the active-filter indication. Use the reset control to return to an unfiltered view.",
    "If the page shows zero values or remains loading, check the backend terminal and `/api/health`. A refused API connection indicates service availability failure, not proof that the underlying dataset contains zero records."
], kind="appendix")
add("Appendix A — Analytics and Forecasting Instructions", [
    "Select Sales Analytics to review supported sales records and trends. Product and Customer Intelligence provide rankings/summary views. Segment and Geographic Analysis allow comparison across dimensions exposed by the API. Confirm date range and filters before interpreting a result.",
    "Use Returns and Risk to review status-related patterns. Open the Forecast view, select a supported forecast horizon/model option, and treat outputs as estimates. Do not use them as guaranteed future revenue or as a substitute for a validated forecasting process.",
    "Anomaly flags are prompts for investigation. Compare the flagged observation with source records, check data quality, and consider operational events before drawing conclusions."
], kind="appendix")
add("Appendix A — Import, Export, and Database Operations", [
    "The data-import page accepts a file through a backend upload endpoint with role enforcement. Only use a correctly structured, approved CSV. Keep a backup of source data, and verify the resulting active dataset and quality view after upload.",
    "Export and report pages request data from the API and create downloadable files. Confirm selected filters, year/month, and output format. Protect exported customer or sales data according to organizational policy.",
    "Database status describes the configured backend. Synchronization is Admin-only in the inspected route. Review the result and counts; do not repeat a destructive replacement operation without understanding its scope and having a backup."
], kind="appendix")
add("Appendix A — User Management, Audit, and Logout", [
    "Users & Roles is available to elevated roles. To invite a user, enter a valid email, set a temporary password of at least eight characters, choose an allowed role, and submit. The application creates the account immediately and shows confirmation. It does not automatically send an email; share the password securely through an approved channel.",
    "Audit Logs display events stored in the current browser's local storage. Clearing browser data or using another browser can change what appears. Do not rely on this interface for compliance retention or centralized incident investigation.",
    "Use the sign-out control to clear the active browser session. For shared devices, close the browser profile after sign-out and avoid saving passwords."
], kind="appendix")
add("Appendix A — Troubleshooting Guide", rows=[
    ["Symptom", "Likely check / action"],
    ["ECONNREFUSED 127.0.0.1:8000", "Start backend with root `npm run dev`; inspect backend startup failure."],
    ["Vite uses 5174", "Port 5173 may already be occupied; use the URL printed by Vite."],
    ["401 response", "Sign in again; verify token expiry and backend secret consistency."],
    ["403 response", "The account role lacks permission for the requested operation."],
    ["Invite fails", "Check email, 8+ character password, duplicate account, role, and API status."],
    ["Dataset missing", "Check DATASET_PATH and configured candidate dataset file."],
    ["Empty charts", "Check API response, filter state, source schema, and quality output."],
], kind="appendix")
add("Appendix B — Verified API Endpoint Inventory", rows=[
    ["Method", "Path", "Purpose / access"],
    ["GET", "/api/health", "Health and loaded data summary; public health route"],
    ["POST", "/api/auth/register", "Create account/register"],
    ["POST", "/api/auth/login", "Authenticate"],
    ["POST", "/api/auth/forgot-password", "Password reset flow"],
    ["POST", "/api/auth/send-otp", "Request OTP"],
    ["POST", "/api/auth/verify-otp-reset", "OTP reset verification"],
    ["GET", "/api/dashboard/kpis", "Protected dashboard KPIs"],
    ["GET", "/api/sales/trend, /api/sales/daily", "Protected time series"],
    ["GET", "/api/sales/daily/report", "Protected daily report"],
    ["GET", "/api/sales/daily/forecast", "Protected forecast"],
    ["GET", "/api/sales/category, /api/sales/records", "Protected sales analysis/records"],
    ["POST/PUT/DELETE", "/api/sales/records...", "Sales mutations; inspect endpoint roles"],
])
add("Appendix B — More APIs and Glossary", rows=[
    ["Method", "Path", "Purpose / access"],
    ["GET", "/api/products/top, /api/customers/top", "Protected rankings"],
    ["GET", "/api/recommendations, /api/customers/rfm", "Protected recommendations/customer analysis"],
    ["GET", "/api/segments/*", "Protected segment breakdowns"],
    ["GET", "/api/sales/anomalies", "Protected anomaly results"],
    ["GET", "/api/ai/advisor", "Protected advisor output"],
    ["GET", "/api/data/quality", "Protected data quality"],
    ["POST", "/api/data/upload", "Admin-gated data upload"],
    ["GET/POST", "/api/db/status, /api/db/sync", "Database status; Admin sync"],
    ["GET/PATCH/DELETE/POST", "/api/management/users...", "Role-gated user management"],
    ["Glossary", "API, BI, KPI, DFD, ERD, RBAC, REST, CSV", "Interface, intelligence, indicator, flow/model, access policy, HTTP design, tabular file"],
], kind="appendix")


def add_page_break(body):
    p = SubElement(body, q("p"))
    run = SubElement(p, q("r"))
    SubElement(run, q("br"), {q("type"): "page"})


def add_field(paragraph_element, instruction: str):
    run = SubElement(paragraph_element, q("r"))
    begin = SubElement(run, q("fldChar"))
    begin.set(q("fldCharType"), "begin")
    run = SubElement(paragraph_element, q("r"))
    instr = SubElement(run, q("instrText"))
    instr.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    instr.text = instruction
    run = SubElement(paragraph_element, q("r"))
    SubElement(run, q("fldChar"), {q("fldCharType"): "end"})


def build_docx():
    document = Element(q("document"), {"xmlns:r": R})
    body = SubElement(document, q("body"))
    for page_number, page in enumerate(pages):
        if page_number:
            add_page_break(body)
        style = "Title" if page["kind"] == "cover" else "Heading1"
        head = paragraph(page["title"], style, align="center" if page["kind"] == "cover" else None, bold=page["kind"] == "cover", size=32 if page["kind"] == "cover" else 28, font="Times New Roman", color="20304A")
        body.append(head)
        if page["kind"] == "cover":
            for text in page["paragraphs"]:
                body.append(paragraph(text, align="center", size=24 if text in {"PROJECT REPORT", "MASTER OF COMPUTER APPLICATIONS (MCA)"} else 22, font="Times New Roman", bold=text in {"PROJECT REPORT", "MASTER OF COMPUTER APPLICATIONS (MCA)"}))
            continue
        if page["kind"] not in {"preliminary", "reference"}:
            number = page["title"].split("—")[0].strip()
            body.append(paragraph(number, "Heading2", bold=True, size=24, font="Times New Roman", color="C2562D"))
        for text in page["paragraphs"]:
            body.append(paragraph(text, font="Times New Roman"))
        for text in page["bullets"]:
            body.append(bullet(text))
        if page["diagram"]:
            body.append(paragraph(page["diagram"], font="Consolas", size=18, color="20304A"))
        if page["rows"]:
            body.append(table(page["rows"]))
    sect = SubElement(body, q("sectPr"))
    SubElement(sect, q("pgSz"), {q("w"): "11906", q("h"): "16838"})
    SubElement(sect, q("pgMar"), {
        q("top"): "1440", q("right"): "1440", q("bottom"): "1440", q("left"): "1800",
        q("header"): "720", q("footer"): "720", q("gutter"): "0",
    })
    SubElement(sect, q("cols"), {q("space"): "720"})

    styles = Element(q("styles"))
    normal = SubElement(styles, q("style"), {q("type"): "paragraph", q("default"): "1", q("styleId"): "Normal"})
    SubElement(normal, q("name"), {q("val"): "Normal"})
    ppr = SubElement(normal, q("pPr"))
    SubElement(ppr, q("spacing"), {q("after"): "120", q("line"): "360", q("lineRule"): "auto"})
    rpr = SubElement(normal, q("rPr"))
    SubElement(rpr, q("rFonts"), {q("ascii"): "Times New Roman", q("hAnsi"): "Times New Roman", q("cs"): "Times New Roman"})
    SubElement(rpr, q("sz"), {q("val"): "24"})
    SubElement(rpr, q("szCs"), {q("val"): "24"})
    for style_id, size in (("Heading1", "30"), ("Heading2", "26"), ("Title", "36")):
        style = SubElement(styles, q("style"), {q("type"): "paragraph", q("styleId"): style_id})
        SubElement(style, q("name"), {q("val"): style_id})
        style_rpr = SubElement(style, q("rPr"))
        SubElement(style_rpr, q("rFonts"), {q("ascii"): "Times New Roman", q("hAnsi"): "Times New Roman"})
        SubElement(style_rpr, q("b"))
        SubElement(style_rpr, q("sz"), {q("val"): size})

    footer = Element(q("ftr"))
    fp = SubElement(footer, q("p"))
    SubElement(SubElement(fp, q("pPr")), q("jc"), {q("val"): "center"})
    fr = SubElement(fp, q("r"))
    SubElement(fr, q("t")).text = "E-Commerce Analytics and Predictive Business Intelligence System  |  "
    add_field(fp, "PAGE")
    sect.append(SubElement(sect, q("footerReference"), {q("type"): "default", f"{{{R}}}id": "rId1"}))

    root_rels = Element(f"{{{PKG}}}Relationships")
    SubElement(root_rels, f"{{{PKG}}}Relationship", {"Id": "rId1", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "Target": "word/document.xml"})
    document_rels = Element(f"{{{PKG}}}Relationships")
    SubElement(document_rels, f"{{{PKG}}}Relationship", {"Id": "rId1", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer", "Target": "footer1.xml"})
    content_types = Element(f"{{{CT}}}Types")
    SubElement(content_types, f"{{{CT}}}Default", {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"})
    SubElement(content_types, f"{{{CT}}}Default", {"Extension": "xml", "ContentType": "application/xml"})
    SubElement(content_types, f"{{{CT}}}Override", {"PartName": "/word/document.xml", "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"})
    SubElement(content_types, f"{{{CT}}}Override", {"PartName": "/word/styles.xml", "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"})
    SubElement(content_types, f"{{{CT}}}Override", {"PartName": "/word/footer1.xml", "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"})
    settings = Element(q("settings"))
    SubElement(settings, q("updateFields"), {q("val"): "true"})

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", tostring(content_types, encoding="utf-8", xml_declaration=True))
        archive.writestr("_rels/.rels", tostring(root_rels, encoding="utf-8", xml_declaration=True))
        archive.writestr("word/document.xml", tostring(document, encoding="utf-8", xml_declaration=True))
        archive.writestr("word/styles.xml", tostring(styles, encoding="utf-8", xml_declaration=True))
        archive.writestr("word/footer1.xml", tostring(footer, encoding="utf-8", xml_declaration=True))
        archive.writestr("word/settings.xml", tostring(settings, encoding="utf-8", xml_declaration=True))
        archive.writestr("word/_rels/document.xml.rels", tostring(document_rels, encoding="utf-8", xml_declaration=True))
    print(json.dumps({"output": str(OUTPUT), "page_breaks": len(pages) - 1, "planned_pages": len(pages), "bytes": OUTPUT.stat().st_size}))


if __name__ == "__main__":
    build_docx()
