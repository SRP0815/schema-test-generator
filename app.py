import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from exporter import generate_csv_bytes, generate_sql_inserts, build_zip_package
from generator import build_dataframes, generate_data
from relationship_engine import summarize_graph
from schema_parser import SchemaMetadata, parse_schema, summarize_schema
from validator import auto_fix_data, build_validation_summary, validate_data
import ai_layer


DATASET_TYPES = [
    "Normal Dataset",
    "Large Dataset",
    "Edge Case Dataset",
    "Stress Testing Dataset",
    "Custom Dataset",
]

SESSION_DEFAULTS = {
    "schema_text": "",
    "metadata": None,
    "table_counts": {},
    "dataset_type": "Normal Dataset",
    "generation_result": {},
    "validation_summary": {},
    "preview_dataframes": {},
}

SAMPLE_SCHEMAS = {
    "Indian Customer Orders": """
CREATE TABLE customers(
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address VARCHAR(200),
    city VARCHAR(80),
    state VARCHAR(80),
    country VARCHAR(80),
    pincode VARCHAR(10),
    pan_number VARCHAR(10),
    gst_number VARCHAR(15),
    aadhaar_number VARCHAR(12)
);
CREATE TABLE products(
    product_id INT PRIMARY KEY,
    product_name VARCHAR(120) NOT NULL,
    category VARCHAR(80),
    price DECIMAL(10,2)
);
CREATE TABLE orders(
    order_id INT PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id),
    product_id INT NOT NULL REFERENCES products(product_id),
    order_date DATE NOT NULL,
    amount DECIMAL(10,2)
);
""",
    "Banking Schema": """
CREATE TABLE accounts(
    account_id INT PRIMARY KEY,
    account_number VARCHAR(32) UNIQUE NOT NULL,
    ifsc_code VARCHAR(20),
    account_type VARCHAR(50),
    balance DECIMAL(12,2)
);
CREATE TABLE clients(
    client_id INT PRIMARY KEY,
    client_name VARCHAR(120) NOT NULL,
    client_email VARCHAR(120),
    phone VARCHAR(20),
    city VARCHAR(80),
    created_at DATE
);
CREATE TABLE transactions(
    transaction_id INT PRIMARY KEY,
    account_id INT NOT NULL REFERENCES accounts(account_id),
    transaction_date DATE,
    amount DECIMAL(10,2),
    transaction_type VARCHAR(50)
);
CREATE TABLE account_holders(
    holder_id INT PRIMARY KEY,
    account_id INT NOT NULL REFERENCES accounts(account_id),
    client_id INT NOT NULL REFERENCES clients(client_id)
);
""",
    "HR Management Schema": """
CREATE TABLE employees(
    employee_id INT PRIMARY KEY,
    first_name VARCHAR(80),
    last_name VARCHAR(80),
    email VARCHAR(120),
    phone VARCHAR(20),
    department VARCHAR(80),
    designation VARCHAR(80),
    salary INT,
    company_name VARCHAR(120),
    hire_date DATE
);
CREATE TABLE departments(
    department_id INT PRIMARY KEY,
    department_name VARCHAR(100)
);
CREATE TABLE employee_roles(
    role_id INT PRIMARY KEY,
    employee_id INT NOT NULL REFERENCES employees(employee_id),
    department_id INT NOT NULL REFERENCES departments(department_id),
    role_name VARCHAR(80)
);
""",
    "E-Commerce Schema": """
CREATE TABLE customers(
    customer_id INT PRIMARY KEY,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    signup_date DATE
);
CREATE TABLE products(
    product_id INT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    category VARCHAR(80),
    price DECIMAL(10,2) NOT NULL
);
CREATE TABLE orders(
    order_id INT PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    total_amount DECIMAL(10,2)
);
CREATE TABLE order_items(
    order_item_id INT PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id),
    product_id INT NOT NULL REFERENCES products(product_id),
    quantity INT NOT NULL,
    item_price DECIMAL(10,2)
);
""",
    "Hospital Schema": """
CREATE TABLE patients(
    patient_id INT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    date_of_birth DATE,
    phone VARCHAR(40),
    city VARCHAR(80)
);
CREATE TABLE doctors(
    doctor_id INT PRIMARY KEY,
    name VARCHAR(120),
    specialty VARCHAR(80)
);
CREATE TABLE appointments(
    appointment_id INT PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES patients(patient_id),
    doctor_id INT NOT NULL REFERENCES doctors(doctor_id),
    appointment_date DATE,
    notes TEXT
);
CREATE TABLE treatments(
    treatment_id INT PRIMARY KEY,
    appointment_id INT NOT NULL REFERENCES appointments(appointment_id),
    treatment_description TEXT,
    cost DECIMAL(10,2)
);
""",
    "College Management Schema": """
CREATE TABLE students(
    student_id INT PRIMARY KEY,
    first_name VARCHAR(80),
    last_name VARCHAR(80),
    email VARCHAR(100),
    city VARCHAR(80)
);
CREATE TABLE courses(
    course_id INT PRIMARY KEY,
    course_name VARCHAR(120),
    credit_hours INT
);
CREATE TABLE enrollments(
    enrollment_id INT PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(student_id),
    course_id INT NOT NULL REFERENCES courses(course_id),
    grade VARCHAR(10)
);
""",
    "Library Management Schema": """
CREATE TABLE books(
    book_id INT PRIMARY KEY,
    title VARCHAR(150),
    author VARCHAR(120),
    isbn VARCHAR(40)
);
CREATE TABLE members(
    member_id INT PRIMARY KEY,
    full_name VARCHAR(120),
    phone VARCHAR(20),
    membership_date DATE
);
CREATE TABLE loans(
    loan_id INT PRIMARY KEY,
    member_id INT NOT NULL REFERENCES members(member_id),
    book_id INT NOT NULL REFERENCES books(book_id),
    loan_date DATE,
    due_date DATE
);
""",
    "Hotel Booking Schema": """
CREATE TABLE guests(
    guest_id INT PRIMARY KEY,
    name VARCHAR(120),
    email VARCHAR(120),
    phone VARCHAR(40),
    city VARCHAR(80)
);
CREATE TABLE rooms(
    room_id INT PRIMARY KEY,
    room_number VARCHAR(20),
    room_type VARCHAR(80)
);
CREATE TABLE bookings(
    booking_id INT PRIMARY KEY,
    guest_id INT NOT NULL REFERENCES guests(guest_id),
    room_id INT NOT NULL REFERENCES rooms(room_id),
    check_in DATE,
    check_out DATE,
    amount DECIMAL(10,2)
);
""",
}


def rerun_app() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


def init_state() -> None:
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, dict) else value


def clear_generated_state() -> None:
    st.session_state.metadata = None
    st.session_state.table_counts = {}
    st.session_state.generation_result = {}
    st.session_state.validation_summary = {}
    st.session_state.preview_dataframes = {}


def reset_workspace() -> None:
    for key, value in SESSION_DEFAULTS.items():
        st.session_state[key] = value.copy() if isinstance(value, dict) else value


def load_sample_schema(sql: str) -> None:
    st.session_state.schema_text = sql.strip()
    clear_generated_state()


def load_manual_schema() -> None:
    clear_generated_state()


def draw_relationship_graph(metadata: SchemaMetadata) -> None:
    graph = nx.DiGraph()
    for table_name, table in metadata.tables.items():
        graph.add_node(table_name)
        for column in table.columns:
            if column.foreign_key:
                parent_table, _ = column.foreign_key
                graph.add_edge(parent_table, table_name)

    if graph.number_of_nodes() == 0:
        st.info("No tables available for graph rendering.")
        return

    fig, ax = plt.subplots(figsize=(8, 4.5))
    pos = nx.spring_layout(graph, seed=42)
    nx.draw_networkx_nodes(graph, pos, node_color="#D8F3DC", edgecolors="#1B4332", node_size=1800, ax=ax)
    nx.draw_networkx_edges(graph, pos, arrows=True, arrowstyle="-|>", edge_color="#457B9D", width=1.8, ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=9, font_weight="bold", ax=ax)
    ax.set_axis_off()
    st.pyplot(fig, clear_figure=True)


def parse_current_schema() -> None:
    schema_text = st.session_state.schema_text.strip()
    if not schema_text:
        st.error("Paste or load a SQL schema before analysis.")
        return

    try:
        metadata = parse_schema(schema_text)
    except Exception as error:
        st.error(f"Failed to parse schema: {error}")
        return

    if not metadata.tables:
        st.error("No CREATE TABLE statements were detected.")
        return

    st.session_state.metadata = metadata
    st.session_state.generation_result = {}
    st.session_state.preview_dataframes = {}
    st.session_state.validation_summary = {}
    st.success("Schema parsed successfully.")
    try:
        if ai_layer.is_enabled():
            st.session_state.ai_insights = ai_layer.analyze_schema(metadata)
        else:
            st.session_state.ai_insights = None
    except Exception:
        st.session_state.ai_insights = None


def generate_current_data(metadata: SchemaMetadata) -> None:
    with st.spinner("Generating schema-aware Indian realistic data..."):
        progress_bar = st.progress(0)
        progress_bar.progress(15)
        generated_rows = generate_data(metadata, st.session_state.table_counts, st.session_state.dataset_type)
        progress_bar.progress(45)
        dataframes = build_dataframes(metadata, generated_rows)
        progress_bar.progress(70)

        issues = validate_data(metadata, dataframes)
        if issues:
            fixed_dfs, repaired_issues = auto_fix_data(metadata, dataframes)
            if not repaired_issues:
                dataframes = fixed_dfs
                issues = {}
                st.success("Auto-correction applied successfully.")
            else:
                issues = repaired_issues
                st.warning("Validation found issues after repair.")

        progress_bar.progress(95)
        # Store results first
        st.session_state.generation_result = generated_rows
        st.session_state.preview_dataframes = dataframes
        st.session_state.validation_summary = build_validation_summary(issues)

        # AI quality review (sample-based) - additive and only when enabled
        try:
            if ai_layer.is_enabled():
                sample_rows = {}
                for tname, df in dataframes.items():
                    sample_rows[tname] = df.head(20).to_dict(orient="records")
                st.session_state.ai_quality = ai_layer.review_generated_data(metadata, sample_rows)
            else:
                st.session_state.ai_quality = None
        except Exception:
            st.session_state.ai_quality = None
        progress_bar.progress(100)
        st.success("Data generation completed.")


st.set_page_config(page_title="Schema Aware Test Data Generator", layout="wide")

st.markdown(
    """
    <style>
    body { background-color: #F7F9FB; color: #111827; }
    .block-container { padding: 1.25rem 2rem 2rem 2rem; max-width: 1600px; }
    .stButton > button, .stDownloadButton > button {
        background-color: #4DA3D9;
        color: #111827;
        font-weight: 700;
        border-radius: 0.45rem;
        border: 1px solid #2F7DA8;
    }
    .section-header {
        font-size: 1.55rem;
        font-weight: 800;
        color: #111827;
        margin-top: 1.5rem;
        margin-bottom: 0.3rem;
    }
    .section-subtitle {
        font-size: 0.95rem;
        color: #374151;
        margin-bottom: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

init_state()

st.markdown(
    """
    <div style="text-align:center; padding:0.75rem 0 0.25rem 0;">
        <h1 style="font-size:3rem; font-weight:900; color:#111827; margin-bottom:0.25rem;">
            Schema Aware Test Data Generator
        </h1>
        <p style="font-size:1.05rem; color:#374151; max-width:950px; margin:0 auto;">
            Indian realistic synthetic data with schema analysis, referential integrity, validation, preview, and export.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

st.markdown("<div class='section-header'>Demo Schemas</div>", unsafe_allow_html=True)
demo_cols = st.columns(4)
for idx, (schema_name, sql) in enumerate(SAMPLE_SCHEMAS.items()):
    if demo_cols[idx % 4].button(schema_name, key=f"sample_{schema_name}"):
        load_sample_schema(sql)
        rerun_app()

st.markdown("<div class='section-header'>Schema Workspace</div>", unsafe_allow_html=True)
st.session_state.schema_text = st.text_area(
    "SQL CREATE TABLE statements",
    value=st.session_state.schema_text,
    height=260,
)

action_cols = st.columns([1, 1, 2])
if action_cols[0].button("Load Manual Schema"):
    load_manual_schema()
    st.success("Schema loaded. Click Analyze Schema to continue.")

if action_cols[1].button("Analyze Schema"):
    parse_current_schema()

with action_cols[2]:
    reset_confirmed = st.checkbox("Confirm workspace reset")
    if st.button("Clear / Reset Workspace"):
        if reset_confirmed:
            reset_workspace()
            st.success("Workspace reset successfully.")
            rerun_app()
        else:
            st.warning("Select the confirmation checkbox before resetting.")

if st.session_state.metadata:
    metadata: SchemaMetadata = st.session_state.metadata
    summary = summarize_schema(metadata)
    graph_summary = summarize_graph(metadata)

    st.markdown("<div class='section-header'>Schema Intelligence</div>", unsafe_allow_html=True)
    metric_cols = st.columns(5)
    metric_cols[0].metric("Tables", summary["total_tables"])
    metric_cols[1].metric("Columns", summary["total_columns"])
    metric_cols[2].metric("Primary Keys", summary["total_primary_keys"])
    metric_cols[3].metric("Foreign Keys", summary["total_foreign_keys"])
    metric_cols[4].metric("Relationships", graph_summary["relationship_count"])

    rel_col, graph_col = st.columns([1, 1])
    with rel_col:
        st.markdown("**Tables**")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "table": table.name,
                        "columns": len(table.columns),
                        "primary_keys": sum(1 for col in table.columns if col.primary_key),
                        "foreign_keys": sum(1 for col in table.columns if col.foreign_key),
                    }
                    for table in metadata.tables.values()
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("**Dependency Order**")
        st.write(" -> ".join(graph_summary["dependency_order"]))
        if graph_summary["relationship_map"]:
            st.markdown("**Relationships**")
            for relation in graph_summary["relationship_map"]:
                st.write(f"- {relation}")
    with graph_col:
        st.markdown("**Relationship Graph**")
        draw_relationship_graph(metadata)

    # AI Insights (additive only)
    st.markdown("<div class='section-header'>AI Insights</div>", unsafe_allow_html=True)
    ai_insights = st.session_state.get("ai_insights")
    ai_quality = st.session_state.get("ai_quality")
    if ai_insights:
        insight_cols = st.columns(3)
        insight_cols[0].markdown(f"**Business Domain**\n\n{ai_insights.get('business_domain', '')}")
        insight_cols[1].markdown(f"**System Type**\n\n{ai_insights.get('system_type', '')}")
        insight_cols[2].markdown(f"**Complexity Score**\n\n{ai_insights.get('complexity_score', '')}")

        st.markdown("**Schema Description**")
        st.write(ai_insights.get("schema_description", ""))

        st.markdown("**Semantic Mapping (sample)**")
        # show up to 12 mappings
        mappings = ai_insights.get("semantic_mapping", {})
        sample_items = list(mappings.items())[:12]
        st.table([{"column": k, "label": v} for k, v in sample_items])
    else:
        st.info("AI Insights disabled. Set OPENAI_API_KEY or GEMINI_API_KEY to enable optional insights.")

    if ai_quality:
        st.markdown("**AI Data Quality Summary**")
        score = ai_quality.get("data_quality_score")
        st.write(f"Score: {score}" if score is not None else "Score: N/A")
        st.write(ai_quality.get("validation_summary", ""))

    st.markdown("<div class='section-header'>Record Counts</div>", unsafe_allow_html=True)
    count_cols = st.columns(3)
    for idx, table_name in enumerate(summary["tables"]):
        st.session_state.table_counts[table_name] = count_cols[idx % 3].number_input(
            f"{table_name} rows",
            min_value=1,
            max_value=100000,
            value=int(st.session_state.table_counts.get(table_name, 50)),
            step=1,
        )

    st.markdown("<div class='section-header'>Generation Mode</div>", unsafe_allow_html=True)
    st.session_state.dataset_type = st.radio(
        "Dataset type",
        DATASET_TYPES,
        index=DATASET_TYPES.index(st.session_state.dataset_type),
        horizontal=True,
    )

    if st.session_state.dataset_type == "Large Dataset":
        for table_name in summary["tables"]:
            st.session_state.table_counts[table_name] = max(500, st.session_state.table_counts[table_name])
    elif st.session_state.dataset_type == "Stress Testing Dataset":
        for table_name in summary["tables"]:
            st.session_state.table_counts[table_name] = max(1000, st.session_state.table_counts[table_name])
    elif st.session_state.dataset_type == "Custom Dataset":
        custom_cols = st.columns(3)
        custom_cols[0].slider("Null percentage", min_value=0, max_value=75, value=10)
        custom_cols[1].slider("Duplicate percentage", min_value=0, max_value=30, value=5)
        custom_cols[2].selectbox("Variation level", ["Low", "Medium", "High"], index=1)

    st.markdown("<div class='section-header'>Generate</div>", unsafe_allow_html=True)
    if st.button("Generate Test Data"):
        generate_current_data(metadata)

if st.session_state.preview_dataframes:
    validation_summary = st.session_state.validation_summary

    st.markdown("<div class='section-header'>Validation Results</div>", unsafe_allow_html=True)
    validation_cols = st.columns(3)
    validation_cols[0].metric("Validation Passed", "Yes" if validation_summary.get("passed") else "No")
    validation_cols[1].metric("Issues Found", validation_summary.get("issue_count", 0))
    validation_cols[2].metric("Tables Generated", len(st.session_state.preview_dataframes))

    for table_name, table_issues in validation_summary.get("details", {}).items():
        st.markdown(f"**{table_name}**")
        for issue in table_issues:
            st.write(f"- {issue}")

    st.markdown("<div class='section-header'>Data Preview</div>", unsafe_allow_html=True)
    preview_tabs = st.tabs(list(st.session_state.preview_dataframes.keys()))
    for tab, table_name in zip(preview_tabs, st.session_state.preview_dataframes.keys()):
        with tab:
            df = st.session_state.preview_dataframes[table_name]
            st.write(f"Rows: {len(df)} | Columns: {len(df.columns)}")
            st.dataframe(df.head(20), use_container_width=True)

    st.markdown("<div class='section-header'>Download Center</div>", unsafe_allow_html=True)
    csv_files = generate_csv_bytes(st.session_state.preview_dataframes)
    sql_files = generate_sql_inserts(st.session_state.metadata, st.session_state.preview_dataframes)
    zip_bytes = build_zip_package(
        st.session_state.metadata,
        st.session_state.preview_dataframes,
        st.session_state.validation_summary,
    )

    download_cols = st.columns(3)
    for idx, (name, content) in enumerate(csv_files.items()):
        download_cols[idx % 3].download_button(
            f"Download {name}",
            data=content,
            file_name=name,
            mime="text/csv",
        )
    st.download_button(
        "Download SQL Inserts",
        data="\n".join(sql_files.values()),
        file_name="generated_inserts.sql",
        mime="text/sql",
    )
    st.download_button(
        "Download ZIP Package",
        data=zip_bytes,
        file_name="schema_test_data_package.zip",
        mime="application/zip",
    )
elif not st.session_state.metadata:
    st.info("Load a demo schema or paste your SQL schema, then click Analyze Schema.")
