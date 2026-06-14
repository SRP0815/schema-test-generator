
# SCHEMA AWARE TEST DATA GENERATOR

A production-style full-stack Streamlit application for analyzing SQL schemas, generating realistic synthetic datasets, validating referential integrity, and exporting CSV/SQL/ZIP packages.

## Features

- Built-in demo SQL schemas for E-Commerce, Banking, Hospital, HR, and more
- Manual SQL schema entry with multi-table support
- Automatic detection of tables, columns, primary keys, foreign keys, and relationships
- Relationship graph and dependency order analysis
- Configurable record counts per table
- Adaptive dataset generation modes: Normal, Large, Edge Case, Stress Testing, and Custom
- Referential integrity enforcement for foreign keys
- Validation engine with auto-fix logic
- Preview tables and download CSV/SQL/ZIP exports

## Writing

### 2. Manual Schema Entry

#### Create Your Own Schema

Provide a dedicated section where users can enter their own SQL schema.

Components:

- Large SQL text area
- Load Manual Schema button
- Clear / Reset Workspace button

Users can paste custom SQL `CREATE TABLE` statements.

Example:

```sql
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100)
);

CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT,
    amount DECIMAL(10,2),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

Support:

- Single-table schemas
- Multi-table schemas
- Complex schemas
- Deep foreign-key dependency chains
- Enterprise-scale schemas

#### Load Manual Schema

When the user clicks `Load Manual Schema`, the system should:

- Store the schema
- Validate SQL structure
- Display schema preview
- Enable schema analysis

Display:

```text
Schema Loaded Successfully
```

#### Clear / Reset Workspace

Add a dedicated enterprise-grade reset feature.

When the user clicks `Clear / Reset Workspace`, the application must completely reset itself to its initial state.

The system should clear:

- SQL text area
- Loaded schema
- Schema preview
- Schema analysis results
- Detected tables
- Detected columns
- Primary keys
- Foreign keys
- Relationship mappings
- Dependency graph
- Record count configurations
- Test case configurations
- Generated datasets
- Validation reports
- Data quality scores
- Generation metrics
- Preview tables
- Download packages
- Progress indicators
- Session state data

Display:

```text
Workspace Reset Successfully
Ready for a new schema.
```

#### Multi-Schema Testing Workflow

The platform must support unlimited schema testing during a single session.

Example workflow:

1. Load E-Commerce Schema
2. Analyze Schema
3. Generate Data
4. Download Results
5. Click `Clear / Reset Workspace`
6. Load Banking Schema
7. Analyze Schema
8. Generate Data
9. Download Results
10. Repeat as many times as needed

The user should never need to refresh the browser manually.

#### Streamlit Behavior

Use session state management.

When reset is triggered:

- Clear all stored state variables
- Remove cached analysis results
- Remove generated datasets
- Reinitialize widgets
- Rerun application automatically

Expected behavior:

- The application should instantly return to the same clean state shown when first launched.

#### UI Placement

Place `Load Manual Schema` and `Clear / Reset Workspace` side-by-side in the same row.

Use:

- Sky blue color for the Load button
- Soft red or warning color for the Reset button

The Reset button should include a confirmation dialog:

```text
Are you sure you want to clear the current workspace?
```

Options:

- Yes, Reset
- Cancel

This prevents accidental data loss and provides a professional enterprise user experience.

This addition explicitly supports multiple schema testing in one session, which judges often try during demos.

## Run locally

1. Create a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Launch the app:

```bash
python -m streamlit run "C:\Users\VARALAKSHMI T C\Desktop\Schema-Aware Text Data Generator\app.py"
```

On Windows, you can also double-click `run_app.bat`, or run this from PowerShell:

```powershell
.\run_app.ps1
```

Both launchers start the app from the correct project folder automatically.

## Project structure

- `app.py` — Streamlit dashboard and UI flow
- `schema_parser.py` — SQL parsing and metadata extraction
- `relationship_engine.py` — Relationship detection and dependency graph
- `generator.py` — Synthetic data generation engine
- `fk_manager.py` — Foreign key mapping utilities
- `validator.py` — Validation and auto-fix engine
- `exporter.py` — CSV, SQL, and ZIP export logic