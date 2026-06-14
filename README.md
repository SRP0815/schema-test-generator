# 🗄️ Schema Aware Test Data Generator

> Automatically generate realistic, constraint-respecting synthetic test data from any SQL schema — no manual INSERT statements needed.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://schema-test-generator-3zejyuvvhl3viy7fttpzab.streamlit.app/)

---

## 📌 Problem Statement

Developers and testers waste hours manually writing INSERT statements to populate databases for testing. Existing tools generate random data that violates constraints like PRIMARY KEY, FOREIGN KEY, UNIQUE, and NOT NULL — breaking test environments before testing even begins.

**Schema Aware Test Data Generator** solves this by reading your SQL schema, understanding all constraints and relationships, and automatically generating realistic, valid synthetic data ready to load into any database.

---

## 👥 Team Members

| Name | Institution | Roll Number |
|---|---|---|
| T C Varalakshmi | AITS Tirupati | 23AK1A05M4 |
| V. Sai Ranga Prasad | AITS Rajampet | 24705A3112 |
| S. Pranathi | AITS Rajampet | 23701A3089 |

---

## ✅ Features Implemented

- 8+ built-in demo schemas (Banking, E-Commerce, Hospital, HR, College, Library, Hotel, Food Delivery)
- Manual SQL schema entry with multi-table support
- Automatic detection of tables, columns, PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL constraints
- Referential integrity enforcement — parent tables always generated before child tables
- Relationship graph and dependency order visualization
- Configurable record counts per table (1 to 100,000)
- 5 dataset generation modes: Normal, Large, Edge Case, Stress Testing, Custom
- Auto-fix engine for constraint violations
- Preview tables before download
- Export as CSV, SQL INSERT statements, and ZIP package
- **AI Insights** powered by Google Gemini:
  - Business domain detection
  - Schema description and system type classification
  - Complexity scoring
  - Semantic column label mapping
  - AI data quality review with score

---

## 🏗️ Architecture Overview

```
User (SQL Schema Input)
        ↓
   schema_parser.py        — Parse tables, columns, constraints, FK relationships
        ↓
   relationship_engine.py  — Build dependency graph, detect generation order
        ↓
   generator.py            — Generate realistic data using Faker (constraint-aware)
        ↓
   fk_manager.py           — Resolve foreign key values from parent tables
        ↓
   validator.py            — Validate generated data, auto-fix violations
        ↓
   ai_layer.py             — Gemini AI: schema insights + data quality review
        ↓
   exporter.py             — Export CSV / SQL INSERT / ZIP
        ↓
   app.py                  — Streamlit UI (input → preview → download)
```

---

## 🛠️ Tools and Technologies

| Category | Tool |
|---|---|
| Language | Python 3.10+ |
| UI Framework | Streamlit |
| Data Generation | Faker library |
| Data Processing | Pandas |
| Graph Analysis | NetworkX, Matplotlib |
| AI / LLM | Google Gemini 1.5 Flash (free tier) |
| Export Formats | CSV, SQL, ZIP |
| Version Control | GitHub |

---

## ⚙️ Setup Instructions

**1. Clone the repository**
```bash
git clone https://github.com/SRP0815/schema-test-generator.git
cd schema-test-generator
```

**2. Create a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set API key (optional — only for AI Insights)**

Windows PowerShell:
```powershell
$env:GEMINI_API_KEY="your_gemini_api_key_here"
```

Mac/Linux:
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

> Get a free Gemini API key at: https://aistudio.google.com

---

## ▶️ Run Instructions

```bash
python -m streamlit run app.py
```

**Windows shortcut:**
```bash
run_app.bat
```

**PowerShell shortcut:**
```powershell
.\run_app.ps1
```

**Live deployed app:**
👉 https://schema-test-generator-3zejyuvvhl3viy7fttpzab.streamlit.app/

---

## 📂 Sample Input

```sql
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(20),
    city VARCHAR(80)
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    amount DECIMAL(10,2)
);
```

## 📤 Sample Output

**CSV (customers.csv)**
```
customer_id,customer_name,email,phone,city
1,Ravi Kumar,ravi.kumar@gmail.com,+91-9876543210,Hyderabad
2,Priya Nair,priya.nair@yahoo.com,+91-8765432109,Chennai
3,Arjun Sharma,arjun.sharma@outlook.com,+91-7654321098,Bangalore
```

**SQL INSERT (orders.sql)**
```sql
INSERT INTO "orders" ("order_id", "customer_id", "order_date", "amount") VALUES (1, 2, '2024-03-15', 1250.00);
INSERT INTO "orders" ("order_id", "customer_id", "order_date", "amount") VALUES (2, 1, '2024-05-22', 3780.50);
INSERT INTO "orders" ("order_id", "customer_id", "order_date", "amount") VALUES (3, 3, '2024-07-10', 890.75);
```

---

## 🤖 AI Capability Demonstrated

**Tool used:** Google Gemini 1.5 Flash (free tier) via REST API

**What AI does in this project:**

| Feature | Description |
|---|---|
| Business Domain Detection | Identifies system type from table names — e.g. "Banking / Finance System" |
| Schema Description | Generates a plain-English summary of what the database manages |
| Complexity Scoring | Scores schema complexity based on tables and foreign key count |
| Semantic Column Mapping | Decodes abbreviated column names — `emp_sal` → `employee_salary` |
| Data Quality Review | Reviews 10-row sample per table and returns a quality score (0–100) |

**AI is never used inside data generation loops** — only for understanding, classification, and insights.

---

## 📁 Project Structure

```
schema-test-generator/
├── app.py                  ← Streamlit UI and app flow
├── schema_parser.py        ← SQL parsing and metadata extraction
├── relationship_engine.py  ← Dependency graph and relationship detection
├── generator.py            ← Synthetic data generation engine
├── fk_manager.py           ← Foreign key resolution utilities
├── validator.py            ← Validation and auto-fix engine
├── exporter.py             ← CSV, SQL, ZIP export logic
├── ai_layer.py             ← Gemini AI insights layer
├── requirements.txt        ← Python dependencies
├── run_app.bat             ← Windows launcher
├── run_app.ps1             ← PowerShell launcher
└── smoke_test.py           ← Basic test cases
```

---

## ⚠️ Assumptions and Limitations

**Assumptions:**
- Input must be standard SQL `CREATE TABLE` syntax
- Foreign key parent tables must be defined before child tables in the schema
- Gemini API key required only for AI Insights — all other features work without it

**Limitations:**
- Does not support `ALTER TABLE` statements
- CHECK constraints are detected but not enforced during generation
- Very complex nested subqueries in constraints are not parsed
- AI Insights requires internet connection and valid Gemini API key
- Generated data is synthetic — not suitable for production use

---

## 🎥 Demo Video

▶️ **[Watch Demo Video](#)**

> 5-7 minute walkthrough showing schema input, data generation, AI insights, and export features.

---

## 📄 License

This project was built as part of the **AI Prototype Challenge** by **Infinite Computer Solutions**.
For educational and demonstration purposes only.
